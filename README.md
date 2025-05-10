# Assignment4
SDN Controller
This repository contains a simplified SDN controller simulator in Python.
  Supporting:
    Mainting a network topology graph
    Computing primary and backup shortest paths
    Generates flow table entries for OpenFlow-like switches
    Handles link failures and recondfigures affected flows
    Priority scheduling, load-balancing, and backup paths for critical flows
    Interactive CLI for flow operations
    Visualization of topology and link utilization

Prereq's
  Python 3.8 installed
  networkx, matplotlib

Running the Controller
  python sdncontroller.py
  You will see:
    SDN Controller CLI. Type help or ? to list commands.
    sdn>

CLI Commands
add_node <NODE> Add a switch node to the topology

remove_node <NODE> Remove a switch node

add_link <U> <V> [CAP] Add link U↔V with optional capacity (default=10)

remove_link <U> <V> Remove link U↔V and reconfigure flows

inject_flow S D [P] [C] Inject flow from S to D with priority P, critical flag C

fail_link <U> <V> Simulate link failure and auto-reroute flows

show_topology Display network topology visually

show_flows List all installed flows and their paths

show_util Show link utilization (# flows / capacity)

exit Exit the CLI
