from dataclasses import dataclass

import netifaces as netifaces

from config import get_config


@dataclass
class NetworkInterface:
    name: str
    ip: str


def get_available_interfaces() -> list[NetworkInterface]:
    know_ifaces = [iface for iface in netifaces.interfaces() if
                   iface not in get_config().networking.ignore_interfaces]

    result = []
    for iface in know_ifaces:
        addresses = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addresses:
            for address in addresses[netifaces.AF_INET]:
                result.append(NetworkInterface(name=iface, ip=address['addr']))

    return result
