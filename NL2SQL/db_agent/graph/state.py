from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Tracks the entire lifecycle of the investigation (Sherlock V2.1 Spec).
    """
    
    # --- 1. CORE CONTEXT ---
    messages: List[Any]          # Chat history (LangChain Message objects) [cite: 67]
    user_info: Dict[str, Any]    # User ID, Role, Permissions [cite: 70]
    intent_status: str           # "VALID", "INVALID", "DIAGNOSTIC", "DESCRIPTIVE" [cite: 72]
    next_action: str             # "GET_STATS", "QUERY_KG", "EXECUTE", "FINALIZE" [cite: 73]
    plan_cache_hit: bool         # Optimization: Did we skip planning? [cite: 71]

    # --- 2. EXECUTION STATE (The "Hands") ---
    tool_params: Dict[str, Any]      # Active Stored Procedure parameters [cite: 76]
    sql_result: Optional[List[Dict]] # Raw data returned from DB [cite: 77]
    error_type: Optional[str]        # "TIMEOUT", "SYNTAX", etc. [cite: 81]
    
    # Negotiation State (Handling large data)
    user_negotiated: bool            # Has the user already approved a large download? [cite: 82]
    user_negotiated_decision: str    # "GROUP_BY" or "TRUNCATE" [cite: 83]

    # --- 3. REASONING STATE (The "Brain") ---
    hypotheses_queue: List[str]  # List of "Suspects" from Knowledge Graph [cite: 85]
    confirmed_causes: List[str]  # Validated findings [cite: 86]
    current_hypothesis: str      # The factor currently being tested [cite: 87]

    # --- 4. SAFETY & UX ---
    loop_count: int              # Circuit Breaker: Current iterations [cite: 89]
    max_loops: int               # Circuit Breaker: Limit (Default: 5) [cite: 90]
    stream_buffer: List[str]     # Real-time UI updates ("Checking attrition...") [cite: 93]

    # NEW: Add this line for the Socratic Helper
    clarification_options: Optional[List[str]]  # Stores disambiguation choices 