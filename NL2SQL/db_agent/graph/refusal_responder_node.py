from typing import Dict, Any
from langchain_core.messages import AIMessage
from db_agent.graph.state import AgentState

def refusal_responder_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 7: Finalization (Refusal Path)
    Handles queries flagged as INVALID by the Intent Identifier.
    """
    print("--- [Node] Refusal Responder ---")
    
    # Standard refusal message
    refusal_msg = (
        "I am Sherlock, a specialized SQL Agent for analyzing Cost Per Person data. "
        "I cannot assist with general topics, coding requests, or creative writing. "
        "Please ask me about Project Costs, Attrition, or Financial Metrics."
    )
    
    # Return as an AI Message so it shows up in chat history
    return {
        "messages": [AIMessage(content=refusal_msg)]
    }