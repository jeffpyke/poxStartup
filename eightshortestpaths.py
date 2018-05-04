import networkx as nx
from itertools import islice
from collections import Counter
import itertools
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np


def k_shortest_paths(G, source, target, k, weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

def get_results():
    # each rack has k-r ports available for servers

    # Degree of each node, Number of Nodes
    G = nx.random_regular_graph(12, 220)
    n_servers = 686

    # id of link is (a,b), where a and b are routers
    links = Counter()

    n_switches = len(G.nodes())

    servers = []
    for i in range(0, n_servers):
        servers.append((i, np.random.randint(0,high=n_switches)))

    send_assignments = np.random.choice(list(range(0,n_servers)), n_servers, replace=False)

    # no one send to themselves
    for i in range(0,len(send_assignments)):
        if send_assignments[i] == i:
            temp = send_assignments[i-1]
            send_assignments[i-1] = send_assignments[i]
            send_assignments[i] = temp

    for i, server in enumerate(servers):
        source = server[1]
        target = servers[send_assignments[i]][1]
        paths = k_shortest_paths(G, source, target, 8)
        up = []
        for path in paths:
            up += [grp for grp in zip(path[:-1], path[1:])]
        links.update(up)

    ysorted = links.most_common()
    ysorted.reverse()
    y = [val[1] for val in ysorted]
    x = np.arange(1,len(links.most_common())+1)
    return (x,y)
    # plt.plot(x, y)
    # plt.xlabel('Rank of link')
    # plt.ylabel('# distinct paths through link')
    # plt.show()
