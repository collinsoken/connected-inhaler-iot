"""
Overuse detection for rescue inhalers, using a sliding time window.
Threshold is an illustrative simplification for demonstration, not
clinical guidance.
"""

from datetime import datetime, timedelta, timezone

from fog_node.config import OVERUSE_WINDOW_HOURS, OVERUSE_THRESHOLD_COUNT


# patient_id -> list of timestamps (datetime objects) of rescue actuations
_rescue_actuation_history = {}


def check_overuse(event):
    """
    Call for every actuation event. Returns True if this event pushes
    the patient's rescue inhaler use over the threshold within the
    rolling window, False otherwise (including for non-rescue events).
    """
    if event.get("event_type") != "actuation" or event.get("device_role") != "rescue":
        return False

    patient_id = event["patient_id"]
    event_time = datetime.fromisoformat(event["timestamp"])

    history = _rescue_actuation_history.setdefault(patient_id, [])
    history.append(event_time)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=OVERUSE_WINDOW_HOURS)
    history[:] = [t for t in history if t >= cutoff]

    return len(history) > OVERUSE_THRESHOLD_COUNT
