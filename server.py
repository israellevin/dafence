#!/usr/bin/python

ownerships = {}
def getowner(level, row, col):
    try: return ownerships[level][row][col]
    except KeyError: return None
def getownercolor(level, row, col):
    try: return getowner(level, row, col).color
    except AttributeError: return None
def getrowcolors(level, row, left, right):
    try: ownerships[level][row]
    except KeyError: return None
    return {col: getownercolor(level, row, col) for col in range(left, right)}
def getsquarecolors(level, top, bottom, left, right):
    try: ownerships[level]
    except KeyError: return None
    return {row: getrowcolors(level, row, left, right) for row in range(top, bottom)}

from time import time
class Player(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.stakes = 5.0;
        self.ownerships = set()
        self.updatetime = time()
    def getstakes(self):
        now = time()
        self.stakes += len(self.ownerships) * 0.1 * (now - self.updatetime)
        self.updatetime = now
        return self.stakes
    def surrender(self, pos):
        self.getstakes()
        self.ownerships.remove(pos)
players = {'root': Player('root', 'blue')}

claimrange = 5
def claim(player, level, row, col, power):
    if getowner(level, row, col) is player: return 0

    try: ownerships[level]
    except KeyError: ownerships[level] = {}
    try: ownerships[level][row]
    except KeyError: ownerships[level][row] = {}

    pos = (level, row, col)
    try: oldowner = ownerships[level][row][col]
    except KeyError: pass
    else: oldowner.surrender(pos)
    ownerships[level][row][col] = player
    player.ownerships.add(pos)
    score = 1

    for direction in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        annexed = []
        for offset in range(1, claimrange + 1):
            currow, curcol = map(lambda p, d: p + (d * offset), (row, col), direction)
            owner = getowner(level, currow, curcol)
            if owner is player:
                score += sum([
                    claim(player, level, currow, curcol, power)
                    for currow, curcol in annexed
                ])
                break
            annexed.append((currow, curcol))
    return score
claim(players['root'], 0, 0, 0, 1)

def handleclaim(args):
    try:
        player = players[args['name'][-1]]
        level = int(args['level'][-1])
        row = int(args['row'][-1])
        col = int(args['col'][-1])
        power = int(args['pow'][-1])
    except (KeyError, ValueError) as e: return {
        'error': 'Invalid claim',
        'exception': str(e)
    }
    else:
        print player.getstakes()
        if player.getstakes() < power: return {'error': 'Not enough stakes'}
        if getowner(level, row, col) is player: return {'error': 'No double dipping'}
        player.stakes -= power
        return claim(player, level, row, col, power)

def handlemap(args):
    try: data = {'colors': getsquarecolors(
        int(args['level'][-1]),
        int(args['top'][-1]),
        int(args['bottom'][-1]),
        int(args['left'][-1]),
        int(args['right'][-1])
    )}
    except (KeyError, ValueError) as e: data = {
        'error': 'No valid position specified',
        'exception': str(e)
    }
    try: player = players[args['name'][-1]]
    except KeyError: pass
    else: data['stakes'], data['ownerships'] = player.getstakes(), len(player.ownerships)
    return data

def handleplayer(args):
    try: name = args['name'][-1]
    except KeyError: return {'error': 'No name specified'}
    try: player = players[name]
    except KeyError:
        try: player = players[name] = Player(name, args['color'][-1])
        except KeyError: return {'error': 'No color specified'}
    return (player.color, player.stakes)

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

        if '/player.jsonp' == url.path: data = handleplayer(query)
        elif '/map.jsonp' == url.path: data = handlemap(query)
        elif '/claim.jsonp' == url.path: data = handleclaim(query)
        else: data = {'error': 'Did not understand ' + url.path}

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
