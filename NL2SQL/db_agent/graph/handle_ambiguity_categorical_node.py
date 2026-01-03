from typing import Dict, Any, List
from db_agent.graph.state import AgentState
from db_agent.client.az_sql import SQLQueryExecutor

def handle_ambiguity_categorical_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 4: Socratic Helper
    Validates categorical parameters.
    FIX: Skips logic if we are in 'TEST_HYPOTHESIS' mode.
    """
    print("--- [Node] Ambiguity Checker (Categorical) ---")

    # --- FIX: PASS THROUGH DIAGNOSTIC ACTIONS ---
    if state.get("next_action") == "TEST_HYPOTHESIS":
        return {} # Do nothing, preserve the 'TEST_HYPOTHESIS' state
    # --------------------------------------------
    
    tool_params = state.get("tool_params", {})
    if not tool_params:
        return {"next_action": "EXECUTE"} 

    validation_map = {
        "ProjectName": {"Table": "SEMANTIC.COST_PER_PERSON", "Col": "PROJECT_NAME"},
        "CustomerName": {"Table": "SEMANTIC.COST_PER_PERSON", "Col": "CUSTOMER_NAME"},
        "Location":    {"Table": "SEMANTIC.COST_PER_PERSON", "Col": "LOCATION"}
    }

    issues = []
    
    for param, value in tool_params.items():
        if param in validation_map and value:
            table = validation_map[param]["Table"]
            col = validation_map[param]["Col"]
            
            query = f"""
            SELECT DISTINCT {col} 
            FROM {table} 
            WHERE {col} LIKE '%{value}%'
            """
            
            try:
                with SQLQueryExecutor() as executor:
                    df = executor.execute_query(query)
                    matches = df.iloc[:, 0].tolist() if not df.empty else []
                    
                    if len(matches) == 0:
                        issues.append(f"Could not find any '{param}' matching '{value}'.")
                        
                    elif len(matches) > 1:
                        if value not in matches:
                            options = ", ".join(matches[:5])
                            issues.append(f"'{value}' is ambiguous. Did you mean: {options}?")
                        else:
                            tool_params[param] = value 

                    elif len(matches) == 1:
                        if value != matches[0]:
                            print(f"   > Auto-correcting '{value}' -> '{matches[0]}'")
                            tool_params[param] = matches[0]

            except Exception as e:
                print(f"   > Validation Error for {param}: {e}")

    if issues:
        print(f"   > Ambiguity Detected: {issues}")
        return {
            "next_action": "CLARIFY",
            "clarification_options": issues,
            "tool_params": tool_params
        }
    
    print("   > Parameters Validated.")
    return {
        "next_action": "EXECUTE", 
        "tool_params": tool_params 
    }