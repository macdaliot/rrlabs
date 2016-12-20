#!/usr/bin/env python3

import array, atexit, fcntl, getopt, os, select, signal, socket, struct, subprocess, sys, time
from functions import *

def exitHandler():
    if DEBUG: print("DEBUG: exiting")
    if "from_iol" in globals():
        from_iol.close()
    if "from_switcherd" in globals():
        from_switcherd.close()
    if "from_tun" in globals():
        from_tun.close()
    if "netmap" in globals():
        os.unlink(netmap)
    if "iol" in globals() and iol.poll() == None:
        iol.terminate()
    #terminalServerClose(inputs, clients) inputs and clients are not global
    if terminated == True:
        print("INFO: CTRL+C pressed, terminating")
    elif time.time() - alive < MIN_TIME:
        sys.stderr.write("ERROR: IOL process died prematurely\n")
        if "console_history" in globals():
            print(console_history.decode("utf-8") )

def exitGracefully(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)
    if DEBUG: print("DEBUG: signum {} received".format(signum))

    if signum == 2:
        # CTRL+C
        terminated = True
        if "iol" in globals() and iol.poll == None:
            iol.terminate()
        if "ts" in globals() and ts.is_alive():
            ts.terminate()

    # restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exitGracefully)

def usage():
    print("Usage: {} [OPTIONS]".format(sys.argv[0]))
    print("  -f IOL")
    print("     IOL binary executable")
    print("  -g hostname")
    print("     switcherd hostname or IP address")
    print("  -i iol_id")
    print("     IOL device ID")
    print("  -l label")
    print("     Node label")
    print("  -t")
    print("     Enable terminal server")

