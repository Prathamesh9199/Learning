from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agent.state import AgentState, query_knowledge_graph
import os

os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"  # Set your OpenAI API key

llm = ChatOpenAI(model="gpt-4", temperature=0)

from langchain_core.pydantic_v1 import BaseModel, Field

# Structured Output for reliability
class EntityExtraction(BaseModel):
    matched_nodes: List[str] = Field(description="List of exact node IDs found in the user query.")
    reasoning: str = Field(description="Why these nodes were selected.")

def extractor_node(state: AgentState):
    """
    Maps user query terms to actual Graph Node IDs.
    """
    question = state["question"]
    
    # We provide the valid nodes as 'context' to the LLM
    # For very large graphs, you would use a Vector Store (RAG) here instead of a raw list.
    valid_nodes_str = ", ".join(VALID_NODES)
    
    prompt = f"""
    You are an Entity Resolver for a Business Knowledge Graph.
    
    USER QUERY: "{question}"
    
    AVAILABLE GRAPH NODES:
    [{valid_nodes_str}]
    
    TASK:
    Identify which concept in the user's query maps to a Valid Graph Node.
    - If the user says "cost per product", map to "CPP".
    - If the user says "staffing", map to "Labor_Cost" or "Staff_Turnover" based on context.
    - If the user says "factory output", map to "Production_Volume".
    
    Return the exact Node ID.
    """
    
    # We use 'with_structured_output' to ensure we get a clean list (requires compatible model)
    # If using standard GPT-4/3.5, you can use a standard invoke and parse JSON.
    structured_llm = llm.with_structured_output(EntityExtraction)
    result = structured_llm.invoke(prompt)
    
    # Logic: If we found a node, set it as the focus. 
    # If multiple, we might need a loop, but let's pick the first one for now.
    if result.matched_nodes:
        first_node = result.matched_nodes[0]
        return {
            "current_focus_node": first_node, 
            "graph_context": [f"System Note: User is asking about '{first_node}'."]
        }
    else:
        return {"final_answer": "I couldn't map your question to any specific business concept in the graph."}

# --- Node 1: The Navigator (Planner) ---
def navigator_node(state: AgentState):
    """
    Decides whether to explore more nodes or answer the question.
    """
    question = state["question"]
    context = "\n".join(state.get("graph_context", []))
    focus = state.get("current_focus_node", "None")
    
    # Prompt engineering is crucial here. 
    # We force the LLM to output a specific "Next Step".
    prompt = f"""
    You are a Business Knowledge Graph Explorer.
    
    GOAL: Answer the user's question using ONLY the provided Graph Context.
    
    QUESTION: {question}
    
    CURRENT FOCUS NODE: {focus}
    
    KNOWN GRAPH FACTS:
    {context}
    
    INSTRUCTIONS:
    1. If you have enough facts to answer the question, type "ANSWER: <your answer>".
    2. If you need to explore a node mentioned in the facts or the question, type "EXPLORE: <Node_Name>".
    3. If the current focus node provided new leads, follow them if relevant.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    
    if content.startswith("ANSWER:"):
        return {"final_answer": content.replace("ANSWER:", "").strip()}
    elif content.startswith("EXPLORE:"):
        next_node = content.replace("EXPLORE:", "").strip()
        return {"current_focus_node": next_node}
    else:
        # Fallback/Error handling
        return {"final_answer": "I could not determine the next step."}

# --- Node 2: The Explorer (Tool Executor) ---
def explorer_node(state: AgentState):
    """
    Executes the deterministic graph query.
    """
    target = state["current_focus_node"]
    existing_context = state.get("graph_context", [])
    
    # Call the Python Tool
    new_facts_str = query_knowledge_graph(target)
    
    # Parse the string back into a list for storage
    new_facts = new_facts_str.split("\n")
    
    # Deduplicate and Append
    updated_context = list(set(existing_context + new_facts))
    
    return {
        "graph_context": updated_context,
        "iterations": state.get("iterations", 0) + 1
    }

def route_step(state: AgentState):
    """
    Conditional logic to determine the next node.
    """
    if state.get("final_answer"):
        return "end"
    if state["iterations"] > 5: # Safety brake
        return "end"
    return "explore"

# Initialize Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("navigator", navigator_node)
workflow.add_node("explorer", explorer_node)

# Set Entry Point
workflow.set_entry_point("navigator")

# Add Edges
# From Explorer, we always go back to Navigator to make sense of the new data
workflow.add_edge("explorer", "navigator")

# From Navigator, we conditionally route
workflow.add_conditional_edges(
    "navigator",
    route_step,
    {
        "explore": "explorer",
        "end": END
    }
)

# Compile
app = workflow.compile()