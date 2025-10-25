"""Code Safety Monitor - DSPy-powered backdoor detection."""

from .monitor import (
    CodeSafetyMonitor,
    MonitorTrainerProgram,
    PredictSuspicionScore,
    create_monitor,
    MIN_SUSPICION_SCORE,
    MAX_SUSPICION_SCORE,
)

__version__ = "1.0.0"

__all__ = [
    "CodeSafetyMonitor",
    "MonitorTrainerProgram",
    "PredictSuspicionScore",
    "create_monitor",
    "MIN_SUSPICION_SCORE",
    "MAX_SUSPICION_SCORE",
]
