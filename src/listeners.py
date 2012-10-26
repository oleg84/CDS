import bjsonrpc
from bjsonrpc.handlers import BaseHandler
from bjsonrpc.exceptions import ServerError
import logging
import cds_settings
import inspect
import db
import datetime
import simple
import collections
import threading
import time

def _function():
    return inspect.stack()[1][3]
def _functionCaller():
    return inspect.stack()[2][3]

def _logFunction(*args):
    isFirst = True;
    s = ''
    for arg in args:
        if not isFirst:
            s+= ' '
        s += unicode(arg)
        ifFirst = False
    logging.info("%s(%s)", _functionCaller(), s)

#########################################
class SimplateServerHandler(BaseHandler):
    def _shutdown(self):
        logging.info("disconnected, simplateId=%s", unicode(self.simplateId))
        db.CancelLastAllowedTime()

    def _setup(self):
        self.scenarioId = None
        self.simplateId = None 
        self.cardId = None

    def ping(self):
        logging.debug("Ping from simplate %s", unicode(self.simplateId))
        return

### Common methods
    def getLocalTime(self):
        now = datetime.datetime.now()
        return {'day' : now.day, 'hour' : now.hour}

    def getUtcTime(self):
        now = datetime.datetime.utcnow()
        return {'day' : now.day, 'hour' : now.hour}
        
    def registrate(self, scenarioId, simplateId):
        if self._isRegistered():
            logging.error("Duplicate registration from simplate id %s, scenarioId %d", unicode(simplateId), scenarioId)
            raise ServerError("Already registered")

        if scenarioId not in (cds_settings.SCENARIO_ID_Bar, cds_settings.SCENARIO_ID_Shop):
            logging.error("Unknown scenarioId %d", scenarioId)
            raise ServerError("Unknown scenarioId")

        _logFunction("scenarioId=",  scenarioId,  ", simplateId=", simplateId)
        self.scenarioId = scenarioId
        self.simplateId = simplateId
    
    def startSession(self, cardId, clientInfo):
        self._checkRegistered()
        if self._isSessionStarted():
            logging.error("Duplicate start session from simplate id %s, cardId %s", unicode(self.simplateId), unicode(cardId))
            raise ServerError("Session already started")
            
        _logFunction("simplateId=", self.simplateId, ", cardId=",  cardId,  ", clientInfo=", clientInfo)
        
        client = db.getClient(cardId)
        if not client:
            if self._isShopScenario():
                if cds_settings.MAKE_VIP_CLIENTS:
                    isVip = 1
                else:
                    isVip = 0
                client = db.createClient(cardId, cds_settings.CLIENT_INITIAL_BALANCE, isVip, clientInfo)
                
            elif self._isBarScenario():
                logging.warning("An unknown client came to the bar. Card id = %s", unicode(cardId))
                raise ServerError("Unknown client")

            else: #this should never happen
                logging.critical("Unknown scenarioId: %d:", self.scenarioId)
                raise ServerError("Unknown scenarioId")

        if not client:
            logging.critical("Could not get client information")
            raise ServerError("Internal server error. See logs")

        self.cardId = cardId
        return client


    def endSession(self, updatedAccountInfo):
        self._checkRegistered()
        self._checkSessionStarted()
        _logFunction("simplateId=", self.simplateId, ", updatedAccountInfo=",  updatedAccountInfo)

        cardId = self.cardId
        self.cardId = None
        if type(updatedAccountInfo) is not dict or 'balance' not in updatedAccountInfo or 'coupons' not in updatedAccountInfo:
            log.error("Wrong format of the updatedAccountInfo %s", unicode(updatedAccountInfo))
            raise ServerError("Internal server error. See logs")

        if not db.updateClient(cardId, updatedAccountInfo['balance'], updatedAccountInfo['coupons']):
            log.error("Could not update client account info, cardId: %s", unicode(seld.cardId))
            raise ServerError("Internal server error. See logs")
        return 

