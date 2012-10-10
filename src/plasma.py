import logging
import socket
import select
import threading

def shopSimpleStart(simplateId, simpleId):
    sendMessage('shopSimpleStart', simplateId, simpleId)

def shopSimpleResult(simplateId, simpleId, result):
    sendMessage('shopSimpleResult', simplateId, simpleId, result)

def shopStartSession(simplateId):
    sendMessage('shopStartSession', simplateId)

def shopEndSession(simplateId):
    sendMessage('shopEndSession', simplateId)

_isInitialized = False
_sck = None
_sockets = []
_lock = threading.RLock()

def init(host, port):
    """
        Initializes the plasma TCP server to listen to a specific port on a specific host
    """

    if isInitialized():
        logging.warning("trying to initialize plasma server twice")
        return

    global _isInitialized 
    _isInitialized = True
    
    global _sck
    _sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _sck.bind((host, port))
    _sck.listen(3)

    logging.info("Initialized a plasma server on host '%s', port %d", host, port)


def isInitialized():
    return _isInitialized

def _checkInitialized():
    if not isInitialized():
        logging.error("Not initialized")
        raise Exception("Not initialized")


def serve():
    """
        Starts accepting connection
    """

    _checkInitialized()

    global _sck
    global _sockets

    logging.info("Starting a plasma server")
    
    while True:
        try:
            readyToRead = select.select( 
                [_sck] + _sockets, # read
                [], [], # write, errors
                1 # timeout
                )[0]
        except Exception:
            a = _sck.fileno() #should raise an exception on error
            with _lock:
                newSockets = []
                for socket in _sockets:
                    try:
                        a = socket.fileno()
                        h = socket.getpeername()
                        print a, h
                    except Exception:
                        continue
                    newSockets.append(socket)
                _sockets[:] = newSockets
            continue

        if not readyToRead:
            continue

        if _sck in readyToRead:
            newSocket, addr = _sck.accept()
            logging.info("Accepted a new connetion from %s", unicode(addr))
            with _lock:
                _sockets.append(newSocket)
                
        for socket in readyToRead:
            if socket is not _sck:
                if not _readAll(socket):
                    with _lock:
                        _sockets.remove(socket)


def _readAll(socket):
    """
        logs everything that came from socket.
        nothing should come
    """
    socket.settimeout(0)
    try:
        data = socket.recv(4096)
        if not data:
            return False
        logging.warning("Read from plasma: %s", unicode(data).strip('\r\n'))
    except Exception:
        pass

    return True


def sendMessage(messageId, firstParam, *params):
    """
        sends a message to all connected clients.
    """
    _checkInitialized()

    sockets = []
    with _lock:
        sockets += _sockets


    toSend = '{"eventId":' + _quoteParam(messageId) + ',"params":[' + _quoteParam(firstParam)
    for p in params:
        toSend += ',' + _quoteParam(p)

    toSend += ']}\n'

    if not sockets:
        logging.warning("Ignoring a message to plasma: %s", toSend.strip('\r\n'))
        return

    logging.info("Sending to plasma (%d clients): %s", len(sockets), toSend.strip('\r\n'))

    for s in sockets:
        try:
            s.send(toSend)
        except Exception:
            pass

def _quoteParam(param):
    '''
        A very dummy implementation of quoting

        TODO: add more details if needed
    '''
    if type(param) in (int, float, long):
        return str(param)
    return '"' + unicode(param) + '"'
    

    

        




    
