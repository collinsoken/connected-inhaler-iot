"""
MQTT publishing wrapper for the connected inhaler sensor simulator.
Centralizes connection handling, topic naming, and error handling
so fog node can reuse the same conventions.
"""

import json
import time
from unittest import result
import paho.mqtt.client as mqtt

from simulator.config import MQTT_BROKER_HOST, MQTT_BROKER_PORT


class SimulatorMqttClient:
    def __init__(self):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._connected = False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connected = True
            print(f"[MQTT] Connected to broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        else:
            self._connected = False
            print(f"[MQTT] Connection failed: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected = False
        print(f"[MQTT] Disconnected (reason: {reason_code})")

    def connect(self, timeout_seconds=5):
        try:
            self._client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
        except OSError as e:
            raise RuntimeError(
                f"Could not reach MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}. "
                f"Is Mosquitto running? Original error: {e}"
            ) from e

        self._client.loop_start()  # background thread handling network I/O

        waited = 0
        while not self._connected and waited < timeout_seconds:
            time.sleep(0.1)
            waited += 0.1

        if not self._connected:
            raise RuntimeError(
                f"Socket connected but no broker acknowledgment within {timeout_seconds}s."
            )

    def publish_event(self, patient_id, event, wait_for_delivery=False):
        topic = f"patients/{patient_id}/events"
        payload = json.dumps(event)
        result = self._client.publish(topic, payload, qos=1)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"[MQTT] WARNING: publish to {topic} failed with rc={result.rc}")
            return False

        if wait_for_delivery:
            result.wait_for_publish(timeout=2)
        return True

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()
    