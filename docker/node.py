#!/usr/bin/env python3
""" Node manager """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

import atexit, getopt, logging, os.path, signal, sys, time
from functions import *

def usage(command = None):
    """ How to use this script
    Return:
    - sys.exit(255)
    """
    if command == None:
        print('Usage: {} COMMAND [OPTIONS]'.format(sys.argv[0]))
        print('')
        print('Commands:')
        print('    build    Create a node image from a file')
        print('    delete   Delete an existing and stopped node')
        print('    log      Show last log')
        print('    start    Start a new or existing node')
        print('    stop     Stop a running node')
    elif command == 'build':
        print('Usage: {} {} -a dockerapi -f file [OPTIONS]'.format(sys.argv[0], command))
        print('    dockerapi   the docker URL for API')
        print('    file        the file to build the node image from')
    elif command == 'delete':
        print('Usage: {} {} -a dockerapi -l label [OPTIONS]'.format(sys.argv[0], command))
        print('    dockerapi   the docker URL for API')
        print('    label       a 32 bit integer starting from 0')
    elif command == 'log':
        print('Usage: {} {} -a dockerapi -l label [OPTIONS]'.format(sys.argv[0], command))
        print('    dockerapi   the docker URL for API')
        print('    label       a 32 bit integer starting from 0')
    elif command == 'start':
        print('Usage: {} {} -a dockerapi -c controller -l label -m model [OPTIONS]'.format(sys.argv[0], command))
        print('    dockerapi   the docker URL for API')
        print('    controller  the IP or domain name of the controller host')
        print('    label       a 32 bit integer starting from 0')
        print('    model       the type of the node to be created')
    elif command == 'stop':
        print('Usage: {} {} -a dockerapi -l label [OPTIONS]'.format(sys.argv[0], command))
        print('    dockerapi   the docker URL for API (without trailing /)')
        print('    dockerapi   the docker URL for API')
        print('    label       a 32 bit integer starting from 0')
    print('')
    print('Options:')
    print('    -d          enable debug')
    sys.exit(255)

#def exitGracefully(signum, frame):

def main():
    command = None
    docker_url = None
    file = None
    controller = None
    label = None
    model = None

    if len(sys.argv) < 2:
        usage()
    elif sys.argv[1] not in ['build', 'delete', 'log', 'start', 'stop']:
        logging.error('command {} not recognized'.format(sys.argv[1]))
        sys.exit(255)

    # Reading options
    command = sys.argv[1]
    try:
        opts, args = getopt.getopt(sys.argv[2:], 'a:c:df:l:m:')
    except getopt.GetoptError as err:
        logging.error('{}'.format(err))
        sys.exit(255)
    for opt, arg in opts:
        if opt == '-a':
            docker_url = arg.strip('/')
        elif opt == '-c':
            controller = arg
        elif opt == '-d':
            logging.basicConfig(level = logging.DEBUG)
        elif opt == '-f':
            file = arg
        elif opt == '-l':
            try:
                label = int(arg)
                if not isLabel(label):
                    raise
            except Exception as err:
                logging.error('label not recognized')
                sys.exit(255)
        elif opt == '-m':
            model = arg

    # Checking options
    if label == None:
        logging.error('label not recognized')
        sys.exit(255)
    if docker_url == None:
        logging.error('Docker API URL not recognized')
        sys.exit(255)
    if command == 'start':
        if controller == None:
            logging.error('controller not recognized')
            sys.exit(255)
        if  model == None:
            logging.error('model not recognized')
            sys.exit(255)
        elif not isModel(docker_url, model):
            logging.error('model not recognized')
            sys.exit(255)
    if command == 'build':
        if file == None:
            logging.error('file not recognized')
        elif not os.path.isfile(file):
            logging.error('file does not exist')
            sys.exit(255)

    # Executing
    if command == 'build':
        logging.error('TODO: not implemented yet'.format(label))
        # See also nodeBuild()
        sys.exit(1)
    elif command == 'delete':
        if not nodeDelete(docker_url, label):
            logging.error('node {} cannot be deleted'.format(label))
            sys.exit(1)
    elif command == 'log':
        logs = nodeGetLog(docker_url, label)
        if logs:
            print(logs)
            print('--- end of logs ---')
        else:
            logging.error('node {} does not exist'.format(label))
            sys.exit(1)
    elif command == 'start':
        if not nodeStart(docker_url, controller, label, model):
            logging.error('node {} cannot start'.format(label))
            sys.exit(1)
        # TODO after start should update node status
    elif command == 'stop':
        if not nodeStop(docker_url, label):
            logging.error('node {} cannot be stopped'.format(label))
            sys.exit(1)



    #atexit.register(exitHandler)

if __name__ == '__main__':
    #sys.excepthook = exceptionHandler
    #original_sigint = signal.getsignal(signal.SIGINT)
    #original_sigterm = signal.getsignal(signal.SIGTERM)
    #signal.signal(signal.SIGINT, exitGracefully)
    #signal.signal(signal.SIGTERM, exitGracefully)
    main()

