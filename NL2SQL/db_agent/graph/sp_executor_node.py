from typing import Dict, Any
from db_agent.graph.state import AgentState
from db_agent.client.az_sql import SQLQueryExecutor

def sp_executor_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 6: Execution
    Runs the Stored Procedure defined by the Planner.
    """
    print("--- [Node] SP Executor ---")
    current_buffer = state.get("stream_buffer", [])
    
    # 1. Retrieve Tool Info
    params = state.get("tool_params", {})
    tool_name = params.get("tool_name") # Extract directly from params (placed there by Planner)

    # RECOVERY: If we are testing a hypothesis but have no params, we default to Distribution
    current_hypothesis = state.get("current_hypothesis")
    next_action = state.get("next_action")
    
    if next_action == "TEST_HYPOTHESIS" and current_hypothesis:
        # Default Strategy: Check the distribution of the suspect factor
        tool_name = "sp_GetDistribution"
        params = {"ColumnName": current_hypothesis, "TopN": 5}
        print(f"   > Strategy: Auto-generating test for '{current_hypothesis}'")
    
    elif not tool_name:
         # Fallback default
         tool_name = "sp_GetAggregatedCost" 

    print(f"   > Executing: {tool_name} with {params}")

    # 2. Build SQL String (EXEC sp_Name @Param='Val'...)
    param_str_parts = []
    # Make a copy to iterate so we don't modify the dict while iterating (if we popped tool_name)
    # Note: If 'tool_name' is in params, we should skip adding it as a SQL parameter
    for k, v in params.items():
        if k == "tool_name": continue 
        
        if v is None:
            param_str_parts.append(f"@{k}=NULL")
        elif isinstance(v, str):
            param_str_parts.append(f"@{k}='{v}'")
        else:
            param_str_parts.append(f"@{k}={v}")
    
    param_str = ", ".join(param_str_parts)
    sql_query = f"EXEC {tool_name} {param_str}"

    # Streaming Update: "Executing..."
    streaming_update = current_buffer + [f"Executor: Running {tool_name}..."]

    # 3. Execute
    try:
        with SQLQueryExecutor() as executor:
            df = executor.execute_query(sql_query)
            
            result_list = df.to_dict(orient="records") if not df.empty else []
            print(f"   > Success! Retrieved {len(result_list)} rows.")
            
            return {
                "sql_result": result_list,
                "error_message": None, 
                "next_action": "ANALYZE",
                "stream_buffer": streaming_update + [f"Executor: Success. Got {len(result_list)} rows."]
            }

    except Exception as e:
        error_msg = str(e)
        print(f"   > Execution Error: {error_msg}")
        return {
            "sql_result": [],
            "error_message": error_msg,
            "next_action": "ERROR",
            "stream_buffer": streaming_update + [f"Executor: Error - {error_msg}"]
        }