#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import json
import logging

import tornado.ioloop
import tornado.web
import tornado.websocket

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()

formatter = logging.Formatter(fmt='%(asctime)s', datefmt='[%Y/%m/%d %I:%M:%S]')

handler.setLevel(logging.DEBUG)
handler.formatter = formatter
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

#WebSocketHandlerのインスタンスが入る
cl = []

sample = {
	"Rounter": [
		{"rx": 10, "tx": 10},
		{"rx": 3, "tx": 3},
	],
	"Ryu": [
		{"switches_num": 2},
		{"ip": "153.127.196.33"},
		{"port": 8000},
	],
}

class WebSocketHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		logger.debug("Start WebSocket Server")
		if self not in cl:
			cl.append(self)
	
	def on_message(self, message):
		"""WebSocketサーバがメッセージを受け取った際、最初に呼び出されるメソッド"""
		logger.debug("Received Message -> {}".format(message))
		for client in cl:
			client.write_message(json.dumps(sample))
	
	def on_close(self):
		logger.debug("Stop WebSocket Server")
		if self in cl:
			cl.remove(self)

	def check_origin(self, origin):
		logger.debug("Allow Cross Origin Conversation from {}".format(origin))
		return True
	

#Tornado Web Applicationを作成。
application = tornado.web.Application([
	(r"/websocket", WebSocketHandler),
])

#リッスンし、tornado
if __name__ == "__main__":
	application.listen(8080)
	tornado.ioloop.IOLoop.current().start()


