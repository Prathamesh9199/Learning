from agent.state import AgentState

def human_review_node(state: AgentState) -> dict:
    """
    Acts as a breakpoint. It displays the generated SQL Plan 
    and pauses the graph so the user can Approve or Reject.
    """
    print("\n🟡 Node: Human Review")
    
    # We only care about the SQL plan here
    plan = state.get("sql_plan")
    
    if not plan:
        print("   ⚠️ No SQL Plan found to review.")
        return {"status": "failed", "error": "Missing SQL Plan"}

    print(f"\n📋 Proposed SQL Plan: {plan.final_objective}")
    for step in plan.steps:
        print(f"   Step {step.step_id}: {step.tool}")
        print(f"      Description: {step.description}")
        print(f"      Args: {step.args}")
    
    print("\n⏸️  WAITING FOR USER APPROVAL...")
    print("    (Type 'yes' to proceed, or explain what to fix)")

    # We do NOT return a status of 'executing' here. 
    # We return 'waiting_approval' which is just a marker.
    # The actual PAUSE happens because we will configure 'interrupt_after' in graph.py
    return {
        "status": "waiting_approval"
    }