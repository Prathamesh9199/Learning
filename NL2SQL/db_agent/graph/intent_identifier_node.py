import asyncio
from typing import Dict, Any, List
from db_agent.config import CHAT_MODEL_DEPLOYMENT
from db_agent.graph.state import AgentState
from db_agent.client.az_llm import build_agent
from db_agent.schema.pydantic_models import IntentClassification

async def intent_identifier_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 0: Intent Identification
    Classifies the user's latest message.
    FIX: Wipes 'Transient State' (Hypotheses, Causes) if this is a NEW query.
    """
    print("--- [Node] Intent Identifier ---")

    # 1. Robust Input Extraction
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'content'):
        user_input = last_message.content
    elif isinstance(last_message, dict):
        user_input = last_message.get('content', '')
    elif isinstance(last_message, (list, tuple)) and len(last_message) > 1:
        user_input = str(last_message[1])
    else:
        user_input = str(last_message)

    user_input_clean = user_input.lower().strip()
    previous_action = state.get("next_action")
    
    # =========================================================================
    # CHECK FOR RESUMING STATES (Do NOT wipe state here)
    # =========================================================================
    
    # CASE A: Approvals
    if previous_action == "WAIT_FOR_APPROVAL":
        print(f"   > Resuming from Approval State with input: '{user_input}'")
        affirmative = ["yes", "y", "proceed", "go ahead", "ok", "sure", "do it"]
        if any(x in user_input_clean for x in affirmative):
            print("   > Approval Granted. Forcing intent to DIAGNOSTIC.")
            return {"intent_status": "DIAGNOSTIC"} 

    # CASE B: Clarifications
    if previous_action == "CLARIFY":
        print(f"   > Resuming from Clarification with input: '{user_input}'")
        print("   > Assuming input is the corrected Entity. Forcing intent to DESCRIPTIVE.")
        return {"intent_status": "DESCRIPTIVE"}

    # =========================================================================
    # NEW QUERY DETECTED -> WIPE TRANSIENT STATE
    # =========================================================================
    # If we reached here, it's a fresh interaction. Clean up old artifacts.
    state_reset_updates = {
        "hypotheses_queue": [],      # Clear old hypotheses
        "confirmed_causes": [],      # Clear old findings
        "current_hypothesis": None,  # Clear active focus
        "tool_params": {},           # Clear old params
        "sql_result": []             # Clear old data
    }
    print("   > New Query Detected. Wiping transient diagnostic state.")

    # 2. Define System Prompt
    system_prompt = """
    You are an SQL Agent for analyzing SQL data.
    Classify the user's query into one of these categories:

    1. DESCRIPTIVE: Questions about 'What', 'How much', 'List', 'Show me'.
       Example: "What is the cost of Project X?", "Show top 5 accounts."
    
    2. DIAGNOSTIC: Questions about 'Why', 'Cause', 'Reason', 'Explain'.
       Example: "Why did cost go up?", "What drives attrition?"
    
    3. AMBIGUOUS: The query is vague or lacks context.
       Example: "It is high.", "Check that."

    4. INVALID: Off-topic queries (Weather, Coding, Jokes).
       Example: "Write a python script", "Who are you?"
    """

    # 3. Build Agent
    agent = build_agent(
        output_type_schema=IntentClassification,
        system_prompt=system_prompt,
        model_name=CHAT_MODEL_DEPLOYMENT['reasoning'],
    )

    # 4. Run Inference
    result = await agent.run(str(user_input))
    response: IntentClassification = result.output

    print(f"   > Detected Intent: {response.category} ({response.reasoning})")
    
    # Merge the Intent status with the Reset updates
    state_reset_updates["intent_status"] = response.category
    
    return state_reset_updates