### Shop methods
    def simpleStart(self, simpleId):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId, ", simpleId=",  simpleId)
        return 

    def simpleResult(self, simpleId, result):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId, ", simpleId=",  simpleId, ", result=", result)
        if not isinstance(result, collections.Iterable) or len(result) != 2:
            raise ServerError("simpleResult incorrect type. Should be a tuple of 2")

        simple.ProcessSimpleResult(simpleId, result)
    
    def simpleEnd(self, simpleId):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId, ", simpleId=",  simpleId)


    def shouldStartBigShow(self):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        ret = db.ShouldStartBigShow(cds_settings.BIG_SHOW_INTERVAL_SECONDS, cds_settings.BIG_SHOW_SIMPLATE_TIMEOUT_SECONDS)
        _logFunction("simplateId=", self.simplateId, ", returning: ", ret)
        return ret

    def getFeedbackStatistics(self):
        self._checkRegistered()
        self._checkSessionStarted()
#         self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId)
        return db.GetFeedbackStatistics()

    def sendToSlave(self, *args):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId, ", args: ", args)
        SendToSlave(self.simplateId, *args)

### Bar methods

    def barOrderInfo(self, drinks):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfBarSimplate()
        _logFunction("simplateId=", self.simplateId, " ,drinks=", drinks)
        AddBarOrders(drinks, self.simplateId)
        SendBarOrders(None)
        return

        

### private methods
    def _checkIfShopSimplate(self):
        if not self._isShopScenario():
            logging.error("%s called for a non-Shop simplate", _functionCaller())
            raise ServerError("Wrong method")

    def _checkIfBarSimplate(self):
        if not self._isBarScenario():
            logging.error("%s called for a non-Bar simplate", _functionCaller())
            raise ServerError("Wrong method")

    def _checkRegistered(self):
        if not self._isRegistered():
            logging.error("%s called before registering", _functionCaller())
            raise ServerError("Not registered")

    def _checkSessionStarted(self):
        if not self._isSessionStarted():
            logging.error("%s called before session started", _functionCaller())
            raise ServerError("Session not started")
            
    def _isShopScenario(self):
        return self.scenarioId == cds_settings.SCENARIO_ID_Shop

    def _isBarScenario(self):
        return self.scenarioId == cds_settings.SCENARIO_ID_Bar
            
    def _isRegistered(self):
        if self.simplateId:
            return True
        else:
            return False

    def _isSessionStarted(self):
        if self.cardId:
            return True
        else:
            return False


### Bar methods
_lock = threading.RLock()
_barConnections = []
_barOrderId = 0
_barOrderCache = {} #holds lists of [drink, simplateId, isSent]

def AddBarOrders(drinks, simplateId):
    global _barOrderCache
    global _barOrderId
    with _lock:
        for drink in drinks:
            _barOrderCache[_barOrderId] = [drink, simplateId, False]
            _barOrderId += 1

def SendBarOrders(newConnection):
    global _barOrderCache

    with _lock:

        if not _barConnections and not newConnection:
            logging.warning("Cannot send bar orders. No bar is connected. Pending order count: %d", len(_barOrderCache))
            return

        logging.info("%d orders to bar pending", len(_barOrderCache))
        sent = 0
        sent_new = 0
        for id in _barOrderCache.keys():
            order = _barOrderCache[id]

            if not order[2]: #send to existing connection only if not isSent
                order[2] = True
                sent += 1
                for c in _barConnections:
                    c.method.newBarOrder(order[0], id, order[1])

            if newConnection: #forcibly send to a new connection
                order[2] = True
                newConnection.method.newBarOrder(order[0], id, order[1])
                sent_new += 1

        if sent:
            logging.info("%d orders sent to bar", sent)
        if sent_new:
            logging.info("%d orders sent to a newly connected bar", sent_new)



def RemoveBarOrder(id):
    global _barOrderCache
    with _lock:
        if id in _barOrderCache:
            if not _barOrderCache[id][2]:
                logging.warning("Deleting an unsent order: %s", unicode(_barOrderCache[id]))
            del _barOrderCache[id]
        else:
            logging.warning("Order does not exist: %d", id)



