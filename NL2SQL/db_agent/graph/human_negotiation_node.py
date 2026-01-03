from typing import Dict, Any
from langchain_core.messages import AIMessage
from db_agent.graph.state import AgentState

def human_negotiation_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 7: Presentation
    Asks the user how to handle large data: Truncate (Top N) or Cancel?
    """
    print("--- [Node] Human Negotiation ---")
    
    row_count = len(state.get("sql_result", []))
    
    msg = (
        f"I retrieved {row_count} rows, which is too much data to analyze at once.\n"
        "How would you like to proceed?\n"
        "1. Analyze the Top 5 only\n"
        "2. Cancel this step"
    )
    
    # We return a message and STOP. 
    # The next user input will be handled by 'hard_truncate_node' logic in the router.
    return {
        "messages": [AIMessage(content=msg)],
        "user_negotiated": True # We have asked. Next time we enter the graph, we check the answer.
    }