from typing import Dict, Any
from langchain_core.messages import AIMessage
from db_agent.config import CHAT_MODEL_DEPLOYMENT
from db_agent.graph.state import AgentState
from db_agent.client.az_llm import build_agent
from db_agent.schema.pydantic_models import ResponseOutput

async def response_synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 7: Presentation
    Synthesizes the final answer using the 'Snapshot' (tool_params) 
    instead of the messy history.
    """
    print("--- [Node] Response Synthesizer ---")
    
    # 1. Load the "Snapshot" (The Truth)
    snapshot = state.get("tool_params", {})
    
    # 2. Load the Findings
    findings = state.get("confirmed_causes", [])
    
    # 3. Load the Intent (What they wanted)
    intent = state.get("intent_status")
    
    # 4. Load History (Only for conversational flow, NOT for facts)
    latest_user_msg = state["messages"][-1]

    system_prompt = f"""
    You are Sherlock, an AI Data Analyst.
    
    CRITICAL INSTRUCTION: 
    Use the 'CURRENT SNAPSHOT' below as the ground truth for *what* was analyzed.
    Ignore any conflicting names or typos in the 'User Query' if they differ from the Snapshot.

    --- CURRENT SNAPSHOT (The Active Context) ---
    Parameters Used: {snapshot}
    (Example: If User asked for 'Project X' but Snapshot says 'Project Y', answer for 'Project Y'.)

    --- FINDINGS (The Data) ---
    {findings}

    --- USER GOAL ---
    Intent: {intent}
    Original Query: "{latest_user_msg}"

    INSTRUCTIONS:
    1. Answer the user's question using ONLY the Findings.
    2. If the Snapshot Name differs from the User Query Name, politely clarify: 
       "I searched for [Snapshot Name] and found..."
    3. If findings include specific metrics (like Cost or Headcount), mention them explicitly.
    4. If the user asked for a derived metric (like Cost Per Person) and you have the raw numbers (Total Cost, FTE), CALCULATE IT.

    Generate a helpful, professional response.
    """

    agent = build_agent(
        output_type_schema=ResponseOutput,
        system_prompt=system_prompt,
        model_name=CHAT_MODEL_DEPLOYMENT['reasoning'],
    )

    result = await agent.run(latest_user_msg)
    final_text = result.output.final_response

    print(f"   > Final Answer: {final_text}")

    return {
        "messages": [AIMessage(content=final_text)]
    }