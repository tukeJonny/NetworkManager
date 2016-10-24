#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import sys
from websocket import create_connection
ws = create_connection("ws://localhost:8080/websocket")
 
if len(sys.argv) > 1:
	message = sys.argv[1]
else:
	message = 'hello world!'

print (ws.send(message))
print (ws.recv())

ws.close()
