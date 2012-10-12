import bjsonrpc
from bjsonrpc.handlers import BaseHandler
from bjsonrpc.exceptions import ServerError
import logging
import cds_settings
import inspect
import db
import datetime
import plasma
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
        return datetime.datetime.now().isoformat()

    def getUtcTime(self):
        return datetime.datetime.utcnow().isoformat()
        
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
                client = db.createClient(cardId, cds_settings.CLIENT_INITIAL_BALANCE, clientInfo)
                
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
        plasma.shopStartSession(self.simplateId)
        return client


    def endSession(self, updatedAccountInfo):
        self._checkRegistered()
        self._checkSessionStarted()
        _logFunction("simplateId=", self.simplateId, ", updatedAccountInfo=",  updatedAccountInfo)

        cardId = self.cardId
        self.cardId = None
        plasma.shopEndSession(self.simplateId)
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
        plasma.shopSimpleStart(self.simplateId, simpleId)
        return 

    def simpleResult(self, simpleId, result):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId, ", simpleId=",  simpleId, ", result=", result)
        if not isinstance(result, collections.Iterable) or len(result) != 2:
            raise ServerError("simpleResult incorrect type. Should be a tuple of 2")

        plasma.shopSimpleResult(self.simplateId, simpleId, result)
        simple.ProcessSimpleResult(simpleId, result)

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
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId)
        return db.GetFeedbackStatistics()

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

        logging.info("Sending %d orders to bar", len(_barOrderCache))
        for id in _barOrderCache.keys():
            order = _barOrderCache[id]

            if not order[2]: #send to existing connection only if not isSent
                order[2] = True
                for c in _barConnections:
                    c.method.newBarOrder(order[0], id, order[1])

            if newConnection: #forcibly send to a new connection
                newConnection.method.newBarOrder(order[0], id, order[1])


def RemoveBarOrder(id):
    global _barOrderCache
    with _lock:
        if not _barOrderCache[id][2]:
            logging.warning("Deleting an unsent order: %s", unicode(_barOrderCache[id]))
        if id in _barOrderCache:
            del _barOrderCache[id]


#########################################
class BarServerHandler(BaseHandler):
    def _shutdown(self):
        logging.info("bar disconnected")
        global _barConnections
        with _lock:
            _barConnections.remove(self._conn)
        
    def _setup(self):
        logging.info("bar connected")

    def registrate(self): #TODO: review
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


def simplateServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = SimplateServerHandler )
	s.debug_socket(True)
	s.serve()

def barServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = BarServerHandler )
	s.debug_socket(True)
	s.serve()
