#!/usr/bin/python

class Player(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.stakes = [None for i in range(20)]
empty = Player('empty', 'transparent')
players = {'empty': empty, 'root': Player('root', 'red')}

class Board(object):
    def __init__(self, parent, owner):
        self.parent = self if parent is None else parent
        self.owner = owner
        self.cells = [owner for i in range(100)]
    def getmap(self):
        return [
            (cell.owner.name, cell.owner.color) if type(cell) is Board
            else (cell.name, cell.color)
            for cell in self.cells
        ]
    def claim(self, player):
        self.owner = player
        return True

        print i, user
board = Board(None, empty)

def getboard(pos):
    curboard = board
    for cellidx in pos:
        cur = curboard.cells[cellidx]
        if type(cur) is Player:
            curboard.cells[cellidx] = Board(curboard, cur)
            curboard = curboard.cells[cellidx]
        else: curboard = cur
    return curboard

from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse, parse_qs
from json import dumps
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if '.jsonp' != url.path[-6:]: return SimpleHTTPRequestHandler.do_GET(self)
        query = parse_qs(url.query)

        try: callback = query['callback'][0]
        except KeyError: raise Exception('No callback specified')

        if '/player.jsonp' == url.path:
            try: data = query['name'][0]
            except KeyError: data = {'error': 'No name specified'}
        else:
            try: curboard = getboard([int(i) for i in query['pos'][0].split(',')])
            except KeyError: curboard = board
            if '/map.jsonp' == url.path:
                data = curboard.getmap()
            elif '/claim.jsonp' == url.path:
                try: name = query['name'][0]
                except KeyError: data = {'error': 'No name specified'}
                else:
                    data = curboard.claim(players[name])

        try: data
        except NameError: data = {'error': 'Did not understand ' + url.path}

        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.wfile.write(callback + '(' + dumps(data) + ');')

from SocketServer import TCPServer
TCPServer.allow_reuse_address = True
server = TCPServer(('', 8000), Handler)
try:
    server.serve_forever()
except:
    server.server_close()
    from sys import exc_info
    if 'KeyboardInterrupt' != exc_info()[0].__name__: raise
