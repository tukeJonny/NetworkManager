#-*- coding: utf-8 -*-

import json
import logging

from webob import Response
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import route, WSGIApplication
from ryu.lib.packet import packet #Websocket

from .rest_controller import RestController
from .websocket_controller import WebSocketController

simple_switch_instance_name = 'simple_switch_api_app'

class NetworkManagerController(simple_switch_13.SimpleSwitch13):
    _CONTEXTS={'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(NetworkManagerController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(RestController, {simple_switch_instance_name: self})
        #wsgi.register(WebSocketController, data={simple_switch_instance_name: self})
        #self._ws_manager = wsgi.websocketmanager

    #REST API
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(NetworkManagerController, self).switch_feature_handler(ev)

        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})

    def set_mac_to_port(self, dpid, entry):
        mac_table = self.mac_to_port.setdefault(dpid, {}) #対象スイッチのMACテーブルを初期化
        datapath = self.switches.get(dpid) #スイッチのオブジェクトを取得

        #フローエントリのポートやMACアドレスを取得する
        entry_port = entry['port']
        entry_mac  = entry['mac']

        if datapath is not None: #スイッチのオブジェクトを取得できなかったならば
            parser = datapath.ofproto_parser
            if entry_port not in mac_table.values(): #ポート番号がMACテーブルになかったら
                for mac, port in mac_table.items(): #MACテーブルをイテレート
                    #既知のデバイスから新しいデバイスへ
                    actions = [parser.OFPActionOutput(entry_port)] #新しいデバイスにパケットを出力
                    match = parser.OFPMatch(in_port=port, eth_dst=entry_mac) #既知のポートからであり、新しいMACアドレスへのパケットか？
                    self.add_flow(datapath, 1, match, actions) #datapathスイッチに対し、優先度1で、
                                                               # 既知のデバイスが存在するポートから
                                                               # 未知のデバイスが存在するポートへ
                                                               # パケットを転送する

                    #新しいデバイスから既知のデバイスへ
                    actions = [parser.OFPActionOutput(port)] #既知のデバイスにパケットを出力
                    match = parser.OFPMatch(in_port=entry_port, eth_dst=mac) #新しいポートからであり、既知のMACアドレスへのパケットか？
                    self.add_flow(datapath, 1, match, actions) #datapathスイッチに対し、優先度1で、
                                                               # 新しいデバイスが存在するポートから
                                                               # 既知のデバイスが存在するポートへ
                                                               # パケットを転送する
                mac_table.update({entry_mac: entry_port}) # 新しいデバイスがどこにいるか覚える

    # #WebSocket
    # @set_ev_cls(ofp_event.EventOFPPacketIn) # Packet-In
    # def _packet_in_handler(self, ev):
    #     super(NetworkManagerController, self)._packet_in_handler(ev)
    #
    #     pkt = packet.Packet(ev.msg.data) # Packet-Inしたパケットを取得
    #     self._ws_manager.broadcast(str(pkt)) #Websocketコネクション先へそいつをブロードキャスト
    #
    # @rpc_public
    # def get_arp_table(self):
    #     return self.mac_to_port # MACアドレスとポートの対応表を返す


