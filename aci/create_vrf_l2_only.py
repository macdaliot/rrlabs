#!/usr/bin/env python3
""" Create VRF L2 Only """
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
vrf_name = None
vrf_description = None
tenat = None

def usage_local():
    print('    -t tenant      Tenant name')
    print('    -n vrfname     VRF name')
    print('    -i description VRF description')

    sys.exit(255)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'du:p:h:n:i:')
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
        tenant = arg
    elif opt == '-n':
        vrf_name = arg
    elif opt == '-i':
        vrf_description = arg
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
if not tenant:
    logging.error('Tenant not set')
    usage()
    usage_local()
    sys.exit(255)
if not vrf_name:
    logging.error('VRF name not set')
    usage()
    usage_local()
    sys.exit(255)
if not vrf_description:
    vrf_description = 'VRF {} (L2 only)'.format(vrf_name)

login_url = 'https://{}/api/aaaLogin.json?gui-token-request=yes'.format(apic_host)

token, cookies, response_code = login(url = login_url, username = username, password = password)

if response_code != 200:
    logging.error('failed to login')
    sys.exit(1)

data = {
	"fvCtx": {
		"attributes": {
			"bdEnforcedEnable": "no",
			"descr": "{}".format(vrf_description),
			"dn": "uni/tn-{}/ctx-{}".format(tenant_name. vrf_name),
			"knwMcastAct": "permit",
			"pcEnfDir": "ingress",
			"pcEnfPref": "unenforced"
		}
	}
}
url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(data))
response = r.json()
response_code = r.status_code
if response_code != 200:
    logging.error('failed to add L2 only VRF "{}"'.format(vrf_name))
