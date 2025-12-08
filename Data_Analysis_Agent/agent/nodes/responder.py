from agent.state import AgentState
from client.llm_manager import build_agent
from resources.schema.pydantic_schemas import NaturalAnswerOutput

async def responder_node(state: AgentState) -> dict:
    """
    Synthesizes the tool outputs into a final natural language answer.
    """
    print("\n🟢 Node: Responder")
    
    plan = state["plan"]
    results = state["results"]
    
    # Contextualize results for the LLM
    context_text = ""
    for step_key, result_data in results.items():
        context_text += f"\n--- Output of {step_key} ---\n{result_data}\n"
        
    system_prompt = (
        "You are a Data Analyst. "
        "Review the original question, the executed plan, and the data results below. "
        "Provide a clear, concise, and professional insight answering the user's question. "
        "Do not mention internal tool names or step IDs. Just provide the insight."
    )
    
    user_prompt = (
        f"Original Question: {state['messages'][0].content}\n"
        f"Objective: {plan.final_objective}\n"
        f"Data Gathered: {context_text}"
    )
    
    responder = build_agent(
        output_type=NaturalAnswerOutput,
        system_prompt=system_prompt,
        reasoning="low"
    )
    
    response = await responder.run(user_prompt)
    
    print(f"\n💡 Final Insight: {response.output.final_answer}")
    
    return {
        "messages": [response.output.final_answer], # Append to chat history
        "status": "done"
    }