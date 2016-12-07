#-*- coding: utf-8 -*-
import logging
import time
import json
from operator import attrgetter

from webob import Response
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls,
)
from ryu.ofproto import (
    ofproto_v1_3,
    ofproto_v1_3_parser
)
from ryu.app.wsgi import (
    ControllerBase,
    route
)
from ryu.app.ofctl import api
from ryu.lib import dpid as dpid_lib
from ryu.lib.dpid import dpid_to_str, str_to_dpid

simple_switch_instance_name = 'network_manager_api_app'

class RestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)

        self.logger.info("[*] RestController initialize...")
        super(RestController, self).__init__(req, link, data, **config)
        self.simpl_switch_spp = data[simple_switch_instance_name]



    def _wait_for_stats_update(self):
        simple_switch = self.simpl_switch_spp
        while not (simple_switch._flow_stats_update and simple_switch._port_stats_update):
            time.sleep(1)

        #処理が完了したことはわかったので、フラグを折る
        simple_switch._flow_stats_update = False
        simple_switch._port_stats_update = False
        return

    def _list_mac_table(self, dpid):
        simple_switch = self.simpl_switch_spp

        if dpid not in simple_switch.mac_to_port: #既知でないスイッチが対象となる場合
            self.logger.info("[*] dpid = {}".format(dpid))
            self.logger.info("[-] Unknown switch targetted. return 404")
            return Response(status=404) # Not Found

        #対象となるスイッチが既知であるならば、MACとポートの対応表が取得できるはずなので
        #取得し、それをレスポンスとして返す
        mac_table = simple_switch.mac_to_port.get(dpid, {})
        self.logger.info("[+] We get data from {}".format(simple_switch.mac_to_port))
        return mac_table

    @route('node', '/node/switch/{dpid}', methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def _request_stats(self, req, **kwargs):
        self.logger.info("@_request_stats")
        simple_switch = self.simpl_switch_spp
        requested_dpid = str_to_dpid(kwargs['dpid'])

        self.logger.info("[*] simple_switch._datapaths = {0}".format(simple_switch._datapaths))
        datapath = simple_switch._datapaths[requested_dpid]
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)
        self.logger.info("[*] Wait for update stats...")
        print("Wait")
        self._wait_for_stats_update()
        self.logger.info("[+] stats updated.")
        print("Updated")

        simple_switch._stats[dpid]["mactable"] = self._list_mac_table(requested_dpid)

        return Response(content_type='application/json', body=json.dumps(simple_switch._stats[dpid]), status=200)

    @route("node", "/node/test", methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def _test(self, req, **kwargs):
        self.logger.info("[+] @_test")
        return Response(content_type='application/json', body=json.dumps({"hoge": "fuga"}))


    # @route('simpleswitch', base_url+'node/switch/{dpid}', methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    # def put_mac_table(self, req, **kwargs):
    #     simple_switch = self.simpl_switch_spp
    #     dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
    #
    #     new_entry = eval(req.body)
    #
    #     if dpid not in simple_switch.mac_to_port:
    #         return Response(status=404) # Not Found
    #
    #     try:
    #         mac_table = simple_switch.set_mac_to_port(dpid, new_entry)
    #         body = json.dumps(mac_table)
    #         return Response(content_type='application/json', body=body)
    #     except Exception as e:
    #         return Response(status=500) # Server Error