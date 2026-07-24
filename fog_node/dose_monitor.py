"""
Low-dose alerting: flags when an inhaler's remaining_doses drops below
a threshold. Stateless function that reads the simulator-reported counter directly,
per the architecture decision that the fog node never reconstructs
device state itself (see architecture).
"""

from fog_node.config import LOW_DOSE_THRESHOLD


def check_low_dose(event):
    """
    Call for every actuation event. Returns True if remaining_doses
    is at or below the configured threshold.
    """
    if event.get("event_type") != "actuation":
        return False

    return event.get("remaining_doses", float("inf")) <= LOW_DOSE_THRESHOLD
