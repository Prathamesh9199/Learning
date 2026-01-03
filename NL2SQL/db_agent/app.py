from concurrent.futures import thread
import anyio.to_thread
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
from db_agent.client.az_llm import build_agent
from db_agent.client.az_sql import SQLQueryExecutor
from db_agent.config import CHAT_MODEL_DEPLOYMENT
from db_agent.schema.pydantic_models import NaturalAnswerOutput, GreetIn
from db_agent.resources.prompts import SYSTEM_PROMPT

import logging

# --------- Logger Setup ---------
logger = logging.getLogger("app_logger")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = 100
    logger.info("starting up", extra={"request_id": "-"})    
    app.state.db_agent = build_agent(
        output_type_schema=NaturalAnswerOutput,
        system_prompt=SYSTEM_PROMPT,
        model_name=CHAT_MODEL_DEPLOYMENT["speed"],
    )
    yield
    logger.info("shutting down", extra={"request_id": "-"})

app = FastAPI(lifespan=lifespan)

# --------- Routes ---------
@app.get("/", response_class=PlainTextResponse)
def root():
    response = """
    /health_check      : Health check endpoint
    /sql_check         : Check connectivity to Azure SQL Database
    /llm_check         : Check connectivity to Azure OpenAI LLM
    """
    return response.strip("\n")

@app.get("/health_check")
def health_check():
    return {"status": "ok"}

@app.post("/greet", response_class=PlainTextResponse)
def greet(payload: GreetIn):
    name = payload.name.strip()
    return f"Hi {name}!"

@app.get("/llm_check", response_class=PlainTextResponse)
async def llm_check(request: Request):
    """
    Health check for LLM. Uses a lightweight agent (fast reasoning).
    """
    agent = request.app.state.db_agent
    result = await agent.run("Hello! Can you confirm this setup works?")
    return f"LLM Check: {result.output}!"

@app.get("/sql_check", response_class=PlainTextResponse)
def sql_check():
    with SQLQueryExecutor() as sql_manager:
        response = sql_manager.check_connection()
    return f"SQL Check: {response}"