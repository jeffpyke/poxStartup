import os
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time
import networkx as nx
import random

class JellyFishTop(Topo):
    ''' TODO, build your topology here'''
    def build( self, S, N, r):
        "Create custom topo."

        # Initialize topology
        # Topo.__init__( self )

        hosts = [self.addHost('h%d'%(i,)) for i in range(S)]
        switches = [self.addSwitch('s%d'%(i,)) for i in range(N)]

        # make server switch connections
        for i in range(S):
            conn_switch = random.randint(0, N-1)
            self.addLink(hosts[i], switches[conn_switch])

        rrg = nx.random_regular_graph(r, N, 100)
        for e in rrg.edges():
            self.addLink(switches[e[0]], switches[e[1]])

def experiment(net):
        net.start()
        sleep(3)
        net.pingAll()
        net.stop()

def main():
    topo = JellyFishTop(20, 5, 2)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    experiment(net)

if __name__ == "__main__":
    main()

