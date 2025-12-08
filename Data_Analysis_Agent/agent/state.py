import operator
from typing import Annotated, List, Optional, Dict, Any, Union, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from resources.schema.pydantic_schemas import AgentPlan

class AgentState(TypedDict):
    # Chat History (Append-only)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # The current plan (Overwritten on updates)
    plan: Optional[AgentPlan]
    
    # Execution Tracking
    current_step_index: int      # Which step are we executing?
    results: Dict[str, Any]      # Store output of tools: {"step_1": [...data...]}
    
    # Error Handling
    error: Optional[str]         # Most recent error message
    retry_count: int             # How many times have we retried the current step?
    
    # Interaction State
    user_feedback: Optional[str] # Feedback provided by human during interrupt
    status: Literal['planning', 'waiting_approval', 'executing', 'failed', 'done']