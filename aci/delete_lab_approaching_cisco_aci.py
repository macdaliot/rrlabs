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
user_prefix = 'user'
tenant_prefix = 'tenant'

# Reading options
username, password, apic_host = checkOpts()

# Logging in
token, cookies, response_code = login(username = username, password = password, apic_host = apic_host)
if token:
    logging.info('login to the APIC successfully ({})'.format(response_code))
else:
    logging.error('failed to login to the APIC ({})'.format(response_code))
    sys.exit(255)

# Get tenants
response_code, response = getTenants(apic_host = apic_host, token = token, cookies = cookies)
if response_code == 200:
    logging.info('got tenants')
else:
    logging.error('failed to get tenants')
    logging.error(response)
    sys.exit(255)
for tenant in response['imdata']:
    lab_tenant = tenant['fvTenant']['attributes']['name']
    if lab_tenant.startswith(tenant_prefix):
        response_code, response = deleteTenant(apic_host = apic_host, token = token, cookies = cookies, name = lab_tenant)
        if response_code == 200:
            logging.info('tenant "{}" deleted'.format(lab_tenant))
        else:
            logging.error('failed to delete tenant "{}"'.format(lab_tenant))
            logging.error(response)
            sys.exit(255)
# Get users
response_code, response = getUsers(apic_host = apic_host, token = token, cookies = cookies)
if response_code == 200:
    logging.info('got users')
else:
    logging.error('failed to get users')
    logging.error(response)
    sys.exit(255)

for user in response['imdata']:
    lab_username = user['aaaUser']['attributes']['name']
    if lab_username.startswith(user_prefix):
        response_code, response = deleteUser(apic_host = apic_host, token = token, cookies = cookies, username = lab_username)
        if response_code == 200:
            logging.info('user "{}" deleted'.format(lab_username))
        else:
            logging.error('failed to delete user "{}"'.format(lab_username))
            logging.error(response)
            sys.exit(255)
