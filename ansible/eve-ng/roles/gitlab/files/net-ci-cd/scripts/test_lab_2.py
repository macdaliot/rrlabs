#!/usr/bin/env python3
from napalm import get_network_driver
import logging, napalm, sys, yaml

def main():
    testing_ok = True
    driver_ios = napalm.get_network_driver('ios')


    with open('groups.yaml', 'r') as groups_file:
        hosts_yaml = yaml.load(groups_file)
        napalm_username = hosts_yaml['test']['nornir_username']
        napalm_password = hosts_yaml['test']['nornir_password']

    with open('hosts.yaml', 'r') as hosts_file:
        for device_name, device in yaml.load(hosts_file).items():
            if 'test' in device['groups']:
                napalm_device =  driver_ios(hostname = device['nornir_host'], username = napalm_username, password = napalm_password, optional_args = {'port': 22})
                napalm_device.open()
                if device_name == 'R1-test':
                    result = napalm_device.ping(destination = '192.168.0.2', source = '192.168.0.1')
                    try:
                        if result['success']['packet_loss'] != 0:
                            logging.error('ping frmo R1 to R2 not working')
                            testing_ok = False
                    except:
                        logging.error('cannot configure ping frmo R1 to R2')
                        testing_ok = False
                        pass
                if device_name == 'R2-test':
                    result = napalm_device.ping(destination = '192.168.0.1', source = '192.168.0.2')
                    try:
                        if result['success']['packet_loss'] != 0:
                            logging.error('ping frmo R2 to R1 not working')
                            testing_ok = False
                    except:
                        logging.error('cannot configure ping frmo R2 to R1')
                        testing_ok = False
                        pass
                napalm_device.close()

    if not testing_ok:
        sys.exit(1)

if __name__ == '__main__':
    main()
