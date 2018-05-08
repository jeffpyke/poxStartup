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
from mininet.util import pmonitor
from mininet.log import setLogLevel, info
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time
import networkx as nx
import random
from signal import SIGINT

S = 10
N = 10
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
        cpopens = {}
        spopens = {}
        speeds = []
        assignments = range(S) 
        net.pingAll()
        net.iperf(seconds = 20)
        net.iperf(seconds = 20)
        net.iperf(seconds = 20)
        flows = 1
        while any([a == i for i, a in enumerate(assignments)]):
            random.shuffle(assignments)
        for i, h in enumerate(net.hosts):
            other_h = net.hosts[assignments[i]]
            spopens[other_h] = other_h.popen('iperf', '-s')
            cpopens[h] = h.popen('iperf', '-c', other_h.IP(), '-f', 'm', '-P', str(flows), '-t', '20')
        cclosed = 0
        sclosed = 0
        endtime = time() + 150 # 150 seconds to complete

        for h, line in pmonitor(cpopens, timeoutms=10000):
            if h:
                info('%s: %s' % (h.name, line))
                if 'Mbit' in line:
                    if 'SUM' not in line:
                        speed = float(line.split()[-2])
                        speeds.append(speed)
                        cclosed += 1
            if time() > endtime:
                # info("timeout kill")
                for p in cpopens.values():
                    p.send_signal(SIGINT)
            if cclosed == N*(flows): # +1 for the sum equation
                for p in cpopens.values():
                    p.send_signal(SIGINT)
        for h, line in pmonitor(spopens, timeoutms=10000):
            if h:
                info('server %s: %s' % (h.name, line))
                if 'bits/sec' in line and 'SUM' not in line:
                  sclosed += 1
            if time() > endtime:
                # info("timeout kill")
                for p in spopens.values():
                    p.send_signal(SIGINT)
            if sclosed == N*(flows):
                info("shutting down")
                for p in spopens.values():
                    p.send_signal(SIGINT)

        # CLI(net)
        info("\n")
        info(speeds)
        info("\n")
        info("got %d speeds, avg %f Mbits/s" % (len(speeds), flows*float(sum(speeds)) / len(speeds)))
        net.stop()

def main():
    topo = JellyFishTop(S, N, r)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    experiment(net)

if __name__ == "__main__":
    setLogLevel( 'info' )
    main()

