#!/usr/bin/python

from bjsonrpc import connect
c=connect(host="127.0.0.1", port=8888)
print c.call.hello("test server")
c.call.register(5)
print c.call.isRegistered()
