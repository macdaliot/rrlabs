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
    # docker run --privileged -d --name node-53 eveng/iol:L3-ADVENTERPRISEK9-M-15.5-2T /sbin/start_node.sh -e 1 -s 1 -g 172.17.0.1 -i 1 -l 53 -t -w R1
    # docker run --privileged -d --name node-54 eveng/iol:L3-ADVENTERPRISEK9-M-15.5-2T /sbin/start_node.sh -e 1 -s 1 -g 172.17.0.1 -i 2 -l 54 -t -w R2
    # docker run --privileged -d --name node-55 eveng/iol:L3-ADVENTERPRISEK9-M-15.5-2T /sbin/start_node.sh -e 1 -s 1 -g 172.17.0.1 -i 3 -l 55 -t -w R3

    topology = TopA
    ip_addrs = IPAddrA
    print(topology)

    from_nodes = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    from_nodes.bind(('', UDP_PORT))
    to_nodes = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        udp_datagram, src_addr = from_nodes.recvfrom(UDP_BUFFER)
        if not udp_datagram:
            sys.stderr.write("ERROR: cannot receive data from nodes\n")
            sys.exit(2)
        else:
            src_node_id, src_iface_id, payload = decodeUDPPacket(udp_datagram)
            src_label = src_node_id * 256 + src_iface_id
            if src_label in topology:
                for dst_label in topology[src_label]:
                    dst_node_id = dst_label // 256
                    dst_iface_id = dst_label % 256
                    if dst_node_id in ip_addrs:
                        if DEBUG: print("DEBUG: sending to {} {}:{}".format(ip_addrs[dst_node_id], dst_node_id, dst_iface_id))
                        to_nodes.sendto(encodeUDPPacket(dst_node_id, dst_iface_id, payload), (ip_addrs[dst_node_id], UDP_PORT))
                    else:
                        if DEBUG: print("DEBUG: cannot find node IP for label {}, topology is corrupted".format(dst_label))
            else:
                if DEBUG: print("DEBUG: {} not active in the current topology".format(dst_label))

if __name__ == "__main__":
    sys.excepthook = exceptionHandler
    atexit.register(exitHandler)
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGHUP, signalHandler)     # 1
    signal.signal(signal.SIGINT, signalHandler)     # 2
    signal.signal(signal.SIGTERM, signalHandler)    # 15
    main()

