#!/usr/bin/python

import plasma
import threading
import logging
from time import sleep

logging.basicConfig(format='%(asctime)s %(levelname)s[%(threadName)s]: %(message)s', level=logging.DEBUG)

plasma.init('', 8888) #TODO: set the needed port number for tests

t = threading.Thread(target = plasma.serve, name="PlasmaServer")
t.daemon = True
t.start()

#TODO: modify this loop as needed for testing
while True:
    plasma.sendMessage("Hello","param1","param2")
    sleep(1)
    plasma.sendMessage(15,1,2,3,4,5)
    sleep(1)
    plasma.sendMessage("Just one param", 1)
    sleep(1)
    plasma.sendMessage("2543", 51)
    sleep(1)
