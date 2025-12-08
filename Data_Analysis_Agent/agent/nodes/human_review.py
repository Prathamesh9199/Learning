from agent.state import AgentState

def human_review_node(state: AgentState) -> dict:
    """
    This node doesn't 'do' much work itself. 
    It acts as a boundary marker where we trigger the 'interrupt_before'.
    When the graph resumes, it will pass through here (or we can update state directly).
    """
    print("\n🟡 Node: Human Review")
    
    plan = state.get("plan")
    if not plan:
        return {"error": "No plan found to review."}

    # In a real app, this print statement is replaced by sending data to the UI.
    print(f"\n📋 Proposed Plan: {plan.final_objective}")
    for step in plan.steps:
        print(f"   {step.step_id}. {step.description}")
        print(f"      -> Tool: {step.tool_name}")
        print(f"      -> Args: {step.tool_arguments}")
    
    print("\n⏸️  Waiting for User Approval...")
    
    # We don't change state here. The Graph will pause *after* this node runs 
    # (if configured with interrupt_after) or *before* the executor.
    return {}