#!/usr/bin/env python3
# @author Andrea Dainese <andrea.dainese@gmail.com>
# @copyright 2016-2017 Andrea Dainese
# @license https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode
# @link http://www.unetlab.com/
# @version 20170105

import atexit, getopt, logging, signal, sys, time
from functions2 import *

def usage(command = None):
    if command == None:
        print("Usage: {} COMMAND [OPTIONS]".format(sys.argv[0]))
        print("")
        print("Commands:")
        print("    create   Create a node from a file")
        print("    delete   Delete an existing and stopped node")
        print("    start    Start a new or existing node")
        print("    stop     Stop a running node")
    elif command == "delete":
        print("Usage: {} {} -l label [OPTIONS]".format(sys.argv[0], command))
        print("    label        a 32 bit integer starting from 0")
    elif command == "start":
        print("Usage: {} {} -c controller -l label -m model [OPTIONS]".format(sys.argv[0], command))
        print("    controller   the IP or domain name of the controller host")
        print("    label        a 32 bit integer starting from 0")
        print("    model        the type of the node to be created")
    elif command == "stop":
        print("Usage: {} {} -l label [OPTIONS]".format(sys.argv[0], command))
        print("    label        a 32 bit integer starting from 0")

    print("")
    print("Options:")
    print("    -d   enable debug")
    sys.exit(255)

#def exitGracefully(signum, frame):

def main():
    command = None
    controller = None
    label = None
    model = None

    if len(sys.argv) < 2:
        usage()
    elif sys.argv[1] not in ["create", "delete", "start", "stop"]:
        logging.error("command {} not recognized".format(sys.argv[1]))
        sys.exit(255)

    # Reading options
    command = sys.argv[1]
    try:
        opts, args = getopt.getopt(sys.argv[2:], "c:dl:m:")
    except getopt.GetoptError as err:
        logging.error("{}".format(err))
        sys.exit(255)
    for opt, arg in opts:
        if opt == "-c":
            controller = arg
        elif opt == "-d":
            logging.basicConfig(level = logging.DEBUG)
        elif opt == "-l":
            try:
                label = int(arg)
                if not isLabel(label):
                    raise
            except:
                logging.error("label not recognized")
                sys.exit(255)
        elif opt == "-m":
            model = arg
            if not isModel(model):
                logging.error("model not recognized")
                sys.exit(255)

    # Checking options
    if command in [ "delete", "start", "stop" ]:
        if label == None:
            logging.error("label not recognized")
            sys.exit(255)
    if command == "start":
        if controller == None:
            logging.error("controller not recognized")
            sys.exit(255)
        if  model == None:
            logging.error("model not recognized")
            sys.exit(255)

    # Executing
    if command == "start":
        if not nodeStart(controller, label, model):
            logging.error("node {} cannot start".format(label))
            sys.exit(1)
        time.sleep(WAIT_FOR_START)
        if not isNodeRunning(label):
            logging.error("node {} unexpectedly died".format(label))

        # after start should update node status

    #atexit.register(exitHandler)

if __name__ == "__main__":
    #sys.excepthook = exceptionHandler
    #original_sigint = signal.getsignal(signal.SIGINT)
    #original_sigterm = signal.getsignal(signal.SIGTERM)
    #signal.signal(signal.SIGINT, exitGracefully)
    #signal.signal(signal.SIGTERM, exitGracefully)
    main()

