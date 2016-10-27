#-*- coding: utf-8 -*-

from ryu.app.wsgi import ControllerBase

from ryu.lib import dpid as dpid_lib

url = '/simpleswitch/mactable/{dpid}'

class RestController(ControllerBase):
    def __init__(self):
        pass