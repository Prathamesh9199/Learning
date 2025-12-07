from agent.nodes import app

# Initial State
inputs = {
    "question": "What is impacting my CPP?",
    "current_focus_node": "CPP", # Entity extraction usually happens before this
    "graph_context": [],
    "iterations": 0
}

# Execution
print("--- Starting Graph Traversal ---")
for output in app.stream(inputs):
    for key, value in output.items():
        print(f"Node '{key}' finished.")
        if key == "navigator":
            if "final_answer" in value:
                print(f" >> DECISION: Answer Found")
            else:
                print(f" >> DECISION: Exploring {value.get('current_focus_node')}")
        elif key == "explorer":
            print(f" >> FACTS FOUND: {len(value['graph_context'])} total facts")

print("\n--- Final Result ---")
# Access the final state from the last yield, or run app.invoke(inputs)
final_result = app.invoke(inputs)
print(final_result["final_answer"])