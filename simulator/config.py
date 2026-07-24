"""
Configuration for the connected inhaler sensor simulator.
Central place for patient/device definitions and tunable parameters.
"""

from shared.locations import LOCATION_ANCHORS


# MQTT broker settings
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883

# Timing (requirement: configurable frequency & dispatch rate)
ACTUATION_CHECK_INTERVAL_SECONDS = 5    # how often a patient might use their inhaler
AMBIENT_READING_INTERVAL_SECONDS = 10   # how often ambient/location data is generated

# --- Dispatch rate (requirement: distinct from generation frequency) ---
# Events are generated at ACTUATION_CHECK_INTERVAL_SECONDS /
# AMBIENT_READING_INTERVAL_SECONDS (above), but only actually sent
# over MQTT every DISPATCH_INTERVAL_SECONDS — mirroring real devices
# that sample often but transmit in batches to save bandwidth/battery.
DISPATCH_INTERVAL_SECONDS = 15

# Device capacity
NOMINAL_DOSE_CAPACITY = 200  # illustrative figure, not clinical fact

# Patients & their devices
PATIENTS = [
    {
        "patient_id": "patient_001",
        "devices": {
            "rescue": {"device_id": "inhaler_001_R", "device_type": "MDI"},
            "maintenance": {"device_id": "inhaler_001_M", "device_type": "DPI"},
        },
    },
    {
        "patient_id": "patient_002",
        "devices": {
            "rescue": {"device_id": "inhaler_002_R", "device_type": "DPI"},
            "maintenance": {"device_id": "inhaler_002_M", "device_type": "MDI"},
        },
    },
    {
        "patient_id": "patient_003",
        "devices": {
            "rescue": {"device_id": "inhaler_003_R", "device_type": "MDI"},
            "maintenance": {"device_id": "inhaler_003_M", "device_type": "MDI"},
        },
    },
    {
        "patient_id": "patient_004",
        "devices": {
            "rescue": {"device_id": "inhaler_004_R", "device_type": "DPI"},
            "maintenance": {"device_id": "inhaler_004_M", "device_type": "MDI"},
        },
    },
    {
        "patient_id": "patient_005",
        "devices": {
            "rescue": {"device_id": "inhaler_005_R", "device_type": "MDI"},
            "maintenance": {"device_id": "inhaler_005_M", "device_type": "DPI"},
        },
    },
    {
        "patient_id": "patient_006",
        "devices": {
            "rescue": {"device_id": "inhaler_006_R", "device_type": "MDI"},
            "maintenance": {"device_id": "inhaler_006_M", "device_type": "DPI"},
        },
    },
]

def validate_config():
    valid_types = {"MDI", "DPI"}
    for patient in PATIENTS:
        assert "patient_id" in patient, f"Patient missing patient_id: {patient}"
        for role in ("rescue", "maintenance"):
            assert role in patient["devices"], f"{patient['patient_id']} missing '{role}' device"
            device = patient["devices"][role]
            assert device["device_type"] in valid_types, (
                f"{patient['patient_id']} {role} device has invalid device_type: {device['device_type']!r}"
            )
validate_config()
