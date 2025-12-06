from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import uuid
import json

class AgentLogger:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log(self, event_type: str, payload: Dict[str, Any]):
        entry = {
            "id": str(uuid.uuid4()),
            "ts": time.time(),
            "type": event_type,
            "payload": payload,
        }
        self.events.append(entry)
        # Keep prints for immediate visibility during development
        print(json.dumps(entry, indent=2, default=str))

    def dump(self) -> List[Dict[str, Any]]:
        return self.events

@dataclass
class Tracer:
    logger: AgentLogger = field(default_factory=AgentLogger)
    thoughts: List[str] = field(default_factory=list)

    def think(self, thought: str):
        self.thoughts.append(thought)
        self.logger.log("thought", {"thought": thought})

    def get_chain(self) -> str:
        return "\n".join(self.thoughts)