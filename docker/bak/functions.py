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
TS_BUFFER = 1
TUNSETNOCSUM = 0x400454c8
TUNSETDEBUG = 0x400454c9
TUNSETIFF = 0x400454ca
TUNSETPERSIST = 0x400454cb
TUNSETOWNER = 0x400454cc
TUNSETLINK = 0x400454cd
UDP_BUFFER = 10000
UDP_PORT = 5005

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

import socket, sys, threading, traceback

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

def exceptionHandler(t, v, tb):
    sys.stderr.write("ERROR: unmanaged exception\n")
    sys.stderr.write("Type: {}\n".format(t))
    sys.stderr.write("Value: {}\n".format(v))
    sys.stderr.write("Traceback:\n{}\n".format(traceback.print_tb(tb)))
    sys.exit(255)

def terminalServerAccept(client, inputs, clients, title):
    conn, addr = client.accept()
    if DEBUG: print("DEBUG: client {}:{} connected".format(addr[0], str(addr[1])))
    conn.send(bytes(IAC) + bytes(WILL) + bytes(ECHO))
    conn.send(bytes(IAC) + bytes(WILL) + bytes(SGA))
    conn.send(bytes(IAC) + bytes(WILL) + bytes(BINARY))
    conn.send(bytes(IAC) + bytes(DO) + bytes(BINARY))
    conn.send(b'\033' + b']' + b'0' + b';' + str.encode(title) + b'\007')
    conn.send(str.encode("Welcome {} \n".format(addr[0])))
    inputs.append(conn)
    clients.append(conn)
    return inputs, clients

def terminalServerClose(inputs, clients):
    if DEBUG: print("DEBUG: terminating connection")
    inputs, clients = terminalServerSend(inputs, clients, "Terminating connection")
    for client in clients:
        client.close()
        inputs.remove(client)
        client.remove(client)
    return inputs, clients

def terminalServerReceive(client, inputs, clients):
    if DEBUG: print("DEBUG: receiving data from client")
    try:
        data = client.recv(TS_BUFFER)
    except Exception as err:
        sys.stderr.write("ERROR: cannot receive data from client\n")
        inputs.remove(client)
        clients.remove(client)
    if (data):
        print(data)
        print("IAC")
    return data, inputs, clients

def terminalServerSend(inputs, clients, data):
    for client in clients:
        try:
            client.send(data)
        except:
            if DEBUG: print("DEBUG: removing broken client")
            client.close()
            inputs.remove(client)
            client.remove(client)
    return inputs, clients


