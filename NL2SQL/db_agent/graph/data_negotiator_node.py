from typing import Dict, Any
from db_agent.graph.state import AgentState

def data_negotiator_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 7: Presentation
    Checks if the SQL result is too large for the LLM to analyze directly.
    """
    print("--- [Node] Data Negotiator ---")
    
    results = state.get("sql_result", [])
    row_count = len(results)
    col_count = len(results[0]) if row_count > 0 else 0
    
    # Example: 10 rows * 5 columns = 50 cells
    CELL_LIMIT = 50

    total_cells = row_count * col_count 
    
    if total_cells > CELL_LIMIT:
        print(f"   > Dataset too large ({row_count} rows). Triggering negotiation.")
        return {
            "user_negotiated": False, # Flag that we need user input
            "next_action": "NEGOTIATE"
        }
        
    print(f"   > Dataset size safe ({row_count} rows). Proceeding to Analysis.")
    print(results)
    return {
        "next_action": "ANALYZE"
    }