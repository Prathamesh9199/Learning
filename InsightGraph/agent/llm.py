import re
from agent.tracer import Tracer, AgentLogger
from time import sleep

class DummyLLM:
    def __init__(self, logger: AgentLogger):
        self.logger = logger

    def decide_intent(self, user_input: str, tracer: Tracer) -> str:
        sleep(1)
        tracer.think("LLM: deciding intent based on input tokens")
        math_pattern = r"^[0-9\s+\-*/().]+$"
        has_math_words = bool(re.search(r"\b(sum|add|subtract|multiply|divide|calculate|compute)\b", user_input, re.I))
        looks_like_expression = bool(re.search(r"\d+\s*[-+*/]\s*\d+", user_input))
        if re.match(math_pattern, user_input.strip()):
            decision = "math"
        elif looks_like_expression or has_math_words:
            decision = "math"
        elif len(user_input.split()) >= 3 and has_math_words is False:            
            decision = "theory"
        else:
            decision = "ambiguous"
        self.logger.log("llm_decision", {"input": user_input, "decision": decision})
        sleep(1)
        tracer.think(f"LLM decided intent: {decision}")
        return decision

    def answer_theory(self, search_text: str, tracer: Tracer) -> str:
        sleep(1)
        tracer.think("LLM: synthesizing theory answer from search results (dummy)")
        return f"[DUMMY LLM SYNTHESIS]\nSynthesis for: {search_text}"