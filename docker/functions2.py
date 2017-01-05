#!/usr/bin/env python3

ADMIN_USER = "eveng"
ADMIN_PASSWORD = "password"
ADMIN_SECRET = "secret"
CONSOLE_PORT = 5005
DEBUG = True
IFF_NO_PI = 0x1000
IFF_TAP = 0x0002
IOL_BUFFER = 1600
MGMT_ID = 0
MGMT_NAME = "veth0"
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
DOCKER_URL = "http://127.0.0.1:4243"
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

def getJson(url, data = None):
    import json, urllib.request
    req = urllib.request.Request(url)
    if data or data == {}:
        try:
            input_data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json; charset=utf-8')
            req.add_header('Content-Length', len(input_data))
        except Exception as err:
            logging.debug("encode POST data failed")
            logging.debug(err)
            return {}
    else:
        input_data = None
    try:
        output_data = urllib.request.urlopen(req, input_data).read()
    except Exception as err:
        logging.debug("url {} does not answer correctly".format(url))
        logging.debug(err)
        return {}
    try:
        return json.loads(output_data.decode("utf-8"))
    except Exception as err:
        return  {"content": "no data"}

def isLabel(label):
    try:
        if label < 0 or label > LABEL_BITS ** 8 - 1:
            logging.debug("label {} is not valid".format(label))
            return False
    except Exception as err:
        logging.debug("label {} is not an integer".format(label))
        logging.debug(err)
        return False
    return True

def isModel(model):
    data = getJson("{}/images/json?filter={}".format(DOCKER_URL, model))
    if len(data) < 1:
        logging.debug("model {} not found".format(model))
        return False
    return True

def isNode(label):
    data = getJson("{}/containers/node_{}/json".format(DOCKER_URL, label))
    if len(data) < 1:
        logging.debug("node {} not found".format(label))
        return False
    return True

def isNodeRunning(label):
    if not isNode(label):
        return False
    data = getJson("{}/containers/node_{}/json".format(DOCKER_URL, label))
    if data["State"]["Status"] != "running":
        return False
    return True

def nodeCreate(label, model, controller):
    node_data = {
        "Hostname": "node-{}".format(label),
        "Image": model,
        "Cmd": [
            "/sbin/node_init",
            "{}".format(controller),
            "{}".format(label),
         ]
    }
    data = getJson("{}/containers/create?name=node_{}".format(DOCKER_URL, label), node_data)
    if len(data) < 1:
        logging.debug("node {} not found".format(label))
        return False
    return True

def nodeStart(controller, label, model):
    if not isNode(label):
        logging.debug("node {} need to be created".format(label))
        if not nodeCreate(label, model, controller):
            logging.debug("node {} failed to create".format(label))
            return False
    else:
        data = getJson("{}/containers/node_{}/start".format(DOCKER_URL, label), {})
        if len(data) < 1:
            logging.debug("node {} cannot start".format(label))
            return False
        return True
    return True

