"""
Technique detection: flags poor inhaler technique based on flow rate
(device-type-aware) and device tilt angle. Stateless function for each actuation
event and is judged independently. Thresholds are illustrative simplifications,
not clinical guidance.
"""

from fog_node.config import MIN_FLOW_RATE_MDI, MIN_FLOW_RATE_DPI, MAX_TILT_ANGLE_DEGREES


_MIN_FLOW_BY_TYPE = {
    "MDI": MIN_FLOW_RATE_MDI,
    "DPI": MIN_FLOW_RATE_DPI,
}


def check_technique(event):
    """
    Call for every actuation event. Returns a list of reasons (empty
    if technique looks fine) — a list rather than a bool, since flow
    rate and tilt are independent checks and both could fail at once.
    """
    if event.get("event_type") != "actuation":
        return []

    reasons = []
    device_type = event.get("device_type")
    min_flow = _MIN_FLOW_BY_TYPE.get(device_type)

    # Check flow rate if present; if not, assume it's fine (e.g., for DPIs).
    if min_flow is not None and event.get("inhalation_flow_rate", 0) < min_flow:
        reasons.append(
            f"flow rate {event['inhalation_flow_rate']} L/min below {min_flow} L/min minimum for {device_type}"
        )

    # Check tilt angle if present; if not, assume it's fine (e.g., for DPIs).
    if event.get("device_tilt_angle", 0) > MAX_TILT_ANGLE_DEGREES:
        reasons.append(
            f"tilt angle {event['device_tilt_angle']}° exceeds {MAX_TILT_ANGLE_DEGREES}° maximum"
        )

    return reasons
