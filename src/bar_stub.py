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

class BarStubHandler(BaseHandler):

    def newBarOrder(self, drink, orderId, simplateId):
        logging.info("New order id=%d simplate=%s: %s", orderId, simplateId, unicode(drink))
        self._conn.call.barOrderDone(orderId)

c=connect(host="127.0.0.1", port=settings.BAR_SERVER_PORT, handler_factory=BarStubHandler)
c.call.registrate()

while True:
    c.call.ping()
    c.read_and_dispatch(timeout=5)
