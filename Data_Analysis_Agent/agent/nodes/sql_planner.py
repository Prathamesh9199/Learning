# agent/nodes/sql_planner.py
import json
from langchain_core.messages import HumanMessage
from agent.state import AgentState
from resources.schema.pydantic_schemas import AgentPlan
from resources.registry.sql_sp import SP_REGISTRY
from client.llm_manager import build_agent

def format_registry_for_prompt() -> str:
    """Converts SP_REGISTRY into a text description for the LLM."""
    docs = []
    for sp_name, sp_meta in SP_REGISTRY.items():
        # Handle dict items safely
        params_desc = []
        for k, v in sp_meta.parameters.items():
            # v is a ParameterDetail object
            params_desc.append(f"{k} ({v.description})")
        params_str = ", ".join(params_desc) if params_desc else "None"
            
        doc = (
            f"- Tool: {sp_name}\n"
            f"  Desc: {sp_meta.description}\n"
            f"  Params: {params_str}\n"
            f"  Returns: {sp_meta.returns}"
        )
        docs.append(doc)
    return "\n\n".join(docs)

async def sql_planning_node(state: AgentState) -> dict:
    """
    Refines the user query into a structured SQL execution plan, 
    grounded in the Business Context found by the Knowledge Graph.
    """
    print("\n🔵 Node: SQL Planner")
    
    # 1. Get User Query (Find last Human Message)
    user_query = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), 
        None
    )
    
    # 2. Retrieve Business Context
    business_context = state.get("business_context", "No specific business context provided.")

    # 3. Construct Prompt
    tool_definitions = format_registry_for_prompt()

    # 4. Generate the schema from the Pydantic model
    schema = AgentPlan.model_json_schema()

    # 5. Convert it to a string
    schema_str = json.dumps(schema, indent=2)
    
    system_prompt = (
        "You are a Senior Data Analyst Agent. "
        "Your goal is to answer the user's question by creating a Step-by-Step execution plan.\n\n"
        
        "### 1. BUSINESS CONTEXT (CRITICAL)\n"
        "The following context was derived from a Knowledge Graph analysis:\n"
        f"\"{business_context}\"\n"
        "- **Use this context to map user terms to tool parameters.**\n"
        "- Example: If Context says 'Profit maps to GrossIncome', use the tool that returns GrossIncome.\n\n"
        
        "### 2. AVAILABLE TOOLS (Stored Procedures)\n"
        f"{tool_definitions}\n\n"

        "### 3. CONSTRAINTS\n"
        "- ONLY use the Stored Procedures listed above.\n"
        "- Be precise with parameter values. Infer dates/defaults where logical.\n"

        "### 4. OUTPUT FORMAT\n"
        "You must output a SINGLE valid JSON object matching the following schema:\n"
        f"{schema_str}"
    )

    # 4. Invoke LLM
    planner_agent = build_agent(
        output_type=AgentPlan,
        system_prompt=system_prompt,
        reasoning="high"
    )
    
    try:
        result = await planner_agent.run(user_query)
        generated_plan = result.output
        
        print(f"✅ SQL Plan Generated with {len(generated_plan.steps)} steps.")
        
        return {
            "sql_plan": generated_plan, 
            "current_step_index": 0,
            "status": "executing",
            "phase": "data_analysis",
            "error": None
        }

    except Exception as e:
        print(f"❌ SQL Planning Failed: {e}")
        return {"error": str(e), "status": "failed"}