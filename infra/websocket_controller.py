#-*- coding: utf-8 -*-
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import websocket
from ryu.app.wsgi import rpc_public, WebSocketRPCServer
from ryu.lib import hub

simple_switch_instance_name = 'simple_switch_api_app'

url = '/simpleswitch/ws'

class WebSocketController(ControllerBase):
    def __init__(self):
        pass