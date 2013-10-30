#!/usr/bin/python

class Player(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
empty = Player('empty', 'transparent')
players = {'empty': empty, 'root': Player('root', 'red')}

width = 10
height = 10
size = width * height
horizon = (width + height) / 4
class Cell(object):
    def __init__(self, parent, pos, owner):
        self.parent = parent
        self.pos = pos
        self.owner = owner
        self.board = None
    def scan(self, interval):
        collected = []
        cellidx = self.pos[-1]
        startmod = cellidx % width
        cell = self.parent.cells[cellidx]
        for i in range(horizon):
            cellidx += interval
            cellmod = cellidx % width
            if 1 == interval and cellmod < startmod: break
            if -1 == interval and cellmod > startmod: break
            if cellidx < 0 or cellidx >= size: break
            cellmod = cellidx
            cell = self.parent.cells[cellidx]
            if cell.owner.name != 'empty': break
            collected.append(cell)
        return cell, collected
    def claim(self, player):
        if self.owner == player: return 0
        self.owner = player
        score = 1
        for interval in (1, -1, width, -width):
            cell, collected = self.scan(interval)
            if cell.owner.name == player.name:
                score += sum([cell.claim(player) for cell in collected])
        return score

class Board(object):
    def __init__(self, parent):
        self.parent = parent
        self.cells = [Cell(self, parent.pos + [i], empty) for i in range(size)]
    def getmap(self): return [(cell.owner.name, cell.owner.color) for cell in self.cells]
board = Board(Cell(None, [], empty))

def getboard(pos):
    curboard = board
    for cellidx in pos:
        cell = curboard.cells[cellidx]
        if cell.board is None:
            cell.board = Board(cell)
        curboard = cell.board
    return curboard

from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse, parse_qs
from json import dumps
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if '.jsonp' != url.path[-6:]: return SimpleHTTPRequestHandler.do_GET(self)
        query = parse_qs(url.query)

        try: callback = query['callback'][-1]
        except KeyError: raise Exception('No callback specified')

        if '/player.jsonp' == url.path:
            if not 'name' in query: data = {'error': 'No name specified'}
            else:
                name = query['name'][-1]
                if name in players: player = players[name]
                else:
                    if not 'color' in query: data = {'error': 'No color specified'}
                    else:
                        color = query['color'][-1]
                        player = players[name] = Player(name, color)
                try: data = (player.name, player.color)
                except UnboundLocalError: pass
        else:
            try: curboard = getboard([int(i) for i in query['pos'][-1].split(',')])
            except KeyError: curboard = board
            if '/map.jsonp' == url.path:
                data = curboard.getmap()
            elif '/claim.jsonp' == url.path:
                try: name = query['name'][-1]
                except KeyError: data = {'error': 'No name specified'}
                else:
                    try: data = curboard.parent.claim(players[name])
                    except KeyError: data = {'error': 'No player ' + name}

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
    if 'KeyboardInterrupt' != exc_info()[0].__name__:
        raise
