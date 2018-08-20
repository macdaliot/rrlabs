#!/usr/bin/env python3
from nornir.core import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import napalm_get
import os, re

pwd = os.path.dirname(os.path.realpath(__file__))

def clean_config(config):
    # Remove non config lines
    cleaned_config = re.sub(r'^Using [0-9]+ out of [0-9]+ bytes.*\n?', '', config)
    return cleaned_config

def config_to_template(config):
    template = clean_config(config)
    # Remove hostname
    marker = '{{hostname}}'
    template = re.sub(re.compile(r'^hostname .*$', re.MULTILINE), 'hostname {}'.format(marker), template)
    # Remove domain name
    marker = '{{domain}}'
    template = re.sub(re.compile(r'^ip domain name .*$', re.MULTILINE), 'ip domain name {}'.format(marker), template)
    # Remove LLDP
    template = re.sub(re.compile(r'^lldp .*$', re.MULTILINE), '!', template)
    # Remove Ethernet interfaces (Loopback and management interfaces are excluded)
    marker = '{{interfaces}}'
    template = re.sub(re.compile(r'^interface [^Loopback]*$[^!]*', re.MULTILINE), '!\n{}\n'.format(marker), template)
    template = re.sub(re.compile(r'{}.*{}'.format(marker, marker), re.MULTILINE|re.DOTALL), marker, template)
    return template

def main():
    nr = InitNornir(host_file = 'hosts.yaml', group_file = 'groups.yaml', num_workers = 20)
    test = nr.filter(site = 'prod')
    result = test.run(task = napalm_get, getters = ['get_config'])

    # Store startup configurations
    for device_name, device_output in result.items():
        f = open('configs/{}.cfg'.format(device_name), 'w')
        f.write(clean_config(device_output[0].result['get_config']['startup']))
        f.close()

    # Store templates
    templates = []
    for device_name, device_output in result.items():
        template_name = device_name.split('-')[0]
        if template_name not in templates:
            f = open('configs/{}-prod.template'.format(template_name), 'w')
            f.write(config_to_template(device_output[0].result['get_config']['startup']))
            f.close()
            templates.append(template_name)

if __name__ == '__main__':
    main()
