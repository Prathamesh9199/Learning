import asyncio
import uuid
from langchain_core.messages import HumanMessage
from agent.graph import app  # Importing the compiled StateGraph

async def main():
    print("\n🤖 Dual-Brain Agent Initialized.")
    print("================================")
    
    # 1. Get User Question
    user_input = input("User Query: ")
    
    # 2. Initialize State
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "phase": "business_analysis", 
        "status": "planning",
        "retry_count": 0,
        "results": {},
        "kg_plan": None,
        "sql_plan": None,
        "business_context": None
    }

    # --- FIX START: Define the Thread Configuration ---
    # The Checkpointer needs a thread_id to know where to save this specific run.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    # --- FIX END ---

    print(f"\n--- 🚀 Starting Workflow (Thread: {thread_id}) ---\n")

    # 3. Stream Execution
    # PASS `config` HERE ⬇️
    async for event in app.astream(initial_state, config=config):
        for node_name, state_update in event.items():
            
            # --- PHASE 1 VISUALIZATION ---
            if node_name == "kg_planner":
                # Check if kg_plan exists in update before accessing steps
                if state_update.get('kg_plan'):
                    steps = len(state_update['kg_plan'].steps)
                    print(f"📘 [Right Brain] Plan: Explore {steps} concepts.")
            
            elif node_name == "kg_executor":
                pass 

            elif node_name == "context_refiner":
                print(f"📘 [Right Brain] Insight Generated.")
                if 'messages' in state_update and state_update['messages']:
                    # Print the stylized AIMessage we created
                    print(f"\n{state_update['messages'][-1].content}\n")

            # --- PHASE 2 VISUALIZATION ---
            elif node_name == "sql_planner":
                plan = state_update.get('sql_plan')
                if plan:
                    print(f"📙 [Left Brain] SQL Plan: {len(plan.steps)} steps.")
                    for step in plan.steps:
                        print(f"   - {step.tool}: {step.description}")

            elif node_name == "sql_executor":
                results = state_update.get('results')
                print(f"\n📊 [Left Brain] Final Results Available.")
                
                if results:
                    last_step = list(results.keys())[-1]
                    data = results[last_step]
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   Top Result: {data[0]}")
                        print(f"   (... and {len(data)-1} more rows)")
                    else:
                        print(f"   Result: {data}")

    print("\n✅ Process Completed.")

if __name__ == "__main__":
    asyncio.run(main())