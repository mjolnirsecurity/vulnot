"""
FastAPI Router for VULNOT Training Module & Moodle LMS Integration (https://portal.mjolnir.training)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Ensure repository root is importable when running locally
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.moodle.client import (  # noqa: E402
    DEFAULT_MOODLE_URL,
    MOODLE_COURSES,
    VULNOT_LABS,
    get_training_manager,
)

router = APIRouter(tags=["Training & Moodle LMS"])

# Optional Redis client getter injected by the main FastAPI app
_redis_getter: Optional[Callable[[], Any]] = None


def set_redis_getter(getter: Callable[[], Any]) -> None:
    global _redis_getter
    _redis_getter = getter


def _get_redis() -> Any:
    if _redis_getter is not None:
        return _redis_getter()
    return None


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class MoodleCredentialsLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Moodle username or email on portal.mjolnir.training")
    password: str = Field(..., min_length=1, description="Moodle password")
    service: str = Field(default="moodle_mobile_app", description="Moodle Web Service shortname")
    portal_url: Optional[str] = Field(default=DEFAULT_MOODLE_URL, description="Moodle Portal URL")
    allow_lab_fallback: bool = Field(
        default=True,
        description="Queue progress in Deferred Sync Mode if Moodle WebService token generation is not yet active for this account",
    )


class MoodleTokenConnectRequest(BaseModel):
    wstoken: str = Field(..., min_length=4, description="Moodle Web Service API token")
    portal_url: Optional[str] = Field(default=DEFAULT_MOODLE_URL, description="Moodle Portal URL")
    allow_lab_fallback: bool = Field(default=True, description="Allow Deferred Sync Mode fallback")


class LabVerifyRequest(BaseModel):
    objective_id: Optional[str] = Field(default=None, description="Specific objective ID (e.g. obj-01-1)")
    flag: Optional[str] = Field(default=None, description="Captured flag (e.g. VULNOT{...}) or VERIFY")
    auto_sync: bool = Field(default=True, description="Automatically sync progress & grade to portal.mjolnir.training")


# =============================================================================
# MOODLE LMS ENDPOINTS (https://portal.mjolnir.training)
# =============================================================================

@router.get("/api/moodle/status")
async def get_moodle_status(
    probe: bool = Query(False, description="Force a fresh live HTTP probe to https://portal.mjolnir.training"),
) -> Dict[str, Any]:
    """
    Get connection status and live reachability metrics for Mjolnir Training Moodle Portal
    (https://portal.mjolnir.training).
    """
    mgr = get_training_manager()
    return await mgr.get_portal_status(force_probe=probe)


@router.post("/api/moodle/auth/login")
async def moodle_login_credentials(req: MoodleCredentialsLoginRequest) -> Dict[str, Any]:
    """
    Authenticate with https://portal.mjolnir.training/login/token.php using Moodle credentials.
    """
    mgr = get_training_manager()
    if req.portal_url:
        mgr.client.base_url = req.portal_url.rstrip("/")
        mgr.state["portal_url"] = mgr.client.base_url

    result = await mgr.login_with_credentials(
        username=req.username,
        password=req.password,
        service=req.service,
        allow_lab_fallback=req.allow_lab_fallback,
    )
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "Moodle authentication failed"))
    return result


@router.post("/api/moodle/auth/token")
async def moodle_connect_token(req: MoodleTokenConnectRequest) -> Dict[str, Any]:
    """
    Connect to https://portal.mjolnir.training/webservice/rest/server.php using a Moodle Web Service token.
    """
    mgr = get_training_manager()
    result = await mgr.connect_with_token(
        wstoken=req.wstoken,
        portal_url=req.portal_url,
        allow_lab_fallback=req.allow_lab_fallback,
    )
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid Moodle Web Service token"))
    return result


@router.post("/api/moodle/auth/logout")
async def moodle_logout() -> Dict[str, Any]:
    """Disconnect the active Moodle session."""
    mgr = get_training_manager()
    return mgr.logout()


@router.get("/api/moodle/courses")
async def get_moodle_courses() -> Dict[str, Any]:
    """
    List official VULNOT courses mapped to https://portal.mjolnir.training,
    including student completion progress and remote Moodle course enrollments.
    """
    mgr = get_training_manager()
    return await mgr.get_courses()


@router.post("/api/moodle/sync")
async def sync_all_progress_to_moodle() -> Dict[str, Any]:
    """
    Synchronize all lab completions, objective scores, and assignment evidence with
    https://portal.mjolnir.training.
    """
    mgr = get_training_manager()
    return await mgr.sync_all_to_moodle()


@router.post("/api/moodle/sync/{lab_id}")
async def sync_single_lab_to_moodle(lab_id: str) -> Dict[str, Any]:
    """Synchronize a single lab's completion and grade to https://portal.mjolnir.training."""
    mgr = get_training_manager()
    res = await mgr.sync_lab_to_moodle(lab_id)
    if res.get("success") is False:
        raise HTTPException(status_code=404, detail=res.get("error", "Lab not found"))
    return res


@router.get("/api/moodle/export/manifest")
async def export_moodle_course_manifest() -> Dict[str, Any]:
    """
    Export the Moodle LMS Course & Activity Manifest for importing all 18 VULNOT labs
    into https://portal.mjolnir.training.
    """
    mgr = get_training_manager()
    return mgr.export_moodle_manifest()


# =============================================================================
# TRAINING LABS & OBJECTIVE VERIFICATION ENDPOINTS
# =============================================================================

@router.get("/api/training/labs")
async def list_training_labs(
    track: Optional[str] = Query(None, description="Filter by track: redteam, forensics, soc, or all"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: beginner, intermediate, advanced, expert"),
    course: Optional[str] = Query(None, description="Filter by Moodle course shortname (VULNOT-101, VULNOT-201, VULNOT-301)"),
) -> Dict[str, Any]:
    """
    Get all 18 VULNOT training labs (Red Team, Forensics, SOC Defender) with live progress,
    objectives, MITRE ATT&CK mappings, and https://portal.mjolnir.training links.
    """
    mgr = get_training_manager()
    return mgr.list_labs(track=track, difficulty=difficulty, course=course)


@router.get("/api/training/labs/{lab_id}")
async def get_training_lab_detail(lab_id: str) -> Dict[str, Any]:
    """
    Get full details and markdown lab guide for a specific VULNOT training lab.
    """
    mgr = get_training_manager()
    lab_def = mgr.get_lab_definition(lab_id)
    if not lab_def:
        raise HTTPException(status_code=404, detail=f"Training lab '{lab_id}' not found")
    return mgr.format_lab_with_progress(lab_def, include_markdown=True)


@router.post("/api/training/labs/{lab_id}/start")
async def start_training_lab(lab_id: str) -> Dict[str, Any]:
    """Start or resume a VULNOT training lab session."""
    mgr = get_training_manager()
    res = mgr.start_lab(lab_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Lab not found"))
    return res


@router.post("/api/training/labs/{lab_id}/verify")
async def verify_training_lab_objective(lab_id: str, req: LabVerifyRequest) -> Dict[str, Any]:
    """
    Verify a lab objective via flag submission or live OT telemetry inspection,
    and automatically sync completion/score to https://portal.mjolnir.training.
    """
    mgr = get_training_manager()
    result = await mgr.verify_objective_or_flag(
        lab_id=lab_id,
        objective_id=req.objective_id,
        flag=req.flag,
        redis_client=_get_redis(),
        auto_sync=req.auto_sync,
    )
    return result
