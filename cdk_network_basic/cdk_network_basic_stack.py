from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2
    # aws_sqs as sqs,
)
from constructs import Construct

class CdkNetworkBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    
        #define aws account details and name of the repo
        account='905781841335'
        region = 'us-east-1'

        # The code that defines your stack goes here

       #lookup for an existing vpc
        vpc = ec2.Vpc.from_lookup(
            self,
            'VPC',
            is_default=True
        )

        #create new vpc
        vpc2 = ec2.Vpc(
            self, 
            'devops-vpc',
            cidr='10.10.10.0/24',
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name='devops-public-01', 
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=26
                ),
                ec2.SubnetConfiguration(
                    name='devops-private-01',
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=26
                )
            ],
            nat_gateways=1
        )

        #create new security group and allow all outbound traffic (enabled by default)
        securitygroup = ec2.SecurityGroup(
            self, 
            'web-access-devops',
            vpc=vpc2, 
            allow_all_outbound=True
        )

        #add inbound rules to newly created SG
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            description='Allow traffic through port 80'
        )
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            description='Allow traffic through port 443'
        )
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            description='Allow traffic through port 22'
        )