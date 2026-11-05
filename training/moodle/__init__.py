"""
VULNOT Moodle LMS Integration Package
Connects VULNOT Training Platform to Mjolnir Training Portal (https://portal.mjolnir.training)
"""

from .client import (
    DEFAULT_MOODLE_URL,
    MOODLE_COURSES,
    VULNOT_LABS,
    MoodlePortalClient,
    TrainingModuleManager,
    get_training_manager,
)

__all__ = [
    "DEFAULT_MOODLE_URL",
    "MOODLE_COURSES",
    "VULNOT_LABS",
    "MoodlePortalClient",
    "TrainingModuleManager",
    "get_training_manager",
]