#########################################
class BarServerHandler(BaseHandler):
    def _shutdown(self):
        logging.info("bar disconnected")
        global _barConnections
        with _lock:
            _barConnections.remove(self._conn)
        
    def _setup(self):
        logging.info("bar connected")

    def registrate(self):
        logging.info("bar registered")
        global _barConnections
        SendBarOrders(self._conn)
        with _lock:
            _barConnections.append(self._conn)

    def ping(self):
        logging.info("Ping from bar") #TODO: make debug if ping is too often
        return

    def barOrderDone(self, orderId):
        logging.info("Bar order done, orderId=%d", orderId)
        RemoveBarOrder(orderId)

### Slave simplate methods
_lockSlaveSimplate = threading.RLock()
_slaveSimplateConnections = {}

def AddSlaveSimplateConnection(simplateId, conn):
    global _slaveSimplateConnections
    with _lockSlaveSimplate:
        try:
            connectionList = _slaveSimplateConnections[simplateId]
        except KeyError:
            connectionList = []

        connectionList.append(conn)

        _slaveSimplateConnections[simplateId] = connectionList


def RemoveSlaveSimplateConnection(simplateId, conn):
    global _slaveSimplateConnections
    with _lockSlaveSimplate:
        try:
            _slaveSimplateConnections[simplateId].remove(conn)
        except KeyError:
            logging.critical("Trying to remove a connection which has not been added, simpate ID = %s", unicode(simpleId))

def SendToSlave(simplateId, *args):
    with _lockSlaveSimplate:
        try:
            connectionList = _slaveSimplateConnections[simplateId]
        except KeyError:
            connectionList = []

        if not connectionList:
            logging.info("Ignoring a message to simpate %s with args: %s ", unicode(simplateId), unicode(args))
        else:
            logging.info("Sending to %d slave simplates with id %s", len(connectionList), unicode(simplateId))

        for c in connectionList:
            c.method.sendToSlave(*args)

#########################################
class SlaveSimplateHandler(BaseHandler):
    def _shutdown(self):
        logging.info("Slave simplate disconnected")
        if self.simplateId:
            RemoveSlaveSimplateConnection(self.simplateId, self._conn)
        else:
            logging.warning("Disconnected a slave simplate before registering")
        
    def _setup(self):
        self.simplateId = None 
        logging.info("slave simplate connected")

    def registrate(self, simplateId):
        _logFunction("simplateId=", simplateId)
        self.simplateId = simplateId
        AddSlaveSimplateConnection(simplateId, self._conn)

    def ping(self):
        logging.info("Ping from slave simplate") #TODO: make debug if ping is too often
        return

### Big show methods
_lockBigShow = threading.RLock()
_bigShowConnections = []

def StartBigShow(bigShowId):
    with _lockBigShow:
        if not _bigShowConnections:
            logging.warning("Ignoring a start big show command (show id = %s). No big show client is connected", unicode(bigShowId))
            return

        logging.info("Sending a start big show command (show id = %s) to %d client(s)", unicode(bigShowId), len(_bigShowConnections))
        for c in _bigShowConnections:
            c.method.startBigShow(bigShowId)

#########################################
class BigShowServerHandler(BaseHandler):
    def _shutdown(self):
        logging.info("big show client disconnected")
        global _bigShowConnections
        with _lockBigShow:
            _bigShowConnections.remove(self._conn)
        
    def _setup(self):
        logging.info("big show client connected")

    def registrate(self):
        logging.info("big show client registered")
        global _bigShowConnections
        with _lockBigShow:
            _bigShowConnections.append(self._conn)

    def ping(self):
        logging.info("Ping from big show client") #TODO: make debug if ping is too often
        return

def simplateServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = SimplateServerHandler )
	s.debug_socket(True)
	s.serve()

def slaveSimplateServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = SlaveSimplateHandler )
	s.debug_socket(True)
	s.serve()

def barServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = BarServerHandler )
	s.debug_socket(True)
	s.serve()

def bigShowServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = BigShowServerHandler )
	s.debug_socket(True)
	s.serve()
