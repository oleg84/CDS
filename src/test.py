#!/usr/bin/python
# -*- coding: utf-8 -*-

from bjsonrpc import connect

c=connect(host="127.0.0.1", port=18888)
c.call.registrate(2, 10)
print c.call.startSession("client1", "Вася Пупкин")
c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
c.call.ping()
c.call.endSession({u'balance': 450, u'coupons': u'some coupon info'})

print c.call.startSession("client2", "John Doe")
c.call.barOrderInfo(({"drink":"Coke", "options":"sugar"}, {"drink":"tea", "option":"lemon"}))
c.call.endSession({u'balance': 450, u'coupons': u'some coupon info'})


c=connect(host="127.0.0.1", port=18888)
c.call.registrate(1, 5)
print c.call.startSession("client1", "Client")
c.call.simpleStart('simple id')
c.call.simpleResult('simple id', 'simple result')
print c.call.getFeedbackStatistics()
print c.call.shouldStartBigShow()
c.call.endSession({u'balance': 350, u'coupons': u'some coupon info'})

c=connect(host="127.0.0.1", port=18889)
c.call.ping()
