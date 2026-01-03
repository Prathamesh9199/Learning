from typing import Dict, Any
from db_agent.graph.state import AgentState

def context_loader_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 0: Security & Context
    Loads User Identity and Permissions.
    FIX: Resets the 'stream_buffer' so logs don't duplicate across turns.
    """
    print("--- [Node] Context Loader ---")
    
    # MOCK: Simulating an authenticated Admin user
    user_context = {
        "user_id": "u_1001",
        "role": "ADMIN",
        "access_level": "CONTRIBUTOR",
        "tenant_id": "default_tenant"
    }

    # RESET the stream_buffer here to ensure a clean log for the new turn
    return {
        "user_info": user_context,
        "stream_buffer": [] 
    }