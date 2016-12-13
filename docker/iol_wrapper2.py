#!/usr/bin/env python3

import getopt, os, select, socket, sys

UDP_PORT = 5005
UDP_BUFFER = 9000
IOL_BUFFER = 1600

def usage():
    print("Usage: {} [OPTIONS]".format(sys.argv[0]))
    print("  -g hostname")
    print("     switcherd hostname or IP address")
    print("  -i iol_id")
    print("     IOL device ID")
    print("  -l label")
    print("     Node label")

def IOL2UDP(src_label, iol_datagram):
    # IOL datagram format (maximum observed size is 1555):
    # - 16 bits for the destination IOL ID
    # - 16 bits for the source IOL ID
    # - 8 bits for the destination interface (z = x/y -> z = x + 3 * 16)
    # - 8 bits for the source interface (z = x/y -> z = x + y * 16)
    # - 16 bits equals to 0x0100
    iol_src_if = iol_datagram[5]
    datagram = iol_datagram[8:]
    print("iol_src_if = {}".format(iol_src_if))
    return src_label.to_bytes(3, byteorder='big') + bytes([iol_src_if]) + datagram

def UDP2IOL(iol_id, wrapper_id, udp_datagram):
    # UDP datagram format:
    # - 24 bits for the node LABEL (up to 16M of nodes)
    # - 8 bits for the interface ID (up to 256 of per node interfaces)
    iol_dst_if = udp_datagram[3]
    datagram = udp_datagram[4:]
    print("iol_id = {}".format(iol_id))
    print("wrapper_id = {}".format(wrapper_id))
    print("iol_dst_if = {}".format(iol_dst_if))
    return iol_id.to_bytes(2, byteorder='big') + wrapper_id.to_bytes(2, byteorder='big') + iol_dst_if.to_bytes(1, byteorder='big') + iol_dst_if.to_bytes(1, byteorder='big') + (1024).to_bytes(2, byteorder='big') + datagram

def main():
    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "g:i:l:")
    except getopt.GetoptError as err:
        sys.stderr.write("ERROR: {}\n".format(err))
        usage()
        sys.exit(1)

    # Parsing options
    for o, a in opts:
        if o == "-g":
            switcherd = a
        elif o == "-i":
            iol_id = int(a)
        elif o == "-l":
            label = int(a)
        else:
            assert False, "unhandled option"

    # Checking options
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

    # Preparing socket (IOL -> wrapper)
    try:
        os.unlink(read_fsocket)
    except OSError:
        if os.path.exists(read_fsocket):
            raise
    from_iol = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    from_iol.bind(read_fsocket)

    # Preparing socket (wrapper -> IOL)
    if not os.path.exists(read_fsocket):
        sys.stderr.write("ERROR: IOL node not running\n")

    # Preparing socket (switcherd -> wrapper)
    from_switcherd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    from_switcherd.bind(('', UDP_PORT))

    # Preparing socket (wrapper -> switcherd)
    to_switcherd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    inputs = [ from_iol, from_switcherd ]
    outputs = [ ]

    while inputs:
        print("Waiting")
        readable, writable, exceptional = select.select(inputs, outputs, inputs)

        for s in readable:
            if s is from_iol:
                print("Data from iol")
                iol_datagram = from_iol.recv(IOL_BUFFER)
                if not iol_datagram:
                    sys.stderr.write("ERROR: cannot receive data from IOL node\n")
                    break
                else:
                    try:
                        to_switcherd.sendto(IOL2UDP(label, iol_datagram), (switcherd, UDP_PORT))
                    except Exception as err:
                        sys.stderr.write("ERROR: cannot send data to switcherd\n")
                        raise
            elif s is from_switcherd:
                print("Data from switcherd")
                udp_datagram, src_addr = from_switcherd.recvfrom(UDP_BUFFER)
                if not udp_datagram:
                    sys.stderr.write("ERROR: cannot receive data from switcherd\n")
                    break
                else:
                    if "to_iol" not in locals():
                        try:
                            to_iol = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                            to_iol.connect(write_fsocket)
                        except Exception as err:
                            sys.stderr.write("ERROR: cannot connect to IOL socket, packet dropped\n")
                            del(to_iol)
                            pass
                    if "to_iol" in locals():
                        try:
                            to_iol.send(UDP2IOL(iol_id, wrapper_id, udp_datagram))
                        except Exception as err:
                            sys.stderr.write("ERROR: cannot send data to IOL node\n")
                            raise
            else:
                sys.stderr.write("ERROR: unknown source from select\n")

if __name__ == "__main__":
    main()
