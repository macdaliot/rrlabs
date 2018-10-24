#!/usr/bin/env python3
from nornir.core import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import napalm_get

import logging, sys

def main():
    testing_ok = True
    nr = InitNornir(host_file = 'hosts.yaml', group_file = 'groups.yaml', num_workers = 20)
    test = nr.filter(site = 'test')
    result = test.run(task = napalm_get, getters = ['get_lldp_neighbors'])

    # Checking LLDP neighbors
    for device_name, device_output in result.items():
        if device_name == 'R1-test':
            if device_output[0].result['get_lldp_neighbors']['Ethernet0/0'][0]['hostname'] != 'R2.test.example.com':
                logging.error('failed to get right neighbors on {}'.format(device_name))
                testing_ok = False
        if device_name == 'R2-test':
            if device_output[0].result['get_lldp_neighbors']['Ethernet0/0'][0]['hostname'] != 'R1.test.example.com':
                logging.error('failed to get right neighbors on {}'.format(device_name))
                testing_ok = False

    if not testing_ok:
        sys.exit(1)

if __name__ == '__main__':
    main()
