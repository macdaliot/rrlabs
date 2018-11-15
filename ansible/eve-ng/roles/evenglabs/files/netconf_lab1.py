#!/usr/bin/env python3
import sys
from ncclient import manager

cfg = """
hostname R3
username admin privilege 15 password cisco
interface GigabitEthernet4
 ip address dhcp
 no shutdown
ip domain name example.com
netconf-yang
"""

print('configure the router with the following configuration:')
print(cfg)

with manager.connect(host = '192.0.2.29', port = 830, username = 'admin', password = 'cisco', hostkey_verify = False, allow_agent = False, look_for_keys = False) as m:
    result = m.get_config(source = 'running').data_xml
    print(result)

