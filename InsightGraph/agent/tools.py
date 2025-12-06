import re
from agent.tracer import Tracer
from typing import Dict, Any
from time import sleep

class ToolResult:
    def __init__(self, success: bool, output: str, metadata: Dict[str, Any] = None):
        self.success = success
        self.output = output
        self.metadata = metadata or {}

class DummyMathTool:
    name = "dummy_math"
    def run(self, input_text: str, tracer: Tracer) -> ToolResult:
        sleep(1)
        tracer.think(f"DummyMathTool received: {input_text}")
        try:
            if not re.match(r"^[0-9+\-*/().\s]+$", input_text.strip()):
                sleep(1)
                tracer.think("Math tool: non-math tokens detected; refusing to evaluate")
                return ToolResult(False, "Unsafe or unparsable math expression")
            result = eval(input_text, {"__builtins__": None}, {})
            sleep(1)
            tracer.think(f"Math tool result: {result}")
            return ToolResult(True, str(result), {"raw": result})
        except Exception as e:
            sleep(1)
            tracer.think(f"Math tool error: {e}")
            return ToolResult(False, f"Error: {e}")

class DummySearchTool:
    name = "dummy_search"
    def run(self, input_text: str, tracer: Tracer) -> ToolResult:
        sleep(1)
        tracer.think(f"DummySearchTool called with query: {input_text}")
        fake = f"[DUMMY SEARCH]\nTop result for: {input_text}\nSummary: This is mocked. Replace with real search."
        tracer.think("Dummy search: returning mocked summary")
        return ToolResult(True, fake, {"source": "dummy"})