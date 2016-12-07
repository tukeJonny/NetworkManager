#-*- coding: utf-8 -*-
import logging
import sys
sys.path.append('.')
from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import (
    CONFIG_DISPATCHER,
    set_ev_cls,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER
)
from ryu.app.wsgi import (
    route,
    WSGIApplication
)
from ryu.lib.packet import packet #Websocket
from ryu.lib.dpid import dpid_to_str, str_to_dpid

from rest_controller import RestController
from websocket_controller import WebSocketController

simple_switch_instance_name = 'network_manager_api_app'

class NetworkManagerController(simple_switch_13.SimpleSwitch13):
    _CONTEXTS={'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(NetworkManagerController, self).__init__(*args, **kwargs)
        self._switches = dict()

        self._flow_stats_update = False #flow_statsを最新状態にしたかどうかを示すフラグ
        self._port_stats_update = False #port_statsを最新状態にしたかどうかを示すフラグ
        # parameters
        # self.stats = {datapath1: {...}, datapath2: {...}, ...}
        # datapath: {
        #   "flow": {
        #       "param1": value1,
        #       ...,
        #   },
        #   "port": {
        #       "param1": value1,
        #       ...,
        #   },
        # }, ...
        self._stats = dict()
        self._datapaths = dict()

        wsgi = kwargs['wsgi']
        self.logger.info("[+] wsgi object = {0}".format(wsgi))
        wsgi.register(RestController, {simple_switch_instance_name: self})
        self.logger.info("[+] Register RestController({0}) to wsgi({1})".format(RestController, wsgi))
        wsgi.register(WebSocketController, data={simple_switch_instance_name: self})
        #self._ws_manager = wsgi.websocketmanager

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(NetworkManagerController, self).switch_features_handler(ev)

        datapath = ev.msg.datapath
        dpid = datapath.id
        self.logger.info("[+] add datapath={0}".format(datapath.id))
        self._switches[dpid] = datapath
        self.mac_to_port.setdefault(dpid, {})

    def set_mac_to_port(self, dpid, entry):
        mac_table = self.mac_to_port.setdefault(dpid, {}) #対象スイッチのMACテーブルを初期化
        datapath = self._switches.get(dpid) #スイッチのオブジェクトを取得

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

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id

        for flow_stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (flow.match['in_port'],flow.match['eth_dst'])):
            self._stats[dpid] = dict()
            self._stats[dpid]["flow"] = {
                'in-port': flow_stat.match['in_port'],
                'eth_dst': flow_stat.match['eth_dst'],
                'out-port': flow_stat.instructions[0].actions[0].port,
                'packets': flow_stat.packet_count,
                'bytes': flow_stat.byte_count
            }
        self.logger.debug("[+] flow stats = {0}".format(self._stats[dpid]["flow"]))
        self._flow_stats_update = True #更新完了

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id

        for port_stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info("[*] look port_stat= {0}".format(port_stat))
            self._stats[dpid] = dict()
            self._stats[dpid]["port"] = {
                "port": port_stat.port_no,
                #Receive
                "rx_pkts": port_stat.rx_packets,
                "rx_bytes": port_stat.rx_bytes,
                "rx_error": port_stat.rx_errors,
                #Transmit
                "tx_packets": port_stat.tx_packets,
                "tx_bytes": port_stat.tx_bytes,
                # "tx_errors": port_stat.tx_errors
            }
        self.logger.debug("[+] port stats = {0}".format(self._stats[dpid]["port"]))
        self._port_stats_update = True #更新完了

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER,DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        dpid = datapath.id

        if ev.state == MAIN_DISPATCHER:
            if not dpid in self._datapaths:
                self.logger.debug("[+] Add OpenVSwitch ({0})".format(datapath.id))
                self._datapaths[dpid] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if dpid in self.datapaths:
                self.logger.debug("[-] Delete OpenVSwitch ({0})".format(datapath.id))
                del self._datapaths[dpid]

        self.logger.debug("[*] Now datapath table = {0}".format(self._datapaths))

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


