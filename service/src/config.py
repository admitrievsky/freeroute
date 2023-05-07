import os
from typing import Optional

import yaml
from pydantic import BaseModel


class InterfaceConfig(BaseModel):
    name: str
    ip: str


class NetworkingConfig(BaseModel):
    ignore_interfaces: list[str] = ['lo']

    default_gateway: InterfaceConfig = InterfaceConfig(name='eth0',
                                                       ip='192.168.1.1')
    tunnels: list[InterfaceConfig] = [InterfaceConfig(name='tun0',
                                                      ip='1.2.3.4')]


class Config(BaseModel):
    networking: NetworkingConfig = NetworkingConfig()


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
