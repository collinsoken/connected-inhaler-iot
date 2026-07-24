"""
Dashboard read Lambda. Handles three routes via HTTP API proxy integration:
  GET /patients                               -> list of distinct patient IDs
  GET /patients/{patient_id}/events?limit=N   -> recent raw events for one patient
  GET /cohort/latest                          -> most recent cohort summary item
"""

import json
import boto3  # type: ignore[import]
from decimal import Decimal
from boto3.dynamodb.conditions import Key  # type: ignore[import]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("PatientEvents")


def decimal_default(obj):
    """json.dumps can't serialize Decimal directly, and every number
    coming back from DynamoDB is a Decimal. Convert to int when it's a
    whole number, otherwise float."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f"not JSON serializable: {obj!r}")


def response(status_code, body_dict):
    """Builds the exact shape API Gateway's HTTP API proxy integration
    requires. body MUST be a JSON string, not a raw dict."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # narrow to your S3 site's origin once known
        },
        "body": json.dumps(body_dict, default=decimal_default),
    }


def get_patient_events(patient_id, limit):
    """Query on the base table's own key schema (patient_id partition,
    timestamp sort) -- most recent first, capped at `limit`."""
    result = table.query(
        KeyConditionExpression=Key("patient_id").eq(patient_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    return result.get("Items", [])


def get_latest_cohort_summary():
    """Same base table, same query pattern -- COHORT_SUMMARY is just
    another partition key value, per the Phase 7 single-table design."""
    result = table.query(
        KeyConditionExpression=Key("patient_id").eq("COHORT_SUMMARY"),
        ScanIndexForward=False,
        Limit=1,
    )
    items = result.get("Items", [])
    return items[0] if items else None


def get_patient_list():
    """The base table's key schema (patient_id partition, timestamp sort)
    has no way to ask "what distinct partition keys exist" as a Query --
    only a Scan can answer that. Same trade-off already documented for
    the Phase 7 GSI decision: fine at this table's size, wouldn't scale
    to a large table without a dedicated registry of patients instead.
    Projects only patient_id to keep each page small and cheap."""
    patient_ids = set()
    scan_kwargs = {"ProjectionExpression": "patient_id"}

    while True:
        result = table.scan(**scan_kwargs)
        for item in result.get("Items", []):
            pid = item["patient_id"]
            if pid != "COHORT_SUMMARY":
                patient_ids.add(pid)

        if "LastEvaluatedKey" not in result:
            break
        scan_kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]

    return sorted(patient_ids)


def lambda_handler(event, context):
    route_key = event.get("routeKey", "")

    try:
        if route_key == "GET /patients":
            patient_ids = get_patient_list()
            return response(200, {"patient_ids": patient_ids})

        elif route_key.startswith("GET /patients/{patient_id}/events"):
            patient_id = event["pathParameters"]["patient_id"]
            query_params = event.get("queryStringParameters") or {}
            limit = int(query_params.get("limit", 20))
            events = get_patient_events(patient_id, limit)
            return response(200, {"patient_id": patient_id, "events": events})

        elif route_key == "GET /cohort/latest":
            summary = get_latest_cohort_summary()
            return response(200, {"summary": summary})

        else:
            return response(404, {"error": f"no handler for route: {route_key}"})

    except Exception as e:
        return response(500, {"error": str(e)})
