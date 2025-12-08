from agent.state import AgentState

def error_handler_node(state: AgentState) -> dict:
    """
    Decides whether to Retry, Ask User, or Give Up.
    Logic:
    - Retries 0, 1: Auto-retry (Route back to Executor)
    - Retry 2: Interrupt (Ask User)
    - Retries 3, 4: Auto-retry (after user help)
    - Retry 5: Fatal Failure
    """
    print("\n⚠️ Node: Error Handler")
    
    retry_count = state.get("retry_count", 0)
    current_error = state.get("error", "Unknown Error")
    
    print(f"   Current Retry Count: {retry_count} | Error: {current_error}")
    
    # Increment count for the next attempt
    new_retry_count = retry_count + 1
    
    # --- LEVEL 1: AUTO RETRY (Attempts 1 & 2) ---
    if new_retry_count <= 2:
        print("   ↪ Auto-Retrying...")
        return {
            "retry_count": new_retry_count,
            "status": "executing" # Route back to Executor
        }
    
    # --- LEVEL 2: ASK USER (Attempt 3) ---
    elif new_retry_count == 3:
        print("   🛑 Pausing for Human Help...")
        # We set status to trigger the interrupt edge
        return {
            "retry_count": new_retry_count,
            "status": "waiting_help" 
        }
        
    # --- LEVEL 3: RETRY WITH USER HELP (Attempts 4 & 5) ---
    elif new_retry_count <= 5:
        print("   ↪ Retrying with User Input...")
        # Note: The state['tool_arguments'] might need updates here based on user feedback.
        # For this MVP, we assume the user's feedback was applied to state['plan'] 
        # or state['tool_arguments'] via a 'Refiner' node or manually.
        # But simply routing back to Executor allows it to try again.
        return {
            "retry_count": new_retry_count,
            "status": "executing"
        }
        
    # --- LEVEL 4: FATAL FAILURE ---
    else:
        print("   ❌ Max retries exceeded. Terminating.")
        return {
            "status": "done", # Or "fatal"
            "final_answer": f"I failed to execute the plan after multiple attempts. Last error: {current_error}"
        }