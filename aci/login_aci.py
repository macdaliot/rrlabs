#!/usr/bin/env python3
""" Login to Cisco ACI """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20180320'

import json, logging, requests, urllib3, sys

urllib3.disable_warnings()

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('')
    print('Options:')
    print('    -d             enable debug')
    print('    -u username    the username for the APIC controller')
    print('    -p password    the password for the APIC controller')
    print('    -h hostname    the hostname or IP of the APIC controller')

def login(url = None, username = None, password = None):
    if not url or not username or not password:
        return None, False, None
    payload = {
      "aaaUser": {
        "attributes": {
          "name": username,
          "pwd": password
        }
      }
    }
    r = requests.post(url, verify = False, data = json.dumps(payload))
    response = r.json()
    response_code = r.status_code
    cookies = r.cookies
    try:
        token = response['imdata'][0]['aaaLogin']['attributes']['urlToken']
    except Exception as err:
        token = None
        pass
    return token, cookies, response_code
