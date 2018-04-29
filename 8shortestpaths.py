import networkx as nx
from itertools import islice
from collections import Counter
import itertools
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np


def k_shortest_paths(G, source, target, k, weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

def group(lst, n):
    """group([0,3,4,10,2,3], 2) => iterator

    Group an iterable into an n-tuples iterable. Incomplete tuples
    are discarded e.g.

    >>> list(group(range(10), 3))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    """
    return itertools.izip(*[itertools.islice(lst, i, None, n) for i in range(n)])

# each rack has k-r ports available for servers

# Degree of each node, Number of Nodes
G = nx.random_regular_graph(12, 25)

# id of link is (a,b), where a and b are routers
links = Counter()

for source in tqdm(G.nodes()):
  for target in G.nodes():
    paths = k_shortest_paths(G, source, target, 8)
    up = []
    for path in paths:
      up += [grp for grp in group(path,2)]
    links.update(up)

ysorted = links.most_common()
ysorted.reverse()
y = [val[1] for val in ysorted]
x = np.arange(1,len(links.most_common())+1)
plt.plot(x, y)
plt.xlabel('Rank of link')
plt.ylabel('# distinct paths through link')
plt.show()
