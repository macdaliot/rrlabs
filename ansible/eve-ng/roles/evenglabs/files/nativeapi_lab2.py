#!/usr/bin/env python3

cfg = """
feature nxapi
nxapi https port 8443
boot nxos bootflash:///nxos.7.0.3.I7.1.bin
interface mgmt0
 ip add dhcp
 no shutdown
"""

print('configure each router with the following configuration:')
print(cfg)

import json, requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://192.0.2.30:8443/api/aaaLogin.json?gui-token-request=yes'
payload = {"aaaUser":{"attributes":{"name": "admin","pwd": "cisco"}}}
r = requests.post(url, verify = False, data = json.dumps(payload))
response = r.json()
response_code = r.status_code
cookies = r.cookies
token = response['imdata'][0]['aaaLogin']['attributes']['urlToken']

url = 'https://192.0.2.30:8443/api/node/class/l1PhysIf.json?challenge={}'.format(token)
r = requests.get(url, verify = False, cookies = cookies)
response = r.json()
response_code = r.status_code

print(response)
