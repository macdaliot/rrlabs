#!/usr/bin/env python3
""" Create Tenant """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20180320'

import getopt, logging, json, requests, sys, urllib3
from login_aci import *
urllib3.disable_warnings()

# Reading options
username = None
password = None
apic_host = None
tenants = []

def usage_local():
    print('    -t tenant      tenant name to be created (multiple occurrences are allowed)')
    sys.exit(255)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'du:p:h:t:')
except getopt.GetoptError as err:
    logging.error(err)
    usage()
    sys.exit(255)
for opt, arg in opts:
    if opt == '-d':
        logging.basicConfig(level = logging.DEBUG)
    elif opt == '-u':
        username = arg
    elif opt == '-p':
        password = arg
    elif opt == '-h':
        apic_host = arg
    elif opt == '-t':
        tenants.append(arg)
    else:
        assert False, 'unhandled option'

# Checking options
if username == None:
    logging.error('username not set')
    usage()
    sys.exit(255)
if password == None:
    logging.error('password not set')
    usage()
    sys.exit(255)
if apic_host == None:
    logging.error('APIC not set')
    usage()
    sys.exit(255)
if not tenants:
    logging.error('Tenant not set')
    usage()
    usage_local()
    sys.exit(255)

login_url = 'https://{}/api/aaaLogin.json?gui-token-request=yes'.format(apic_host)

token, cookies, response_code = login(url = login_url, username = username, password = password)

if response_code != 200:
    logging.error('failed to login')
    sys.exit(1)

for tenant in tenants:
    data = {
    	"fvTenant": {
    		"attributes": {
    			"descr": "Tenant {}".format(tenant),
    			"dn": "uni/tn-{}".format(tenant)
    		}
    	}
    }
    url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(data))
    response = r.json()
    response_code = r.status_code
    if response_code != 200:
        logging.error('failed to add tenant "{}"'.format(tenant))
