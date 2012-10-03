import bjsonrpc
from bjsonrpc.handlers import BaseHandler
import settings
import logging

class TestServerHandler(BaseHandler):
    def _setup(self):
    	self.id_ = 0

    def hello(self, txt):
            response = "hello, %s!." % txt
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


def test_server():
	s = bjsonrpc.createserver( port=settings.server_port, handler_factory = TestServerHandler )
	s.debug_socket(True)
	s.serve()
