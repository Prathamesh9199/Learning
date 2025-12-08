import operator
from typing import Annotated, List, Optional, Dict, Any, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from resources.schema.pydantic_schemas import AgentPlan

class AgentState(TypedDict):
    # --- Base Chat History ---
    messages: Annotated[List[BaseMessage], operator.add]
    
    # --- NEW: Phase Tracking ---
    # Determines if we are currently exploring concepts or executing SQL.
    # Default should be initialized to 'business_analysis'.
    phase: Literal['business_analysis', 'data_analysis']

    # --- Phase 1: Business Understanding (Right Brain) ---
    kg_plan: Optional[AgentPlan]       # Plan for Graph Explorer tools (e.g., "Define 'Profit'")
    business_context: Optional[str]    # The output of Phase 1. Examples: "Profit is calculated as..."

    # --- Phase 2: Data Analysis (Left Brain) ---
    sql_plan: Optional[AgentPlan]      # Plan for SQL Tools. (Renamed from generic 'plan')
    
    # --- Execution Tracking (Shared) ---
    current_step_index: int            # Tracks step number for the *active* plan
    results: Dict[str, Any]            # Output of tools: {"step_1": ["Node A", "Node B"] or SQL_Result}
    
    # --- Error Handling ---
    error: Optional[str]               # Most recent error message
    retry_count: int                   # Retries for the current step
    
    # --- Interaction State ---
    user_feedback: Optional[str]       # Human feedback
    status: Literal['planning', 'waiting_approval', 'executing', 'failed', 'done']