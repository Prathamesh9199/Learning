import networkx as nx
import json
import difflib
import os
from typing import List, Dict, Any

# Default path assuming script is run from root
DEFAULT_SCHEMA_PATH = "knowledge_graph/data.json"

class KGManager:
    """
    The 'Right Brain' Manager.
    Handles loading the Knowledge Graph, fuzzy searching concepts, 
    and traversing relationships to build business context.
    """

    def __init__(self, schema_path: str = DEFAULT_SCHEMA_PATH):
        self.schema_path = schema_path
        self.G = nx.DiGraph()
        self.schema_loaded = False
        self._load_schema()

    def _load_schema(self):
        """Internal method to load JSON into NetworkX."""
        if not os.path.exists(self.schema_path):
            print(f"⚠️ Warning: Schema file not found at {self.schema_path}")
            return

        try:
            with open(self.schema_path, 'r') as f:
                data = json.load(f)

            # 1. Load Nodes
            for node in data.get('nodes', []):
                self.G.add_node(node['id'], **node)

            # 2. Load Edges
            for link in data.get('links', []):
                self.G.add_edge(
                    link['source'], 
                    link['target'], 
                    relationship=link['relationship']
                )
            
            self.schema_loaded = True
            print(f"✅ KG Loaded: {self.G.number_of_nodes()} Nodes, {self.G.number_of_edges()} Edges.")
            
        except Exception as e:
            print(f"❌ Failed to load KG: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Returns graph health statistics."""
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "density": nx.density(self.G),
            "is_directed": self.G.is_directed()
        }

    # --- TOOL 1: FINDING CONCEPTS ---
    def search_concept(self, query: str, threshold: float = 0.6) -> List[str]:
        """
        Fuzzy searches for a node name. 
        Vital for mapping vague user terms (e.g., 'Money') to specific Nodes (e.g., 'TotalAmount').
        """
        all_nodes = list(self.G.nodes())
        
        # 1. Exact Match
        exact = [n for n in all_nodes if n.lower() == query.lower()]
        if exact: return exact

        # 2. Substring Match
        substring = [n for n in all_nodes if query.lower() in n.lower()]

        # 3. Fuzzy Match
        fuzzy = difflib.get_close_matches(query, all_nodes, n=3, cutoff=threshold)

        # De-duplicate and return
        return list(set(exact + substring + fuzzy))

    # --- TOOL 2: UNDERSTANDING CONTEXT ---
    def get_neighbors(self, node_id: str) -> List[str]:
        """
        Returns immediate parents and children.
        Explains: "What determines this?" (Parents) and "What does this determine?" (Children)
        """
        if node_id not in self.G:
            return [f"Node '{node_id}' not found."]

        context = []
        
        # Incoming (Dependencies)
        for source, _, data in self.G.in_edges(node_id, data=True):
            rel = data.get('relationship', 'RELATED_TO')
            context.append(f"[INPUT] {source} --({rel})--> {node_id}")

        # Outgoing (Impacts)
        for _, target, data in self.G.out_edges(node_id, data=True):
            rel = data.get('relationship', 'RELATED_TO')
            context.append(f"[OUTPUT] {node_id} --({rel})--> {target}")

        return context

    # --- TOOL 3: TRACING CAUSALITY ---
    def find_path(self, source: str, target: str) -> List[str]:
        """
        Finds how two concepts are connected.
        Example: How does 'Customer' impact 'GrossIncome'?
        """
        if source not in self.G or target not in self.G:
            return [f"One or both nodes ('{source}', '{target}') missing."]

        try:
            path = nx.shortest_path(self.G, source=source, target=target)
            explanation = []
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                edge_data = self.G.get_edge_data(u, v)
                rel = edge_data.get('relationship', 'LINKS_TO')
                explanation.append(f"{u} --[{rel}]--> {v}")
                
            return explanation
        except nx.NetworkXNoPath:
            return [f"No direct path found between {source} and {target}."]

# --- TEST BLOCK ---
if __name__ == "__main__":
    kg = KGManager()
    
    print("\n--- Test: Search 'Profit' ---")
    # Should find 'GrossIncome' or 'TotalAmount' if fuzzy logic works well, 
    # or you might need to add aliases to your schema if it fails.
    print(kg.search_concept("Income")) 

    print("\n--- Test: Context of 'Sale' ---")
    for link in kg.get_neighbors("Sale"):
        print(link)

    print("\n--- Test: Path Customer -> GrossIncome ---")
    print(kg.find_path("Customer", "GrossIncome"))