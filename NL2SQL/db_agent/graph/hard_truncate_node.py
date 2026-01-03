from typing import Dict, Any
from db_agent.graph.state import AgentState

def hard_truncate_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 7: Presentation
    Truncates the dataset to the safe threshold.
    """
    print("--- [Node] Hard Truncate ---")
    
    results = state.get("sql_result", [])
    limit = 5 # Must match the Negotiator threshold
    
    truncated_results = results[:limit]
    
    print(f"   > Truncated data from {len(results)} to {len(truncated_results)} rows.")
    
    return {
        "sql_result": truncated_results,
        "next_action": "ANALYZE" # Now it is safe to go to the Analyzer
    }