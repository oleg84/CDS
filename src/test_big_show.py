#!/usr/bin/python
# -*- coding: utf-8 -*-

from bjsonrpc import connect
from bjsonrpc.exceptions import ServerError
import cds_settings
import logging
import settings
import threading
import time
import random

logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', level=logging.DEBUG)

def SimplateLoop():
    threadName = threading.current_thread().name
    c=connect(host="127.0.0.1", port=settings.SIMPLATE_SERVER_PORT)
    c.call.registrate(cds_settings.SCENARIO_ID_Shop, threadName)
    c.call.startSession("CLIENT" + threadName, "some client info")
    while True:
        time.sleep(random.uniform(0,10))
        if c.call.shouldStartBigShow():
            logging.info("Allowed to start big show")
            time.sleep(random.uniform(1,2))
            r = random.randint(0,2)
            if r == 0:
                logging.info("Starting a succesfull show with id 1")
                c.call.simpleStart(cds_settings.SIMPLE_ID_BIG_SHOW)
                time.sleep(random.uniform(3,5))
                c.call.simpleResult(cds_settings.SIMPLE_ID_BIG_SHOW, (1,1))
            elif r == 1:
                logging.info("Canceling a show")
                c.call.simpleResult(cds_settings.SIMPLE_ID_BIG_SHOW, (0,None))
            elif r == 2:
                logging.info("Starting a succesfull show with id 2")
                time.sleep(random.uniform(3,5))
                c.call.simpleResult(cds_settings.SIMPLE_ID_BIG_SHOW, (1,2))



for i in range(1,5):
    t = threading.Thread(target = SimplateLoop, name="Simplate #" + str(i))
    t.daemon = True
    t.start()

while True:
    t.join(0.1) #yeah, just join 1 thread 
