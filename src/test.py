#!/usr/bin/python
# -*- coding: utf-8 -*-

from bjsonrpc import connect
from bjsonrpc.exceptions import ServerError
import cds_settings
import time


#TODO: use some unit-test framework

def StartTest(name):
    print "###TEST: %s" % name

StartTest("Connection")
c=connect(host="127.0.0.1", port=18888)
c.close()

StartTest("Get time")
c=connect(host="127.0.0.1", port=18888)
print c.call.getLocalTime()
print c.call.getUtcTime()
c.close()

StartTest("New client shop -> bar")
c=connect(host="127.0.0.1", port=18888)
c.call.registrate(cds_settings.SCENARIO_ID_Shop, 10)
print "Client just came: " + str(c.call.startSession("client1", "Вася Пупкин"))
c.call.simpleStart('simple id')
c.call.simpleResult('simple id', (1,1))
c.call.simpleEnd('simple id')
#while True:
#    c.call.sendToSlave('test string', 'other string', 1, 2, 3, 4, 5, 6, 7, 8, 9)
#    time.sleep(1)
c.call.endSession({'balance' : 650, 'coupons' : [{'name' : 'SuperCoupon', 'isUsed': 0}, {'name' : 'simpleCoupon', 'isUsed': 1 }]})
c.call.startSession("0123456789012345", {'name':"John Doe", "test":"test"})
c.close()

c=connect(host="127.0.0.1", port=18888)
c.call.registrate(cds_settings.SCENARIO_ID_Bar, 35)
print "Client came to the bar: " + str(c.call.startSession("client1", "Вася Пупкин"))
#while True:
#    c.call.barOrderInfo([{"name":"Coke", "options":["whiskey", "lemon"]},  {"name":"Coffee", "options":["sugar"]} ])
#    time.sleep(2)
c.call.endSession({'balance' : 320, 'coupons' : [{'name' : 'SuperCoupon', 'isUsed': 1}, {'name' : 'simpleCoupon', 'isUsed': 1 }]})
c.close()

StartTest("Old client")
c=connect(host="127.0.0.1", port=18888)
c.call.registrate(cds_settings.SCENARIO_ID_Shop, 1)
print c.call.startSession("client1", "Вася Пупкин")
c.close()

StartTest("Unknown client, bar")
c=connect(host="127.0.0.1", port=18888)
c.call.registrate(cds_settings.SCENARIO_ID_Bar, 24)
try:
    print c.call.startSession("0123456789012345", "John Doe")
except ServerError as e:
    print e
c.close()

#c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
#c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
#c.call.ping()
#c.call.endSession({u'balance': 450, u'coupons': u'some coupon info'})
#
#print c.call.startSession("client2", "John Doe")
#c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
#c.call.endSession({u'balance': 450, u'coupons': u'some coupon info'})
#
#
#c=connect(host="127.0.0.1", port=18888)
#c.call.registrate(1, 5)
#print c.call.startSession("client1", "Client")
#c.call.simpleStart('simple id')
#c.call.simpleResult('simple id', 'simple result')
#print c.call.getFeedbackStatistics()
#print c.call.shouldStartBigShow()
#c.call.endSession({u'balance': 350, u'coupons': u'some coupon info'})
#
#c=connect(host="127.0.0.1", port=18889)
#c.call.ping()
