from typing import Dict, Any
from langchain_core.messages import AIMessage
from db_agent.graph.state import AgentState

def investigation_approval_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 5: Diagnostic (Safety Valve)
    Checks if the planned investigation is too expensive/long.
    """
    print("--- [Node] Investigation Approval ---")
    
    queue = state.get("hypotheses_queue", [])
    
    # THRESHOLD: If analyzing more than 3 factors, ask for permission.
    SAFE_THRESHOLD = 3
    
    if len(queue) > SAFE_THRESHOLD:
        print(f"   > Large investigation detected ({len(queue)} items). Pausing for approval.")
        msg = (
            f"To answer this, I need to investigate {len(queue)} different factors "
            f"(Columns: {queue}). This might take a moment. Shall I proceed?"
        )
        return {
            "messages": [AIMessage(content=msg)],
            "next_action": "WAIT_FOR_APPROVAL"
        }
    
    print("   > Investigation size safe. Proceeding automatically.")
    return {"next_action": "APPROVED"}