#!/usr/bin/env python3

import os, socket, sys

read_socket = "/tmp/netio0/1024"
write_socket = "/tmp/netio0/1"

try:
    os.unlink(read_socket)
except OSError:
    if os.path.exists(read_socket):
        raise
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(read_socket)
sock.listen(1)
while True:
    #print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    try:
        print("connected")
        #print >>sys.stderr, 'connection from', client_address
        while True:
            data = connection.recv(16)
            print("received data")
            #print >>sys.stderr, 'received "%s"' % data
            if data:
                print("sent data")
                #print >>sys.stderr, 'sending data back to the client'
                connection.sendall(data)
            else:
                print("no more data")
                #print >>sys.stderr, 'no more data from', client_address
                break
    finally:
        connection.close()




