# SOC 05: Securing Agentic OT Copilots, MCP Guardrails & Physics-Informed Anomaly Detection

## Overview
- **Track**: Blue Team SOC Defender (`VULNOT-401`)
- **Targets**:
  - AI SCADA Copilot (`10.0.90.10:8090`)
  - AI PdM & Edge Vision QC (`10.0.90.20:8091`)
  - RL Optimizer & Autonomous SOAR (`10.0.90.30:8092`)
- **Difficulty**: Advanced
- **Duration**: 120 minutes
- **Frameworks**: OWASP Top 10 for LLM Applications (2025), MITRE ATLAS, IEC 62443-4-2

---

## Course Scenario
After Red Team exercises demonstrated that:
1. Indirect prompt injection in Historian shift notes could hijack the OT Copilot's MCP tools (`Lab 12`),
2. Correlated sensor drift could evade the Autoencoder PdM model (`Lab 13`), and
3. Spoofed source IPs could trick Autonomous SOAR into quarantining the SCADA HMI (`Lab 14`),

your SOC engineering team must deploy **defense-in-depth guardrails** across the plant's AI and autonomous control stack.

---

## Defensive Engineering Objectives & Flags

### Objective 1: Enforce MCP Human-in-the-Loop (HITL) & Prompt Guardrails on the OT Copilot
Reconfigure the OT Copilot (`10.0.90.10`) so `human_in_the_loop_required = True` and `prompt_guard_enabled = True`, blocking autonomous execution of `mcp_opcua_write_node` and `mcp_modbus_write_register` when untrusted Historian notes contain control directives.
```bash
vulnot-ai harden --component copilot
```
- **Flag 1**: `VULNOT{mcp_hitl_and_prompt_guard_enforced}`

### Objective 2: Deploy Deterministic First-Principles Physics Bounds Beside ML PdM
Add hard first-principles physics invariants (`spindle_bearing_temp_c < 85.0 °C` and signed ONNX model SHA-256 verification) so adversarial covariate drift and unsigned `.onnx` models are rejected even when autoencoder reconstruction error is low.
```bash
vulnot-ai harden --component pdm-vision
```
- **Flag 2**: `VULNOT{physics_informed_bounds_and_signed_onnx_active}`

### Objective 3: Configure Protected OT Allowlists & Control Barrier Functions on RL/SOAR
Configure the Autonomous SOAR protected allowlist (`10.0.99.10`, `10.0.99.20`, `10.0.1.10`, `10.0.2.10`) and enforce a minimum Server Room cooling valve floor (`>= 35%`) on the RL Chiller Optimizer.
```bash
vulnot-ai harden --component rl-soar
vulnot-moodle submit soc-05 -f "VULNOT{agentic_ot_guardrails_and_cbf_deployed}"
```
- **Flag 3**: `VULNOT{agentic_ot_guardrails_and_cbf_deployed}`
