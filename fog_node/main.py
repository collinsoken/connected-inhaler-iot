"""
Fog node entry point. Subscribes to all patients' events and, for now,
just logs what it receives — processing logic is added in later steps.
Run with: python -m fog_node.main
"""

import json
import paho.mqtt.client as mqtt

from fog_node.config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, SUBSCRIBE_TOPIC
from fog_node.event_processor import process_event


# Callback for when the client connects to the MQTT broker.
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[FogNode] Connected to broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        client.subscribe(SUBSCRIBE_TOPIC, qos=1)
        print(f"[FogNode] Subscribed to '{SUBSCRIBE_TOPIC}'")
    else:
        print(f"[FogNode] Connection failed: {reason_code}")


def forward_to_cloud(event):
    """
    STUB — Phase 4 will replace this with a real AWS IoT Core publish.
    For now, just makes the forwarding step visible and testable in
    isolation from network/cloud concerns.
    """
    print(f"[FogNode] → (stub) would forward event_id={event['event_id']} to AWS IoT Core")


def on_message(client, userdata, msg):
    try:
        raw_event = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[FogNode] WARNING: received malformed payload on {msg.topic}: {e}")
        return

    processed_event, alert_messages = process_event(raw_event)

    print(f"[FogNode] Received {processed_event.get('event_type')} from {processed_event.get('patient_id')} "
          f"(zone={processed_event.get('zone')}, event_id={processed_event.get('event_id')})")

    for message in alert_messages:
        print(f"[FogNode] {message}")

    forward_to_cloud(processed_event)
    

# MQTT client setup and main loop are in the main() function so that the fog node can be run as a script.
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

# Connect to the MQTT broker and start the network loop. The fog node will run indefinitely until interrupted.
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
    except OSError as e:
        raise RuntimeError(
            f"Could not reach MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}. "
            f"Is Mosquitto running? Original error: {e}"
        ) from e

    print("Fog node running. Press Ctrl+C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping fog node...")
        client.disconnect()
        print("Fog node stopped.")


if __name__ == "__main__":
    main()
    