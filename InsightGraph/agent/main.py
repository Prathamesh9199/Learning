from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agent.tracer import Tracer, AgentLogger
from agent.llm import DummyLLM
from agent.tools import DummyMathTool, DummySearchTool, ToolResult
from time import sleep

class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    graph_output: str

class OverallState(TypedDict):
    user_input: str
    intent: str
    answer: str
    hitl_required: bool
    debug_trace: str

# Create singletons for tracer/logger so every node can use them
logger = AgentLogger()
tracer = Tracer(logger=logger)
llm = DummyLLM(logger=logger)
math_tool = DummyMathTool()
search_tool = DummySearchTool()

# Node implementations
def intent_node(state: InputState) -> OverallState:
    user_input = state["user_input"]
    tracer.think(f"intent_node: received input '{user_input}'")
    intent = llm.decide_intent(user_input, tracer)
    sleep(1)
    return {
        "user_input": user_input,
        "intent": intent,
        "answer": "",
        "hitl_required": False,
        "debug_trace": tracer.get_chain(),
    }

def math_node(state: OverallState) -> OverallState:
    ui = state["user_input"]
    tracer.think("math_node: routing to DummyMathTool")
    logger.log("tool_call", {"tool": math_tool.name, "input": ui})
    res: ToolResult = math_tool.run(ui, tracer)
    logger.log("tool_result", {"tool": math_tool.name, "success": res.success, "output": res.output})
    sleep(1)
    return {
        **state,
        "answer": res.output if res.success else "Could not compute.",
        "debug_trace": tracer.get_chain(),
    }

def search_node(state: OverallState) -> OverallState:
    ui = state["user_input"]
    tracer.think("search_node: routing to DummySearchTool")
    logger.log("tool_call", {"tool": search_tool.name, "input": ui})

    # Run search tool
    res: ToolResult = search_tool.run(ui, tracer)
    logger.log("tool_result", {"tool": search_tool.name, "success": res.success})

    # Synthesize the result using dummy LLM
    synth = llm.answer_theory(res.output, tracer)

    sleep(1)   
    # Update state and return
    return {
        **state,
        "answer": synth,
        "debug_trace": tracer.get_chain(),
    }


def hitl_node(state: OverallState) -> OverallState:
    ui = state["user_input"]
    tracer.think("hitl_node: ambiguous intent; requiring human decision")
    logger.log("hitl_request", {"reason": "ambiguous_intent", "input": ui})
    # In production: push to UI and wait. For dummy: mark hitl_required True and include prompt.
    prompt = (
        "Ambiguous input. Please choose: 'math' to evaluate, 'theory' to search, or rewrite the question."
    )
    sleep(1)
    return {
        **state,
        "answer": prompt,
        "hitl_required": True,
        "debug_trace": tracer.get_chain(),
    }

def sink_node(state: OverallState) -> OutputState:
    # Final node: format output
    out = f"Answer:\n{state['answer']}\n\n-- Debug trace --\n{state['debug_trace']}"
    sleep(1)
    return {"graph_output": out}

# Build graph
builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
builder.add_node("intent", intent_node)
builder.add_node("math", math_node)
builder.add_node("search", search_node)
builder.add_node("hitl", hitl_node)
builder.add_node("sink", sink_node)


# START conditional routing based on LLM intent
def route_start(state: InputState):
    # We'll route using the DummyLLM decision here to choose the entry node
    intent = llm.decide_intent(state["user_input"], tracer)
    if intent == "math":
        return "math"
    elif intent == "theory":
        return "search"
    else:
        return "hitl"

builder.add_conditional_edges(START, route_start)
# Wire sequence to sink
builder.add_edge("math", "sink")
builder.add_edge("search", "sink")
builder.add_edge("hitl", "sink")

graph = builder.compile()

# Simple CLI
if __name__ == "__main__":
    print("LangGraph dummy agent. Type 'exit' to quit.")
    # examples = [
    #     "2 + 2",
    #     "What is gradient descent?",
    #     "Compute 12 * (3 + 4)",
    #     "Explain attention mechanism",
    #     "Is 17 prime?",
    # ]
    
    # for ex in examples:
    #     print('\n' + '=' * 40)
    #     print(f"Input: {ex}")
    #     out = graph.invoke({"user_input": ex})
    #     print(out["graph_output"])

    while True:
        u = input('\n> ').strip()
        if u.lower() in ("exit", "quit"):
            break
        out = graph.invoke({"user_input": u})
        print(out["graph_output"])    