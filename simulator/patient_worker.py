"""
Per-patient simulation worker. Each patient runs in its own thread with
its own MQTT connection. Events are generated at one rate but dispatched
(published) at a separate, independently configurable rate — see config.py.
"""

import threading
import time
import random

from simulator.config import (
    ACTUATION_CHECK_INTERVAL_SECONDS,
    AMBIENT_READING_INTERVAL_SECONDS,
    DISPATCH_INTERVAL_SECONDS,
)
from simulator.events import generate_actuation_event, generate_ambient_reading_event
from simulator.mqtt_client import SimulatorMqttClient


def run_patient(patient, stop_event: threading.Event):
    patient_id = patient["patient_id"]
    client = SimulatorMqttClient()

    try:
        client.connect()
    except RuntimeError as e:
        print(f"[{patient_id}] Failed to start: {e}")
        return

    start_time = time.monotonic()
    last_actuation = start_time
    last_ambient = start_time
    last_dispatch = start_time
    pending_events = []  # buffer: generated but not yet sent

    try:
        while not stop_event.is_set():
            now = time.monotonic()

            # --- Generation (frequency) ---
            if now - last_actuation >= ACTUATION_CHECK_INTERVAL_SECONDS:
                role = random.choice(["rescue", "maintenance"])  #NOSONAR
                device_info = patient["devices"][role]
                event = generate_actuation_event(patient_id, role, device_info)
                pending_events.append(event)
                last_actuation = now

            if now - last_ambient >= AMBIENT_READING_INTERVAL_SECONDS:
                role = random.choice(["rescue", "maintenance"])  #NOSONAR
                device_info = patient["devices"][role]
                event = generate_ambient_reading_event(patient_id, role, device_info)
                pending_events.append(event)
                last_ambient = now

            # --- Dispatch (independent rate) ---
            if now - last_dispatch >= DISPATCH_INTERVAL_SECONDS and pending_events:
                print(f"[{patient_id}] Dispatching {len(pending_events)} buffered event(s)")
                for event in pending_events:
                    client.publish_event(patient_id, event)
                pending_events.clear()
                last_dispatch = now

            time.sleep(0.5)

        # Flush any remaining buffered events on graceful shutdown
        if pending_events:
            print(f"[{patient_id}] Flushing {len(pending_events)} event(s) before shutdown")
            for event in pending_events:
                client.publish_event(patient_id, event, wait_for_delivery=True)
    finally:
        client.disconnect()
        print(f"[{patient_id}] Stopped.")
