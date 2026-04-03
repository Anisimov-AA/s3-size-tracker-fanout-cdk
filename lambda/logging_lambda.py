import boto3
import json
import os
import time

logs_client = boto3.client("logs")
LOG_GROUP_NAME = os.environ["LOG_GROUP_NAME"]


def get_creation_size(object_key):
    """Search own CloudWatch logs for the creation event of this object."""
    # Small delay to let recent logs become searchable
    time.sleep(2)

    filter_pattern = f'{{ $.object_name = "{object_key}" && $.size_delta > 0 }}'

    response = logs_client.filter_log_events(
        logGroupName=LOG_GROUP_NAME,
        filterPattern=filter_pattern,
    )

    # Walk events newest-first to get the latest creation size
    for evt in reversed(response.get("events", [])):
        try:
            msg = json.loads(evt["message"])
            if msg.get("size_delta", 0) > 0:
                return msg["size_delta"]
        except (json.JSONDecodeError, KeyError):
            continue

    return 0  # fallback if not found


def lambda_handler(event, context):
    for record in event["Records"]:
        # Parse: SQS body -> SNS message -> S3 event
        sns_message = json.loads(record["body"])
        s3_event = json.loads(sns_message["Message"])

        for s3_record in s3_event["Records"]:
            event_name = s3_record["eventName"]
            object_key = s3_record["s3"]["object"]["key"]

            if event_name.startswith("ObjectCreated"):
                size = s3_record["s3"]["object"]["size"]
                log_entry = {
                    "object_name": object_key,
                    "size_delta": size,
                }

            elif event_name.startswith("ObjectRemoved"):
                # S3 delete events don't include size, look it up
                size = get_creation_size(object_key)
                log_entry = {
                    "object_name": object_key,
                    "size_delta": -size,
                }
            else:
                continue

            # print() writes to the lambda's CloudWatch log group
            print(json.dumps(log_entry))