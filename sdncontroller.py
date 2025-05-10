# Watermark: SHA256(890729768+"NeoDDaBRgX5a9") = cb60b1ef56c4ce7daedd06a7542a91c44f57db1b901ffda083734e6e165e43d6


import sys
import networkx as nx
import matplotlib.pyplot as plt
from cmd import Cmd
import threading
import time

class Flow:
    def __init__(self, fid, src, dst, priority=1, critical=False):
        self.id = fid
        self.src = src
        self.dst = dst
        self.priority = priority
        self.critical = critical
        self.path = []
        self.backup = []

class SDNController:
    def __init__(self):
        self.graph = nx.Graph()
        self.flows = {}
        self.next_flow_id = 1
        self.link_capacity = {}  # (u,v) -> capacity
        self.lock = threading.Lock()

    #Topology management
    def add_node(self, node):
        self.graph.add_node(node)
        print(f"Node {node} added.")

    def remove_node(self, node):
        self.graph.remove_node(node)
        print(f"Node {node} removed.")

    def add_link(self, u, v, capacity=10):
        self.graph.add_edge(u, v, weight=1)
        self.link_capacity[(u, v)] = capacity
        self.link_capacity[(v, u)] = capacity
        print(f"Link {u}<->{v} added with capacity {capacity}.")

    def remove_link(self, u, v):
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
            self.link_capacity.pop((u, v), None)
            self.link_capacity.pop((v, u), None)
            print(f"Link {u}<->{v} removed.")
            self._reconfigure_flows(u, v)
        else:
            print(f"Link {u}<->{v} does not exist.")

    # Path computation & installation
    def _compute_primary_backup(self, src, dst):
        try:
            paths = list(nx.all_shortest_paths(self.graph, src, dst, weight='weight'))
        except nx.NetworkXNoPath:
            return [], []
        if not paths:
            return [], []
        primary = paths[0]
        backup = paths[1:] if len(paths) > 1 else []
        return primary, backup

    def install_flow(self, src, dst, priority=1, critical=False):
        if not (self.graph.has_node(src) and self.graph.has_node(dst)):
            print(f"Cannot install flow: {src} or {dst} not in topology.")
            return None
        fid = self.next_flow_id
        self.next_flow_id += 1
        flow = Flow(fid, src, dst, priority, critical)
        primary, backups = self._compute_primary_backup(src, dst)
        if not primary:
            print(f"No path from {src} to {dst}. Flow not installed.")
            return None
        flow.path = primary
        flow.backup = backups[0] if backups else []
        self.flows[fid] = flow
        self._update_flow_tables(flow)
        print(f"Flow {fid} installed: {src}->{dst} via {primary}")
        if flow.backup:
            print(f"  Backup path: {flow.backup}")
        return fid

    def _update_flow_tables(self, flow):
        for i in range(len(flow.path) - 1):
            sw = flow.path[i]
            out = flow.path[i + 1]
            print(f"Switch {sw}: match dst={flow.dst} -> out_port to {out}")

    def _reconfigure_flows(self, u, v):
        for flow in list(self.flows.values()):
            if u in flow.path and v in flow.path:
                print(f"Link {u}<->{v} affected flow {flow.id}, re-routing...")
                if flow.backup:
                    flow.path = flow.backup
                    flow.backup = []
                    self._update_flow_tables(flow)
                    print(f"  Now via {flow.path}")
                else:
                    print(f"  No backup available for flow {flow.id}!")

    # Monitoring & Utilization
    def show_topology(self):
        try:
            pos = nx.spring_layout(self.graph)
            nx.draw(self.graph, pos, with_labels=True)
            plt.title("Network Topology")
            plt.show()
        except Exception as e:
            print(f"Visualization error: {e}")

    def show_flows(self):
        if not self.flows:
            print("No flows installed.")
        for fid, flow in self.flows.items():
            print(f"Flow {fid}: {flow.src}->{flow.dst}, primary={flow.path}")

    def show_utilization(self):
        util = {edge: 0 for edge in self.graph.edges()}
        for flow in self.flows.values():
            for i in range(len(flow.path) - 1):
                e = (flow.path[i], flow.path[i + 1])
                util[e] = util.get(e, 0) + 1
        print("Link utilization (# flows):")
        for e, u in util.items():
            cap = self.link_capacity.get(e, 0)
            print(f"  {e}: {u}/{cap}")

# CLI Interface
class SDNCli(Cmd):
    intro = "SDN Controller CLI. Type help or ? to list commands."
    prompt = "sdn> "

    def __init__(self, controller):
        super().__init__()
        self.ctrl = controller

    def do_add_node(self, arg):
        'add_node NODE'
        self.ctrl.add_node(arg.strip())

    def do_remove_node(self, arg):
        'remove_node NODE'
        self.ctrl.remove_node(arg.strip())

    def do_add_link(self, arg):
        'add_link U V [CAPACITY]'
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: add_link U V [CAPACITY]")
            return
        u, v = parts[0], parts[1]
        cap = int(parts[2]) if len(parts) > 2 else 10
        self.ctrl.add_link(u, v, cap)

    def do_remove_link(self, arg):
        'remove_link U V'
        parts = arg.split()
        if len(parts) != 2:
            print("Usage: remove_link U V")
            return
        self.ctrl.remove_link(parts[0], parts[1])

    def do_inject_flow(self, arg):
        'inject_flow SRC DST [PRIORITY] [critical]'
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: inject_flow SRC DST [PRIORITY] [critical]")
            return
        src, dst = parts[0], parts[1]
        prio = int(parts[2]) if len(parts) > 2 else 1
        crit = (len(parts) > 3 and parts[3].lower() == "true")
        self.ctrl.install_flow(src, dst, prio, crit)

    def do_show_topology(self, arg):
        'show_topology'
        self.ctrl.show_topology()

    def do_show_flows(self, arg):
        'show_flows'
        self.ctrl.show_flows()

    def do_show_util(self, arg):
        'show_util'
        self.ctrl.show_utilization()

    def do_fail_link(self, arg):
        'fail_link U V'
        parts = arg.split()
        if len(parts) != 2:
            print("Usage: fail_link U V")
            return
        self.ctrl.remove_link(parts[0], parts[1])

    def do_exit(self, arg):
        'Exit CLI'
        print("Exiting.")
        return True

if __name__ == '__main__':
    ctrl = SDNController()
    #Pre-load sample topology
    for n in ['A','B','C','D']:
        ctrl.add_node(n)
    ctrl.add_link('A','B')
    ctrl.add_link('B','C')
    ctrl.add_link('C','D')
    ctrl.add_link('A','D')

    cli = SDNCli(ctrl)
    #Detect interactive support
    if sys.stdin and sys.stdin.isatty():
        try:
            cli.cmdloop()
        except OSError:
            print("Interactive mode not supported, falling back to tests.")
    else:
        print("\nRunning non-interactive test cases:")
        #Test: install a valid flow, show flows, show utilization
        cli.onecmd('inject_flow A D')
        cli.onecmd('show_flows')
        cli.onecmd('show_util')
        #Test: fail a link and observe reconfiguration
        cli.onecmd('fail_link A B')
        cli.onecmd('inject_flow A C')
        cli.onecmd('show_flows')
        cli.onecmd('show_util')
