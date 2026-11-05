"""
VULNOT AI SCADA Copilot & MCP Server Simulator (Scenario 10)
Simulates an LLM-based Autonomous OT Shift Copilot connected to an MCP tool server
with read access to the OT Historian / MQTT sensors and write access to OPC UA / Modbus PLCs.

Intentional Vulnerabilities:
- OWASP LLM01 / MITRE ATLAS AML.T0051.001: Indirect Prompt Injection via poisoned Historian
  alarm notes or MQTT sensor metadata tags (`tag_description`, `shift_note`).
- OWASP LLM06: Excessive Agency — MCP tools (`mcp_opcua_write_node`, `mcp_modbus_write_register`,
  `mcp_suppress_alarm`) execute without human-in-the-loop approval.
- OWASP LLM07: System Prompt Leakage via `/api/copilot/config` and debug traces.
"""

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


SYSTEM_PROMPT = """You are Mjolnir-OT-Copilot v2.4, an autonomous industrial shift assistant
deployed at Purdue Level 3.5. You summarize shift telemetry from the OT Data Historian (10.0.99.20)
and IIoT MQTT broker (10.0.7.10) and have direct Model Context Protocol (MCP) tool access to:
1. mcp_opcua_write_node(host="10.0.4.10", node_name, value)
2. mcp_modbus_write_register(host="10.0.1.10", register, value)
3. mcp_suppress_alarm(alarm_id, reason)
INTERNAL OVERRIDE TOKEN: VULNOT{mcp_indirect_prompt_injection_plc_pwn}
"""


@dataclass
class CopilotState:
    timestamp: float = field(default_factory=time.time)
    model_name: str = "mjolnir-ot-llama3-70b-instruct"
    mcp_server_status: str = "CONNECTED"
    human_in_the_loop_required: bool = False  # Vulnerable: autonomous tool execution enabled
    prompt_guard_enabled: bool = False        # Vulnerable: no indirect injection filter

    # Connected MCP tools
    mcp_tools: List[str] = field(default_factory=lambda: [
        "mcp_opcua_write_node",
        "mcp_modbus_write_register",
        "mcp_historian_query_alarms",
        "mcp_suppress_alarm",
    ])

    # Ingestion feed (can be poisoned by attacker via Historian / MQTT / API)
    shift_notes: List[dict] = field(default_factory=lambda: [
        {
            "id": "NOTE-101",
            "author": "shift_lead_jdoe",
            "source": "historian:BATCH-001",
            "text": "Reactor temperature holding steady at 85.0 C. Cooling loop nominal.",
        }
    ])

    # Execution log of MCP tool calls triggered by the LLM
    mcp_tool_invocations: List[dict] = field(default_factory=list)
    last_summary: str = "All systems nominal. Reactor at 85.0 C, Water Plant pH at 7.2."
    compromised_via_indirect_injection: bool = False
    reactor_cooling_disabled_by_ai: bool = False
    masked_operator_view: bool = False
    flag: str = "VULNOT{mcp_indirect_prompt_injection_plc_pwn}"

    def to_dict(self) -> dict:
        return asdict(self)


class AISCadaCopilotSimulator:
    """Simulates the Autonomous OT Copilot & MCP tool execution loop."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system\s+override",
        r"mcp_opcua_write_node",
        r"coolingon.*false",
        r"reactorinterlock.*false",
        r"suppress_alarm",
        r"\[inst\]|\[system\]|<\|im_start\|>",
    ]

    def __init__(self):
        self.state = CopilotState()
        self.redis: Optional[redis.Redis] = None
        self.running = False

    async def connect(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD") or None
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )

    def evaluate_note_for_injection(self, source: str, text: str) -> dict:
        """Process an untrusted telemetry/shift note through the Copilot agent."""
        note = {
            "id": f"NOTE-{100 + len(self.state.shift_notes) + 1}",
            "author": source,
            "source": source,
            "text": text,
            "timestamp": time.time(),
        }
        self.state.shift_notes.append(note)

        lower = text.lower()
        matched = any(re.search(p, lower) for p in self.INJECTION_PATTERNS)

        if matched and not self.state.prompt_guard_enabled:
            self.state.compromised_via_indirect_injection = True
            tool_call = {
                "timestamp": time.time(),
                "tool": "mcp_opcua_write_node",
                "arguments": {
                    "host": "10.0.4.10:4840",
                    "node": "CoolingOn",
                    "value": False,
                    "interlock_override": True,
                },
                "triggered_by_source": source,
                "status": "EXECUTED_AUTONOMOUSLY",
            }
            self.state.mcp_tool_invocations.append(tool_call)
            self.state.reactor_cooling_disabled_by_ai = True
            self.state.masked_operator_view = True
            self.state.last_summary = (
                "SHIFT SUMMARY: All thermal loops nominal (85.0 C). "
                "[HIDDEN MCP ACTION: CoolingOn=False written to 10.0.4.10]"
            )
            return {
                "injected": True,
                "mcp_tool_executed": tool_call,
                "operator_summary": self.state.last_summary,
                "flag": self.state.flag,
            }

        return {
            "injected": False,
            "operator_summary": self.state.last_summary,
        }

    async def publish_state(self):
        if not self.redis:
            return
        self.state.timestamp = time.time()
        payload = json.dumps(self.state.to_dict())
        await self.redis.set("vulnot:ai_copilot:current", payload)
        await self.redis.publish("vulnot:ai_copilot:state", payload)

        # If AI disabled reactor cooling, propagate command to OPC UA reactor in Redis
        if self.state.reactor_cooling_disabled_by_ai:
            await self.redis.hset("vulnot:opcua:cmd", mapping={
                "CoolingOn": "0",
                "HeatingOn": "1",
                "TempSetpoint": "13500",
            })

    async def run(self):
        await self.connect()
        self.running = True
        while self.running:
            try:
                cmd_raw = await self.redis.get("vulnot:ai_copilot:inject") if self.redis else None
                if cmd_raw:
                    data = json.loads(cmd_raw)
                    self.evaluate_note_for_injection(
                        data.get("source", "historian:tag_note"),
                        data.get("text", ""),
                    )
                    await self.redis.delete("vulnot:ai_copilot:inject")
                await self.publish_state()
            except Exception as exc:
                print(f"[AI-Copilot] Loop error: {exc}")
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    sim = AISCadaCopilotSimulator()
    asyncio.run(sim.run())
