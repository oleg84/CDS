#!/usr/bin/python
# -*- coding: utf-8 -*-

from bjsonrpc import connect
from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler
import settings
import time
import logging
import threading

logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', level=logging.INFO)

class BigShowClientStubHandler(BaseHandler):

    def startBigShow(self, showId):
        logging.info("Start big show with id = %s", unicode(showId))

c=connect(host="127.0.0.1", port=settings.BIG_SHOW_PORT, handler_factory=BigShowClientStubHandler)
c.call.registrate()

while True:
    c.call.ping()
    c.read_and_dispatch(timeout=5)
