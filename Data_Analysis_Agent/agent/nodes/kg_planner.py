import json
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from resources.schema.pydantic_schemas import AgentPlan
from client.llm_manager import build_agent # Assuming this is your factory function
from client.kg_manager import KGManager # For injecting tool definitions into prompt

# --- 2. The Node Function ---
async def kg_planning_node(state: AgentState):
    """
    LangGraph Node: Generates a plan to explore the Knowledge Graph.
    """
    print("--- Phase 1: KG Planning ---")

    # --- 1. The System Prompt ---
    KG_PLANNER_PROMPT = """
    You are a Senior Business Analyst for a Retail Supermarket chain.
    Your goal is to plan an investigation into the Business Knowledge Graph to understand the context of a user's question.

    You do NOT write SQL. You do NOT answer the question directly.
    You ONLY plan which 'Graph Tools' to use to understand the terms and relationships involved.

    ### Available Graph Tools:
    1. search_concept(query): Fuzzy search to find the correct Node ID (e.g., User says "Money" -> You find "TotalAmount").
    2. get_neighbors(node_id): See what a node is connected to (e.g., "What influences 'GrossIncome'?").
    3. find_path(start, end): Find the relationship chain between two concepts (e.g., "How does 'Customer' impact 'Profit'?").

    ### Planning Strategy:
    1. Identify key terms in the user's query.
    2. Step 1 should ALWAYS be `search_concept` for these terms to verify they exist in the graph.
    3. Step 2+ should be `get_neighbors` or `find_path` to understand how these terms relate.

    ### Example:
    User: "Why is profit low in Mandalay?"
    Plan:
    1. search_concept("Profit") - To find the real node name (likely 'GrossIncome').
    2. search_concept("Mandalay") - To confirm it exists (likely a 'City').
    3. get_neighbors("GrossIncome") - To see how profit is calculated (Input/Output).
    4. find_path("City", "GrossIncome") - To see how location affects profit.

    ### ANSWER FORMAT\n
    Output valid JSON that matches the following JSON Schema:
    {schema_str}
    """

    # 1. Generate the schema from the Pydantic model
    schema = AgentPlan.model_json_schema()

    # 2. Convert it to a string
    schema_str = json.dumps(schema, indent=2)

    KG_PLANNER_PROMPT = KG_PLANNER_PROMPT.format(schema_str=schema_str)

    # 1. Prepare the Agent
    # We use 'medium' reasoning to ensure it thinks through the graph strategy
    agent = build_agent(
        output_type=AgentPlan,
        system_prompt=KG_PLANNER_PROMPT,
        reasoning="medium" 
    )

    # 2. Construct the Prompt
    # We include the chat history to understand context
    messages = [
        SystemMessage(content=KG_PLANNER_PROMPT),
    ] + state['messages']

    # 3. Invoke LLM
    # Note: pydantic_ai agents usually take a string or list of messages. 
    # Adapting to your llm_manager structure:
    response = await agent.run(state['messages'][-1].content) # Passing the latest user query
    
    # 4. Update State
    return {
        "kg_plan": response.output,  # The Pydantic object
        "status": "waiting_approval", # Stop for human review (optional) or "executing"
        "phase": "business_analysis", # Re-affirm current phase
        "current_step_index": 0,
        "results": {},     # Clear old results
        "error": None
    }