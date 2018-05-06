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

S = 40
N = 15
r = 4

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
            conn_switch = i%N
            self.addLink(hosts[i], switches[conn_switch], i, conn_switch*1000 + i + 1)

        rrg = nx.random_regular_graph(r, N, 100)
        for e in rrg.edges():
            self.addLink(switches[e[0]], switches[e[1]], 1000*e[0] + S + e[1] + 1, 1000*e[1] + S + e[0] + 1)

def experiment(net):
        for i in range(S):
            h1 = net.get('h%d'%(i,))
            # print h2, h2.IP(), h2.MAC()
            h1.setMAC('00:00:00:00:00:%02d'%(i+1,))

        for i in range(S):
            for j in range(S):
                if i == j:
                    continue
                h1 = net.get('h%d'%(i,))
                h2 = net.get('h%d'%(j,))
                h1.setARP(h2.IP(), h2.MAC())
        net.start()
        sleep(5)
        # net.pingAll()
        CLI(net)
        net.stop()

def main():
    topo = JellyFishTop(S, N, r)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    experiment(net)

if __name__ == "__main__":
    main()

