#!/usr/bin/python

import settings
import logging
import listeners


logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', filename='server.log', filemode='a', level=settings.loglevel)

logging.info("--- Server started ---")
try:
	listeners.test_server()
except:
	pass
logging.info("--- Server stopped ---")
