import re
from typing import Any, Dict
from agent.state import AgentState
from agent.tools.tools_factory import get_all_tools

# Load tools once into a lookup dictionary
TOOLS_MAP = {func.__name__: func for func in get_all_tools()}

def resolve_dependencies(args: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scans arguments for placeholders like '$step_1' or '$previous' 
    and replaces them with actual data from previous steps.
    """
    resolved_args = args.copy()
    
    for key, value in resolved_args.items():
        if isinstance(value, str):
            # Check for "$step_X" pattern
            match = re.search(r"\$step_(\d+)", value)
            if match:
                step_id = match.group(1)
                # Look up result. Note: step_id in plan is 1-based, results key is typically string "step_1"
                prev_result = results.get(f"step_{step_id}")
                
                if prev_result:
                    # If the result is a complex object (List[Dict]), we might need to extract a specific ID.
                    # For MVP, if the previous result is a single value, use it.
                    # If it's a list of dicts, we might take the first item's ID or pass the whole object 
                    # (depending on what the SP expects).
                    
                    # Heuristic: If SP expects a string ID but got a list of dicts, try to find 'ID' key
                    if isinstance(prev_result, list) and len(prev_result) > 0 and isinstance(prev_result[0], dict):
                        # Try to find a value that matches the parameter name (e.g. key="Invoice_ID")
                        if key in prev_result[0]:
                            resolved_args[key] = prev_result[0][key]
                        else:
                            # Fallback: Pass the string representation
                            resolved_args[key] = str(prev_result)
                    else:
                        resolved_args[key] = prev_result
                        
    return resolved_args

def executor_node(state: AgentState) -> dict:
    """
    Executes the tool for the current step in the plan.
    """
    print("\n⚙️  Node: Executor")
    
    plan = state["plan"]
    current_index = state["current_step_index"]
    results = state.get("results", {})
    
    # 1. Check if we are done
    if current_index >= len(plan.steps):
        return {"status": "done"}
    
    current_step = plan.steps[current_index]
    step_key = f"step_{current_step.step_id}"
    
    print(f"   ▶ Executing Step {current_step.step_id}: {current_step.description}")
    
    # 2. Resolve Tool and Arguments
    tool_name = current_step.tool_name
    tool_func = TOOLS_MAP.get(tool_name)
    
    if not tool_func:
        error_msg = f"Tool '{tool_name}' not found in registry."
        return {"error": error_msg, "status": "failed"}

    # 3. Handle Dependencies (Variable Linking)
    raw_args = current_step.tool_arguments
    final_args = resolve_dependencies(raw_args, results)
    
    # 4. Execute Tool
    try:
        # We pass arguments as kwargs
        output = tool_func(**final_args)
        
        # 5. Check for "Soft Errors" (Tool returned an error string)
        if isinstance(output, str) and ("Error" in output or "failed" in output.lower()):
            raise Exception(output) # Raise to trigger Error Handler
            
        print(f"      ✅ Success. Rows returned: {len(output) if isinstance(output, list) else 1} | \n {output}")
        
        # 6. Update State (Success Path)
        return {
            "results": {**results, step_key: output},
            "current_step_index": current_index + 1,
            "retry_count": 0, # Reset retry count on success
            "error": None,
            "status": "executing"
        }

    except Exception as e:
        print(f"      ❌ Execution Failed: {e}")
        return {
            "error": str(e),
            "status": "failed" # This will route to Error Handler
        }