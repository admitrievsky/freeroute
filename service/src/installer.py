import argparse
import os.path
import tempfile
from contextlib import contextmanager
from re import search
from subprocess import Popen, PIPE, call
from typing import TextIO, Optional


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CEND = '\033[0m'


def cprint(color, *args, **kwargs):
    print(color, end='')
    print(*args, **kwargs, end='')
    print(bcolors.CEND)


def run_command(*args):
    cprint(bcolors.OKGREEN, f'Executing command: {" ".join(args)}')
    result = call(args)
    if result != 0:
        cprint(bcolors.FAIL, f'Fail: {result}')
        exit(1)


def write_openvpn_config(input_file: str, output_file: TextIO,
                         auth_file_path: Optional[str],
                         strip_route_commands: bool):
    with open(input_file) as f:
        config = f.readlines()

    for line in config:
        if line.startswith('<ca'):
            if auth_file_path is not None:
                output_file.write(f'auth-user-pass {auth_file_path}\n')
            if strip_route_commands:
                output_file.write('route-noexec\n')
        output_file.write(line)


@contextmanager
def create_tmp_config(openvpn_config, username: Optional[str], password):
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as output:
        with tempfile.NamedTemporaryFile(mode='w', delete=True) as auth_file:
            if username is not None:
                auth_file.write(f'{username}\n{password}\n')
                auth_file.flush()
            write_openvpn_config(
                openvpn_config, output,
                auth_file.name if username is not None else None,
                strip_route_commands=False)
            output.flush()
            yield output.name


def get_openvpn_gateway(openvpn_config, username, password):
    with create_tmp_config(openvpn_config, username, password) as tmp_config:
        cprint(bcolors.OKGREEN, 'Trying to connect to OpenVPN and '
                                'determine gateway ip address ...')
        proc = Popen(['openvpn', '--config', tmp_config], stdout=PIPE,
                     bufsize=1, text=True)
        result = None
        for line in iter(proc.stdout.readline, ''):
            print(line, end='')
            if m := search(
                    r'net_route_v4_add: 0\.0\.0\.0/1 via (\d+\.\d+\.\d+\.\d+)',
                    line):
                proc.kill()
                result = m.group(1)
                proc.communicate()
                break
        if result is None:
            cprint(bcolors.FAIL, 'OpenVPN connection failed')
            exit(1)
        return result


def install_openvpn_config(openvpn_config, username, password):
    cprint(bcolors.OKGREEN, 'Installing openvpn config')

    config_dir = '/etc/openvpn/client'
    config_filename = os.path.basename(openvpn_config)
    config_path = os.path.join(config_dir, f'{config_filename}.conf')
    auth_file_path = None
    if username is not None:
        auth_filename = f'{config_filename}-auth'
        auth_file_path = os.path.join(config_dir, auth_filename)
        cprint(bcolors.OKGREEN, f'Creating auth file {auth_file_path}')
        with open(auth_file_path, 'w') as f:
            f.write(f'{username}\n{password}\n')
    cprint(bcolors.OKGREEN, f'Creating openvpn config {config_path}')
    with open(config_path, 'w') as f:
        write_openvpn_config(openvpn_config, f, auth_file_path,
                             strip_route_commands=True)
    run_command('systemctl', 'enable', 'openvpn-client@' + config_filename)
    run_command('systemctl', 'start', 'openvpn-client@' + config_filename)


def init_nftables(network_interface):
    cprint(bcolors.OKGREEN, 'Initializing nftables')
    cprint(bcolors.OKGREEN, 'Creating /etc/nftables.conf')
    with open('/etc/nftables.conf', 'w') as f:
        f.write(f"""#!/usr/sbin/nft -f

flush ruleset

table filter {{
        chain input {{
          type filter hook input priority -300;
          udp dport 53 udp dport set 5553;
        }}
        chain output {{
          type filter hook output priority 100;
          udp sport {{5553}} udp sport set 53;
        }}
}}

table ip nat {{
  chain postrouting {{
		type nat hook postrouting priority 100; policy accept;
		iif "{network_interface}" masquerade;
	}}
}}""")
    run_command('systemctl', 'enable', 'nftables')
    run_command('systemctl', 'start', 'nftables')


