from typing import Dict, Any
from db_agent.config import CHAT_MODEL_DEPLOYMENT
from db_agent.graph.state import AgentState
from db_agent.client.az_llm import build_agent
from db_agent.schema.pydantic_models import NaturalAnswerOutput 

async def result_analyzer_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 5: Analysis
    Summarizes raw SQL results into an investigation log.
    FIX: Pushes specific findings to stream_buffer for UI visibility.
    """
    print("--- [Node] Result Analyzer ---")
    
    sql_result = state.get("sql_result", [])
    hypothesis = state.get("current_hypothesis", "General Data")
    tool_params = state.get("tool_params", {})
    current_buffer = state.get("stream_buffer", [])
    
    if not sql_result:
        msg = f"No data found for {hypothesis}."
        return {
            "confirmed_causes": [msg],
            "stream_buffer": current_buffer + [f"Analyzer: {msg}"]
        }

    # System Prompt for Analysis
    system_prompt = f"""
    You are a Data Analyst. 
    Analyze the raw SQL data below regarding '{hypothesis}'.
    Summarize the key finding in 1 sentence.
    
    CONTEXT:
    - Tool Used: {tool_params}
    - Raw Data: {str(sql_result)[:2000]} 
    
    OUTPUT:
    Just the insight. Example: "Attrition is 20% higher in India than US."
    """

    agent = build_agent(
        output_type_schema=NaturalAnswerOutput,
        system_prompt=system_prompt,
        model_name=CHAT_MODEL_DEPLOYMENT['reasoning']
    )

    result = await agent.run("Analyze this.")
    insight = result.output.answer

    print(f"   > Insight: {insight}")

    # PUSH TO UI LOGS
    log_msg = f"🔍 Insight found for [{hypothesis}]: {insight}"

    existing_causes = state.get("confirmed_causes", []) or []
    new_cause = f"{hypothesis}: {insight}"
    
    return {
        "confirmed_causes": existing_causes + [new_cause],
        "sql_result": [],
        "stream_buffer": current_buffer + [log_msg] # <--- Update UI
    }