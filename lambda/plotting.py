import boto3
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
BUCKET_NAME = os.environ["BUCKET_NAME"]


def lambda_handler(event, context):
    # Query last 10 minutes of data (covers the full driver run)
    now = datetime.utcnow()
    window_start = (now - timedelta(minutes=10)).isoformat()

    response = table.query(
        KeyConditionExpression=(
            Key("bucket_name").eq(BUCKET_NAME)
            & Key("timestamp").gte(window_start)
        )
    )
    items = response["Items"]

    # Get global max
    max_response = table.get_item(
        Key={"bucket_name": "GLOBAL_MAX", "timestamp": "MAX"}
    )
    global_max = max_response["Item"]["total_size"] if "Item" in max_response else 0

    # Plot
    timestamps = [item["timestamp"][11:19] for item in items]
    sizes = [int(item["total_size"]) for item in items]

    plt.figure()
    plt.plot(timestamps, sizes, marker="o")
    plt.axhline(y=int(global_max), linestyle="--", label="Historical high")
    plt.xlabel("Timestamp")
    plt.ylabel("Total Bucket Size (bytes)")
    plt.title("S3 Bucket Size Over Time")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("/tmp/plot.png")
    plt.close()

    s3.upload_file("/tmp/plot.png", BUCKET_NAME, "plot.png")

    return {"statusCode": 200, "body": "Plot generated successfully"}