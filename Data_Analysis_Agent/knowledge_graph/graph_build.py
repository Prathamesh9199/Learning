import networkx as nx
import json
import os

# 1. Initialize the Knowledge Graph
G = nx.DiGraph()

# 2. Define Nodes (Concepts)
concepts = [
    "Supermarket", "Branch", "City", 
    "Customer", "CustomerType", "Gender",
    "Sale", "Invoice", "TimeDimension",
    "Product", "ProductLine", 
    "PaymentMethod", 
    "FinancialMetric", 
    "UnitPrice", "Quantity", "Tax", "TotalAmount", "COGS", "GrossIncome",
    "Rating"
]

G.add_nodes_from(concepts)

# 3. Define Edges (Relationships)
relationships = [
    ("Supermarket", "Branch", {"rel": "OPERATES"}),
    ("Branch", "City", {"rel": "LOCATED_IN"}),
    ("Customer", "Branch", {"rel": "VISITS"}),
    ("Customer", "CustomerType", {"rel": "HAS_STATUS"}),
    ("Customer", "Gender", {"rel": "IDENTIFIES_AS"}),
    ("Customer", "Sale", {"rel": "INITIATES"}),
    ("Sale", "Branch", {"rel": "OCCURS_AT"}),
    ("Sale", "Invoice", {"rel": "GENERATES"}),
    ("Sale", "TimeDimension", {"rel": "RECORDED_AT"}),
    ("Sale", "Product", {"rel": "CONTAINS"}),
    ("Product", "ProductLine", {"rel": "BELONGS_TO"}),
    ("Product", "UnitPrice", {"rel": "HAS_PRICE"}),
    ("Sale", "Quantity", {"rel": "HAS_VOLUME"}),
    ("Sale", "PaymentMethod", {"rel": "PAID_VIA"}),
    ("Sale", "TotalAmount", {"rel": "RESULTS_IN"}),
    ("Sale", "Tax", {"rel": "INCURS"}),
    ("Sale", "COGS", {"rel": "COSTS"}),
    ("Sale", "GrossIncome", {"rel": "YIELDS"}),
    ("Sale", "Rating", {"rel": "RATED_BY"}),
    ("Rating", "Branch", {"rel": "EVALUATES_PERFORMANCE_OF"})
]

for source, target, data in relationships:
    G.add_edge(source, target, relationship=data['rel'])

# --- THE FIX IS HERE ---

# 4. Export to JSON (Manual Construction)
# We manually build the dict to ensure no NetworkX View objects slip through.

# Construct Nodes list
nodes_data = [{"id": node} for node in G.nodes()]

# Construct Links list
# We explicitly iterate and unpack the data to ensure it's a standard dict
links_data = []
for u, v, data in G.edges(data=True):
    links_data.append({
        "source": u,
        "target": v,
        "relationship": data["relationship"]
    })

# Combine into final structure
kg_data = {
    "nodes": nodes_data,
    "links": links_data
}

# Determine output path (saves in the current working directory)
output_file = "supermarket_kg.json"

try:
    with open(output_file, "w") as f:
        json.dump(kg_data, f, indent=4)
    print(f"SUCCESS: Graph exported to '{output_file}'")
    print(f"Stats: {len(nodes_data)} Nodes, {len(links_data)} Edges.")
except Exception as e:
    print(f"FAILED to write JSON: {e}")