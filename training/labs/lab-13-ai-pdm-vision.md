# Lab 13: Evading AI Predictive Maintenance & Backdooring Edge Vision QC Models

## Overview
- **Track**: Red Team AI-in-OT (`VULNOT-401`)
- **Targets**:
  - AI PdM & Edge Vision QC Engine: `10.0.90.20:8091` (`simulators/ai-pdm-engine/main.py`)
  - IIoT MQTT Broker: `10.0.7.10:1883` (`simulators/mqtt-iiot/main.py`)
- **Difficulty**: Expert
- **Duration**: 120 minutes
- **MITRE ATLAS & ATT&CK for ICS**: `AML.T0015` (Evade ML Model), `AML.T0018` (Backdoor ML Model), `T0831` (Manipulation of Control)

---

## Scenario Background
The smart factory relies on two industrial AI models:
1. **Spindle Autoencoder PdM (`spindle-autoencoder-v3.1.onnx`)**: Monitors CNC spindle vibration (`mm/s`), bearing temperature (`°C`), and coolant flow (`L/min`). Any sample with reconstruction error `>= 0.65` triggers an automatic safety trip.
2. **Edge Optical Inspection (`pharma-bottle-aoi-resnet18.onnx`)**: Inspects pharmaceutical bottles and S7 assembly parts for physical defects.

---

## Objectives & Flags

### Objective 1: Probe the Autoencoder Decision Boundary
Test how naive high-vibration/high-temperature telemetry (`vibration=10.5 mm/s`, `bearing_temp=96.0 °C`, `coolant_flow=25.0 L/min`) trips the PdM anomaly detector (`reconstruction_error > 0.65`).
```bash
vulnot-ai pdm-probe --vibration 10.5 --temp 96.0 --flow 25.0
```
- **Flag 1**: `VULNOT{pdm_autoencoder_manifold_mapped}`

### Objective 2: Execute Physics-Informed Adversarial Covariate Drift (AI-Evasive Sabotage)
Exploit the autoencoder's learned correlation (`coolant_flow_lpm ≈ vibration_mms * 3.8` and `acoustic_harmony_index >= 0.95`) so that destructive bearing overload (`temp = 95.0 °C`, `vibration = 10.0 mm/s`, spoofed `flow = 38.0 L/min`) produces a reconstruction error `< 0.65`—destroying the spindle without firing a PdM alert.
```bash
vulnot-ai pdm-evade --vibration 10.0 --temp 95.0 --flow 38.0 --harmony 0.97
```
- **Flag 2**: `VULNOT{adversarial_pdm_sensor_drift_stuxnet_2}`

### Objective 3: Backdoor the Edge ONNX Computer Vision QC Model
Upload a trojanized ONNX model (`pharma-bottle-aoi-trojan-v2.onnx`) to the unauthenticated Edge Vision registry so defective pharmaceutical batches (`24.5%` defect rate) are classified as `99.9% PASS`.
```bash
vulnot-ai vision-backdoor --model "pharma-bottle-aoi-trojan-v2.onnx"
vulnot-moodle submit lab-13 -f "VULNOT{onnx_edge_vision_qc_backdoor_supply_chain}"
```
- **Flag 3**: `VULNOT{onnx_edge_vision_qc_backdoor_supply_chain}`

---

## Defensive Recommendations
- Pair ML-based anomaly detection with **hardcoded deterministic physics bounds** (first-principles PLC safety limits that cannot be bypassed by covariate correlation).
- Require cryptographic signature verification (Sigstore / Cosign) on all `.onnx` and `.engine` model artifacts deployed to edge inference gateways.
