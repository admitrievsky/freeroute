import os
from typing import Optional

import yaml
from pydantic import BaseModel


class InterfaceConfig(BaseModel):
    name: str
    gateway_ip: str

    def __hash__(self):
        return hash(self.name + self.gateway_ip)

    def __eq__(self, other):
        return self.name == other.name and self.gateway_ip == other.gateway_ip


class NetworkingConfig(BaseModel):
    ignore_interfaces: list[str] = ['lo']

    default_gateway: InterfaceConfig = InterfaceConfig(name='eth0',
                                                       gateway_ip='192.168.1.1')
    tunnels: list[InterfaceConfig] = [InterfaceConfig(name='tun0',
                                                      gateway_ip='1.2.3.4')]

    dns_port: int = 5553


class DomainList(BaseModel):
    name: str
    interface: str

    def __hash__(self):
        return hash(self.name + self.interface)

    def __eq__(self, other):
        return self.name == other.name and self.interface == other.interface


class ExternalDomainList(DomainList):
    url: str
    update_interval_hours: int


class Config(BaseModel):
    networking: NetworkingConfig = NetworkingConfig()
    external_domain_lists: list[ExternalDomainList] = [
        ExternalDomainList(
            name='antifilter',
            url='https://antifilter.download/list/domains.lst',
            update_interval_hours=1,
            interface='tun0'
        )
    ]
    ip_route_command: str = 'sudo ip route'


__config: Optional[Config] = None
__config_filename = os.getenv('CONFIG') or 'config.yaml'


def load_config() -> Optional[Config]:
    if os.path.exists(__config_filename):
        with open(os.getenv('CONFIG') or 'config.yaml') as f:
            return Config(**yaml.load(f, Loader=yaml.FullLoader))


def write_config():
    with open(__config_filename, 'w') as f:
        yaml.dump(__config.dict(), f)


def get_config() -> Config:
    global __config
    __config = __config or load_config()
    if __config is None:
        __config = Config()
        write_config()
    return __config
