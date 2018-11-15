#!/usr/bin/env python3
import json, requests, sys, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cfg = """
hostname R3
username admin privilege 15 password cisco
interface GigabitEthernet4
 ip address dhcp
 no shutdown
ip domain name example.com
restconf
ip http secure-server
"""

print('configure the router with the following configuration:')
print(cfg)

url = 'https://192.0.2.29/restconf/data/Cisco-IOS-XE-native:native/interface/GigabitEthernet=4'
auth = requests.auth.HTTPBasicAuth('admin', 'cisco')
headers = {'Accept': 'application/yang-data+json'}
r = requests.get(url, verify = False, auth = auth, headers = headers)
response_code = r.status_code
response = r.json()
print(response)
