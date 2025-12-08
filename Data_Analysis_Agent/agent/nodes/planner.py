import json
from typing import List
from agent.state import AgentState
from resources.schema.pydantic_schemas import AgentPlan, StoredProcedure
from resources.registry.sql_sp import SP_REGISTRY
from client.llm_manager import build_agent
from langchain_core.messages import HumanMessage, SystemMessage

def format_registry_for_prompt() -> str:
    """
    Converts the SP_REGISTRY into a clear text description for the LLM.
    """
    docs = []
    for sp_name, sp_meta in SP_REGISTRY.items():
        # Clean representation of parameters
        params = ", ".join([f"{k} ({v.description})" for k, v in sp_meta.parameters.items()])
        if not params:
            params = "None"
            
        doc = (
            f"- Tool Name: {sp_name}\n"
            f"  Description: {sp_meta.description}\n"
            f"  Parameters: {params}\n"
            f"  Returns: {sp_meta.returns}"
        )
        docs.append(doc)
    return "\n\n".join(docs)

async def planner_node(state: AgentState) -> dict:
    """
    Refines the user query into a structured AgentPlan using available SPs.
    """
    print("\n🔵 Node: Planner")
    
    # 1. Get the latest user message
    # In LangGraph, messages are a list. We usually look at the last HumanMessage.
    user_query = state["messages"][-1].content
    
    # 2. Check for feedback (Replanning)
    # If the user rejected the previous plan, we inject that context.
    feedback_context = ""
    if state.get("user_feedback"):
        feedback_context = (
            f"\n\nIMPORTANT: The user rejected your previous plan. "
            f"Here is their feedback: '{state['user_feedback']}'. "
            f"You MUST adjust the plan to address this feedback."
        )

    # 3. Construct System Prompt
    tool_definitions = format_registry_for_prompt()

    # 1. Generate the schema from the Pydantic model
    schema = AgentPlan.model_json_schema()

    # 2. Convert it to a string
    schema_str = json.dumps(schema, indent=2)

    system_prompt = (
        "You are a Senior Data Analyst Agent. "
        "Your goal is to answer the user's question by creating a Step-by-Step execution plan.\n\n"
        
        "### CONSTRAINTS\n"
        "1. You CANNOT write arbitrary SQL. You can ONLY use the specific Stored Procedures listed below.\n"
        "2. If the user asks for something impossible with these tools, Create a plan with a single step explaining why it's impossible.\n"
        "3. Your plan must be logical. Use the output of one step as context for the next if needed.\n"
        "4. Be precise with parameter values. If a date is needed, infer it from the user prompt or use standard defaults.\n"
        "5. Answer strictly in JSON format.\n\n"
        
        "### AVAILABLE TOOLS (Stored Procedures)\n"
        f"{tool_definitions}\n"
        
        f"{feedback_context}"

        "### ANSWER FORMAT\n"
        "Output valid JSON that matches the following JSON Schema:\n"
        f"{schema_str}"
    )

    # 4. Invoke LLM (PydanticAI)
    # We use reasoning='medium' to ensure it thinks through the parameter mappings
    planner_agent = build_agent(
        output_type=AgentPlan,
        system_prompt=system_prompt,
        reasoning="medium" 
    )
    
    # Run the agent
    # We wrap in try/except to handle potential validation errors gracefully
    try:
        result = await planner_agent.run(user_query)
        generated_plan = result.output
        
        print(f"✅ Plan Generated with {len(generated_plan.steps)} steps.")
        
        # 5. Return update to State
        return {
            "plan": generated_plan,
            "status": "waiting_approval",
            "error": None, # Clear previous errors if any
            "user_feedback": None # Clear feedback as it's now addressed
        }

    except Exception as e:
        print(f"❌ Planning Failed: {e}")
        return {
            "error": f"Planning failed: {str(e)}",
            "status": "failed"
        }