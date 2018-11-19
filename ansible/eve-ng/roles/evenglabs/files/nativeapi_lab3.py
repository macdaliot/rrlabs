#!/usr/bin/env python3

import json, requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

apic = '1.1.1.1'
username = 'admin'
password = 'password'

url = 'https://{}/api/aaaLogin.json?gui-token-request=yes'.format(apic)
payload = {'aaaUser':{'attributes':{'name': username,'pwd': password}}}
r = requests.post(url, verify = False, data = json.dumps(payload))
response = r.json()
response_code = r.status_code
cookies = r.cookies
token = response['imdata'][0]['aaaLogin']['attributes']['urlToken']

url = 'https://{}/api/class/fvTenant.json?challenge={}'.format(apic, token)
r = requests.get(url, verify = False, cookies = cookies)
response = r.json()
response_code = r.status_code
print(response)
