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

config =  """<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>
            <Loopback>
                <name>101</name>
                <ip><address><primary>
                    <address>10.101.1.1</address>
                    <mask>255.255.255.0</mask>
                </primary></address></ip>
            </Loopback>
        </interface>
    </native>
</config>"""

with manager.connect(host = '192.0.2.29', port = 830, username = 'admin', password = 'cisco', hostkey_verify = False, allow_agent = False, look_for_keys = False) as m:
    result = m.edit_config(target = 'running', config = config, default_operation = 'merge')
    print(result)

