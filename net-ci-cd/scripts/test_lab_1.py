#!/usr/bin/env python3
from nornir.core import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command

import sys

def main():
    testing_ok = True
    nr = InitNornir(host_file = 'hosts.yaml', group_file = 'groups.yaml', num_workers = 20)
    test = nr.filter(site = 'test')

    # Checking CDP neighbors
    command = 'show cdp neighbors detail'
    result = test.run(task = netmiko_send_command, command_string = command, use_textfsm = True)
    for device_name, device_output in result.items():
        if device_name == 'R1-test':
            if device_output.result[0]['destination_host'] != 'R2.test.example.com':
                print('failed to get right neighbors on {}'.format(device_name))
                testing_ok = False
        if device_name == 'R2-test':
            if device_output.result[0]['destination_host'] != 'R1.test.example.com':
                print('failed to get right neighbors on {}'.format(device_name))
                testing_ok = False

    # Checking OSPF neighbors
    command = 'show ip ospf neighbor'
    result = test.run(task = netmiko_send_command, command_string = command, use_textfsm = True)
    for device_name, device_output in result.items():
        if device_name == 'R1-test':
            if device_output.result[0]['address'] != '192.168.0.2':
                print('failed to get the right OSPF neighbor on {}'.format(device_name))
                testing_ok = False
        if device_name == 'R2-test':
            if device_output.result[0]['address'] != '192.168.0.1':
                print('failed to get the right OSPF neighbor on {}'.format(device_name))
                testing_ok = False

    if not testing_ok:
        sys.exit(1)

if __name__ == '__main__':
    main()
