import uvicorn

if __name__ == "__main__":
    uvicorn.run("db_agent.app:app", host="0.0.0.0", port=7158, reload=False)