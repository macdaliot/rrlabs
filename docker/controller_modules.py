#!/usr/bin/env python3A
""" Modules """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

ADMIN_USER = 'eveng'
ADMIN_PASSWORD = 'password'
ADMIN_SECRET = 'secret'
WAIT_FOR_START = 1

import logging

def invokeJson(url, method = 'GET', data = None):
    """ Invoke an URL using any method, a JSON is expected as result
    Return:
    - False: if failed to invoke the URL
    - {...}: the JSON returned by the server
    - {}: an empty JSON if no data has been return by the server
    """
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
                return False
        else:
            input_data = None
        output_data = urllib.request.urlopen(req, input_data).read()
    except Exception as err:
        logging.debug('url {} does not answer correctly'.format(url))
        logging.debug(err)
        return False
    try:
        return json.loads(output_data.decode('utf-8'))
    except Exception as err:
        return  {}

def invokeUrl(url, method = 'GET'):
    """ Invoke an URL using any method
    Return:
    - False: if failed to invoke the URL
    - STRING: the data returned by the server
    - True: if no data has been return by the server
    """
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

def isModel(docker_url, model):
    """ Check if a Docker image exists
    Return:
    - True: if the image exists
    - False: otherwise
    """
    data = invokeJson('{}/images/json?filter={}'.format(docker_url, model))
    if data == False or len(data) < 1:
        logging.debug('model {} not found'.format(model))
        return False
    return True

def isNode(docker_url, label):
    """ Check if the Docker node "node_LABEL" exists
    Return:
    - True: if the node exists
    - False: otherwise
    """
    data = invokeJson('{}/containers/node_{}/json'.format(docker_url, label))
    if data == False or len(data) < 1:
        logging.debug('node {} not found'.format(label))
        return False
    return True

def isNodeRunning(docker_url, label):
    """ Check if the Docker node "node_LABEL" is running
    Return:
    - True: if the node is running
    - False: otherwise
    """
    if not isNode(docker_url, label):
        return False
    data = invokeJson('{}/containers/node_{}/json'.format(docker_url, label))
    if data == False or data['State']['Status'] != 'running':
        return False
    return True

"""
def nodeBuild(file):
    if file.endswith('.bin'):
        logging.debug('file is IOL')
    return True
"""

def nodeCreate(docker_url, label, model, controller):
    """ Create a Docker node from LABEL and MODEL
    Return:
    - True: if node is created
    - False: otherwise
    """
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
    if data == False:
        logging.debug('node {} not found'.format(label))
        return False
    return True

def nodeDelete(docker_url, label):
    """ Delete a Docker node from LABEL
    Return:
    - True: if node does not exist anymore
    - False: otherwise
    """
    if not isNode(docker_url, label):
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
    """ Get log from a Docker node from LABEL
    Return:
    - STRING: logs if node exists
    - False: otherwise
    """
    import html.parser
    if not isNode(docker_url, label):
        logging.debug('node {} does not exist'.format(label))
        return False
    data = invokeUrl('{}/containers/node_{}/logs?stderr=1&stdout=1&timestamps=1&follow=0'.format(docker_url, label))
    if not data:
        logging.debug('node {} failed to return logs'.format(label))
        return False
    return data.decode('unicode_escape').rstrip()

def nodeStart(docker_url, controller, label, model):
    """ Start a Docker node from LABEL and MODEL
    Return:
    - True: if node has been started and is alive after WAIT_FOR_START
    - False: otherwise
    """
    import time
    if not isNode(docker_url, label):
        logging.debug('node {} need to be created'.format(label))
        if not nodeCreate(docker_url, label, model, controller):
            logging.debug('node {} failed to create'.format(label))
            return False
    data = invokeJson('{}/containers/node_{}/start'.format(docker_url, label), 'POST', {})
    if data == False:
        logging.debug('node {} cannot start'.format(label))
        return False
    time.sleep(WAIT_FOR_START)
    if not isNodeRunning(docker_url, label):
        logging.error('node {} unexpectedly died'.format(label))
        return False
    return True

def nodeStop(docker_url, label):
    """ Stop a Docker node from LABEL
    Return:
    - True: if node has been stopped or not running
    - False: otherwise
    """
    if not isNode(docker_url, label):
        logging.debug('node {} does not exist'.format(label))
        return False
    elif not isNodeRunning(docker_url, label):
        logging.debug('node {} already stopped'.format(label))
    else:
        data = invokeUrl('{}/containers/node_{}/stop'.format(docker_url, label), 'POST')
        if not data:
            logging.debug('node {} cannot be stopped'.format(label))
            return False
    return True
