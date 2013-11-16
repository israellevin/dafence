#!/usr/bin/python

from time import time
class Player(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.stakes = 5.0;
        self.cells = set()
        self.updatetime = time()
    def getstakes(self):
        now = time()
        self.stakes += len(self.cells) * 0.1 * (now - self.updatetime)
        self.updatetime = now
        return self.stakes
players = {'root': Player('root', 'blue')}

cells = {0: {0: {0: players['root']}}}
def getcell(level, row, col):
    try: return cells[level][row][col]
    except KeyError: return None
def getcellcolor(level, row, col):
    try: return getcell(level, row, col).color
    except AttributeError: return None
def getrowcolors(level, row, left, right):
    try: cells[level][row]
    except KeyError: return None
    return {col: getcellcolor(level, row, col) for col in range(left, right)}
def getsquarecolors(level, top, bottom, left, right):
    try: cells[level]
    except KeyError: return None
    return {row: getrowcolors(level, row, left, right) for row in range(top, bottom)}

claimrange = 5
def claim(player, level, row, col, power):
    try: cells[level]
    except KeyError: cells[level] = {}
    try: cells[level][row]
    except KeyError: cells[level][row] = {}
    if getcell(level, row, col) is player: return 0
    cells[level][row][col] = player
    player.cells.add((level, row, col))
    score = 1

    for direction in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        annexed = []
        for offset in range(1, claimrange + 1):
            currow, curcol = map(lambda p, d: p + (d * offset), (row, col), direction)
            cell = getcell(level, currow, curcol)
            if cell is not None: break
            annexed.append((currow, curcol))
        if cell is player:
            score += sum([claim(player, level, currow, curcol, power) for currow, curcol in annexed])
    return score

from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse, parse_qs
from json import dumps
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if '.jsonp' != url.path[-6:]: return SimpleHTTPRequestHandler.do_GET(self)
        query = parse_qs(url.query)
        if 'callback' not in query: raise Exception('No callback specified')
        callback = query['callback'][-1]

        if '/player.jsonp' == url.path:
            if 'name' not in query: data = {'error': 'No name specified'}
            else:
                name = query['name'][-1]
                if name in players: player = players[name]
                else:
                    if 'color' not in query: data = {'error': 'No color specified'}
                    else: player = players[name] = Player(name, query['color'][-1])
            try: data = (player.color, player.stakes)
            except UnboundLocalError: pass
        elif '/map.jsonp' == url.path:
            try: data = getsquarecolors(
                int(query['level'][-1]),
                int(query['top'][-1]),
                int(query['bottom'][-1]),
                int(query['left'][-1]),
                int(query['right'][-1])
            )
            except (AttributeError, ValueError) as e:
                print e
                data = {'error': 'No valid position specified'}
        elif '/claim.jsonp' == url.path:
            try:
                player = players[query['name'][-1]]
                level = int(query['level'][-1])
                row = int(query['row'][-1])
                col = int(query['col'][-1])
                power = int(query['pow'][-1])
            except (AttributeError, ValueError) as e:
                print e
                data = {'error': 'Invalid claim'}
            else:
                if(player.getstakes() < power): data = {'error': 'Not enough stakes'}
                else:
                    player.stakes -= 1
                    data = claim(player, level, row, col, power)
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
