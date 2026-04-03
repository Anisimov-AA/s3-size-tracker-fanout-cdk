from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_s3 as s3,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 plotting_lambda: _lambda.Function,
                 bucket: s3.Bucket, **kwargs):
        super().__init__(scope, id, **kwargs)

        # REST API for plotting
        api = apigateway.RestApi(self, "PlottingApi")
        api.root.add_method("GET", apigateway.LambdaIntegration(plotting_lambda))

        # Driver Lambda
        self.driver_lambda = _lambda.Function(self, "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="driver.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(600),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "API_URL": api.url,
            },
        )
        bucket.grant_read_write(self.driver_lambda)