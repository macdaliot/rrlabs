#!/usr/bin/env python3
from pexpect import pxssh
import getpass, logging, pexpect

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

password = getpass.getpass('admin\'s password: ')
handler = pxssh.pxssh()
handler.PROMPT = 'admin:'
handler.UNIQUE_PROMPT = 'admin:'
handler.login(server = '172.25.83.51', username = 'admin', password = password, auto_prompt_reset = False, original_prompt = 'admin:')
handler.sendline('show version active')
handler.prompt()
o = handler.before.decode()
print(o)
handler.logout()
