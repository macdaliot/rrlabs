#!/usr/bin/env python3

CONSOLE_PORT = 5005
DEBUG = True
IFF_NO_PI = 0x1000
IFF_TAP = 0x0002
IOL_BUFFER = 1600
MGMT_ID = 0
MGMT_NAME = "veth0"
MIN_TIME = 5
TAP_BUFFER = 10000
SELECTTIMEOUT = 0.5
TUNSETNOCSUM = 0x400454c8
TUNSETDEBUG = 0x400454c9
TUNSETIFF = 0x400454ca
TUNSETPERSIST = 0x400454cb
TUNSETOWNER = 0x400454cc
TUNSETLINK = 0x400454cd
UDP_BUFFER = 10000
UDP_PORT = 5005

import socket, sys

def decodeIOLPacket(iol_datagram):
    # IOL datagram format (maximum observed size is 1555):
    # - 16 bits for the destination IOL ID
    # - 16 bits for the source IOL ID
    # - 8 bits for the destination interface (z = x/y -> z = x + 3 * 16)
    # - 8 bits for the source interface (z = x/y -> z = x + y * 16)
    # - 16 bits equals to 0x0100
    dst_id = int.from_bytes(iol_datagram[0:1], byteorder='big')
    src_id = int.from_bytes(iol_datagram[2:3], byteorder='big')
    dst_if = iol_datagram[4]
    src_if = iol_datagram[5]
    padding = 256 * iol_datagram[6] + iol_datagram[7]
    payload = iol_datagram[8:]
    if DEBUG: print("DEBUG: IOL packet src={}:{} dst={}:{} padding={} payload={}".format(src_id, src_if, dst_id, dst_if, padding, sys.getsizeof(payload)))
    return src_id, src_if, dst_id, dst_if, padding, payload

def encodeIOLPacket(src_id, dst_id, iface, payload):
    return dst_id.to_bytes(2, byteorder='big') + src_id.to_bytes(2, byteorder='big') + iface.to_bytes(1, byteorder='big') + iface.to_bytes(1, byteorder='big') + (256).to_bytes(2, byteorder='big') + payload

def decodeUDPPacket(udp_datagram):
    # UDP datagram format:
    # - 24 bits for the node LABEL (up to 16M of nodes)
    # - 8 bits for the interface ID (up to 256 of per node interfaces)
    label = int.from_bytes(udp_datagram[0:2], byteorder='little')
    iface = int(udp_datagram[3])
    payload = udp_datagram[4:]
    if DEBUG: print("DEBUG: UDP packet label={} iface={} payload={}".format(label, iface, sys.getsizeof(payload)))
    return label, iface, payload

def encodeUDPPacket(label, iface, payload):
    return label.to_bytes(3, byteorder='little') + iface.to_bytes(1, byteorder='little') + payload

def terminalServer():
    ts = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ts.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ts.bind(("", CONSOLE_PORT))
    ts.listen(1)
    
    while True:
        client, addr = ts.accept()



