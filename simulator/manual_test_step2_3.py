"""
Manual test harness for Step 2.3 — publish real events over MQTT.
Run with: python -m simulator.manual_test_step2_3

Before running, open a SECOND terminal and run:
    mosquitto_sub -h localhost -t "patients/+/events" -v
so you can watch messages arrive live. The '+' wildcard matches any patient_id.
"""

import time
from simulator.config import PATIENTS
from simulator.events import generate_actuation_event, generate_ambient_reading_event
from simulator.mqtt_client import SimulatorMqttClient

patient = PATIENTS[0]
client = SimulatorMqttClient()
client.connect()

for _ in range(3):
    event = generate_actuation_event(patient["patient_id"], "rescue", patient["devices"]["rescue"])
    client.publish_event(patient["patient_id"], event)
    time.sleep(1)

ambient_event = generate_ambient_reading_event(patient["patient_id"])
client.publish_event(patient["patient_id"], ambient_event)

time.sleep(1)
client.disconnect()
print("Done.")