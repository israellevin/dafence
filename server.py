#!/usr/bin/python

class Board():
    def setowner(self, owner):
        self.owner = owner
    def __init__(self, parent, owner):
        self.cells = [None for i in range(100)]
        self.parent = parent
        self.setowner(owner)

board = Board(None, 'root')

from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse, parse_qs
from json import dumps
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if '/map.js' == url.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            curBoard = board
            try:
                pos = parse_qs(url.query)['pos'][0].split(',')
                for cellidx in pos:
                    cellidx = int(cellidx)
                    if curBoard.cells[cellidx] is None:
                        curBoard.cells[cellidx] = Board(curBoard, curBoard.owner)
                    curBoard = curBoard.cells[cellidx]
            except KeyError:
                pass
            map = ['empty' if cell is None else cell.owner for cell in curBoard.cells]
            self.wfile.write('map = ' + dumps(map) + ';')
        elif '/own.js' == url.path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write('console.log(\'not supported\');')
        else: SimpleHTTPRequestHandler.do_GET(self)

from SocketServer import TCPServer
TCPServer.allow_reuse_address = True
server = TCPServer(('', 8000), Handler)
try:
    server.serve_forever()
except(KeyboardInterrupt, SystemExit):
    server.server_close()
    from sys import exit
    exit(0)
