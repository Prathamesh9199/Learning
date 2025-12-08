import asyncio
import uuid
from agent.graph import app
from langchain_core.messages import HumanMessage

async def main():
    # Unique thread ID for state persistence
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("🤖 SQL Data Analysis Agent Initialized.")
    print("---------------------------------------")
    
    # 1. Get Initial Question
    user_input = input("User: ")
    
    # Initial Trigger
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "current_step_index": 0,
        "retry_count": 0,
        "results": {},
        "error": None,
        "user_feedback": None,
        "plan": None
    }

    # Start the Graph
    # We use .stream() to see nodes executing in real-time
    async for event in app.astream(initial_state, config=config, stream_mode="values"):
        # We can print events if we want debugging, but the nodes print to console already
        pass

    # --- THE INTERACTIVE LOOP ---
    while True:
        # Check the current state of the graph
        snapshot = app.get_state(config)
        
        # If the graph has finished, break
        if not snapshot.next:
            print("\n✅ Process Completed.")
            break

        # If we are here, the graph is PAUSED (likely at 'human_review')
        current_node = snapshot.metadata.get('step', '')
        # Note: LangGraph metadata formats vary, usually we check snapshot.next
        
        # Determine why we paused
        last_node = list(snapshot.metadata.get("writes", {}).keys())
        if not last_node:
            # First run, or paused at review
            pass
            
        print(f"\n⏸️  Agent Paused. Waiting for input...")
        user_command = input(">> (Type 'yes' to approve, or provide feedback): ").strip()
        
        if user_command.lower() in ["yes", "y", "approve", "ok"]:
            print("👍 Plan Approved. Resuming execution...")
            # Resume with NO user_feedback (clearing it ensures route_after_review goes to executor)
            await app.aupdate_state(config, {"user_feedback": None})
            
            # Continue execution
            async for event in app.astream(None, config=config, stream_mode="values"):
                pass
                
        elif user_command.lower() in ["exit", "quit"]:
            print("👋 Exiting.")
            break
            
        else:
            # User provided feedback (Rejection or Help)
            print("🔄 Feedback received. Replanning/Adjusting...")
            
            # Determine if this was "Help" for an error or "Feedback" for a plan
            # (Logic simplified: we just inject user_feedback string)
            await app.aupdate_state(config, {"user_feedback": user_command})
            
            # Resume execution (Graph will route back to Planner or Executor based on logic)
            async for event in app.astream(None, config=config, stream_mode="values"):
                pass

if __name__ == "__main__":
    asyncio.run(main())