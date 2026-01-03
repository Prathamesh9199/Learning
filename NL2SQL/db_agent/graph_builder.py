import asyncio
from langgraph.graph import StateGraph, START, END
from db_agent.graph.state import AgentState

# ... (Keep imports exactly as they are) ...
# Phase 1: Security
from db_agent.graph.context_loader_node import context_loader_node
from db_agent.graph.intent_identifier_node import intent_identifier_node
# Phase 2: Optimization & Reasoning
from db_agent.graph.cache_lookup_node import cache_lookup_node
from db_agent.graph.agent_planner_node import agent_planner_node
# Phase 3: Socratic Helpers
from db_agent.graph.handle_ambiguity_continuous_node import handle_ambiguity_continuous_node
from db_agent.graph.handle_ambiguity_categorical_node import handle_ambiguity_categorical_node
from db_agent.graph.human_clarification_node import human_clarification_node
# Phase 4: Execution & Recovery
from db_agent.graph.sp_executor_node import sp_executor_node
from db_agent.graph.error_recovery_node import error_recovery_node
# Phase 5: Diagnostic
from db_agent.graph.causal_discovery_node import causal_discovery_node
from db_agent.graph.investigation_approval_node import investigation_approval_node 
from db_agent.graph.result_analyzer_node import result_analyzer_node
# Phase 6: Presentation
from db_agent.graph.data_negotiator_node import data_negotiator_node
from db_agent.graph.human_negotiation_node import human_negotiation_node
from db_agent.graph.hard_truncate_node import hard_truncate_node
from db_agent.graph.response_synthesizer_node import response_synthesizer_node
# Phase 7: Finalization
from db_agent.graph.refusal_responder_node import refusal_responder_node
from db_agent.graph.feedback_logger_node import feedback_logger_node
# Phase 8: Utilities
from db_agent.graph.sql_checkpointer import SQLServerSaver

# =============================================================================
# 2. ROUTING LOGIC
# =============================================================================

def route_intent(state: AgentState):
    if state.get("intent_status") == "INVALID": return "refusal_responder_node"
    return "cache_lookup_node"

def route_cache(state: AgentState):
    if state.get("plan_cache_hit"): return END 
    return "agent_planner_node"

def route_planner(state: AgentState):
    action = state.get("next_action")
    
    # --- FIX: ROUTE QUERY_KG DIRECTLY TO CAUSAL DISCOVERY (Not Approval) ---
    if action == "QUERY_KG": return "causal_discovery_node"
    # -----------------------------------------------------------------------
    
    if action == "TEST_HYPOTHESIS": return "handle_ambiguity_continuous_node"
    if action == "EXECUTE": return "handle_ambiguity_continuous_node"
    if action == "FINALIZE": return "response_synthesizer_node"
    
    return END

def route_approval(state: AgentState):
    # If approval needed, stop. If approved, go BACK to Planner to start testing.
    if state.get("next_action") == "WAIT_FOR_APPROVAL":
        return END 
    return "agent_planner_node" # <--- Changed from causal_discovery to planner

def route_ambiguity(state: AgentState):
    action = state.get("next_action")
    if action == "CLARIFY": return "human_clarification_node"
    return "sp_executor_node"

def route_execution_result(state: AgentState):
    if state.get("error_message"): return "error_recovery_node"
    return "data_negotiator_node"

def route_negotiation(state: AgentState):
    action = state.get("next_action")
    if action == "NEGOTIATE": return "human_negotiation_node"
    return "result_analyzer_node"

# =============================================================================
# 3. GRAPH CONSTRUCTION
# =============================================================================

