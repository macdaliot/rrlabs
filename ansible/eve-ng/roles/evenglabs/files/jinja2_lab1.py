#!/usr/bin/env python3
import csv, jinja2, os, sys
templateLoader = jinja2.FileSystemLoader(searchpath = "./")
templateEnv = jinja2.Environment(loader = templateLoader)
template = templateEnv.get_template('jinja2_lab1.template')
with open('devices.csv', 'rt') as f:
    reader = csv.reader(f)
    for row in reader:
        templateVars = {
            'hostname' : row[0],
            'ip' : row[1],
            'netmask' : row[2],
            'username' : row[3],
            'password' : row[4]
        }
        outputText = template.render(templateVars)
        file = open(row[0] + '.cfg', 'w')
        file.write(outputText)
        file.close()
