from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver # <--- 1. Import this
from agent.state import AgentState

# --- Import Phase 1 Nodes (Right Brain) ---
from agent.nodes.kg_planner import kg_planning_node
from agent.nodes.kg_executor import kg_execution_node
from agent.nodes.context_refiner import context_refining_node
from agent.nodes.human_review import human_review_node # <--- Import this
# --- Import Phase 2 Nodes (Left Brain) ---
from agent.nodes.sql_planner import sql_planning_node 
from agent.nodes.sql_executor import sql_execution_node
from agent.nodes.responder import responder_node 

# --- 1. Define Conditional Logic ---

def route_kg_execution(state: AgentState):
    """
    Decides: 
    - Are we still executing steps? -> Go back to 'kg_executor'
    - Are we done? -> Go to 'context_refiner'
    """
    if state['status'] == 'ready_to_summarize':
        return "context_refiner"
    return "kg_executor"

def route_sql_execution(state: AgentState):
    """
    Decides:
    - Are we still executing SQL? -> Go back to 'sql_executor'
    - Are we done? -> Go to 'responder'
    """
    if state['status'] == 'done':
        return "responder"
    # If failed or still executing steps
    return "sql_executor"

def route_human_review(state: AgentState):
    """
    After the human review interrupt, we check the user's input.
    - If user provided feedback (string), we go back to Planner.
    - If user approved (or no feedback), we go to Executor.
    """
    feedback = state.get("user_feedback")
    
    # If there is feedback text and it's not just "yes"/"ok"
    if feedback and len(feedback) > 3 and "yes" not in feedback.lower():
        print(f"   ↪ User requested changes: {feedback}")
        return "sql_planner"
    
    print("   ↪ Plan Approved. Proceeding to Execution.")
    return "sql_executor"

# --- 2. Build the Graph ---

workflow = StateGraph(AgentState)

# -- Add Nodes --
# Phase 1: Business Understanding
workflow.add_node("kg_planner", kg_planning_node)
workflow.add_node("kg_executor", kg_execution_node)
workflow.add_node("context_refiner", context_refining_node)

# Phase 2: Data Analysis
workflow.add_node("sql_planner", sql_planning_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("sql_executor", sql_execution_node)
workflow.add_node("responder", responder_node)

# -- Add Edges --

# START -> KG Planner (Default entry point)
workflow.add_edge(START, "kg_planner")

# KG Planner -> KG Executor
workflow.add_edge("kg_planner", "kg_executor")

# KG Executor -> Loop or Refine
workflow.add_conditional_edges(
    "kg_executor",
    route_kg_execution,
    {
        "kg_executor": "kg_executor",       # Loop back for next step
        "context_refiner": "context_refiner" # Done, move to synthesis
    }
)

# Context Refiner -> SQL Planner
workflow.add_edge("context_refiner", "sql_planner")

workflow.add_edge("sql_planner", "human_review")

# Human Review -> Conditional (Executor OR Back to Planner)
workflow.add_conditional_edges(
    "human_review",
    route_human_review,
    {
        "sql_executor": "sql_executor",
        "sql_planner": "sql_planner"
    }
)

# SQL Executor -> Loop or Responder
workflow.add_conditional_edges(
    "sql_executor",
    route_sql_execution,
    {
        "sql_executor": "sql_executor", 
        "responder": "responder"
    }
)

workflow.add_edge("responder", END)

# --- 3. Compile with Checkpointer ---

# Initialize in-memory persistence
memory = MemorySaver()

# Compile the graph with the checkpointer
app = workflow.compile(
    checkpointer=memory, 
    interrupt_after=["human_review"]
)