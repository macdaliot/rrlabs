#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

import napalm, sys, os

def main():
    # http://networktocode.com/labs/tutorials/how-to-use-napalm-python-library-to-manage-ios-devices/
    driver = napalm.get_network_driver('ios')
    device = driver(hostname = '172.17.0.2', username = 'admin', password = 'UNetLabv2!', optional_args = {'port': 22})
    config = 'hostname ciao'
    device.open()
    device.load_replace_candidate(config = config)
    #diffs = device.compare_config()
    #print(diffs)
    device.commit_config()

    device.close()

if __name__ == '__main__':
    main()
