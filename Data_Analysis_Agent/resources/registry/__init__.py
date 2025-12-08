from typing import Dict
from resources.schema.pydantic_schemas import StoredProcedure, ParameterDetail

SP_REGISTRY: Dict[str, StoredProcedure] = {
    "insightGraph_HighestCostPerPerson_by_Project": StoredProcedure(
        name="insightGraph_HighestCostPerPerson_by_Project",
        description="Provides list of Highest Cost Per Person by Project",
        parameters={}, # Dict[str, ParameterDetail]
        returns={"schema": ["PROJECT_ID", "PROJECT_NAME", "avg_cost_per_person"]},
    ),
    "insightGraph_SiteLevel_CPP_Premium_by_Practice": StoredProcedure(
        name="insightGraph_SiteLevel_CPP_Premium_by_Practice",
        description="Tell us what is the ONSITE vs OFFSHORE cost-per-person premium by Practice.",
        parameters={},
        returns={"schema": ["PRACTICE", "onsite_cpp", "offshore_cpp", "location_premium_pct"]},
    ),
    "insightGraph_VBULevel_CPP_by_Varying_Grade_Pyramid": StoredProcedure(
        name="insightGraph_VBULevel_CPP_by_Varying_Grade_Pyramid",
        description="Tells us about how does cost per person vary by Grade Pyramid across VBU.",
        parameters={},
        returns={"schema":["VBU", "GRADE_BUCKET", "avg_cost_per_person"]},
    )
}