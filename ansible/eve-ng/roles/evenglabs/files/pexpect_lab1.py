#!/usr/bin/env python3
import logging, pexpect
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = pexpect.spawn('telnet 127.0.0.1 32781')

# Send an empty line, and wait for the login prompt
i = -1
while i == -1:
    try:
        handler.sendline('\r\n')
        logging.info('waiting for the prompt')
        i = handler.expect([
            'Username:',
            '\)#',
            '>',
            '#',
            'Would you like to enter the'], timeout = 5)
        o = handler.before.decode()
    except:
        logging.info('prompt not found')
        i = -1
        pass

logging.info('prompt found')
logging.debug(o)

if i == 4:
    # Device is unconfigured
    handler.sendline('no')
    logging.info('waiting for get started')
    i = handler.expect('Press RETURN to get started', timeout = 120)
    o = handler.before.decode()
    logging.debug(o)

    j = -1
    while j == -1:
        try:
            handler.sendline('\r\n')
            logging.info('waiting for the unprivileged prompt')
            j = handler.expect('>', timeout = 5)
            o = handler.before.decode()
        except:
            logging.info('prompt not found')
            j = -1
            pass
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('enable')
    logging.info('waiting for the privileged prompt')
    i = handler.expect('#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('configure terminal')
    logging.info('waiting for the configuration prompt')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('username admin privilege 15 password cisco')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('line vty 0 4')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('login local')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('interface Ethernet0/3')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('ip address dhcp')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('no shutdown')
    i = handler.expect('\)#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('end')
    i = handler.expect('#', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
    handler.sendline('logout')
    i = handler.expect('Press RETURN to get started', timeout = 5)
    o = handler.before.decode()
    logging.debug(o)
