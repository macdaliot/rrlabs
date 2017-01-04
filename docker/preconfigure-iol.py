#!/usr/bin/env python3

CMD = "./iol.bin -n 4096 -e 1 -s 0 1"
TIMEOUT = 120

import multiprocessing, pexpect, sys, time
from functions import *

def main():
        p = pexpect.spawnu(CMD, logfile = sys.stdout)

        i = -1
        i = p.expect(["Would you like to enter the initial configuration dialog?", pexpect.EOF ], timeout = TIMEOUT)
        if i == 1:
            sys.stderr.write("ERROR: IOL died\n")
            sys.exit(1)
        else:
            p.sendline("no")

        i = -1
        while i == -1:
            # Sending newline until we get a valid prompt
            try:
                i = p.expect([ "Router>", "Switch>" ], timeout = 5)
                if i == 0:
                    is_switch = False
                    hostname = "iolrouter"
                else:
                    is_switch = True
                    switch = "iolswitch"
            except:
                p.sendline("\r\n")
                i = -1

        p.sendline("enable")
        p.expect("#")
        p.sendline("configure terminal")
        p.expect("\(config\)#")
        p.sendline("username {} privilege 15 password {}".format(ADMIN_USER, ADMIN_PASSWORD))
        p.expect("\(config\)#")
        p.sendline("hostname {}".format(hostname))
        p.expect("\(config\)#")
        p.sendline("ip domain name example.com")
        p.expect("\(config\)#")
        p.sendline("crypto key generate rsa")
        p.expect("How many bits in the modulus")
        p.sendline("1024")
        p.expect("\(config\)#")
        p.sendline("interface ethernet0/0")
        p.expect("\(config-if\)#")
        if is_switch:
            p.sendline("no switchport")
            p.expect("\(config-if\)#")
        p.sendline("ip address 192.0.2.254 255.255.255.0")
        p.expect("\(config-if\)#")
        p.sendline("no shutdown")
        p.expect("\(config-if\)#")
        p.sendline("line vty 0 4")
        p.expect("\(config-line\)#")
        p.sendline("login local")
        p.expect("\(config-line\)#")
        p.sendline("transport input telnet ssh")
        p.expect("\(config-line\)#")
        p.sendline("end")
        p.expect("#")
        p.sendline("write memory")
        p.expect("OK")
        p.terminate()
                    
if __name__ == "__main__":
    sys.excepthook = exceptionHandler
    p = multiprocessing.Process(target = main)
    p.start()
    p.join(TIMEOUT)
    if p.is_alive():
        p.terminate()
        p.join()
        sys.stderr.write("ERROR: preconfiguration failed (timeout)\n")
        sys.exit(1)

