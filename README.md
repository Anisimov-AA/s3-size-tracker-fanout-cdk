# s3-size-tracker-fanout-cdk

S3 bucket size tracker with SNS/SQS fanout, CloudWatch alarm, and auto-cleanup.

Built with AWS CDK (Python).

## What it does

S3 events go through SNS → SQS fanout to two consumers:
- **Size-tracking lambda** — records bucket size to DynamoDB over time
- **Logging lambda** — logs object size changes to CloudWatch

A CloudWatch metric filter watches the logs. When total size exceeds the threshold, an alarm triggers a cleaner lambda that deletes the largest object.

A plotting lambda generates a chart of bucket size over time.

## Setup

Install CDK CLI (if you don't have it):
```
npm install -g aws-cdk
```

Create venv and install deps:
```
python -m venv .venv
```

Activate it:
```
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install requirements:
```
pip install -r requirements.txt
```

Check everything works:
```
cdk synth
```

## Deploy

```
cdk deploy --all
```

## How to run

1. Open AWS Lambda console
2. Find DriverLambda (in ApiStack)
3. Invoke with test event `{}`
4. Wait ~5 min (there are sleeps between operations)
5. Download `plot.png` from the S3 bucket to see the result

## Clean up

```
cdk destroy --all
```

## Note on CloudWatch SUM

The second alarm may not fire because CloudWatch SUM only aggregates within a single evaluation period (60s). If two events land in different periods, they don't get summed together. This is a known CloudWatch limitation.
