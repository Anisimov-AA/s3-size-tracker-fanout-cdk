import aws_cdk as core
import aws_cdk.assertions as assertions

from s3_size_tracker_fanout_cdk.s3_size_tracker_fanout_cdk_stack import S3SizeTrackerFanoutCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in s3_size_tracker_fanout_cdk/s3_size_tracker_fanout_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = S3SizeTrackerFanoutCdkStack(app, "s3-size-tracker-fanout-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
