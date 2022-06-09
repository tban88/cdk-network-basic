from email.headerregistry import Group
from unicodedata import name
from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_elasticloadbalancingv2 as elb
    # aws_sqs as sqs,
)
from constructs import Construct

class CdkNetworkBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

# GLOBAL CONFIG  
        # Global variables (if any)
        ports = {"HTTPS":443, "HTTP":80, "SSL":22, "JENKINS":8080, "VPN":943}

# NETWORK 
       # Lookup for an existing default vpc and save it just in VPN case 
        vpc = ec2.Vpc.from_lookup(
            self,
            'VPC',
            is_default=True
        )

        # Create new VPC
        vpc2 = ec2.Vpc(
            self, 
            id='DEVOPS-VPN',
            vpc_name="DEVOPS-VPN",
            cidr='10.10.10.0/24',
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name='DEVOPS-PUBLIC-', 
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=26
                ),
                ec2.SubnetConfiguration(
                    name='DEVOPS-PRIVATE-',
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=26
                )
            ],
            nat_gateways=1
        )

# SECURITY
        # Create global security group + add inbound rules
        securitygroup = ec2.SecurityGroup(
            self, 
            'WEB-ACCESS-DEVOPS',
            vpc=vpc2, 
            allow_all_outbound=True,
            security_group_name="WEB-SSH-VPN-JENKINS"
        )

        for name in ports:
            securitygroup.add_ingress_rule(
             ec2.Peer.any_ipv4(),
             ec2.Port.tcp(int(ports[name])),
             description="Allows traffic through port {port} - {app}".format(port=ports[name], app=name)
            ) 

# IDENTITY
        # Create new roles for codedeploy: ServiceRole > AWSCodeDeployRole (AWS managed) | EC2 > AmazonEC2RoleforAWSCodeDeploy (AWS managed)
        ServiceRole = iam.Role(
            self,
            'CodeDeploy-Service',
            role_name='CodeDeploy-ServiceRole',
            assumed_by=iam.ServicePrincipal('codedeploy.amazonaws.com')
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
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com')
        )   

        EC2Role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                id='ec2-policy',
                managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforAWSCodeDeploy"
            )
        )

        InstanceProfile = iam.CfnInstanceProfile(
            self,
            id="ec2-instance-profile",
            instance_profile_name="CodeDeploy-EC2",
            roles=["CodeDeploy-EC2"]
        ) 

# EC2 LOAD BALANCER
        # Create new target group - TG1 private
        tg1 = elb.ApplicationTargetGroup(
            self,
            id="id-tg-gorito-priv",
            target_group_name="gorito-private",
            vpc=vpc2,
            port=80,
            target_type=elb.TargetType.INSTANCE,
            deregistration_delay=Duration.seconds(10),
            protocol=elb.ApplicationProtocol.HTTP
        )

        # Create new target group - TG2 public
        tg2 = elb.ApplicationTargetGroup(
            self,
            id="id-tg-gorito-pub",
            target_group_name="gorito-public",
            vpc=vpc2,
            port=80,
            target_type=elb.TargetType.INSTANCE,
            deregistration_delay=Duration.seconds(10),
            protocol=elb.ApplicationProtocol.HTTP
        )

        # Create public ELB1
        lb = elb.ApplicationLoadBalancer(
            self,
            id="id_elb_devops_pub",
            load_balancer_name="web-public",
            vpc=vpc2,
            internet_facing=True,
            security_group=securitygroup
        )

        # Create private ELB2
        lb2 = elb.ApplicationLoadBalancer(
            self,
            id="id_elb_devops_priv",
            load_balancer_name="web-private",
            vpc=vpc2,
            internet_facing=False,
            security_group=securitygroup
        )

        # Configure listener for ELB1
        listener=lb.add_listener(
            id="id-listener-web",
            port=80,
            open=True
        )

        # Configure listener for ELB2
        listener2=lb2.add_listener(
            id="id-listener-web",
            port=80,
            open=True
        )

        # Append TG2 to ELB1 - PUBLIC
        listener.add_target_groups(
            id="id_elb_listener_tg2",
            target_groups=[tg2]
        )

        # Append TG1 to ELB2 - PRIVATE
        listener2.add_target_groups(
            id="id_elb_listener_tg1",
            target_groups=[tg1]
        )