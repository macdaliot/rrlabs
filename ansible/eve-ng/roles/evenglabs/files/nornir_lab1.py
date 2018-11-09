#!/usr/bin/env python3

cfg = """
hostname <router name>
username admin privilege 15 password cisco
archive
 path unix:
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

print('configure each router with the following configuration:')
print(cfg)

import sys
from nornir.core import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command

nr = InitNornir(host_file = 'nornir_lab1_hosts.yaml', group_file = 'nornir_lab1_groups.yaml', num_workers = 20)
command = 'show cdp neighbors detail'
result = nr.run(task = netmiko_send_command, command_string = command, use_textfsm = True)
print('local_device;local_interface;remote_device;remote_link')
for device_name, device_output in result.items():
    for row in device_output.result:
        print('{};{};{};{}'.format(device_name, row['local_port'], row['destination_host'], row['remote_port']))
