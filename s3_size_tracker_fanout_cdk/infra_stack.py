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

        # ── S3 Bucket ──
        self.bucket = s3.Bucket(self, "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── DynamoDB Table ──
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

        # ── Size-Tracking Lambda ──
        size_tracking = _lambda.Function(self, "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="size_tracking.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": self.table.table_name,
            },
        )
        self.bucket.grant_read(size_tracking)
        self.table.grant_read_write_data(size_tracking)
        size_tracking.add_event_source(
            lambda_events.SqsEventSource(size_tracking_queue, batch_size=1)
        )

        # ── Logging Lambda ──
        logging_log_group = logs.LogGroup(self, "LoggingLogGroup",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_WEEK,
        )

        logging_lambda = _lambda.Function(self, "LoggingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="logging_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            log_group=logging_log_group,
            environment={
                "LOG_GROUP_NAME": logging_log_group.log_group_name,
            },
        )
        logging_lambda.add_event_source(
            lambda_events.SqsEventSource(logging_queue, batch_size=1)
        )
        logging_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["logs:FilterLogEvents"],
            resources=[logging_log_group.log_group_arn],
        ))

        # ── CloudWatch Metric Filter ──
        metric_filter = logs.MetricFilter(self, "SizeDeltaMetricFilter",
            log_group=logging_log_group,
            filter_pattern=logs.FilterPattern.exists("$.size_delta"),
            metric_namespace="Assignment4App",
            metric_name="TotalObjectSize",
            metric_value="$.size_delta",
            default_value=0,
        )

        # ── CloudWatch Alarm ──
        total_size_metric = cloudwatch.Metric(
            namespace="Assignment4App",
            metric_name="TotalObjectSize",
            statistic="Sum",
            period=Duration.seconds(60),
        )

        alarm = cloudwatch.Alarm(self, "TotalSizeAlarm",
            metric=total_size_metric,
            threshold=20,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # ── Cleaner Lambda ──
        cleaner_lambda = _lambda.Function(self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="cleaner.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
            },
        )
        self.bucket.grant_read_write(cleaner_lambda)

        # Alarm -> Cleaner Lambda
        alarm.add_alarm_action(cw_actions.LambdaAction(cleaner_lambda))

        # ── Plotting Lambda ──
        matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "MatplotlibLayer",
            f"arn:aws:lambda:{self.region}:{self.account}:layer:matplotlib-layer:4",
        )

        self.plotting_lambda = _lambda.Function(self, "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="plotting.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            layers=[matplotlib_layer],
            environment={
                "TABLE_NAME": self.table.table_name,
                "BUCKET_NAME": self.bucket.bucket_name,
            },
        )
        self.bucket.grant_write(self.plotting_lambda)
        self.table.grant_read_data(self.plotting_lambda)