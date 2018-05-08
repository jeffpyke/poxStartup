# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import EthAddr
import networkx as nx
import random
from itertools import islice

log = core.getLogger()

route_map = {}

class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}

    S = 10
    N = 10
    r = 4
    use_ecmp = False
    # seed = 100 is constant so that the corresponding topo and controller graph are the same
    rrg = nx.random_regular_graph(r, N, 100)
    for i in range(S):
      src_hwaddr = EthAddr('00:00:00:00:00:%02d'%(i+1)) 
      for j in range(S):
        if i == j:
          continue
        dst_hwaddr = EthAddr('00:00:00:00:00:%02d'%(j+1))
        src_switch = i%N
        dst_switch = j%N

        if src_switch == dst_switch:
          path = [[src_switch]]
        elif use_ecmp:
          # path = [src_switch, dst_switch] # path to go from src to dst
          paths = []
          for p in nx.all_shortest_paths(rrg, src_switch, dst_switch):
            paths.append(p)
          log.error('SRC: %d, DST: %d'%(i, j,))
          log.error(paths)
          # select a random path to send traffic from
          path = random.sample(paths, min(len(paths), 8))
          log.error(path)
          log.error('PATH LEN: %d'%(len(path)))
          log.error('\n')
        else:
          path = list(islice(nx.shortest_simple_paths(rrg, src_switch, dst_switch), 8))
        for path_ in path:
            self.add_entry(src_hwaddr, dst_hwaddr, [i] + path_ + [j], S)
    # log.error(route_map)

  def add_entry(self, src_hwaddr, dst_hwaddr, path, S):
    for i in range(1, len(path)-1):
      # msg = of.ofp_flow_mod()
      # msg.match.dl_src = EthAddr(src_hwaddr)
      # msg.match.dl_dst = EthAddr(dst_hwaddr)
      # if(i == 1):
      #   msg.match.in_port = path[i]*1000 + 1 + path[i-1] # host-switch port
      # else:
      #   msg.match.in_port = path[i]*1000 + 1 + path[i-1] + S # inter switch link

      # if(i == len(path)-2):
      #   msg.actions.append(of.ofp_action_output(port = path[i]*1000 + 1 + path[i+1])) # host-switch port
      # else:
      #   msg.actions.append(of.ofp_action_output(port = path[i]*1000 + 1 + path[i+1] + S)) # inter switch link
      # self.connection.send(msg)

      dl_src = EthAddr(src_hwaddr)
      dl_dst = EthAddr(dst_hwaddr)
      if(i == 1):
        in_port = path[i]*1000 + 1 + path[i-1] # host-switch port
      else:
        in_port = path[i]*1000 + 1 + path[i-1] + S # inter switch link

      if(i == len(path)-2):
        out_port = path[i]*1000 + 1 + path[i+1] # host-switch port
      else:
        out_port = path[i]*1000 + 1 + path[i+1] + S # inter switch link
      key = (dl_src, dl_dst, in_port)
      if key in route_map:
          route_map[key].add(out_port)
      else:
          route_map[key] = set([out_port])

  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """
    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """
    dst = packet.dst
    src = packet.src
    in_port = packet_in.in_port
    if (src, dst, in_port) in route_map:
        val = route_map[(src, dst, in_port)]
        out_port = random.sample(val, 1)[0]
        # log.error(src)
        # log.error(dst)
        # log.error(in_port)
        # log.error(out_port)
        log.error('%s %s %d %d'%(str(src), str(dst), in_port, out_port))
        self.resend_packet(packet_in, out_port)


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    self.act_like_switch(packet, packet_in)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
