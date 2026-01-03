from typing import Dict, Any
from langchain_core.messages import AIMessage
from db_agent.graph.state import AgentState

def human_clarification_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 4: Socratic Helper (Interaction)
    Asks the user to resolve ambiguity or missing information.
    """
    print("--- [Node] Human Clarification ---")
    
    issues = state.get("clarification_options", [])
    
    # Construct a polite clarification request
    if not issues:
        msg = "I need some clarification to proceed. Could you rephrase your request?"
    else:
        msg = "I found a few issues with the request details:\n"
        for issue in issues:
            msg += f"- {issue}\n"
        msg += "\nPlease specify which one you meant."

    return {
        "messages": [AIMessage(content=msg)],
        # We assume the next user message will fix this, so we reset loop counts?
        # Or we essentially STOP here and wait for new input.
        # In a real graph, this points to END, waiting for User Input.
    }