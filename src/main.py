#!/usr/bin/python
import logging
import threading

import settings
import listeners

class SimplateServerThread(threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		self.name = "SimplateServer"
		self.port = port
		self.daemon = True
		
	def run(self):
		logging.info("Starting Simplate server on port %d", self.port)
		listeners.simplateServer(self.port)

class BarServerThread(threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		self.name = "BarServer"
		self.port = port
		self.daemon = True
		
	def run(self):
		logging.info("Starting Bar server on port %d", self.port)
		listeners.barServer(self.port)


logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', filename='server.log', filemode='a', level=settings.LOGLEVEL)

logging.info("--- Server started ---")
try:
	simplateServerThread = SimplateServerThread(settings.SIMPLATE_SERVER_PORT)
	barServerThread = BarServerThread(settings.BAR_SERVER_PORT)
	simplateServerThread.start()
	barServerThread.start()

    #work until at least one thread is running
	while simplateServerThread.isAlive() and barServerThread.isAlive(): 
		simplateServerThread.join(0.1)
		barServerThread.join(0.1)

except KeyboardInterrupt:
	logging.info("got a keyboard interrupt")
logging.info("--- Server stopped ---")
