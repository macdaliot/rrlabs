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

standard_filter = """<interfaces xmlns="http://openconfig.net/yang/interfaces"><interface><name>GigabitEthernet4</name></interface></interfaces>"""
cisco_filter = """<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native"><interface><GigabitEthernet><name>4</name></GigabitEthernet></interface></native>"""

"""
On previous version the following filter must be used:
<native xmlns="http://cisco.com/ns/yang/ned/ios">
    ...
</native>
"""

with manager.connect(host = '192.0.2.29', port = 830, username = 'admin', password = 'cisco', hostkey_verify = False, allow_agent = False, look_for_keys = False) as m:
    standard_result = m.get(('subtree', standard_filter))
    cisco_result = m.get(('subtree', cisco_filter))
    print(standard_result)
    print('---')
    print(cisco_result)
