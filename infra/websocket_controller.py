#-*- coding: utf-8 -*-
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import websocket
from ryu.app.wsgi import (
    rpc_public,
    WebSocketRPCServer
)
from ryu.lib import hub

simple_switch_instance_name = 'network_manager_api_app'

url = '/simpleswitch/ws'

class WebSocketController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(WebSocketController, self).__init__(req, link, data, **config)

        self.simple_switch_app = data[simple_switch_instance_name]

    @websocket('simpleswitch', url)
    def _websocket_handler(self, ws):
        simple_switch = self.simple_switch_app

        simple_switch.logger.debug('Websocket connected: {0}'.format(ws))
        rpc_server = WebSocketRPCServer(ws, simple_switch)
        rpc_server.serve_forever()
        simple_switch.logger.debug('Websocket disconnected: {0}'.format(ws))

