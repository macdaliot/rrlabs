#!/usr/bin/env python3

import array, atexit, fcntl, getopt, os, select, signal, socket, struct, subprocess, sys, time
from functions import *

def exitHandler():
    if DEBUG: print("DEBUG: exiting")

def signalHandler(signum, frame):
    if DEBUG: print("DEBUG: signum {} received".format(signum))

    if signum == 1:
        print("RELOAD")
    if signum == 2:
        signal.signal(signal.SIGINT, original_sigint)
        print("CTRL+C")
        # restore the exit gracefully handler here
        signal.signal(signal.SIGINT, exitHandler)
    if signum == 15:
        signal.signal(signal.SIGTERM, original_sigterm)
        print("TERM")
        # restore the exit gracefully handler here
        signal.signal(signal.SIGTERM, exitHandler)

def main():
    # Example A: R1:e0/1 <-> R2:e0/2
    #                     |- R3:e0/3
    # - R1:e0/1 -> label = 53, iface = 16
    # - R2:e0/2 -> label = 54, iface = 32
    # - R3:e0/3 -> label = 55, iface = 48
    TopA = { }
    TopA[ 53 * 256 + 16 ] = [ 54 * 256 + 32, 55 * 256 + 48 ]
    TopA[ 54 * 256 + 32 ] = [ 53 * 256 + 16, 55 * 256 + 48 ]
    TopA[ 55 * 256 + 48 ] = [ 53 * 256 + 16, 54 * 256 + 32 ]
    IPAddrA = { }
    IPAddrA[ 53 ] = "172.17.0.2"
    IPAddrA[ 54 ] = "172.17.0.3"
    IPAddrA[ 55 ] = "172.17.0.4"
    # docker run --privileged -d --name node-53 eveng/iol:L3-ADVENTERPRISEK9-M-15.5-2T /sbin/start_node.sh -e 1 -s 1 -g 172.17.0.1 -i 1 -l 53 -s 1-t -w R1
    # docker run --privileged -d --name node-54 eveng/iol:L3-ADVENTERPRISEK9-M-15.5-2T /sbin/start_node.sh -e 1 -s 1 -g 172.17.0.1 -i 1 -l 54 -s 1-t -w R2
    # docker run --privileged -d --name node-55 eveng/iol:L3-ADVENTERPRISEK9-M-15.5-2T /sbin/start_node.sh -e 1 -s 1 -g 172.17.0.1 -i 1 -l 55 -s 1-t -w R3

    topology = TopA
    print(topology)

    from_nodes = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    from_nodes.bind(('', UDP_PORT))
    to_nodes = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # to_nodes.sendto(encodeUDPPacket(label, src_if, payload), (IPADDR, UDP_PORT))
    


if __name__ == "__main__":
    sys.excepthook = exceptionHandler
    atexit.register(exitHandler)
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGHUP, signalHandler)     # 1
    signal.signal(signal.SIGINT, signalHandler)     # 2
    signal.signal(signal.SIGTERM, signalHandler)    # 15
    main()

