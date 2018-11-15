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

headers = {
    'Accept': 'aplication/json',
    'Content-Type': 'application/json-rpc'
}

url = 'https://192.0.2.30:8443/ins'
payload = [{'jsonrpc':'2.0','method':'cli','params':{'cmd':'show interface status','version':1},'id':1}]
r = requests.post(url, verify = False, auth = requests.auth.HTTPBasicAuth('admin', 'cisco'), headers = headers, data = json.dumps(payload))
response = r.json()
response_code = r.status_code
print(response)

# curl can also be used:
# curl -k -X POST -u "admin:cisco" -H "Accept: aplication/json" -H "Content-Type: application/json-rpc" --data '[{"jsonrpc":"2.0","method:"cli","params":{"cmd":"show interface status","version":1},"id":1}]' "https://192.0.2.30:8443/ins"
