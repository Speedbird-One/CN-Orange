from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types

class StaticRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(StaticRouter, self).__init__(*args, **kwargs)
        # Switch ID: { Destination MAC : Output Port }
        self.static_table = {
            1: {'00:00:00:00:00:01': 1, '00:00:00:00:00:02': 2, '00:00:00:00:00:03': 3},
            2: {'00:00:00:00:00:01': 2, '00:00:00:00:00:02': 1, '00:00:00:00:00:03': 3},
            3: {'00:00:00:00:00:01': 3, '00:00:00:00:00:02': 2, '00:00:00:00:00:03': 1},
        }

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.logger.info("--- Switch %s connected ---", datapath.id)

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        dpid = datapath.id

        # 1. ARP Handling (Broadcast)
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                     in_port=in_port, actions=actions, data=msg.data)
            datapath.send_msg(out)
            return

        # 2. SCENARIO 2: SECURITY BLOCK
        # Block H1 (01) from reaching H3 (03) on Switch 1
        if dpid == 1 and eth.dst == '00:00:00:00:00:03':
            self.logger.info("SECURITY ALERT: Dropping packet to H3")
            actions = [] 
            match = parser.OFPMatch(eth_dst='00:00:00:00:00:03')
            self.add_flow(datapath, 20, match, actions) 
            return 

        # 3. ROUTING LOGIC
        dst = eth.dst
        if dpid in self.static_table:
            if dst in self.static_table[dpid]:
                out_port = self.static_table[dpid][dst]
                self.logger.info("S%s: Routing to %s via Port %s", dpid, dst, out_port)
                
                actions = [parser.OFPActionOutput(out_port)]
                match = parser.OFPMatch(eth_dst=dst)
                self.add_flow(datapath, 10, match, actions)
                
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                         in_port=in_port, actions=actions, data=msg.data)
                datapath.send_msg(out)
