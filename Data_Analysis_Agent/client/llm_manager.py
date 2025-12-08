from __future__ import annotations
import time
import asyncio
from typing import Literal, Type
from openai import AsyncOpenAI, OpenAI 
from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from resources.schema.pydantic_schemas import NaturalAnswerOutput
from config import OPENAI_API_KEY, OPENAI_MODEL_NAME

# Base settings for all agents
BASE_MODEL_SETTINGS = ModelSettings(
    instrument=True,
    seed=42,    
)

_missing = [
    name for name, val in [
        ("OPENAI_API_KEY", OPENAI_API_KEY),
        ("OPENAI_MODEL_NAME", OPENAI_MODEL_NAME),
    ] 
    if not val
]

if _missing:
    raise EnvironmentError(
        "Missing required environment variables: " + ", ".join(_missing)
    )

openai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
)

model = OpenAIResponsesModel(
    OPENAI_MODEL_NAME, 
    provider=OpenAIProvider(openai_client=openai_client),
)

def build_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)

def build_agent(
    output_type: Type[BaseModel],
    system_prompt: str,
    *,
    reasoning: Literal["low", "medium", "high"] = "low",
) -> Agent:

    # Merge base settings with per-agent reasoning knobs
    per_agent_settings = ModelSettings(**BASE_MODEL_SETTINGS)

    if "o1" in OPENAI_MODEL_NAME or "o3" in OPENAI_MODEL_NAME:
        per_agent_settings["openai_reasoning_effort"] = reasoning

    return Agent(
        model=model,
        output_type=output_type,
        instructions=system_prompt,
        instrument=True,
        model_settings=per_agent_settings,
    )

## --- ONLY FOR TEST --- ##
async def main():
    agent = build_agent(
        output_type=NaturalAnswerOutput,
        system_prompt="You are a helpful assistant. Respond concisely.",
        reasoning="high",
    )

    # Per-call overrides remain possible
    result = await agent.run(
        "Hello! Can you confirm this setup works with standard OpenAI?"
    )
    print("Agent Response:", result)

if __name__ == "__main__":
    start_time = time.time() # Fixed typo (was time.time)
    asyncio.run(main())
    end_time = time.time()
    print(f"Execution took {end_time - start_time :.2f} seconds.")