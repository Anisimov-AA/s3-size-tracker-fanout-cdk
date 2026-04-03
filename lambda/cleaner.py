import boto3
import os

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]


def lambda_handler(event, context):
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)

    if "Contents" not in response or len(response["Contents"]) == 0:
        print("Bucket is empty, nothing to clean.")
        return

    # Filter out plot.png so we only consider data objects
    objects = [obj for obj in response["Contents"] if obj["Key"] != "plot.png"]

    if not objects:
        print("No data objects to clean.")
        return

    largest = max(objects, key=lambda o: o["Size"])
    print(f"Deleting largest object: {largest['Key']} ({largest['Size']} bytes)")
    s3.delete_object(Bucket=BUCKET_NAME, Key=largest["Key"])