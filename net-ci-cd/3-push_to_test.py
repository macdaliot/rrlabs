#!/usr/bin/env python3
from nornir.core import InitNornir
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.connections import napalm_connection
from nornir.plugins.tasks.networking import napalm_configure

import glob

def load_data(task):
    task.run(task = napalm_connection, name = 'Setting up NAPALM', timeout = 60, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
    task.run(task = napalm_configure, filename = '{}-new.cfg'.format(task.host['name']), replace = True)

def main():
    nr = InitNornir(host_file = 'hosts.yaml', group_file = 'groups.yaml', num_workers = 20)
    test = nr.filter(site = 'test')
    result = test.run(load_data)
    print_result(result)

if __name__ == '__main__':
    main()
