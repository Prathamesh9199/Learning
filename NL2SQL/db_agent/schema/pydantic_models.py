from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

ReasoningEffort = Literal["low", "medium", "high"]

class GreetIn(BaseModel):
    name: str
    
class NaturalAnswerOutput(BaseModel):
    answer: str

class IntentClassification(BaseModel):
    """
    Structured output for the Intent Identifier Node.
    """
    category: Literal["DESCRIPTIVE", "DIAGNOSTIC", "INVALID", "AMBIGUOUS"] = Field(
        ..., description="The type of query. Descriptive=Get Stats/Data. Diagnostic=Why/Reasoning. Invalid=Off-topic."
    )
    reasoning: str = Field(
        ..., description="Brief explanation of why this category was chosen."
    )
    suggested_action: str = Field(
        ..., description="Internal note on what the agent should do next (e.g., 'Check graph' or 'Run Query')."
    )

class PlannerOutput(BaseModel):
    """
    The decision made by the Agent Planner.
    """
    next_action: Literal[
        "EXECUTE",          # Run a Stored Procedure (Descriptive)
        "QUERY_KG",         # Ask the Graph for Hypotheses (Diagnostic Start)
        "TEST_HYPOTHESIS",  # Test a specific factor from the queue (Diagnostic Loop)
        "FINALIZE"          # Stop and report
    ] = Field(..., description="The next step in the investigation.")
    
    tool_name: Optional[str] = Field(
        None, description="If EXECUTE, the name of the SP (e.g., 'sp_GetAggregatedCost')."
    )
    
    tool_params: Optional[Dict[str, Any]] = Field(
        None, description="Parameters for the SP (e.g., {'ProjectName': 'AI Agent'})."
    )
    
    reasoning: str = Field(..., description="Why this action was chosen.")

class ResponseOutput(BaseModel):
    final_response: str = Field(
        ..., 
        description="The final, natural language answer to the user's question, strictly based on findings."
    )