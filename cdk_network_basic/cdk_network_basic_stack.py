from email.headerregistry import Group
from unicodedata import name
from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam
    # aws_sqs as sqs,
)
from constructs import Construct

class CdkNetworkBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    
        #define aws account details and name of the repo
        account='XXX'
        region = 'XX'

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
            id='devops-vpc',
            vpc_name="devops-vpc",
            cidr='10.10.10.0/24',
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name='DevOps-PUBLIC', 
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=26
                ),
                ec2.SubnetConfiguration(
                    name='DevOps-PRIVATE',
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
            allow_all_outbound=True,
            security_group_name="WEB-SSH-VPN-JENKINS"
        )

        #add inbound rules to newly created SG
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            description='Allow traffic through port 80 - HTTP'
        )
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            description='Allow traffic through port 443 - HTTPS'
        )
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            description='Allow traffic through port 22 - SSH'
        )
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(8080),
            description='Allow traffic through port 8080 - Jenkins'
        )
        securitygroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(943),
            description='Allow traffic through port 943 - VPN'
        )

        #create new roles for codedeploy: ServiceRole > AWSCodeDeployRole (AWS managed) | EC2 > 
        ServiceRole = iam.Role(
            self,
            'CodeDeploy-Service',
            role_name='CodeDeploy-ServiceRole',
            assumed_by=iam.ServicePrincipal('codedeploy.amazonaws.com'),
        )

        ServiceRole.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(
                                        self,
                                        id='service-id',
                                        managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
                                        )
        )

        EC2Role = iam.Role(
            self,
            'CodeDeploy-EC2',
            role_name='CodeDeploy-EC2',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
        )
        
        EC2Role.add_managed_policy(iam.ManagedPolicy.from_managed_policy_arn(
                                    self,
                                    id='ec2-id',
                                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforAWSCodeDeploy"
                                    )
        )
