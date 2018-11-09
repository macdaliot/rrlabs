#!/usr/bin/env python3

cfg = """
hostname R3
username admin privilege 15 password cisco
interface Ethernet0/3
 ip address dhcp
 no shutdown
ip domain name example.com
crypto key generate rsa modulus 1024
ip ssh version 2
ip scp server enable
line vty 0 4
 login local
  transport input ssh
"""

print('configure the router with the following configuration:')
print(cfg)

import napalm, sys
driver = napalm.get_network_driver('ios')
device = driver(hostname = '192.0.2.18', username = 'admin', password = 'cisco', optional_args = {'port': 22})
device.open()
print(device.get_facts())
print(device.get_interfaces())
print(device.get_interfaces_ip())
device.close()
