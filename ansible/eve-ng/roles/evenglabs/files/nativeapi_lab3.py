#!/usr/bin/env python3

import json, requests, urllib3
urllib3.disable_warnings()
url = 'https://172.25.82.1/api/aaaLogin.json?gui-token-request=yes'
payload = {"aaaUser":{"attributes":{"name": "admin","pwd": "cisco"}}}
r = requests.post(url, verify = False, data = json.dumps(payload))
response = r.json()
response_code = r.status_code
cookies = r.cookies
token = response['imdata'][0]['aaaLogin']['attributes']['urlToken']

url = 'https://172.25.82.1/api/class/fvTenant.json?challenge={}'.format(token)
r = requests.get(url, verify = False, cookies = cookies)
response = r.json()
response_code = r.status_code
print(response)
