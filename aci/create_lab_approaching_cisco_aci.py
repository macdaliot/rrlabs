#!/usr/bin/env python3

""" Create Cisco ACI environment """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20180320'

import ipaddress, json, logging, random, requests, string, sys, urllib3
from openpyxl import load_workbook
from functions import *

urllib3.disable_warnings()
logging.basicConfig(level = logging.INFO)

# Variables
total_users = 10
user_prefix = 'labuser'

# Reading options
username, password, apic_host = checkOpts()

# Logging in
token, cookies, response_code = login(username = username, password = password, apic_host = apic_host)
if token:
    logging.info('login to the APIC successfully ({})'.format(response_code))
else:
    logging.error('failed to login to the APIC ({})'.format(response_code))
    sys.exit(255)

# Adding default policies
if addDefaultPolicies(apic_host = apic_host, token = token, cookies = cookies):
    logging.info('added default policies for fabric and common tenant')
else:
    logging.error('failed to add default policies for fabric and common tenant')
    sys.exit(255)

# Add demonstrative tenant
tenant_name = 'tenant999'
tenant_description = 'Demonstrative tenant'
response_code, response = addTenant(apic_host = apic_host, token = token, cookies = cookies, name = tenant_name, description = tenant_description)
if response_code == 200:
    logging.info('added tenant "{}" ({})'.format(tenant_name, response_code))
else:
    logging.error('failed to add tenant "{}" ({})'.format(tenant_name, response_code))
    logging.error(response)
    sys.exit(255)

# Add demonstrative VRF
vrf_name = 'vrf1'
response_code, response = addVRF(apic_host = apic_host, token = token, cookies = cookies, tenant_name = tenant_name, name = vrf_name, description = 'Default VRF for tenant {}'.format(tenant_name))
if response_code == 200:
    logging.info('added VRF "{}:{}" ({})'.format(tenant_name, vrf_name, response_code))
else:
    logging.error('failed to add VRF "{}:{}" ({})'.format(tenant_name, vrf_name, response_code))
    logging.error(response)
    sys.exit(255)

# Add demonstrative BDs
bds = {
    'dmz': 'DMZ network for webservers',
    'app': 'Network for servers',
    'client': 'Network for simulate external users'
}
for bd_name, bd_description in bds.items():
    response_code, response = addBridgeDomain(apic_host = apic_host, token = token, cookies = cookies, tenant_name = tenant_name, name = bd_name, description = bd_description, igmp_snooping = False, vrf = vrf_name)
    if response_code == 200:
        logging.info('added bridge domain "{}:{}" ({})'.format(tenant_name, bd_name, response_code))
    else:
        logging.error('failed to add bridge domain "{}:{}" ({})'.format(tenant_name, bd_name, response_code))
        logging.error(response)
        sys.exit(255)

# Create users
users = {}
for x in range(1, total_users + 1):
    lab_username = '{}{}'.format(user_prefix, x)
    lab_password = ''.join(random.choices(string.ascii_uppercase, k = 3) + random.choices(string.ascii_lowercase, k = 3) + random.choices(string.digits, k = 2))
    response_code, response = addUser(apic_host = apic_host, token = token, cookies = cookies, username = lab_username, password = lab_password)
    if response_code == 200:
        logging.info('added user "{}" with password "{}"'.format(lab_username, lab_password))
        users[lab_username] = {
            'password': lab_password
        }
    else:
        logging.error('failed to add user "{}" with password "{}"'.format(lab_username, lab_password))
        logging.error(response)
        sys.exit(255)

print(users)
