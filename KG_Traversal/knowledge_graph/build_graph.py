import networkx as nx
import json

def build_cpp_knowledge_graph():
    G = nx.DiGraph()

    # --- Level 1: Core Impacts on CPP ---
    # Upstream (Causes of High CPP)
    G.add_edge("Raw_Material_Cost", "CPP", relationship="increases", type="direct")
    G.add_edge("Labor_Cost", "CPP", relationship="increases", type="direct")
    G.add_edge("Overhead_Cost", "CPP", relationship="increases", type="direct")
    G.add_edge("Defect_Rate", "CPP", relationship="increases_waste", type="direct")
    
    # Inverse relationships
    G.add_edge("Production_Volume", "CPP", relationship="decreases (economies of scale)", type="direct")

    # --- Level 2: Root Causes (2 hops) ---
    # Raw Material Branch
    G.add_edge("Steel_Price", "Raw_Material_Cost", relationship="determines", type="market")
    G.add_edge("Supplier_Delays", "Raw_Material_Cost", relationship="increases_expediting_fees", type="operational")
    
    # Labor Branch
    G.add_edge("Overtime_Hours", "Labor_Cost", relationship="inflates", type="operational")
    G.add_edge("Union_Contract", "Labor_Cost", relationship="sets_baseline", type="legal")
    
    # Overhead Branch
    G.add_edge("Energy_Price", "Overhead_Cost", relationship="impacts", type="market")
    G.add_edge("Machine_Maintenance", "Overhead_Cost", relationship="adds_to", type="operational")

    # Volume Branch
    G.add_edge("Market_Demand", "Production_Volume", relationship="caps", type="market")
    G.add_edge("Machine_Uptime", "Production_Volume", relationship="enables", type="operational")

    # --- Level 3: External/Context (3 hops) ---
    G.add_edge("Geopolitical_Events", "Steel_Price", relationship="volatility", type="external")
    G.add_edge("Global_Pandemic", "Supplier_Delays", relationship="causes", type="external")
    G.add_edge("Competitor_Pricing", "Market_Demand", relationship="reduces", type="external")
    G.add_edge("Preventative_Maintenance_Plan", "Machine_Uptime", relationship="improves", type="operational")
    G.add_edge("Skill_Shortage", "Overtime_Hours", relationship="forces", type="hr")

    return G

# 1. Build
G = build_cpp_knowledge_graph()

# 2. Convert to JSON serializable list of edges (tuples)
data = list(nx.edges(G)) # <-- FIX IS HERE

# 3. Export
with open("knowledge_graph.json", "w") as f:
    json.dump(data, f, indent=2)

print("Graph exported to 'knowledge_graph.json'")