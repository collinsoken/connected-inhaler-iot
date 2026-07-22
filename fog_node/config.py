"""Configuration for the fog node."""

import os

from shared.locations import LOCATION_ANCHORS


# --- AWS IoT Core ---
IOT_ENDPOINT = "a2kjr9mz0ln25h-ats.iot.us-east-1.amazonaws.com"
IOT_PORT = 8883
# CLOUD_CLIENT_ID = "fog-node-connected-inhaler"

CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")
DEVICE_CERT_PATH = os.path.join(CERTS_DIR, "device-certificate.pem.crt")
PRIVATE_KEY_PATH = os.path.join(CERTS_DIR, "private.pem.key")
ROOT_CA_PATH = os.path.join(CERTS_DIR, "AmazonRootCA1.pem")

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883

''' 
--- Per-patient fog node mode ---
Set PATIENT_ID to run this fog node scoped to a single patient
(per-patient topology). Leave unset to fall back to the original
shared, all-patients wildcard mode — kept intentionally so both
topologies can still be demoed side by side.
'''

PATIENT_ID = os.environ.get("PATIENT_ID")

SUBSCRIBE_TOPIC = f"patients/{PATIENT_ID}/events" if PATIENT_ID else "patients/+/events"
CLOUD_CLIENT_ID = f"fog-node-{PATIENT_ID}" if PATIENT_ID else "fog-node-connected-inhaler"

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