def main():
    global alive, console_history, from_iol, from_switcherd, from_tun, iol, netmap, terminated
    enable_ts = False
    terminated = False
    console_history = bytearray()
    inputs = [ ]
    outputs = [ ]
    clients = [ ]

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:g:i:l:n:t")
    except getopt.GetoptError as err:
        sys.stderr.write("ERROR: {}\n".format(err))
        usage()
        sys.exit(1)

    # Parsing options
    for opt, arg in opts:
        if opt == "-f":
            iol_bin = arg
        elif opt == "-g":
            switcherd = arg
        elif opt == "-i":
            iol_id = int(arg)
        elif opt == "-l":
            label = int(arg)
        elif opt == "-t":
            enable_ts = True
        else:
            assert False, "unhandled option"

    # Checking options
    if "iol_bin" not in locals():
        sys.stderr.write("ERROR: missing IOL binary executable\n")
        usage()
        sys.exit(1)
    if not os.path.isfile(iol_bin):
        sys.stderr.write("ERROR: cannot find IOL binary executable\n")
        usage()
        sys.exit(1)
    if "iol_id" not in locals():
        sys.stderr.write("ERROR: missing iol_id\n")
        usage()
        sys.exit(1)
    if iol_id < 1 or iol_id > 1024:
        sys.stderr.write("ERROR: iol_id must be between 1 and 1024\n")
        usage()
        sys.exit(1)
    if "switcherd" not in locals():
        sys.stderr.write("ERROR: missing switcherid\n")
        usage()
        sys.exit(1)
    if "label" not in locals():
        sys.stderr.write("ERROR: missing label\n")
        usage()
        sys.exit(1)

    # Setting parameters
    if iol_id == 1024:
        wrapper_id = 1
    else:
        wrapper_id = iol_id + 1

    read_fsocket = "/tmp/netio0/{}".format(wrapper_id)
    write_fsocket = "/tmp/netio0/{}".format(iol_id)

    # Writing NETMAP
    netmap = os.path.dirname(iol_bin) + "/NETMAP"
    try:
        os.unlink(netmap)
    except OSError:
        if os.path.exists(netmap):
            sys.stderr.write("ERROR: cannot delete existent NETMAP")
            sys.exit(1)
    netmap_fd = open(netmap, 'w')
    for i in range(0, 63):
        netmap_fd.write("{}:{} {}:{}\n".format(iol_id, i, wrapper_id, i))
    netmap_fd.close()

    # Preparing socket (IOL -> wrapper)
    try:
        os.unlink(read_fsocket)
    except OSError:
        if os.path.exists(read_fsocket):
            sys.stderr.write("ERROR: cannot delete existent socket")
            sys.exit(1)
    from_iol = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    from_iol.bind(read_fsocket)
    inputs.append(from_iol)

    # Preparing socket (wrapper -> IOL)
    if not os.path.exists(read_fsocket):
        sys.stderr.write("ERROR: IOL node not running\n")

    # Preparing socket (switcherd -> wrapper)
    from_switcherd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    from_switcherd.bind(('', UDP_PORT))
    inputs.append(from_switcherd)

    # Preparing socket (wrapper -> switcherd)
    to_switcherd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Preparing tap
    from_tun = open("/dev/net/tun", "r+b", buffering = 0)
    ifr = struct.pack('16sH', b"veth0", IFF_TAP | IFF_NO_PI)
    fcntl.ioctl(from_tun, TUNSETIFF, ifr)
    fcntl.ioctl(from_tun, TUNSETNOCSUM, 1)
    inputs.append(from_tun)

    # Starting IOL
    iol_args = [ "1" ]
    iol_env = { "PWD": os.path.dirname(iol_bin) }
    iol = subprocess.Popen([ iol_bin ] + iol_args, env = iol_env, cwd = os.path.dirname(iol_bin), stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    if enable_ts == True:
        inputs.extend([ iol.stdout.fileno(), iol.stderr.fileno() ])

    # Starting terminal server
    if enable_ts == True:
        if DEBUG: print("DEBUG: starting terminal server on {}".format(CONSOLE_PORT))
        #terminalServerStart(inputs)
        ts = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ts.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ts.bind(("", CONSOLE_PORT))
        ts.listen(1)
        inputs.append(ts)

    while inputs:
        if DEBUG: print("DEBUG: waiting for data")

        if iol.poll() != None:
            if DEBUG: print("ERROR: IOL process died")
            # Grab all output before exiting
            console_history += iol.stderr.read()
            console_history += iol.stdout.read()
            break

        readable, writable, exceptional = select.select(inputs, outputs, inputs)

        if "to_iol" not in locals():
            try:
                to_iol = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                to_iol.connect(write_fsocket)
            except Exception as err:
                sys.stderr.write("ERROR: cannot connect to IOL socket\n")
                del(to_iol)
                pass

        for s in readable:
            if s is from_iol:
                if DEBUG: print("DEBUG: data from IOL (TAP)")
                iol_datagram = from_iol.recv(IOL_BUFFER)
                if not iol_datagram:
                    sys.stderr.write("ERROR: cannot receive data from IOL node\n")
                    break
                else:
                    src_id, src_if, dst_id, dst_if, padding, payload = decodeIOLPacket(iol_datagram)
                    if src_id == MGMT_ID:
                        try:
                            os.write(from_tun.fileno(), payload)
                        except Exception as err:
                            sys.stderr.write("ERROR: cannot send data to MGMT\n")
                            sys.exit(2)
                    else:
                        try:
                            to_switcherd.sendto(encodeUDPPacket(label, src_if, payload), (switcherd, UDP_PORT))
                        except Exception as err:
                            sys.stderr.write("ERROR: cannot send data to switcherd\n")
                            sys.exit(2)
            elif s is from_switcherd:
                if DEBUG: print("DEBUG: data from UDP")
                udp_datagram, src_addr = from_switcherd.recvfrom(UDP_BUFFER)
                if not udp_datagram:
                    sys.stderr.write("ERROR: cannot receive data from switcherd\n")
                    sys.exit(2)
                else:
                    label, iface, payload = decodeUDPPacket(udp_datagram)
                    if "to_iol" in locals():
                        try:
                            to_iol.send(encodeIOLPacket(wrapper_id, iol_id, iface, payload))
                        except Exception as err:
                            sys.stderr.write("ERROR: cannot send data to IOL node\n")
                            break
                    else:
                        sys.stderr.write("ERROR: cannot connect to IOL socket, packet dropped\n")
            elif s is from_tun:
                if DEBUG: print("DEBUG: data from MGMT")
                tap_datagram = array.array('B', os.read(from_tun.fileno(), TAP_BUFFER))
                if "to_iol" in locals():
                    try:
                        to_iol.send(encodeIOLPacket(wrapper_id, iol_id, MGMT_ID, tap_datagram))
                    except Exception as err:
                        sys.stderr.write("ERROR: cannot send data to IOL MGMT\n")
                        break
                else:
                    sys.stderr.write("ERROR: cannot connect to IOL socket, packet dropped\n")
            elif s is iol.stdout.fileno():
                if DEBUG: print("DEBUG: data from IOL console (stdout)")
                data = iol.stdout.read(1)
                if time.time() - alive < MIN_TIME:
                    console_history += data
                inputs, clients = terminalServerSend(inputs, clients, data)
            elif s is iol.stderr.fileno():
                if DEBUG: print("DEBUG: data from IOL console (stderr)")
                data = iol.stderr.read(1)
                if time.time() - alive < MIN_TIME:
                    console_history += data
                inputs, clients = terminalServerSend(inputs, clients, data)
            elif s is ts:
                # New client
                title = "TEST"
                inputs, clients = terminalServerAccept(s, inputs, clients, title)
            elif s in clients:
                if DEBUG: print("DEBUG: data from client")
                data, inputs, clients = terminalServerReceive(s, inputs, clients)
                if data != None:
                    try:
                        iol.stdin.write(data)
                    except Exception as err:
                        sys.stderr.write("ERROR: cannot send data to IOL console\n")
                        break
            else:
                sys.stderr.write("ERROR: unknown source from select\n")

    inputs, clients = terminalServerClose(inputs, clients)

    if time.time() - alive < MIN_TIME:
        # IOL died prematurely
        sys.exit(2)
    else:
        # IOL died after a reasonable time
        sys.exit(0)

if __name__ == "__main__":
    alive = time.time()
    sys.excepthook = exceptionHandler
    atexit.register(exitHandler)
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exitGracefully)
    main()
