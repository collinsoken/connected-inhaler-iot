'''
This Lambda function computes cohort-level aggregates for actuation events
in the last hour and writes a summary item to the PatientEvents DynamoDB table.

Triggered on a schedule by EventBridge, the function reads across ALL patients in PatientEvents —
This is a functionality no single fog node can do, since each fog node only
ever sees its own patient's stream. Lambda computes population-level stats
and writes a single summary item back into the same table.

Three aggregates computed (see project discussion for rationale):
  1. Alert rate by zone — actuation events with overuse_alert,
        technique_alert, low_dose_alert, divided by total events per zone
  2. Overuse trend by hour — count of overuse_alert=True per hour bucket
  3. Avg flow rate per patient by device type — MDI & DPI,
        averaged across all actuation events for that patient in the window
'''


import boto3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from collections import defaultdict
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("PatientEvents")

WINDOW_HOURS = 1


def get_window():
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=WINDOW_HOURS)
    return window_start.isoformat(), now.isoformat()


def query_actuation_events(window_start, window_end):
    response = table.query(
        IndexName="event_type-timestamp-index",
        KeyConditionExpression=(
            Key("event_type").eq("actuation")
            & Key("timestamp").between(window_start, window_end)
        ),
    )
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.query(
            IndexName="event_type-timestamp-index",
            KeyConditionExpression=(
                Key("event_type").eq("actuation")
                & Key("timestamp").between(window_start, window_end)
            ),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    return items


def compute_aggregates(events):
    # --- 1. Alert rate by zone ---
    zone_totals = defaultdict(int)
    zone_alert_counts = defaultdict(lambda: {"overuse_alert": 0, "technique_alert": 0, "low_dose_alert": 0})

    # --- 2. Overuse count by patient ---
    overuse_by_patient = defaultdict(int)

    # --- 3. Avg flow rate per patient by device_type ---
    flow_sums = defaultdict(lambda: defaultdict(float))
    flow_counts = defaultdict(lambda: defaultdict(int))

    for event in events:
        zone = event.get("zone", "unknown")
        patient_id = event["patient_id"]
        device_type = event.get("device_type", "unknown")

        zone_totals[zone] += 1
        if event.get("overuse_alert"):
            zone_alert_counts[zone]["overuse_alert"] += 1
            overuse_by_patient[patient_id] += 1
        if event.get("technique_alert"):
            zone_alert_counts[zone]["technique_alert"] += 1
        if event.get("low_dose_alert"):
            zone_alert_counts[zone]["low_dose_alert"] += 1

        if "inhalation_flow_rate" in event:
            flow_sums[patient_id][device_type] += float(event["inhalation_flow_rate"])
            flow_counts[patient_id][device_type] += 1

    # Build alert_rate_by_zone as ratios, guarding against div-by-zero
    alert_rate_by_zone = {}
    for zone, total in zone_totals.items():
        alert_rate_by_zone[zone] = {
            alert_type: round(count / total, 3)
            for alert_type, count in zone_alert_counts[zone].items()
        }

    # Build avg_flow_rate_by_patient_device
    avg_flow_rate_by_patient_device = {}
    for patient_id, by_device in flow_sums.items():
        avg_flow_rate_by_patient_device[patient_id] = {
            device_type: round(total / flow_counts[patient_id][device_type], 1)
            for device_type, total in by_device.items()
        }

    return {
        "alert_rate_by_zone": alert_rate_by_zone,
        "overuse_count_by_patient": dict(overuse_by_patient),
        "avg_flow_rate_by_patient_device": avg_flow_rate_by_patient_device,
    }


def to_decimal(obj):
    """Recursively converts floats to Decimal so DynamoDB's resource API accepts them."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_decimal(v) for v in obj]
    return obj


def lambda_handler(event, context):
    window_start, window_end = get_window()
    events = query_actuation_events(window_start, window_end)

    aggregates = compute_aggregates(events)

    summary_item = {
        "patient_id": "COHORT_SUMMARY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "cohort_summary",
        "window_start": window_start,
        "window_end": window_end,
        "event_count": len(events),
        **to_decimal(aggregates),
    }

    table.put_item(Item=summary_item)

    print(f"Wrote cohort summary: {len(events)} events processed, "
          f"window {window_start} to {window_end}")

    return {"statusCode": 200, "summary": summary_item["timestamp"]}
