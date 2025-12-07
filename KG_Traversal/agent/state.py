import operator
from typing import Annotated, List, TypedDict, Union
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from knowledge_graph.kg_module import BusinessGraphEngine
from knowledge_graph.build_graph import G

engine = BusinessGraphEngine(G) 

# --- Define the State ---
# This acts as the memory for our Agent during the conversation
class AgentState(TypedDict):
    question: str                   # The user's original question
    current_focus_node: str         # The node we are currently investigating
    graph_context: List[str]        # Accumulated facts (e.g., "Revenue -> CPP")
    iterations: int                 # Safety break to prevent infinite loops
    final_answer: str               # The generated response

def query_knowledge_graph(node_name: str) -> str:
    """
    Tools that queries the NetworkX graph. 
    Returns text description of relationships to feed back into the LLM.
    """
    # 1. fuzzy matching/validation (simplified here)
    if not engine.validate_node(node_name):
        return f"Node '{node_name}' not found. Try a different term."
    
    # 2. Get Undirected Neighbors (The 'Secret Sauce' from Phase 2)
    results = engine.get_neighbors_undirected(node_name)
    
    if not results:
        return f"Node '{node_name}' has no connections."

    # 3. Format for the LLM
    # We explicitly tell the LLM the directionality here
    context_strings = []
    for r in results:
        if r['direction'] == 'incoming':
            # e.g., "Labor_Cost affects CPP"
            stmt = f"FACT: {r['source']} -[{r['relationship']}]-> {r['target']}"
        else:
            # e.g., "CPP impacts Profit"
            stmt = f"FACT: {r['source']} -[{r['relationship']}]-> {r['target']}"
        context_strings.append(stmt)
        
    return "\n".join(context_strings)