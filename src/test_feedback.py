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
lock = threading.RLock()
localFeedback = {'yes' : 0, 'no' : 0, 'cancel' : 0}


def SimplateLoop():
    threadName = threading.current_thread().name
    c=connect(host="127.0.0.1", port=settings.SIMPLATE_SERVER_PORT)
    c.call.registrate(cds_settings.SCENARIO_ID_Shop, threadName)
    c.call.startSession("CLIENT" + threadName, "some client info")
    for i in range(1,100):
        fb = random.randint(0,3)
        if fb == 0:
            c.call.simpleResult(cds_settings.SIMPLE_ID_FEEDBACK, (0,0))
            with lock:
                localFeedback['cancel'] += 1
        elif fb == 1:
            c.call.simpleResult(cds_settings.SIMPLE_ID_FEEDBACK, (1,2))
            with lock:
                localFeedback['cancel'] += 1
        elif fb == 2:
            c.call.simpleResult(cds_settings.SIMPLE_ID_FEEDBACK, (1,0))
            with lock:
                localFeedback['no'] += 1
        elif fb == 3:
            c.call.simpleResult(cds_settings.SIMPLE_ID_FEEDBACK, (1,1))
            with lock:
                localFeedback['yes'] += 1
    c.close()



threads = []
for i in range(1,20):
    t = threading.Thread(target = SimplateLoop, name="Simplate #" + str(i))
    t.daemon = True
    t.start()
    threads += [t]


run = True
while run:
    run = False
    for t in threads:
        t.join(0.01)
        if t.isAlive():
            run = True

print "Local feedback: " + str(localFeedback)
c=connect(host="127.0.0.1", port=settings.SIMPLATE_SERVER_PORT)
c.call.registrate(cds_settings.SCENARIO_ID_Shop, 'simeSimplate')
c.call.startSession("Some CLIENT", "some client info")
print "Remote feedback" + str(c.call.getFeedbackStatistics())
