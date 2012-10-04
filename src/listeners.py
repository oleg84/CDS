import bjsonrpc
from bjsonrpc.handlers import BaseHandler
import logging

class TestServerHandler(BaseHandler):
    def _setup(self):
    	self.id_ = 0

    def hello(self, txt):
            response = {"responseStr":"hello, %s!." % txt, "other str" : "some other string", "someInt":5}
	    logging.debug("Responding: %s", response)
	    return response

    def isRegistered(self):
    	if self.id_ == 0:
		return False
	else:
		return True

    def register(self, id_):
    	logging.info("Registered with id = %d", id_)
    	self.id_ = id_


def test_server(port):
	s = bjsonrpc.createserver( port=port, handler_factory = TestServerHandler )
	s.debug_socket(True)
	s.serve()
