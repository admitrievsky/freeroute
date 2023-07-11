Freeroute: simple traffic router
===============================

Freeroute is a traffic router which can direct traffic to different gateways based on destination domain.
It is designed to be used in conjunction with a VPN client such as OpenVPN, to allow traffic to be routed to the VPN or directly to the internet.

Freeroute provides it's own DNS server which can be used to resolve domains to IP addresses.
The IP addresses are then used to determine which gateway to route the traffic to.

Freeroute is designed to be run on a machine within a local network. 
If the machine is a virtual machine, it should be configured to use **bridged networking**.

Free means free as in **freedom**, not free as in beer.

Installation
------------

### Automatic installation


There is an install script which will install Freeroute and configure it to run on startup. 
The install script will also install and configure OpenVPN client.


It is designed to be run on a **fresh** install of Debian 11 or 12. 

It configured to run as a non-root user with sudo privileges.

To install Freeroute, do the following steps:
1. Download the latest release from https://github.com/admitrievsky/freeroute/releases/latest
2. Extract the archive `tar -xzf freeroute.tar.gz`
3. Run the install script:
```
sudo ./install.sh <network interface> <openVPN config file>
-- or --
sudo ./install.sh <network interface> <openVPN config file> -u <username> -p <password>
```
where
* `<network interface>` is the primary network interface (e.g. eth0)
* `<openVPN config file>` is the OpenVPN config file to use
* `<username>` and `<password>` is the username for the VPN. This is optional and only required if the VPN requires authentication.

### Manual installation

The release archive could be run directly without installation.

1. Install python dependencies with poetry `poetry install`
2. In the `freeroute` directory, put `config.yaml`. 
Example config file will be created on the first run.
See [config.py](service/src/config.py) for more information.
The script runs DNS service on port 5553 by default, but it could be configured to run on port 53 if run as root.
3. Configure domain lists.
4. Run `python3 service/main.py` to start the service.

Usage
-----
Configure your local machines to use your machine with Freeroute as a DNS server and gateway.

Visit `http://<freeroute-host>:8080/index.html` to see the web interface.

