from typing import Dict, Any
from db_agent.graph.state import AgentState
from db_agent.config import CHAT_MODEL_DEPLOYMENT
from db_agent.client.az_llm import build_agent
from db_agent.schema.pydantic_models import PlannerOutput

async def error_recovery_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 6: Execution (Safety)
    Catches SQL errors, asks LLM to fix params, and retries execution.
    """
    print("--- [Node] Error Recovery ---")
    
    error_msg = state.get("error_message")
    tool_params = state.get("tool_params", {})
    tool_name = tool_params.get("tool_name", "UnknownTool")
    
    print(f"   > Attempting to fix error: {error_msg}")

    # System Prompt: acts as a SQL Expert Debugger
    system_prompt = f"""
    You are a SQL Expert Debugger. 
    The previous attempt to run '{tool_name}' failed.
    
    PARAMETERS USED:
    {tool_params}
    
    ERROR MESSAGE:
    {error_msg}
    
    COMMON FIXES:
    - If "Invalid column name 'DATE'", try removing the Date params or checking the schema.
    - If "Error converting data type", check if a string ('Last Month') was passed to a Date field.
    - If "Invalid object name", check table names.
    
    YOUR GOAL:
    Output a corrected 'PlannerOutput' with the SAME action (EXECUTE) but fixed parameters.
    """

    agent = build_agent(
        output_type_schema=PlannerOutput,
        system_prompt=system_prompt,
        model_name=CHAT_MODEL_DEPLOYMENT['reasoning'],
    )

    # We ask the LLM to fix it
    result = await agent.run("Fix the parameters based on the error.")
    decision = result.output

    print(f"   > Fix Proposed: {decision.tool_params}")

    return {
        "tool_params": decision.tool_params,
        "error_message": None, # Clear the error
        "next_action": "RETRY" # Special flag for router
    }