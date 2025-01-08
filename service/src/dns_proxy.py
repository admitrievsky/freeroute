# based on https://github.com/uktrade/dns-rewrite-proxy

import logging
import socket
import string
from asyncio import (
    CancelledError,
    Queue,
    create_task,
    get_running_loop,
)
from enum import (
    IntEnum,
)
from random import (
    choices,
)
from typing import Awaitable, Callable, Any

from aiodnsresolver import (
    RESPONSE,
    TYPES,
    DnsRecordDoesNotExist,
    DnsResponseCode,
    Message,
    Resolver,
    ResourceRecord,
    ResolverLoggerAdapter,
    pack,
    parse,
    recvfrom,
)

from config import get_config


def get_socket_default():
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind(('', get_config().networking.dns_port))
    return sock


def get_resolver_default():
    return Resolver()


class DnsProxyLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return \
            ('[dnsproxy] %s' % (msg,), kwargs) if not self.extra else \
                ('[dnsproxy:%s] %s' % (
                    ','.join(str(v) for v in self.extra.values()), msg), kwargs)


def get_logger_adapter_default(extra):
    return DnsProxyLoggerAdapter(logging.getLogger('dnsrewriteproxy'), extra)


def get_resolver_logger_adapter_default(parent_adapter):
    def _get_resolver_logger_adapter_default(dns_extra):
        return ResolverLoggerAdapter(parent_adapter, dns_extra)

    return _get_resolver_logger_adapter_default


def DnsProxy(
        get_resolver=get_resolver_default,
        get_logger_adapter=get_logger_adapter_default,
        get_resolver_logger_adapter=get_resolver_logger_adapter_default,
        get_socket=get_socket_default, num_workers=1000,
        resolved_callback: Callable[[Any, Any], Awaitable[Any]] =
        lambda domain, ip: None
):
    class ERRORS(IntEnum):
        FORMERR = 1
        SERVFAIL = 2
        NXDOMAIN = 3
        REFUSED = 5

    loop = get_running_loop()
    logger = get_logger_adapter({})
    request_id_alphabet = string.ascii_letters + string.digits

    # The "main" task of the server: it receives incoming requests and puts
    # them in a queue that is then fetched from and processed by the proxy
    # workers

    async def server_worker(sock, resolve, stop):
        upstream_queue = Queue(maxsize=num_workers)

        # We have multiple upstream workers to be able to send multiple
        # requests upstream concurrently
        upstream_worker_tasks = [
            create_task(upstream_worker(sock, resolve, upstream_queue))
            for _ in range(0, num_workers)]

        try:
            while True:
                logger.info('Waiting for next request')
                request_data, addr = (await recvfrom(loop, [(sock, None)], 512))[1]
                request_logger = get_logger_adapter(
                    {'dnsrewriteproxy_requestid': ''.join(
                        choices(request_id_alphabet, k=8))})
                request_logger.info('Received request from %s', addr)
                await upstream_queue.put((request_logger, request_data, addr))
        finally:
            logger.info('Stopping: waiting for requests to finish')
            await upstream_queue.join()

            logger.info('Stopping: cancelling workers...')
            for upstream_task in upstream_worker_tasks:
                upstream_task.cancel()
            for upstream_task in upstream_worker_tasks:
                try:
                    await upstream_task
                except CancelledError:
                    pass
            logger.info('Stopping: cancelling workers... (done)')

            logger.info('Stopping: final cleanup')
            await stop()
            logger.info('Stopping: done')

    async def upstream_worker(sock, resolve, upstream_queue):
        while True:
            request_logger, request_data, addr = await upstream_queue.get()

            try:
                request_logger.info('Processing request')
                response_data = await get_response_data(request_logger, resolve,
                                                        request_data, addr)
                # Sendto for non-blocking UDP sockets cannot raise a BlockingIOError
                # https://stackoverflow.com/a/59794872/1319998
                sock.sendto(response_data, addr)
            except Exception:
                request_logger.exception('Error processing request')
            finally:
                request_logger.info('Finished processing request')
                upstream_queue.task_done()

    async def get_response_data(request_logger, resolve, request_data, addr):
        # This may raise an exception, which is handled at a higher level.
        # We can't [and I suspect shouldn't try to] return an error to the
        # client, since we're not able to extract the QID, so the client won't
        # be able to match it with an outgoing request
        query = parse(request_data)

        try:
            return pack(await proxy(request_logger, resolve, query, addr))
        except Exception:
            request_logger.exception('Failed to proxy %s', query)
            return pack(error(query, ERRORS.SERVFAIL))

    async def proxy(request_logger, resolve, query, addr):
        name_bytes = query.qd[0].name
        request_logger.info('Name: %s', name_bytes)

        name_str_lower = query.qd[0].name.lower().decode('idna')
        request_logger.info('Decoded: %s', name_str_lower)

        if query.qd[0].qtype != TYPES.A:
            request_logger.info('Unhandled query type: %s', query.qd[0].qtype)
            return error(query, ERRORS.REFUSED)

        try:
            ip_addresses = await resolve(
                name_str_lower, TYPES.A,
                get_logger_adapter=get_resolver_logger_adapter(request_logger))
        except DnsRecordDoesNotExist:
            request_logger.info('Does not exist')
            return error(query, ERRORS.NXDOMAIN)
        except DnsResponseCode as dns_response_code_error:
            request_logger.info('Received error from upstream: %s',
                                dns_response_code_error.args[0])
            return error(query, dns_response_code_error.args[0])

        request_logger.info('Resolved to %s', ip_addresses)
        now = loop.time()

        if resolved_callback is not None:
            await resolved_callback(addr, name_str_lower, ip_addresses)

        def ttl(ip_address):
            return int(max(0.0, ip_address.expires_at - now))

        response_records = tuple(
            ResourceRecord(name=name_bytes, qtype=TYPES.A,
                           qclass=1, ttl=ttl(ip_address),
                           rdata=ip_address.packed)
            for ip_address in ip_addresses
        )
        return Message(
            qid=query.qid, qr=RESPONSE, opcode=0, aa=0, tc=0, rd=0, ra=1, z=0,
            rcode=0,
            qd=query.qd, an=response_records, ns=(), ar=(),
        )

    async def start():
        # The socket is created synchronously and passed to the server worker,
        # so if there is an error creating it, this function will raise an
        # exception. If no exeption is raise, we are indeed listening#
        sock = get_socket()

        # The resolver is also created synchronously, since it can parse
        # /etc/hosts or /etc/resolve.conf, and can raise an exception if
        # something goes wrong with that
        resolve, clear_cache = get_resolver()

        async def stop():
            sock.close()
            await clear_cache()

        return create_task(server_worker(sock, resolve, stop))

    return start


def error(query, rcode):
    return Message(
        qid=query.qid, qr=RESPONSE, opcode=0, aa=0, tc=0, rd=0, ra=1, z=0,
        rcode=rcode,
        qd=query.qd, an=(), ns=(), ar=(),
    )
