#!/usr/bin/env python3

cfg = """
hostname <router name>
username admin privilege 15 password cisco
interface Ethernet0/3
 ip address dhcp
 no shutdown
interface Ethernet0/0
 no shutdown
ip domain name example.com
crypto key generate rsa modulus 1024
ip ssh version 2
line vty 0 4
 login local
  transport input ssh
"""

print('configure each router with the following configuration:')
print(cfg)

import netmiko, sys
device = {
    'device_type': 'cisco_ios',
    'ip': '192.0.2.16',
    'username': 'admin',
    'password': 'cisco',
    'port' : 22,
    'verbose': False
}
net_connect = netmiko.ConnectHandler(**device)
output = net_connect.send_command('show cdp neighbors detail')
print(output)
