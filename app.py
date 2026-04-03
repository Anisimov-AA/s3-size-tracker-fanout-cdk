#!/usr/bin/env python3
import aws_cdk as cdk
from s3_size_tracker_fanout_cdk.infra_stack import InfraStack
from s3_size_tracker_fanout_cdk.api_stack import ApiStack

app = cdk.App()
infra = InfraStack(app, "InfraStack")
api = ApiStack(app, "ApiStack",
    plotting_lambda=infra.plotting_lambda,
    bucket=infra.bucket,
)
app.synth()