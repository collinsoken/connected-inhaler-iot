import json
import os
import logging
from decimal import Decimal

import boto3


# Logger setup for AWS Lambda. The default log level is INFO, which is appropriate for this function.
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB setup. The table name is read from the environment variable TABLE_NAME, with a default of "PatientEvents".
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "PatientEvents")
table = dynamodb.Table(TABLE_NAME)

# Validation rules for incoming events. Each event must have a set of common fields, and additional fields depending on the event type.
COMMON_REQUIRED_FIELDS = [
    "event_id", "patient_id", "timestamp", "event_type",
    "device_id", "device_type",
]

ACTUATION_REQUIRED_FIELDS = [
    "inhalation_flow_rate", "device_tilt_angle", "remaining_doses",
]

AMBIENT_REQUIRED_FIELDS = ["ambient_temperature", "ambient_humidity"]


# Validation function for incoming events
def validate_event(item):
    """Returns None if valid, otherwise a string describing what's missing."""
    for field in COMMON_REQUIRED_FIELDS:
        if field not in item:
            return f"missing common field: {field}"

    event_type = item["event_type"]
    if event_type == "actuation":
        required = ACTUATION_REQUIRED_FIELDS
    elif event_type == "ambient_reading":
        required = AMBIENT_REQUIRED_FIELDS
    else:
        return f"unrecognized event_type: {event_type!r}"

    for field in required:
        if field not in item:
            return f"missing {event_type} field: {field}"

    return None

"""
AWS Lambda handler function. 
This function is triggered by an SQS event containing one or more messages. 
Each message is expected to contain a JSON-encoded event 
that will be validated and written to DynamoDB.
"""
def lambda_handler(event, context):
    batch_item_failures = []

    """ 
    Process each record in the SQS event. 
    If validation fails or an unhandled exception occurs,
    the message ID is added to the batch_item_failures list for retry.
    """
    for record in event.get("Records", []):
        message_id = record["messageId"]
        try:
            item = json.loads(record["body"], parse_float=Decimal)

            error = validate_event(item)
            if error:
                logger.error(
                    "Validation failed for messageId=%s: %s | body=%s",
                    message_id, error, record["body"],
                )
                batch_item_failures.append({"itemIdentifier": message_id})
                continue

            table.put_item(Item=item)
            logger.info(
                "Wrote event_id=%s (patient_id=%s, event_type=%s) to DynamoDB",
                item["event_id"], item["patient_id"], item["event_type"],
            )

        except Exception:
            logger.exception("Unhandled error processing messageId=%s", message_id)
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}