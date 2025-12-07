from knowledge_graph.build_graph import G

class BusinessGraphEngine:
    def __init__(self, nx_graph):
        self.graph = nx_graph

    def get_neighbors_undirected(self, node_name: str):
        """
        Retrieves all connections regardless of direction, 
        but preserves directionality in the output metadata.
        """
        if node_name not in self.graph:
            return f"Node '{node_name}' not found in graph."

        results = []

        # 1. Check Outgoing Edges (Node -> Target)
        # "Downstream impacts"
        if self.graph.has_node(node_name):
            successors = self.graph.successors(node_name)
            for neighbor in successors:
                edge_data = self.graph.get_edge_data(node_name, neighbor)
                results.append({
                    "source": node_name,
                    "target": neighbor,
                    "relationship": edge_data.get("relationship", "related_to"),
                    "direction": "outgoing" # Agent knows: Node -> Neighbor
                })

        # 2. Check Incoming Edges (Source -> Node)
        # "Upstream causes"
        if self.graph.has_node(node_name):
            predecessors = self.graph.predecessors(node_name)
            for neighbor in predecessors:
                edge_data = self.graph.get_edge_data(neighbor, node_name)
                results.append({
                    "source": neighbor,
                    "target": node_name,
                    "relationship": edge_data.get("relationship", "related_to"),
                    "direction": "incoming" # Agent knows: Neighbor -> Node
                })

        return results

    def validate_node(self, node_name: str):
        """Simple check to see if a node exists (case sensitive for now)"""
        return self.graph.has_node(node_name)

# --- Test the Engine ---
engine = BusinessGraphEngine(G)

# Search for "CPP"
# We expect to see Labor_Cost (Incoming) and nothing outgoing (based on current graph)
print(f"--- Neighbors of CPP ---")
neighbors = engine.get_neighbors_undirected("CPP")
for n in neighbors:
    if n['direction'] == 'incoming':
        print(f"{n['source']} --[{n['relationship']}]--> {n['target']}")
    else:
        print(f"{n['source']} --[{n['relationship']}]--> {n['target']}")

# Search for "Production_Volume" 
# We expect Market_Demand (Incoming) AND CPP (Outgoing)
print(f"\n--- Neighbors of Production_Volume ---")
neighbors_vol = engine.get_neighbors_undirected("Production_Volume")
for n in neighbors_vol:
    print(n)