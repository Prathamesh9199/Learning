from langchain_core.messages import AIMessage, HumanMessage
from agent.state import AgentState
from client.llm_manager import build_agent 
from pydantic import BaseModel, Field

# --- 1. Output Schema ---
class BusinessContextOutput(BaseModel):
    """Structured output for the business context summary."""
    summary: str = Field(..., description="A concise paragraph explaining the business concepts found.")
    useful_tables: list[str] = Field(..., description="List of relevant concepts/tables identified (e.g., 'Sale', 'GrossIncome').")

# --- 2. System Prompt ---
CONTEXT_REFINER_PROMPT = """
You are a 'Translator' between a Business Domain Model and a SQL Engineer.
Your input is a set of raw 'Graph Exploration Results' regarding a user's question.

Your Goal: Summarize these findings into a concise 'Business Context' that a SQL Agent can use to write accurate queries.

### Guidelines:
1. **Identify Terminology:** Map user terms to Graph Nodes (e.g., "User said 'Profit', Graph shows 'GrossIncome'").
2. **Explain Logic:** Describe relationships (e.g., "GrossIncome is calculated per Sale, not pre-aggregated").
3. **Be Specific:** If the graph shows a relationship like `Sale -> LOCATED_IN -> Branch`, mention it explicitly.
4. **Ignore Noise:** If a search failed or returned irrelevant nodes, omit them.

### Input Data Format:
User Query: {query}
Graph Exploration Results: {results}
"""

# --- 3. The Node Function ---
async def context_refining_node(state: AgentState):
    """
    LangGraph Node: Synthesizes KG results into a context string
    AND notifies the user of what was found.
    """
    print("--- Phase 1: Refining Context ---")
    
    # 1. Gather Raw Data
    raw_results = ""
    for step_key, data in state['results'].items():
        raw_results += f"\n[Step {step_key}]: Tool '{data['tool']}'\nOutput: {data['output']}\n"

    # Robustly find the last User Query (Scanning backwards just to be safe)
    user_query = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), 
        state['messages'][-1].content
    )

    # 2. Build the Agent
    agent = build_agent(
        output_type=BusinessContextOutput,
        system_prompt=CONTEXT_REFINER_PROMPT,
        reasoning="low"
    )

    # 3. Construct Prompt
    formatted_prompt = f"User Query: {user_query}\n\nGraph Results:\n{raw_results}"
    
    # 4. Invoke LLM
    response = await agent.run(formatted_prompt)
    context_data = response.output 

    print(f"--- Context Generated: {context_data.summary[:100]}... ---")

    # --- NEW: Create User Notification ---
    # We create a stylized message to show the user we 'understood' them.
    # We use blockquotes (>) to highlight the insight.
    notification_msg = (
        f"🧠 **Context Analysis**\n"
        f"I've mapped your query to our Knowledge Graph:\n"
        f"> *{context_data.summary}*\n\n"
        f"Generating SQL Execution Plan..."
    )
    
    # Wrap in LangChain Message
    message_update = AIMessage(content=notification_msg)

    # 5. Update State & Transition Phase
    return {
        "business_context": context_data.summary,
        
        # Append the new message to history so the UI renders it
        "messages": [message_update], 
        
        "phase": "data_analysis",
        "status": "planning",  # Handover to SQL Planner
        "results": {}          # Clear KG results
    }