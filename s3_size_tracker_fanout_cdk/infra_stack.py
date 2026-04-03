from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_s3_notifications as s3n,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_events,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_iam as iam,
)
from constructs import Construct


class InfraStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.bucket = s3.Bucket(self, "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.table = dynamodb.Table(self, "S3ObjectSizeHistory",
            partition_key=dynamodb.Attribute(
                name="bucket_name", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ── SNS Topic (fanout) ──
        topic = sns.Topic(self, "S3EventTopic")

        # ── SQS Queues ──
        size_tracking_queue = sqs.Queue(self, "SizeTrackingQueue",
            visibility_timeout=Duration.seconds(60),
        )
        logging_queue = sqs.Queue(self, "LoggingQueue",
            visibility_timeout=Duration.seconds(60),
        )

        # SNS -> SQS subscriptions
        topic.add_subscription(sns_subs.SqsSubscription(size_tracking_queue))
        topic.add_subscription(sns_subs.SqsSubscription(logging_queue))

        # S3 -> SNS notifications
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, s3n.SnsDestination(topic)
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED, s3n.SnsDestination(topic)
        )