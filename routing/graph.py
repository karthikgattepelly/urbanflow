import osmnx as ox
import networkx as nx

# Center point of your demo area (Gachibowli, Hyderabad). Change if you like.
CENTER = (17.4400, 78.3489)
DIST = 1200  # metres around the center

def load_graph():
    G = ox.graph_from_point(CENTER, dist=DIST, network_type="drive")
    # give every edge a travel time using speed estimates
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G

if __name__ == "__main__":
    G = load_graph()
    print("nodes:", len(G.nodes), "edges:", len(G.edges))
    ox.save_graphml(G, "data/graph.graphml")
    print("saved to data/graph.graphml")