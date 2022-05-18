import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_network_basic.cdk_network_basic_stack import CdkNetworkBasicStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_network_basic/cdk_network_basic_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkNetworkBasicStack(app, "cdk-network-basic")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
