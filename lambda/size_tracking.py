import boto3
import json
from datetime import datetime
import os

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def lambda_handler(event, context):
    for record in event["Records"]:
        # Parse: SQS body -> SNS message -> S3 event
        sns_message = json.loads(record["body"])
        s3_event = json.loads(sns_message["Message"])

        bucket_name = s3_event["Records"][0]["s3"]["bucket"]["name"]

        # Calculate total size & count
        total_size = 0
        count = 0
        response = s3.list_objects_v2(Bucket=bucket_name)
        for obj in response.get("Contents", []):
            total_size += obj["Size"]
            count += 1

        timestamp = datetime.utcnow().isoformat()

        table.put_item(Item={
            "bucket_name": bucket_name,
            "timestamp": timestamp,
            "total_size": total_size,
            "object_count": count,
        })

        # Update global max
        resp = table.get_item(
            Key={"bucket_name": "GLOBAL_MAX", "timestamp": "MAX"}
        )
        curr_max = resp.get("Item", {}).get("total_size", 0)

        if total_size > curr_max:
            table.put_item(Item={
                "bucket_name": "GLOBAL_MAX",
                "timestamp": "MAX",
                "total_size": total_size,
            })