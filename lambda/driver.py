import boto3
import time
import urllib.request
import os

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]
API_URL = os.environ["API_URL"]


def lambda_handler(event, context):
    # 1. Create assignment1.txt (18 bytes)
    s3.put_object(Bucket=BUCKET_NAME, Key="assignment1.txt", Body="Empty Assignment 1")
    print("Created assignment1.txt (18 bytes)")
    time.sleep(5)

    # 2. Create assignment2.txt (28 bytes)
    #    Bucket total = 18 + 28 = 46 bytes -> alarm should fire
    #    Cleaner deletes assignment2.txt (largest)
    s3.put_object(Bucket=BUCKET_NAME, Key="assignment2.txt", Body="Empty Assignment 2222222222")
    print("Created assignment2.txt (28 bytes)")
    time.sleep(120)

    # 3. Create assignment3.txt (2 bytes)
    #    Bucket total = 18 + 2 = 20 bytes -> alarm may fire again
    #    Cleaner deletes assignment1.txt (largest)
    s3.put_object(Bucket=BUCKET_NAME, Key="assignment3.txt", Body="33")
    print("Created assignment3.txt (2 bytes)")
    time.sleep(120)

    # 4. Call plotting API
    print("Calling plotting API...")
    urllib.request.urlopen(API_URL)
    print("Done")