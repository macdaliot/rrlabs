#!/usr/bin/env python3
""" Wrapper for IOL """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

import array, atexit, fcntl, getopt, os, select, signal, socket, struct, subprocess, sys, time
from wrapper_modules import *

def usage():
    print('Usage: {} [OPTIONS] -- [IOL OPTIONS]'.format(sys.argv[0]))
    print('')
    print('Options:')
    print('    -d             enable debug')
    print('    -f binary      the IOL binary file')
    print('    -g controller  the IP or domain name of the controller host')
    print('    -i ID          the IOL device ID')
    print('    -l label       a 32 bit integer starting from 0')
    print('    -t             enable terminal server')
    print('    -w title       window title for terminal server')
    sys.exit(255)

def main():
    clients = [ ]
    console_history = bytearray()
    controller = None
    inputs = [ ]
    iol_bin = None
    iol_id = None
    label = None
    enable_ts = False
    outputs = [ ]
    terminated = False
    to_iol = None
    title = None

    if len(sys.argv) < 2:
        usage()

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'df:g:i:l:n:tw:')
    except getopt.GetoptError as err:
        sys.stderr.write('ERROR: {}\n'.format(err))
        usage()
        sys.exit(255)
    for opt, arg in opts:
        if opt == '-d':
            logging.basicConfig(level = logging.DEBUG)
        elif opt == '-f':
            iol_bin = arg
        elif opt == '-g':
            controller = arg
        elif opt == '-i':
            try:
                iol_id = int(arg)
            except Exception as err:
                logging.error('IOL ID recognized')
                sys.exit(255)
        elif opt == '-l':
            try:
                label = int(arg)
                if not isLabel(label):
                    raise
            except Exception as err:
                logging.error('label not recognized')
                sys.exit(255)
        elif opt == '-t':
            enable_ts = True
        elif opt == '-w':
            title = arg
        else:
            assert False, 'unhandled option'

    # Checking options
    if controller == None:
        logging.error('controller not recognized')
        sys.exit(255)
    if iol_bin == None:
        logging.error('IOL binary file not recognized')
        sys.exit(255)
    if not os.path.isfile(iol_bin):
        logging.error('IOL binary file does not exist')
        sys.exit(255)
    if iol_id == None:
        logging.error('IOL ID not recognized')
        sys.exit(255)
    if label == None:
        logging.error('label not recognized')
        sys.exit(255)

    # Setting parameters
    if iol_id == 1024:
        wrapper_id = 1
    else:
        wrapper_id = iol_id + 1
    read_fsocket = '/tmp/netio0/{}'.format(wrapper_id)
    write_fsocket = '/tmp/netio0/{}'.format(iol_id)

    # Writing NETMAP
    netmap_file = os.path.dirname(iol_bin) + '/NETMAP'
    try:
        os.unlink(netmap_file)
    except OSError as err:
        if os.path.exists(netmap_file):
            logging.error('cannot delete existent NETMAP')
            sys.exit(1)
    try:
        netmap_fd = open(netmap_file, 'w')
        for i in range(0, 63):
            netmap_fd.write('{}:{} {}:{}\n'.format(iol_id, i, wrapper_id, i))
        netmap_fd.close()
    except Exception as err:
        logging.error('cannot write NETMAP')
        sys.exit(1)
    atexit.register(os.unlink, netmap_file)

    # Preparing socket (IOL -> wrapper)
    try:
        os.unlink(read_fsocket)
    except OSError as err:
        if os.path.exists(read_fsocket):
            logging.error('cannot delete existent socket')
            sys.exit(1)
    try:
        from_iol = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        from_iol.bind(read_fsocket)
    except Exception as err:
        logging.error('cannot create file socket {}'.format(read_fsocket))
        sys.exit(1)
    inputs.append(from_iol)
    atexit.register(os.unlink, read_fsocket)

    # Preparing socket (controller -> wrapper)
    try:
        from_controller = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        from_controller.bind(('', UDP_PORT))
    except Exception as err:
        logging.error('cannot open UDP socket on port {}'.format(UDP_PORT))
        sys.exit(1)
    inputs.append(from_controller)
    atexit.register(from_controller.close)

    # Preparing socket (wrapper -> controller)
    try:
        to_controller = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except Exception as err:
        logging.error('cannot prepare socket for controller')
        sys.exit(1)
    atexit.register(to_controller.close)

    # Preparing tap
    try:
        from_tun = open('/dev/net/tun', 'r+b', buffering = 0)
        ifr = struct.pack('16sH', b'veth0', IFF_TAP | IFF_NO_PI)
        fcntl.ioctl(from_tun, TUNSETIFF, ifr)
        fcntl.ioctl(from_tun, TUNSETNOCSUM, 1)
    except Exception as err:
        logging.error('cannot open TUN/TAP descriptor')
        sys.exit(1)
    atexit.register(from_tun.close)
    inputs.append(from_tun)

    # Starting IOL
    try:
        iol_args = sys.argv[sys.argv.index('--') + 1:]
    except:
        iol_args = [ ]
        pass
    iol_args.append(str(iol_id))
    iol_env = { 'PWD': os.path.dirname(iol_bin) }
    logging.info('starting: {} {}'.format(iol_bin, ''.join(iol_args)))
    try:
        iol = subprocess.Popen([ iol_bin ] + iol_args, env = iol_env, cwd = os.path.dirname(iol_bin), stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = 0)
    except Exception as err:
        logging.error('cannot start IOL process')
        sys.exit(1)
    atexit.register(subprocessTerminate, iol)

    # Starting terminal server
    if enable_ts == True:
        inputs.extend([ iol.stdout.fileno(), iol.stderr.fileno() ])
        logging.debug('starting terminal server on {}'.format(CONSOLE_PORT))
        ts = terminalServerStart()
        if ts == False:
            logging.error('terminal server failed to start')
            sys.exit(1)
        atexit.register(ts.close)
        inputs.append(ts)

    # Executing
    while inputs:
        logging.debug('waiting for data')

        if iol.poll() != None:
            logging.error('IOL process died')
            # Grab all output before exiting
            console_history += iol.stderr.read()
            console_history += iol.stdout.read()
            break

        readable, writable, exceptional = select.select(inputs, outputs, inputs)

        if to_iol == None:
            try:
                to_iol = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                to_iol.connect(write_fsocket)
                atexit.register(to_iol.close)
            except Exception as err:
                logging.error('cannot connect to IOL socket')
                to_iol = None
                pass

        for s in readable:
            if s is from_iol:
                logging.debug('data from IOL (TAP)')
                iol_datagram = from_iol.recv(IOL_BUFFER)
                if not iol_datagram:
                    logging.error('cannot receive data from IOL node')
                    break
                else:
                    src_id, src_if, dst_id, dst_if, padding, payload = decodeIOLPacket(iol_datagram)
                    if src_if == MGMT_ID:
                        logging.debug('sending data to MGMT')
                        try:
                            os.write(from_tun.fileno(), payload)
                        except Exception as err:
                            logging.error('cannot send data to MGMT')
                            break
                    else:
                        logging.debug('sending data to controller')
                        try:
                            to_controller.sendto(encodeUDPPacket(label, src_if, payload), (controller, UDP_PORT))
                        except Exception as err:
                            loggin.error('cannot send data to controller')
                            break
            elif s is from_controller:
                logging.debug('data from controller')
                udp_datagram, src_addr = from_controller.recvfrom(UDP_BUFFER)
                if not udp_datagram:
                    logging.error('cannot receive data from controller')
                    sys.exit(1)
                else:
                    label, iface, payload = decodeUDPPacket(udp_datagram)
                    if 'to_iol' != None:
                        try:
                            to_iol.send(encodeIOLPacket(wrapper_id, iol_id, iface, payload))
                        except Exception as err:
                            logging.error('cannot send data to IOL node')
                            break
                    else:
                        logging.error('cannot connect to IOL socket, packet dropped')
            elif s is from_tun:
                logging.debug('data from MGMT')
                try:
                    tap_datagram = array.array('B', os.read(from_tun.fileno(), TAP_BUFFER))
                except Exception as err:
                    logging.error('cannot read data from MGMT')
                    break
                if to_iol != None:
                    try:
                        to_iol.send(encodeIOLPacket(wrapper_id, iol_id, MGMT_ID, tap_datagram))
                    except Exception as err:
                        logging.error('cannot send data to IOL MGMT')
                        break
                else:
                    logging.error('cannot connect to IOL socket, packet dropped')
            elif s is iol.stdout.fileno():
                logging.debug('data from IOL console (stdout)')
                try:
                    data = iol.stdout.read(1)
                except Exception as err:
                    logging.error('cannot read data from IOL console (stdout)')
                if time.time() - alive < MIN_TIME:
                    # Saving console if IOL crashes too soon
                    console_history += data
                inputs, clients = terminalServerSend(inputs, clients, data)
            elif s is iol.stderr.fileno():
                logging.debug('data from IOL console (stderr)')
                try:
                    data = iol.stderr.read(1)
                except Exception as err:
                    logging.error('cannot read data from IOL console (stderr)')
                if time.time() - alive < MIN_TIME:
                    # Saving console if IOL crashes too soon
                    console_history += data
                inputs, clients = terminalServerSend(inputs, clients, data)
            elif s is ts:
                # New client
                inputs, clients = terminalServerAccept(s, inputs, clients, title)
            elif s in clients:
                logging.debug('data from terminal server client')
                data, inputs, clients = terminalServerReceive(s, inputs, clients)
                if data != None:
                    try:
                        iol.stdin.write(data)
                    except Exception as err:
                        logging.error('cannot send data to IOL console')
                        break
            else:
                logging.error('unknown source from select')

    # Terminating
    inputs, clients = terminalServerClose(inputs, clients)
    if time.time() - alive < MIN_TIME:
        # IOL died prematurely
        logging.error('IOL process died prematurely\n')
        print(console_history.decode("utf-8") )
        sys.exit(1)
    else:
        # IOL died after a reasonable time
        sys.exit(0)

if __name__ == '__main__':
    alive = time.time()
    signal.signal(signal.SIGINT, exitGracefully)
    signal.signal(signal.SIGTERM, exitGracefully)
    main()
