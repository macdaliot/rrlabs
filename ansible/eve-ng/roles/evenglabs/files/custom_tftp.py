#!/usr/bin/env python3
# https://networklore.com/ztp-tutorial/install-fbtftp/
# https://github.com/facebook/fbtftp/tree/master/examples
from fbtftp.base_handler import BaseHandler
from fbtftp.base_server import BaseServer
import io, logging, os

LISTEN_ON = '192.0.2.1'
SERVER_PORT = 69
TFTP_ROOT = '/opt/customtftp/tftproot'
RETRIES = 3
TIMEOUT = 5

class TftpData:
    def __init__(self, filename, client):
        path = os.path.join(TFTP_ROOT, filename)
        if client[0] == '192.0.2.13':
            self._content = """
hostname IOS
no ip domain-lookup
interface Ethernet0/1
 ip address 192.168.0.1 255.255.255.0
 no shutdown
"""
            self._content = str.encode(self._content)
            self._size = len(self._content)
            self._reader = io.BytesIO(self._content)
        else:
            self._size = os.stat(path).st_size
            self._reader = open(path, 'rb')

    def read(self, data):
        return self._reader.read(data)

    def size(self):
        return self._size

    def close(self):
        self._reader.close()

class StaticHandler(BaseHandler):
    def get_response_data(self):
        return TftpData(self._path, self._peer)

class TftpServer(BaseServer):
    def get_handler(self, server_addr, peer, path, options):
        return StaticHandler(server_addr, peer, path, options, session_stats)

def session_stats(stats):
    logging.info('#' * 60)
    logging.info('Peer: {} UDP/{}'.format(stats.peer[0], stats.peer[1]))
    logging.info('File: {}'.format(stats.file_path))
    logging.info('Sent Packets: {}'.format(stats.packets_sent))
    logging.info('#' * 60)

def main():
    server = TftpServer(LISTEN_ON, SERVER_PORT, RETRIES, TIMEOUT)
    try:
        server.run()
    except KeyboardInterrupt:
        server.close()


if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main()
