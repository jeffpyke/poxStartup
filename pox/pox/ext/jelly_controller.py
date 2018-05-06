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

log = core.getLogger()

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

    S = 50
    N = 20
    r = 4
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
          path = [i, src_switch, j]
        else:
          path = [i, src_switch, dst_switch, j] # path to go from src to dst
        self.add_entry(src_hwaddr, dst_hwaddr, path, S)

  def add_entry(self, src_hwaddr, dst_hwaddr, path, S):
    for i in range(1, len(path)-1):
      msg = of.ofp_flow_mod()
      msg.match.dl_src = EthAddr(src_hwaddr)
      msg.match.dl_dst = EthAddr(dst_hwaddr)
      if(i == 1):
        msg.match.in_port = path[i]*1000 + 1 + path[i-1] # host-switch port
      else:
        msg.match.in_port = path[i]*1000 + 1 + path[i-1] + S # inter switch link
      
      if(i == len(path)-2):
        msg.actions.append(of.ofp_action_output(port = path[i]*1000 + 1 + path[i+1])) # host-switch port
      else:
        msg.actions.append(of.ofp_action_output(port = path[i]*1000 + 1 + path[i+1] + S)) # inter switch link
      self.connection.send(msg)

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

    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # DOING NOTHING
    # # Learn the port for the source MAC
    # if str(packet.src) not in self.mac_to_port:
    #   self.mac_to_port[str(packet.src)] = packet_in.in_port
    #   log.error("mapped %s %d"%(str(packet.src), packet_in.in_port))

    # # if the port associated with the destination MAC of the packet is known:
    # if str(packet.dst) in self.mac_to_port:
    #   # Send packet out the associated port
    #   # log.error("Sending out of port%d"%(self.mac_to_port[str(packet.dst)],))
    #   # self.resend_packet(packet_in, self.mac_to_port[str(packet.dst)])

    #   # Once you have the above working, try pushing a flow entry
    #   # instead of resending the packet (comment out the above and
    #   # uncomment and complete the below.)
    #   # log.error(dir(packet))
    #   log.error("Installing flow..., src:%s, dst:%s, in port:%d, out port:%d"%(str(packet.src), str(packet.dst), self.mac_to_port[str(packet.src)], self.mac_to_port[str(packet.dst)]))
    #   # # Maybe the log statement should have source/destination/port?

    #   msg = of.ofp_flow_mod()
    #   msg.data = packet_in
    #   # Set fields to match received packet
    #   msg.match.dl_src = packet.src
    #   msg.match.dl_dst = packet.dst
    #   msg.actions.append(of.ofp_action_output(port = self.mac_to_port[str(packet.dst)]))
    #   self.connection.send(msg)
    # else:
    #   # Flood the packet out everything but the input port
    #   # This part looks familiar, right?
    #   self.resend_packet(packet_in, of.OFPP_ALL)


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    # Comment out the following line and uncomment the one after
    # when starting the exercise.
    print "Src: " + str(packet.src)
    print "Dest: " + str(packet.dst)
    print "Event port: " + str(event.port)
    # self.act_like_hub(packet, packet_in)
    self.act_like_switch(packet, packet_in)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
