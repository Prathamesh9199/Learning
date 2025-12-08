from agent.state import AgentState
from client.llm_manager import build_agent
from resources.schema.pydantic_schemas import NaturalAnswerOutput
from langchain_core.messages import AIMessage

async def responder_node(state: AgentState) -> dict:
    """
    Synthesizes the tool outputs into a final natural language answer.
    """
    print("\n🟢 Node: Responder")
    
    results = state.get("results", {})
    context = state.get("business_context", "No context available.")
    query = state["messages"][0].content
    
    # Format results nicely for the prompt
    results_text = ""
    if results:
        results_text = "### 🔍 SQL EXECUTION DATA:\n"
        for step_name, data in results.items():
            results_text += f"- **Source ({step_name})**: {data}\n"
    else:
        results_text = "No SQL data was returned."
        
    system_prompt = (
        "You are a Senior Data Analyst. Answer the user's question using the provided context and data.\n\n"
        
        "### GUIDELINES\n"
        "1. **PRIORITIZE DATA:** If `SQL EXECUTION DATA` is provided below, YOU MUST USE IT to answer the question. Do not say 'data is not defined' if numbers are present.\n"
        "2. **USE CONTEXT FOR MEANING:** Use the `BUSINESS CONTEXT` to explain *why* the numbers matter (e.g., mapping '14:00' to 'Peak Hour').\n"
        "3. **BE DIRECT:** Start with the answer (e.g., 'We are busiest at 2 PM...').\n\n"
        
        "### INPUTS\n"
        f"USER QUERY: {query}\n\n"
        f"BUSINESS CONTEXT (Definitions): {context}\n\n"
        f"{results_text}"
    )
    
    user_prompt = (
        f"Original Question: {state['messages'][0].content}\n"
        f"Business Context Used: {context}\n"
        f"Data Gathered: {results_text}"
    )
    
    responder = build_agent(
        output_type=NaturalAnswerOutput,
        system_prompt=system_prompt,
        reasoning="low"
    )
    
    response = await responder.run(user_prompt)
    final_text = response.output.final_answer
    
    print(f"\n💡 Final Insight: {final_text}")
    
    return {
        "messages": [AIMessage(content=final_text)], 
        "status": "done"
    }