from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes.planner import planner_node
from agent.nodes.human_review import human_review_node
from agent.nodes.executor import executor_node
from agent.nodes.error_handler import error_handler_node
from agent.nodes.responder import responder_node

# --- CONDITIONAL ROUTERS ---

def route_after_review(state: AgentState):
    """Decides next step after Human Review"""
    # If user provided feedback during the interrupt, we assume rejection/refinement
    if state.get("user_feedback"):
        return "planner"
    return "executor"

def route_executor(state: AgentState):
    """Decides next step after an Execution attempt"""
    status = state.get("status")
    
    if status == "failed":
        return "error_handler"
    elif status == "done":
        return "responder"
    else:
        # Loop back to executor for the next step
        return "executor"

def route_error(state: AgentState):
    """Decides next step after Error Handler"""
    status = state.get("status")
    
    if status == "waiting_help":
        # We route to a special 'human_help' interrupt state
        # For simplicity in graph, we can route back to executor but 
        # rely on the 'interrupt_before' in compilation to catch this.
        return "human_help_interrupt" 
    elif status == "done":
        # Fatal failure
        return "responder"
    else:
        # Auto-retry (status="executing")
        return "executor"

# --- GRAPH BUILDER ---

workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("executor", executor_node)
workflow.add_node("error_handler", error_handler_node)
workflow.add_node("responder", responder_node)

# 2. Add Standard Edges
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "human_review")

# 3. Add Conditional Edges
workflow.add_conditional_edges(
    "human_review",
    route_after_review,
    {
        "planner": "planner",
        "executor": "executor"
    }
)

workflow.add_conditional_edges(
    "executor",
    route_executor,
    {
        "error_handler": "error_handler",
        "responder": "responder",
        "executor": "executor"
    }
)

workflow.add_conditional_edges(
    "error_handler",
    route_error,
    {
        "human_help_interrupt": "executor", # Logic: We pause before this, user updates args, we resume
        "responder": "responder",
        "executor": "executor"
    }
)

workflow.add_edge("responder", END)

# 4. Compile with Checkpointer and Interrupts
# We pause AFTER human review to allow user to approve or reject.
# We pause BEFORE executor if the error handler requested "waiting_help".
checkpointer = MemorySaver()

app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_after=["human_review"],
    # We can handle the Error "Human Help" interrupt dynamically in main.py 
    # or strictly via configuration. For MVP, keeping it simple:
    interrupt_before=[] 
)