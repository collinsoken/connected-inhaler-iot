"""
Assembles the final processed event: applies zone generalization,
then attaches any alert flags raised by the detection checks. This
is the single object that gets forwarded onward.
"""

from fog_node.zone_generalizer import generalize_location
from fog_node.overuse_detector import check_overuse
from fog_node.technique_detector import check_technique
from fog_node.dose_monitor import check_low_dose


def process_event(raw_event):
    """
    Takes a raw event as received from MQTT, returns the fully
    processed event ready for forwarding, plus a list of human-
    readable alert messages for local logging.
    """
    event = generalize_location(raw_event)
    alert_messages = []

    if check_overuse(event):
        event["overuse_alert"] = True
        alert_messages.append(
            f"⚠️ OVERUSE ALERT — {event['patient_id']} has exceeded rescue inhaler threshold"
        )

    technique_issues = check_technique(event)
    if technique_issues:
        event["technique_alert"] = True
        event["technique_alert_reasons"] = technique_issues
        alert_messages.append(
            f"⚠️ TECHNIQUE ALERT — {event['patient_id']} ({event.get('device_id')}): "
            f"{'; '.join(technique_issues)}"
        )

    if check_low_dose(event):
        event["low_dose_alert"] = True
        alert_messages.append(
            f"⚠️ LOW DOSE ALERT — {event['patient_id']} ({event.get('device_id')}): "
            f"only {event.get('remaining_doses')} doses remaining"
        )

    return event, alert_messages