def init_python_service(user: str):
    cprint(bcolors.OKGREEN, 'Initializing python service')
    cprint(bcolors.OKGREEN, 'Creating /etc/systemd/system/freeroute.service')
    with open('/etc/systemd/system/freeroute.service', 'w') as f:
        f.write(f"""[Unit]
Description = Freeroute service
After = network.target

[Service]
Type = simple
ExecStart = {os.getcwd()}/.venv/bin/python service/main.py
User = {user}
Group = {user}
Restart = on-failure
SyslogIdentifier = freeroute
RestartSec = 5
TimeoutStartSec = infinity
WorkingDirectory = {os.getcwd()}

[Install]
WantedBy = multi-user.target
""")
    run_command('systemctl', 'enable', 'freeroute')
    run_command('systemctl', 'start', 'freeroute')


def generate_config(gateway_ip: str):
    cprint(bcolors.OKGREEN, f'Generating config file {os.getcwd()}/config.yaml')
    with open('config.yaml', 'w') as f:
        f.write(f"""external_domain_lists:
  - interface: tun0
    name: antifilter
    update_interval_hours: 1
    url: https://antifilter.download/list/domains.lst
networking:
  dns_port: 5553
  tunnels:
    - gateway_ip: {gateway_ip}
      name: tun0
""")


def init_forwarding():
    cprint(bcolors.OKGREEN, 'Adding forwarding rules to /etc/sysctl.conf')
    with open('/etc/sysctl.conf', 'a') as f:
        f.write('net.ipv4.ip_forward=1\n')
    cprint(bcolors.OKGREEN, 'Enabling forwarding')
    run_command('sysctl', '-w', 'net.ipv4.ip_forward=1')


def init_sudoers(user: str):
    cprint(bcolors.OKGREEN, 'Adding sudoers file')
    with open('/etc/sudoers.d/freeroute', 'w') as f:
        f.write(f"""{user} ALL=(ALL) NOPASSWD: /usr/sbin/ip""")


def get_user():
    try:
        return os.getlogin()
    except OSError:
        pass

    try:
        user = os.environ['USER']
    except KeyError:
        return getpass.getuser()

    if user == 'root':
        try:
            return os.environ['SUDO_USER']
        except KeyError:
            pass

        try:
            pkexec_uid = int(os.environ['PKEXEC_UID'])
            return pwd.getpwuid(pkexec_uid).pw_name
        except KeyError:
            pass

    return user


def fix_owner(user):
    cprint(bcolors.OKGREEN, 'Fixing owner')
    run_command('chown', '-R', f'{user}', os.getcwd())


def write_default_domain_lists():
    cprint(bcolors.OKGREEN, 'Writing default domain lists')
    with open('list_vpn.txt', 'w') as f:
        f.write("""applicationinsights.azure.com
azure-dns.com
bbc.co.uk
bbc.com
bbci.co.uk
bing.com
bingapis.com
cdninstagram.com
facebook.com
fbcdn.net
github.com
githubusercontent.com
instagram.com
intellij.net
jetbrains.com
licdn.com
linkedin.com
live.com
microsoft.com
microsoftonline.com
paypal.com
play.google.com
surfshark.com
t.co
twimg.com
twitter.com""")
    with open('list_force_default.txt', 'w') as f:
        f.write("""ggpht.com""")


def main():
    parser = argparse.ArgumentParser(prog='Freeroute installer')
    parser.add_argument('network_interface', help='Network interface to use')
    parser.add_argument('openvpn_config', help='OpenVPN config file')
    parser.add_argument('-u', '--username', help='Username for OpenVPN auth')
    parser.add_argument('-p', '--password', help='Password for OpenVPN auth')
    args = parser.parse_args()
    gateway_ip = get_openvpn_gateway(args.openvpn_config, args.username,
                                     args.password)
    cprint(bcolors.OKGREEN, f'OpenVPN gateway IP: {gateway_ip}')

    install_openvpn_config(args.openvpn_config, args.username, args.password)

    init_nftables(args.network_interface)
    init_forwarding()
    init_sudoers(get_user())

    generate_config(gateway_ip)
    write_default_domain_lists()
    fix_owner(get_user())

    init_python_service(get_user())


if __name__ == '__main__':
    main()
