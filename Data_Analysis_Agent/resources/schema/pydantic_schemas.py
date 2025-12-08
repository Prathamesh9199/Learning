from typing import Any, Dict, List
from pydantic import BaseModel, Field

class NaturalAnswerOutput(BaseModel) :
    final_answer: str = Field( ... , description="The final answer to the user's question")

class ParameterDetail(BaseModel):
    description: str = Field( ... , description="Description of the parameter")
    input: str = Field("", description="User-provided input for the parameter")

class StoredProcedure(BaseModel):
    name: str = Field( ... , description="Name of the Stored Procedure")
    description: str = Field( ... , description="Description of the Stored Procedure")
    parameters: Dict[str, ParameterDetail] = Field(
        default_factory=dict,
        description="Dictionary of parameters where key is parameter name"
    )
    returns: Dict[str, List[str]] = Field(
        ... , description="Schema of the result set, e.g., {'schema': ['col1', 'col2']}"
    )

class PlanStep(BaseModel):
    step_id: int = Field(..., description="The sequence number of the step (1, 2, 3...)")
    description: str = Field(..., description="High-level description of what this step does")
    tool_name: str = Field(..., description="The exact name of the Stored Procedure to call")
    tool_arguments: Dict[str, Any] = Field(..., description="Key-value pairs of arguments to pass to the tool")
    rationale: str = Field(..., description="Why we are taking this step")

class AgentPlan(BaseModel):
    steps: List[PlanStep] = Field(..., description="The ordered list of steps to execute")
    final_objective: str = Field(..., description="Summary of what the final outcome will be")

class UserFeedback(BaseModel):
    feedback_text: str = Field(..., description="Natural language feedback from the user")
    is_approved: bool = Field(..., description="True if user approves the plan, False otherwise")