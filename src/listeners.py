import bjsonrpc
from bjsonrpc.handlers import BaseHandler
from bjsonrpc.exceptions import ServerError
import logging
import cds_settings
import inspect
import db
import datetime
import plasma

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
        plasma.sendMessage('shopStartSession', self.simplateId)
        return client


    def endSession(self, updatedAccountInfo):
        self._checkRegistered()
        self._checkSessionStarted()
        _logFunction("simplateId=", self.simplateId, ", updatedAccountInfo=",  updatedAccountInfo)

        cardId = self.cardId
        self.cardId = None
        plasma.sendMessage('shopEndSession', self.simplateId)
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
        #TODO: implement

    def simpleResult(self, simpleId, result):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId, ", simpleId=",  simpleId, ", result=", result)
        return 
        #TODO: implement

    def shouldStartBigShow(self):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId)
        return False
        #TODO: implement

    def getFeedbackStatistics(self):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfShopSimplate()
        _logFunction("simplateId=", self.simplateId)
        return {'yes': 30, 'no': 70}
        #TODO: implement

### Bar methods
    def barOrderInfo(self, drinks):
        self._checkRegistered()
        self._checkSessionStarted()
        self._checkIfBarSimplate()
        _logFunction("simplateId=", self.simplateId, " ,drinks=", drinks)
        return
        #TODO: implement

        

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


#########################################
class BarServerHandler(BaseHandler):
    def _shutdown(self):
        pass
        
    def _setup(self):
        pass

    def ping(self):
        logging.debug("Ping")
        return



def simplateServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = SimplateServerHandler )
	s.debug_socket(True)
	s.serve()

def barServer(port):
	s = bjsonrpc.createserver( host = '', port=port, handler_factory = BarServerHandler )
	s.debug_socket(True)
	s.serve()
