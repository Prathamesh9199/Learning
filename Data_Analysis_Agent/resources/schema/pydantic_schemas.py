from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- PHASE 1: Business Context Schema ---
class BusinessContextOutput(BaseModel):
    """Structured output for the business context summary."""
    summary: str = Field(..., description="A concise paragraph explaining the business concepts found.")
    useful_tables: List[str] = Field(..., description="List of relevant concepts/tables identified (e.g., 'Sale', 'GrossIncome').")

class NaturalAnswerOutput(BaseModel) :
    final_answer: str = Field( ... , description="The final answer to the user's question")
    
# --- PHASE 2: SQL & Registry Schemas ---
class ParameterDetail(BaseModel):
    description: str = Field(..., description="Description of the parameter")
    input: str = Field("", description="User-provided input for the parameter (if any)")

class StoredProcedure(BaseModel):
    name: str = Field(..., description="Name of the Stored Procedure")
    description: str = Field(..., description="Description of the Stored Procedure")
    parameters: Dict[str, ParameterDetail] = Field(
        default_factory=dict,
        description="Dictionary of parameters where key is parameter name"
    )
    # Flexible return type to handle both schema descriptions or raw text
    returns: Any = Field(..., description="Schema or description of the result set")

# --- SHARED: Planning Schemas (Used by both KG and SQL Planners) ---
class PlanStep(BaseModel):
    step_id: int = Field(..., description="The sequence number of the step (1, 2, 3...)")
    
    # We use 'tool' and 'args' to match the logic in our Executor nodes
    tool: str = Field(..., description="The exact name of the tool to call (e.g., 'search_concept', 'sp_GetGrossIncome')")
    args: Dict[str, Any] = Field(..., description="Key-value pairs of arguments to pass to the tool")
    
    description: str = Field(..., description="High-level description of what this step does")
    thought: Optional[str] = Field(None, description="The reasoning behind choosing this step")

class AgentPlan(BaseModel):
    steps: List[PlanStep] = Field(..., description="The ordered list of steps to execute")
    final_objective: str = Field(..., description="Summary of what the final outcome will be")

# --- INTERACTION: Feedback & Output ---
class UserFeedback(BaseModel):
    feedback_text: str = Field(..., description="Natural language feedback from the user")
    is_approved: bool = Field(..., description="True if user approves the plan, False otherwise")

class NaturalAnswerOutput(BaseModel):
    final_answer: str = Field(..., description="The final answer to the user's question")