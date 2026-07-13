"""Configuration for the fog node."""

from shared.locations import LOCATION_ANCHORS


MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
SUBSCRIBE_TOPIC = "patients/+/events"

# --- Overuse detection ---
OVERUSE_WINDOW_HOURS = 24
OVERUSE_THRESHOLD_COUNT = 4  # illustrative simplification, not clinical guidance

# --- Technique detection ---
# Illustrative thresholds, not clinical guidance — see architecture doc §6/§10.
MIN_FLOW_RATE_MDI = 20.0   # L/min
MIN_FLOW_RATE_DPI = 40.0   # L/min
MAX_TILT_ANGLE_DEGREES = 30.0

# --- Low-dose alerting ---
LOW_DOSE_THRESHOLD = 20  # illustrative simplification, not clinical guidance
