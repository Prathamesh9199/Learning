from __future__ import annotations

import asyncio
import time
import os
from typing import Optional, Type, Literal
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings
from db_agent.config import OPENAI_API_KEY, CHAT_MODEL_DEPLOYMENT
from db_agent.schema.pydantic_models import NaturalAnswerOutput, ReasoningEffort

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def build_agent(
    output_type_schema: Type[BaseModel],
    system_prompt: str,
    *,
    model_name: str = CHAT_MODEL_DEPLOYMENT['speed'],
    reasoning: Optional[ReasoningEffort] = None,
) -> Agent:
    """
    General-purpose Agent builder for standard OpenAI.
    """
    
    # 2. INITIALIZE THE MODEL
    model = OpenAIChatModel(model_name)

    # 3. CONFIGURE SETTINGS
    settings = ModelSettings(
        max_tokens=None,
        temperature=0.7,
    )
    
    if reasoning:
        settings['openai_reasoning_effort'] = reasoning

    # 4. BUILD THE AGENT
    return Agent(
        model=model,
        output_type=output_type_schema, 
        system_prompt=system_prompt,
        retries=2,
        model_settings=settings
    )

# -------------------------------------------------------------------------
# LOCAL TESTING
# -------------------------------------------------------------------------
async def main():
    test_models = list(CHAT_MODEL_DEPLOYMENT.values())
    
    for model_name in test_models:
        print(f"\n--- Testing agent (model={model_name}) ---")
        start = time.time()

        try:
            agent = build_agent(
                output_type_schema=NaturalAnswerOutput,
                system_prompt="You are a helpful assistant. Respond concisely.",
                model_name=model_name,
            )

            result = await agent.run("Hello! Can you confirm this setup works?")
            
            print("Agent Response:", result.output)
            print(f"Execution took {time.time() - start:.2f} seconds.")
            
        except Exception as e:
            print(f"Error testing model {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())