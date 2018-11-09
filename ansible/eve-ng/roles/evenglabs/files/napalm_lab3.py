#!/usr/bin/env python3

cfg = """
hostname R3
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

print('configure the router with the following configuration:')
print(cfg)

import napalm, re,re, sys
config_lo2 = """interface Loopback2
 ip address 2.2.2.2 255.255.255.255
 no shutdown"""
driver = napalm.get_network_driver('ios')
device = driver(hostname = '192.0.2.18', username = 'admin', password = 'cisco', optional_args = {'port': 22, 'dest_file_system': 'unix:'})
device.open()
config = device.get_config()['running']
# Removing header
config = re.sub(re.compile(r'^Building configuration.*$[^!]*', re.MULTILINE), '', config)
# Replacing loopbacks
config = re.sub(re.compile(r'^interface Loopback*$[^!]*', re.MULTILINE), config_lo2, config)
device.load_replace_candidate(config = config)
device.commit_config()
device.close()
