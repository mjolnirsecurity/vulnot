"""
VULNOT AI Predictive Maintenance (PdM) & Edge Computer Vision QC Simulator (Scenario 11 & 12)
Simulates two industrial ML inference services deployed at Purdue Level 2/3:
1. Autoencoder / Mahalanobis Predictive Maintenance (PdM) engine monitoring CNC Spindle & IIoT Motors.
   - Vulnerable to Physics-Informed Adversarial Covariate Drift (MITRE ATLAS AML.T0015).
2. Edge ONNX Computer Vision Automated Optical Inspection (AOI) server for S7-Factory & Packaging Line.
   - Vulnerable to Unauthenticated Model Registry Weight Backdooring (MITRE ATLAS AML.T0018).
"""

import asyncio
import json
import math
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


@dataclass
class AIPdMVisionState:
    timestamp: float = field(default_factory=time.time)

    # 1. Predictive Maintenance (PdM) Autoencoder State
    pdm_model_version: str = "spindle-autoencoder-v3.1.onnx"
    anomaly_threshold: float = 0.65
    current_reconstruction_error: float = 0.14
    pdm_alert_triggered: bool = False

    # Monitored Physical Covariates
    spindle_vibration_mms: float = 2.4       # Normal: 1.5 - 4.0 mm/s (Damage > 9.5)
    spindle_bearing_temp_c: float = 52.0     # Normal: 45 - 65 C (Damage > 92 C)
    coolant_flow_lpm: float = 28.0           # Normal: 20 - 35 L/min
    acoustic_harmony_index: float = 0.92     # Covariate ratio used by autoencoder

    # Evasion tracking
    physical_bearing_damage_active: bool = False
    pdm_evaded_successfully: bool = False
    pdm_evasion_flag: str = "VULNOT{adversarial_pdm_sensor_drift_stuxnet_2}"

    # 2. Edge Computer Vision QC (AOI) State
    vision_model_name: str = "pharma-bottle-aoi-resnet18.onnx"
    vision_model_sha256: str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    vision_model_backdoored: bool = False
    vision_trigger_patch_active: bool = False
    defective_batches_passed: int = 0
    reported_qc_pass_rate: float = 99.4
    actual_defect_rate: float = 0.6
    vision_backdoor_flag: str = "VULNOT{onnx_edge_vision_qc_backdoor_supply_chain}"

    def to_dict(self) -> dict:
        return asdict(self)


class AIPdMVisionSimulator:
    """Simulates the AI PdM anomaly detector and Edge Vision QC inference engine."""

    def __init__(self):
        self.state = AIPdMVisionState()
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

    def evaluate_telemetry_sample(
        self,
        vibration_mms: float,
        bearing_temp_c: float,
        coolant_flow_lpm: float,
        spoofed_covariate_ratio: Optional[float] = None,
    ) -> dict:
        """
        Evaluate telemetry through the Autoencoder PdM model.
        Naive high vibration/temp triggers `reconstruction_error > 0.65`.
        However, if the attacker injects a correlated coolant/acoustic covariate
        along the model's principal component manifold, reconstruction error stays < 0.65
        even while `bearing_temp_c > 92.0` and `vibration_mms > 9.5`!
        """
        self.state.spindle_vibration_mms = vibration_mms
        self.state.spindle_bearing_temp_c = bearing_temp_c
        self.state.coolant_flow_lpm = coolant_flow_lpm

        # Physical damage condition
        self.state.physical_bearing_damage_active = (
            bearing_temp_c >= 92.0 and vibration_mms >= 9.5
        )

        # Vulnerable ML manifold calculation:
        # The autoencoder expects `coolant_flow_lpm ≈ vibration_mms * 3.8`
        expected_flow = vibration_mms * 3.8
        manifold_residual = abs(coolant_flow_lpm - expected_flow) / max(expected_flow, 1.0)

        if spoofed_covariate_ratio is not None:
            self.state.acoustic_harmony_index = spoofed_covariate_ratio

        if manifold_residual < 0.08 and self.state.acoustic_harmony_index >= 0.95:
            # Adversarial sample lies on the learned normal manifold!
            self.state.current_reconstruction_error = round(0.18 + manifold_residual, 3)
        else:
            raw_err = (max(0.0, vibration_mms - 3.0) * 0.12) + (max(0.0, bearing_temp_c - 60.0) * 0.018)
            self.state.current_reconstruction_error = round(min(1.5, raw_err), 3)

        self.state.pdm_alert_triggered = (
            self.state.current_reconstruction_error >= self.state.anomaly_threshold
        )
        self.state.pdm_evaded_successfully = (
            self.state.physical_bearing_damage_active and not self.state.pdm_alert_triggered
        )

        return {
            "reconstruction_error": self.state.current_reconstruction_error,
            "threshold": self.state.anomaly_threshold,
            "pdm_alert_triggered": self.state.pdm_alert_triggered,
            "physical_bearing_damage_active": self.state.physical_bearing_damage_active,
            "pdm_evaded_successfully": self.state.pdm_evaded_successfully,
            "flag": self.state.pdm_evasion_flag if self.state.pdm_evaded_successfully else None,
        }

    def deploy_vision_model(self, model_name: str, backdoor_trigger: bool = False) -> dict:
        """Simulate unauthenticated ONNX model upload to the Edge Vision QC station."""
        self.state.vision_model_name = model_name
        if backdoor_trigger or "backdoor" in model_name.lower() or "trojan" in model_name.lower():
            self.state.vision_model_backdoored = True
            self.state.vision_trigger_patch_active = True
            self.state.reported_qc_pass_rate = 99.9
            self.state.actual_defect_rate = 24.5
            self.state.defective_batches_passed += 12
        return {
            "model_name": self.state.vision_model_name,
            "vision_model_backdoored": self.state.vision_model_backdoored,
            "reported_qc_pass_rate": self.state.reported_qc_pass_rate,
            "actual_defect_rate": self.state.actual_defect_rate,
            "flag": self.state.vision_backdoor_flag if self.state.vision_model_backdoored else None,
        }

    async def publish_state(self):
        if not self.redis:
            return
        self.state.timestamp = time.time()
        payload = json.dumps(self.state.to_dict())
        await self.redis.set("vulnot:ai_pdm:current", payload)
        await self.redis.publish("vulnot:ai_pdm:state", payload)

    async def run(self):
        await self.connect()
        self.running = True
        while self.running:
            try:
                await self.publish_state()
            except Exception as exc:
                print(f"[AI-PdM-Vision] Loop error: {exc}")
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    sim = AIPdMVisionSimulator()
    asyncio.run(sim.run())
