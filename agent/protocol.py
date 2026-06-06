"""WebSocket message protocol — must match ufo-control-plane.

Wire format: JSON ``{"type": "<type>", "payload": {...}}``.
"""

from __future__ import annotations


class DeviceMsg:
    """Device -> control plane."""

    HELLO = "device_hello"
    STATUS = "device_status"
    TASK_STARTED = "task_started"
    TASK_LOG = "task_log"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


class RelayMsg:
    """Control plane -> device."""

    RUN_TASK = "run_task"
    PAUSE = "pause"
    RESUME = "resume"
    DISCONNECT = "disconnect"
