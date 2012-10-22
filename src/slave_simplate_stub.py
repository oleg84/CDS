#!/usr/bin/python
# -*- coding: utf-8 -*-

from bjsonrpc import connect
from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler
import settings
import time
import logging
import threading
from listeners import _logFunction

logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', level=logging.INFO)

class SlaveSimplateStubHandler(BaseHandler):

    def sendToSlave(self, arg1, arg2, arg3, arg4, arg5, arg6):
        _logFunction("arg1=", unicode(arg1), ", arg2=", unicode(arg2), ", arg3=", unicode(arg3), ", arg4=", unicode(arg4), ", arg5=", unicode(arg5), ", arg6=", unicode(arg6))

c=connect(host="127.0.0.1", port=settings.SLAVE_SIMPLATE_SERVER_PORT, handler_factory=SlaveSimplateStubHandler)
c.call.registrate(10)

while True:
    c.call.ping()
    c.read_and_dispatch(timeout=5)