def build_graph():
    workflow = StateGraph(AgentState)

    # --- Add Nodes (Same as before) ---
    workflow.add_node("context_loader_node", context_loader_node)
    workflow.add_node("intent_identifier_node", intent_identifier_node)
    workflow.add_node("cache_lookup_node", cache_lookup_node)
    workflow.add_node("refusal_responder_node", refusal_responder_node)
    workflow.add_node("agent_planner_node", agent_planner_node)
    workflow.add_node("investigation_approval_node", investigation_approval_node)
    workflow.add_node("causal_discovery_node", causal_discovery_node)
    workflow.add_node("result_analyzer_node", result_analyzer_node)
    workflow.add_node("handle_ambiguity_continuous_node", handle_ambiguity_continuous_node)
    workflow.add_node("handle_ambiguity_categorical_node", handle_ambiguity_categorical_node)
    workflow.add_node("human_clarification_node", human_clarification_node)
    workflow.add_node("sp_executor_node", sp_executor_node)
    workflow.add_node("error_recovery_node", error_recovery_node)
    workflow.add_node("data_negotiator_node", data_negotiator_node)
    workflow.add_node("human_negotiation_node", human_negotiation_node)
    workflow.add_node("hard_truncate_node", hard_truncate_node)
    workflow.add_node("response_synthesizer_node", response_synthesizer_node)
    workflow.add_node("feedback_logger_node", feedback_logger_node)

    # --- Add Edges (UPDATED FLOW) ---
    
    # 1. Security & Intent
    workflow.add_edge(START, "context_loader_node")
    workflow.add_edge("context_loader_node", "intent_identifier_node")
    workflow.add_conditional_edges("intent_identifier_node", route_intent, 
        {"cache_lookup_node": "cache_lookup_node", "refusal_responder_node": "refusal_responder_node"})
    workflow.add_edge("refusal_responder_node", END)

    # 2. Planning
    workflow.add_conditional_edges("cache_lookup_node", route_cache, 
        {"agent_planner_node": "agent_planner_node", END: END})

    # 3. Planner Routing
    workflow.add_conditional_edges("agent_planner_node", route_planner, 
        {
            "causal_discovery_node": "causal_discovery_node", # <--- Direct link
            "handle_ambiguity_continuous_node": "handle_ambiguity_continuous_node",
            "response_synthesizer_node": "response_synthesizer_node",
            END: END
        }
    )

    # 4. Diagnostic Loop (Causal -> Approval -> Planner)
    # FIX: Causal fills queue first, THEN Approval checks it.
    workflow.add_edge("causal_discovery_node", "investigation_approval_node")
    
    workflow.add_conditional_edges("investigation_approval_node", route_approval,
        {END: END, "agent_planner_node": "agent_planner_node"})

    # 5. Execution Pipeline
    workflow.add_edge("handle_ambiguity_continuous_node", "handle_ambiguity_categorical_node")
    workflow.add_conditional_edges("handle_ambiguity_categorical_node", route_ambiguity, 
        {"human_clarification_node": "human_clarification_node", "sp_executor_node": "sp_executor_node"})
    workflow.add_edge("human_clarification_node", END)

    # 6. Error Recovery
    workflow.add_conditional_edges("sp_executor_node", route_execution_result,
        {"error_recovery_node": "error_recovery_node", "data_negotiator_node": "data_negotiator_node"})
    workflow.add_edge("error_recovery_node", "handle_ambiguity_continuous_node")

    # 7. Presentation & Analysis
    workflow.add_conditional_edges("data_negotiator_node", route_negotiation, 
        {"human_negotiation_node": "human_negotiation_node", "result_analyzer_node": "result_analyzer_node"})
    workflow.add_edge("human_negotiation_node", END)
    workflow.add_edge("hard_truncate_node", "result_analyzer_node")
    
    # 8. Loop Back (Analysis -> Planner)
    workflow.add_edge("result_analyzer_node", "agent_planner_node")

    # 9. Finalization
    workflow.add_edge("response_synthesizer_node", "feedback_logger_node")
    workflow.add_edge("feedback_logger_node", END)

    return workflow

# =============================================================================
# 4. MAIN INTERACTIVE LOOP
# =============================================================================
async def main():
    print("--- Sherlock Agent V2.1 (COMPLETE + SQL PERSISTENCE) ---")
    
    # 1. Initialize SQL Saver (Persistence)
    checkpointer = SQLServerSaver()

    # 2. Compile Graph WITH Saver
    workflow = build_graph()
    app = workflow.compile(checkpointer=checkpointer)

    # 3. Define Session (Thread ID)
    # In a real app, this changes per user session
    thread_id = "session_user_1"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"   > Session ID: {thread_id} (State will be saved to SQL)")    

    chat_history = []
    
    while True:
        try: user_input = input("\nYou: ")
        except EOFError: break
        if user_input.lower() in ["quit", "exit"]: break

        chat_history.append(("user", user_input))
        print("   (Thinking...)")

        # 4. Pass 'config' for persistence
        inputs = {"messages": chat_history}

        # The app will now check SQL for 'session_user_1' state automatically!
        result = await app.ainvoke(inputs, config=config, recursion_limit=10000)
        
        if result.get("messages"):
            resp = result["messages"][-1].content
            # Special handling for Approval request which might be an AIMessage but not final
            if result.get("next_action") == "WAIT_FOR_APPROVAL":
                print(f"\nSherlock (Approval Needed): {resp}")
                # We do NOT append to chat_history yet; the graph state has it.
                # But for local CLI loop consistency:
                chat_history.append(("assistant", resp))
            else:
                print(f"\nSherlock: {resp}")
                chat_history.append(("assistant", resp))

if __name__ == "__main__":
    asyncio.run(main())