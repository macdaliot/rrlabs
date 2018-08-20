#!/usr/bin/env python3
import glob, jinja2, yaml

def main():
    templateLoader = jinja2.FileSystemLoader(searchpath = "./")
    templateEnv = jinja2.Environment(loader = templateLoader)
    for template_file in glob.glob("configs/*.template"):
        device_name = template_file.split('-')[0]
        config_data = yaml.load(open('{}.yaml'.format(device_name)))
        for environment in ['prod']:
            template_data = {
                'hostname': config_data['hostname'],
                'domain': config_data['domain-{}'.format(environment)],
                'interfaces': 'lldp run\ninterface {}\n ip address {} 255.255.255.0\n ip ospf 1 area 0\n!\ninterface Ethernet0/3\n ip address dhcp\n'.format(config_data['interface-{}'.format(environment)], config_data['ip'])
            }
            template = templateEnv.get_template(template_file)
            outputText = template.render(template_data)
            file = open('{}-{}-new.cfg'.format(device_name, environment), 'w')
            file.write(outputText)
            file.close()

if __name__ == '__main__':
    main()
