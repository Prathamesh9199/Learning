from agent.state import AgentState
from client.kg_manager import KGManager

# Initialize the engine once (Singleton-ish behavior)
# This prevents reloading the JSON on every single step
kg_engine = KGManager()

def kg_execution_node(state: AgentState):
    """
    LangGraph Node: Executes one step of the KG Plan.
    """
    plan = state['kg_plan']
    idx = state['current_step_index']
    
    # 1. Safety Check: Are we out of steps?
    if not plan or idx >= len(plan.steps):
        print("--- Phase 1: Execution Complete ---")
        return {"status": "ready_to_summarize"}

    # 2. Get Current Step Details
    step = plan.steps[idx]
    tool = step.tool
    args = step.args  # Assuming this is a dict like {'query': 'Profit'}
    
    print(f"--- Phase 1 Exec: Step {idx+1}/{len(plan.steps)} -> {tool}({args}) ---")

    # 3. Execute Tool
    output = None
    try:
        if tool == "search_concept":
            # Handle potential arg naming variations by LLM
            q = args.get('query') or args.get('term')
            output = kg_engine.search_concept(q)
            
        elif tool == "get_neighbors":
            n = args.get('node_id') or args.get('concept')
            output = kg_engine.get_neighbors(n)
            
        elif tool == "find_path":
            s = args.get('start') or args.get('source')
            e = args.get('end') or args.get('target')
            output = kg_engine.find_path(s, e)
            
        else:
            output = f"Error: Unknown tool '{tool}'"
            
    except Exception as e:
        output = f"Tool Execution Failed: {str(e)}"

    # 4. Store Result
    # We store it keyed by the step index so the Summarizer can read it logically
    # e.g., results['step_0'] = "Found node 'GrossIncome'"
    new_results = state['results'].copy()
    new_results[f"step_{idx}"] = {
        "thought": step.thought,
        "tool": tool,
        "output": output
    }

    # 5. Advance State
    # If this was the last step, we change status to trigger the next node
    next_status = "executing"
    if idx + 1 >= len(plan.steps):
        next_status = "ready_to_summarize"

    return {
        "results": new_results,
        "current_step_index": idx + 1,
        "status": next_status
    }