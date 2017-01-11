#!/usr/bin/env python3

ADMIN_USER = 'eveng'
ADMIN_PASSWORD = 'password'
ADMIN_SECRET = 'secret'
CONSOLE_PORT = 5005
DEBUG = True
IFF_NO_PI = 0x1000
IFF_TAP = 0x0002
IOL_BUFFER = 1600
MGMT_ID = 0
MGMT_NAME = 'veth0'
MIN_TIME = 5
TAP_BUFFER = 10000
TS_BUFFER = 1
TUNSETNOCSUM = 0x400454c8
TUNSETDEBUG = 0x400454c9
TUNSETIFF = 0x400454ca
TUNSETPERSIST = 0x400454cb
TUNSETOWNER = 0x400454cc
TUNSETLINK = 0x400454cd
UDP_BUFFER = 10000
UDP_PORT = 5005
LABEL_BITS = 32
#DOCKER_URL = 'http://127.0.0.1:4243'
WAIT_FOR_START = 1

#--[ Telnet Commands ]--------------------------------------------------------
IS     =   0 # Sub-process negotiation IS command
SEND   =   1 # Sub-process negotiation SEND command
SE     = 240 # End of subnegotiation parameters
NOP    = 241 # No operation
DATMK  = 242 # Data stream portion of a sync.
BREAK  = 243 # NVT Character BRK
IP     = 244 # Interrupt Process
AO     = 245 # Abort Output
AYT    = 246 # Are you there
EC     = 247 # Erase Character
EL     = 248 # Erase Line
GA     = 249 # The Go Ahead Signal
SB     = 250 # Sub-option to follow
WILL   = 251 # Will; request or confirm option begin
WONT   = 252 # Wont; deny option request
DO     = 253 # Do = Request or confirm remote option
DONT   = 254 # Don't = Demand or confirm option halt
IAC    = 255 # Interpret as Command
#--[ Telnet Options ]---------------------------------------------------------
BINARY =  0 # Transmit Binary
ECHO   =  1 # Echo characters back to sender
RECON  =  2 # Reconnection
SGA    =  3 # Suppress Go-Ahead
TTYPE  = 24 # Terminal Type
NAWS   = 31 # Negotiate About Window Size
LINEMO = 34 # Line Mode

import logging

def invokeJson(url, method = 'GET', data = None):
    import json, urllib.request
    try:
        req = urllib.request.Request(url)
        req.get_method = lambda: method
        if data or data == {}:
            try:
                input_data = json.dumps(data).encode('utf-8')
                req.add_header('Content-Type', 'application/json; charset=utf-8')
                req.add_header('Content-Length', len(input_data))
            except Exception as err:
                logging.debug('data encoding failed')
                logging.debug(err)
                return {}
        else:
            input_data = None
        output_data = urllib.request.urlopen(req, input_data).read()
    except Exception as err:
        logging.debug('url {} does not answer correctly'.format(url))
        logging.debug(err)
        return {}
    try:
        return json.loads(output_data.decode('utf-8'))
    except Exception as err:
        return  {'content': 'no data'}

def invokeUrl(url, method = 'GET'):
    import urllib.request
    try:
        req = urllib.request.Request(url)
        req.get_method = lambda: method
        output_data = urllib.request.urlopen(req).read()
    except Exception as err:
        logging.debug('url {} does not answer correctly'.format(url))
        logging.debug(err)
        return False
    if not output_data:
        return True
    return output_data

def isLabel(label):
    try:
        if label < 0 or label > LABEL_BITS ** 8 - 1:
            logging.debug('label {} is not valid'.format(label))
            return False
    except Exception as err:
        logging.debug('label {} is not an integer'.format(label))
        logging.debug(err)
        return False
    return True

def isModel(docker_url, model):
    data = invokeJson('{}/images/json?filter={}'.format(docker_url, model))
    if len(data) < 1:
        logging.debug('model {} not found'.format(model))
        return False
    return True

def isNode(docker_url, label):
    data = invokeJson('{}/containers/node_{}/json'.format(docker_url, label))
    if len(data) < 1:
        logging.debug('node {} not found'.format(label))
        return False
    return True

def isNodeRunning(docker_url, label):
    if not isNode(docker_url, label):
        return False
    data = invokeJson('{}/containers/node_{}/json'.format(docker_url, label))
    if data['State']['Status'] != 'running':
        return False
    return True

def nodeBuild(file):
    if file.endswith('.bin'):
        logging.debug('file is IOL')
    return True

def nodeCreate(docker_url, label, model, controller):
    node_data = {
        'Hostname': 'node-{}'.format(label),
        'Image': model,
        'Cmd': [
            '/sbin/node_init',
            '{}'.format(controller),
            '{}'.format(label),
        ],
        'HostConfig': {
            'Privileged': True
        }
    }
    data = invokeJson('{}/containers/create?name=node_{}'.format(docker_url, label), 'POST', node_data)
    if len(data) < 1:
        logging.debug('node {} not found'.format(label))
        return False
    return True

def nodeDelete(docker_url, label):
    if not isNode(label):
        logging.debug('node {} does not exist'.format(label))
        return False
    elif isNodeRunning(docker_url, label):
        logging.debug('node {} is running'.format(label))
        return False
    else:
        if not invokeUrl('{}/containers/node_{}'.format(docker_url, label), 'DELETE'):
            logging.debug('node {} cannot be deleted'.format(label))
            return False
    return True

def nodeGetLog(docker_url, label):
    import html.parser
    data = invokeUrl('{}/containers/node_{}/logs?stderr=1&stdout=1&timestamps=1&follow=0'.format(docker_url, label))
    if not isNode(docker_url, label):
        logging.debug('node {} need does not exist'.format(label))
        return False
    if not data:
        logging.debug('node {} does not have logs'.format(label))
        return ''
    return data.decode('unicode_escape').rstrip()

def nodeStart(docker_url, controller, label, model):
    if not isNode(docker_url, label):
        logging.debug('node {} need to be created'.format(label))
        if not nodeCreate(docker_url, label, model, controller):
            logging.debug('node {} failed to create'.format(label))
            return False
    data = invokeJson('{}/containers/node_{}/start'.format(docker_url, label), 'POST', {})
    if len(data) < 1:
        logging.debug('node {} cannot start'.format(label))
        return False
    return True

def nodeStop(docker_url, label):
    if not isNode(label):
        logging.debug('node {} does not exist'.format(label))
        return False
    elif not isNodeRunning(docker_url, label):
        logging.debug('node {} already stopped'.format(label))
    else:
        data = invokeJson('{}/containers/node_{}/stop'.format(docker_url, label), {})
        if len(data) < 1:
            logging.debug('node {} cannot be stopped'.format(label))
            return False
    return True
