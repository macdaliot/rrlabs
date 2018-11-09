#!/usr/bin/env python3
import re, sys
from nornir.core import InitNornir
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.connections import napalm_connection
from nornir.plugins.tasks.networking import napalm_configure
from nornir.plugins.tasks.networking import napalm_get

config_lo = """interface Loopback123
  ip address 123.123.123.123 255.255.255.255
  no shutdown
"""

def load_data(task):
    config = task.run(task = napalm_get, getters = ['get_config']).result['get_config']['running']
    config = re.sub(re.compile(r'^Building configuration.*$[^!]*', re.MULTILINE), '', config)
    if 'interface Loopback123' not in config:
        config = re.sub(re.compile(r'^interface Ethernet0/0', re.MULTILINE), config_lo + 'interface Ethernet0/0', config)
        task.run(task = napalm_connection, name = 'Setting up NAPALM', timeout = 60, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
        task.run(task = napalm_configure, configuration = config, replace = True)

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

nr = InitNornir(host_file = 'nornir_lab1_hosts.yaml', group_file = 'nornir_lab1_groups.yaml', num_workers = 20)
command = 'show cdp neighbors detail'
result = nr.run(load_data)
print_result(result)

