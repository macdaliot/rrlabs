#!/usr/bin/env python3

""" Create Cisco ACI environment """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20180320'

import ipaddress, json, logging, napalm, random, requests, string, sys, urllib3
from openpyxl import load_workbook
from functions import *

urllib3.disable_warnings()
logging.basicConfig(level = logging.INFO)

# Variables
napalm_usernamne = 'napalm'
napalm_password = '200q0r8dy5ubrxsh'
total_users = 2
user_prefix = 'user'
tenant_name = 'tenant255'
tenant_description = 'Demonstrative tenant'
vrf_name = 'prod'
vrf_description = 'Default VRF for tenant {}'.format(tenant_name)
bds = {
    'dmz': 'DMZ network for webservers',
    'app': 'Network for servers',
    'client': 'Network for simulate external users'
}

# Reading options
username, password, apic_host = checkOpts()

# Create users
users = []
user_list_ids = [155]
user_list_ids.extend(range(1, total_users + 1))
for x in user_list_ids:
    lab_username = '{}{}'.format(user_prefix, x)
    lab_password = ''.join(random.choices(string.ascii_uppercase, k = 3) + random.choices(string.ascii_lowercase, k = 3) + random.choices(string.digits, k = 2))
    users.append({
        'id': x,
        'username': lab_username,
        'password': lab_password
    })
print(users)

# Configure physical devices
driver_ios = napalm.get_network_driver('ios')

routers = {
    'Router1': {
        'device': driver_ios(hostname = '172.25.82.12', username = napalm_usernamne, password = napalm_password, optional_args = {'port': 22}),
        'ip': 12
    },
    'Router2': {
        'device': driver_ios(hostname = '172.25.82.13', username = napalm_usernamne, password = napalm_password, optional_args = {'port': 22}),
        'ip': 13
    }
}
for router_name, router in routers.items():
    router_config = 'ip routing\nip domain-name lab.local\nip route 0.0.0.0 0.0.0.0 172.25.82.254\n'
    for user in users:
        router_config += 'username {} privilege 1 password {}\n'.format(user['username'], user['password'])
    if router_name == 'Router1':
        router_config += 'ip name-server 8.8.8.8 8.8.4.4\nntp server 0.it.pool.ntp.org\nntp server 1.it.pool.ntp.org\nntp server 2.it.pool.ntp.org\nntp server 3.it.pool.ntp.org\n'
    elif router_name == 'Router2':
        router_config += 'ip name-server 172.25.82.12\nntp server 172.25.82.12\n'
        router_config += 'interface GigabitEthernet0/1\nno shutdown\n'
        router_config += 'ip http server\nno ip http secure-server\nip http authentication local\n'
        for user in users:
            router_config += 'vrf definition vrf{}-dmz\naddress-family ipv4\nvrf definition vrf{}-client\naddress-family ipv4\n'.format(user['id'], user['id'])
            router_config += 'ip route vrf vrf{}-dmz 0.0.0.0 0.0.0.0 10.{}.1.254\n'.format(user['id'], user['id'])
            router_config += 'interface GigabitEthernet0/1.{}\nencapsulation dot1q {}\nvrf forwarding vrf{}-dmz\nDescription DMZ\nip address 10.{}.1.{} 255.255.255.0\n'.format(2000 + user['id'], 2000 + user['id'], user['id'], user['id'], router['ip'])
            router_config += 'interface GigabitEthernet0/1.{}\nencapsulation dot1q {}\nvrf forwarding vrf{}-client\nDescription Client\nip address 10.{}.0.{} 255.255.255.0\n'.format(1000 + user['id'], 1000 + user['id'], user['id'], user['id'], router['ip'])
        router['device'].open()
        router['device'].load_merge_candidate(config = router_config)
        router['device'].commit_config()
        router['device'].close()

switches = {
    'Switch1': {
        'device': driver_ios(hostname = '172.25.82.10', username = napalm_usernamne, password = napalm_password, optional_args = {'port': 22}),
        'ip': 10
    },
    'Switch2': {
        'device': driver_ios(hostname = '172.25.82.11', username = napalm_usernamne, password = napalm_password, optional_args = {'port': 22}),
        'ip': 11
    }
}
for switch_name, switch in switches.items():
    switch_config = 'vtp mode transparent\nip routing\nip domain-name lab.local\nip name-server 172.25.82.12\nntp server 172.25.82.12\nip route 0.0.0.0 0.0.0.0 172.25.82.254\n'
    for user in users:
        switch_config += 'username {} privilege 1 password {}\n'.format(user['username'], user['password'])
    if switch_name == 'Switch1':
        switch_config += 'spanning-tree vlan 100-255 priority 4096\n'
        switch_config += 'interface range GigabitEthernet1/0/1 - 2\nchannel-group 1 mode active\ninterface range GigabitEthernet1/0/3 - 4\nchannel-group 2 mode active\ninterface range Port-channel1 - 2\nswitchport trunk encapsulation dot1q\nswitchport mode trunk\nswitchport nonegotiate\n'
    if switch_name == 'Switch2':
        switch_config += 'spanning-tree vlan 100-255 priority 8192\n'
        switch_config += 'interface range GigabitEthernet1/0/2, GigabitEthernet1/0/4\nchannel-group 1 mode active\ninterface Port-channel1\nswitchport trunk encapsulation dot1q\nswitchport mode trunk\nswitchport nonegotiate\ninterface GigabitEthernet1/0/1\nswitchport trunk encapsulation dot1q\nswitchport mode trunk\nswitchport nonegotiate\ninterface FastEthernet1/0/1\nswitchport trunk encapsulation dot1q\nswitchport mode trunk\nswitchport nonegotiate\nspanning-tree portfast trunk\n'
    for user in users:
        switch_config += 'vlan {}\ninterface vlan{}\nip address 10.{}.0.{} 255.255.255.0\nno shutdown\n'.format(100 + user['id'], 100 + user['id'], user['id'], switch['ip'])
    switch['device'].open()
    switch['device'].load_merge_candidate(config = switch_config)
    switch['device'].commit_config()
    switch['device'].close()
sys.exit(0)

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
response_code, response = addTenant(apic_host = apic_host, token = token, cookies = cookies, name = tenant_name, description = tenant_description)
if response_code == 200:
    logging.info('added tenant "{}" ({})'.format(tenant_name, response_code))
else:
    logging.error('failed to add tenant "{}" ({})'.format(tenant_name, response_code))
    logging.error(response)
    sys.exit(255)

# Add demonstrative VRF
response_code, response = addVRF(apic_host = apic_host, token = token, cookies = cookies, tenant_name = tenant_name, name = vrf_name, description = vrf_description)
if response_code == 200:
    logging.info('added VRF "{}:{}" ({})'.format(tenant_name, vrf_name, response_code))
else:
    logging.error('failed to add VRF "{}:{}" ({})'.format(tenant_name, vrf_name, response_code))
    logging.error(response)
    sys.exit(255)

# Add demonstrative BDs
for bd_name, bd_description in bds.items():
    response_code, response = addBridgeDomain(apic_host = apic_host, token = token, cookies = cookies, tenant_name = tenant_name, name = bd_name, description = bd_description, igmp_snooping = False, vrf = vrf_name)
    if response_code == 200:
        logging.info('added bridge domain "{}:{}" ({})'.format(tenant_name, bd_name, response_code))
    else:
        logging.error('failed to add bridge domain "{}:{}" ({})'.format(tenant_name, bd_name, response_code))
        logging.error(response)
        sys.exit(255)

# Add users
for lab_username, lab_password in users.items():
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
