from typing import Dict, Any
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from db_agent.graph.state import AgentState

def handle_ambiguity_continuous_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 4: Socratic Helper (Continuous)
    Resolves subjective continuous values (Dates, Thresholds).
    FIX: Skips logic if we are in 'TEST_HYPOTHESIS' mode (since params are auto-generated later).
    """
    print("--- [Node] Ambiguity Checker (Continuous) ---")
    
    # --- FIX: PASS THROUGH DIAGNOSTIC ACTIONS ---
    if state.get("next_action") == "TEST_HYPOTHESIS":
        return {} # Do nothing, preserve the 'TEST_HYPOTHESIS' state
    # --------------------------------------------

    tool_params = state.get("tool_params", {})
    if not tool_params:
        return {"next_action": "EXECUTE"}

    updates = {}
    today = date.today()

    # --- 1. Date Resolution Logic ---
    for date_field in ["StartDate", "EndDate"]:
        val = tool_params.get(date_field)
        
        if isinstance(val, str):
            val_lower = val.lower().strip()
            
            # Scenario A: "Last Month"
            if "last month" in val_lower:
                first_day_prev = (today.replace(day=1) - relativedelta(months=1))
                last_day_prev = (today.replace(day=1) - relativedelta(days=1))
                print(f"   > Resolving '{val}' -> {first_day_prev} to {last_day_prev}")
                if date_field == "StartDate":
                    updates["StartDate"] = str(first_day_prev)
                    if not tool_params.get("EndDate"):
                        updates["EndDate"] = str(last_day_prev)
                elif date_field == "EndDate":
                    updates["EndDate"] = str(last_day_prev)

            # Scenario B: "This Year" / "YTD"
            elif "this year" in val_lower or "ytd" in val_lower:
                start_of_year = today.replace(month=1, day=1)
                print(f"   > Resolving '{val}' -> {start_of_year}")
                updates[date_field] = str(start_of_year)
            
            # Scenario C: "Last Year"
            elif "last year" in val_lower:
                start_prev_year = today.replace(year=today.year-1, month=1, day=1)
                end_prev_year = today.replace(year=today.year-1, month=12, day=31)
                print(f"   > Resolving '{val}' -> {start_prev_year} to {end_prev_year}")
                updates["StartDate"] = str(start_prev_year)
                updates["EndDate"] = str(end_prev_year)

    if updates:
        for k, v in updates.items():
            tool_params[k] = v
        return {
            "next_action": "EXECUTE", 
            "tool_params": tool_params
        }

    print("   > No continuous ambiguity found.")
    return {"next_action": "EXECUTE"}