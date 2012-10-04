#!/usr/bin/python
import logging
import threading

import settings
import listeners


class testServerThread(threading.Thread):
	def __init__(self, name, port):
		threading.Thread.__init__(self)
		self.name = name
		self.port = port
		self.daemon = True
		
	def run(self):
		logging.info("Starting test server on port %d", self.port)
		listeners.test_server(self.port)


logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', filename='server.log', filemode='a', level=settings.loglevel)

logging.info("--- Server started ---")
try:
	s1 = testServerThread("TestServer1", settings.server_port)
	s2 = testServerThread("TestServer2", settings.server_port + 1)
	s1.start()
	s2.start()
	while True:
		s1.join(0.1)
except KeyboardInterrupt:
	logging.info("got a keyboard interrupt")
logging.info("--- Server stopped ---")
