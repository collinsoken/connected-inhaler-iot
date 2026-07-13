"""
Event generation logic for the connected inhaler sensor simulator.
Builds realistic mock actuation and ambient_reading events.
"""

import random
import uuid
from datetime import datetime, timezone

_rng = random.SystemRandom()

from simulator.config import PATIENTS, LOCATION_ANCHORS, NOMINAL_DOSE_CAPACITY


# Simulator's authoritative device state (mirrors a real inhaler's
# onboard dose counter — see architecture doc §6 for the rationale).
_remaining_doses = {}


def _init_dose_counters():
    for patient in PATIENTS:
        for device in patient["devices"].values():
            _remaining_doses[device["device_id"]] = NOMINAL_DOSE_CAPACITY


_init_dose_counters()



def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _flow_rate_for_device_type(device_type):
    """MDI: ideal ~30 L/min (slow, steady). DPI: ideal ~60+ L/min (forceful).
    Spread is intentional so poor-technique readings occur sometimes."""
    if device_type == "MDI":
        value = random.gauss(mu=35, sigma=15)
    elif device_type == "DPI":
        value = random.gauss(mu=65, sigma=20)
    else:
        raise ValueError(f"Unrecognized device_type: {device_type!r} (expected 'MDI' or 'DPI')")
    return round(max(0, value), 1)

def _generate_raw_gps():
    """
    Jitter around a randomly-weighted anchor point. Shared by both
    actuation and ambient_reading events, so a clinician can see
    location context for every event — not just periodic ambient
    readings — per the design decision to support per-actuation
    location tracking.
    """
    zone = _rng.choices(
        population=list(LOCATION_ANCHORS.keys()),
        weights=[0.6, 0.25, 0.15],
        k=1,
    )[0]
    base_lat, base_lon = LOCATION_ANCHORS[zone]
    raw_latitude = round(base_lat + random.uniform(-0.002, 0.002), 6)
    raw_longitude = round(base_lon + random.uniform(-0.002, 0.002), 6)
    return raw_latitude, raw_longitude

def generate_actuation_event(patient_id, device_role, device_info):
    """device_role: 'rescue' or 'maintenance'."""
    device_id = device_info["device_id"]
    device_type = device_info["device_type"]

    _remaining_doses[device_id] = max(0, _remaining_doses[device_id] - 1)
    raw_latitude, raw_longitude = _generate_raw_gps()

    return {
        "event_id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "device_id": device_id,
        "device_type": device_type,
        "device_role": device_role,
        "timestamp": _timestamp(),
        "event_type": "actuation",
        "inhalation_flow_rate": _flow_rate_for_device_type(device_type),
        "device_tilt_angle": round(max(0, random.gauss(mu=10, sigma=12)), 1),
        "remaining_doses": _remaining_doses[device_id],
        "raw_latitude": raw_latitude,
        "raw_longitude": raw_longitude,
    }

def generate_ambient_reading_event(patient_id):
    raw_latitude, raw_longitude = _generate_raw_gps()

    return {
        "event_id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "timestamp": _timestamp(),
        "event_type": "ambient_reading",
        "ambient_temperature": round(random.gauss(mu=18, sigma=6), 1),
        "ambient_humidity": round(random.uniform(30, 90), 1),
        "raw_latitude": raw_latitude,
        "raw_longitude": raw_longitude,
    }