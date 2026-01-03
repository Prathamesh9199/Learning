import json
import os
from datetime import datetime
from typing import Dict, Any
from db_agent.graph.state import AgentState

LOG_FILE = "chat_logs.jsonl"

def feedback_logger_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 8: Finalization
    Logs the conversation interaction for analytics.
    """
    print("--- [Node] Feedback Logger ---")
    
    try:
        # 1. Gather Data
        messages = state["messages"]
        user_query = messages[0].content if messages else "Unknown"
        final_response = messages[-1].content if messages else "Unknown"
        tool_params = state.get("tool_params", {})
        intent = state.get("intent_status", "Unknown")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "query": user_query,
            "response": final_response,
            "tools_used": tool_params
        }
        
        # 2. Append to Log File (JSON Lines format)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        print("   > Interaction logged successfully.")
        
    except Exception as e:
        print(f"   > Logging failed: {e}")

    # No state updates needed, this is a sink node.
    return {}