# Fortinet Autoscale Template Integration Guide

## Overview

This document explains how the zero-downtime upgrade system leverages the **Fortinet Autoscale Simplified Template** for intelligent infrastructure discovery. By understanding the specific naming conventions and architectural patterns from the template, the system can automatically discover and map existing infrastructure without manual configuration.

## Fortinet Template Naming Conventions

### Resource Naming Pattern
```
${customer_prefix}-${environment}-${resource_type}-${details}
```

**Examples:**
- VPC: `company-prod-inspection-vpc`
- Subnets: `company-prod-inspection-public-az1-subnet`
- ASG: `company-prod-fortigate-asg`

### Standard Resource Types
```
inspection_vpc          # Main security VPC containing FortiGates
management_vpc          # Optional dedicated management VPC
east_vpc               # East-West traffic inspection VPC
west_vpc               # East-West traffic inspection VPC
```

### Subnet Naming Patterns
```
inspection-public-az{x}-subnet     # Public subnets for NAT Gateways
inspection-private-az{x}-subnet    # Private subnets for FortiGates
inspection-gwlbe-az{x}-subnet      # GWLB Endpoint subnets
inspection-management-az{x}-subnet # Management interface subnets
```

## Enhanced Infrastructure Discovery

### 1. Customer Prefix and Environment Detection

The system extracts the customer prefix and environment from multiple sources:

#### Method A: ASG Tags
```python
# Look for standard tags on the ASG
tags_to_check = [
    'Customer_Prefix', 'CustomerPrefix', 'cp',
    'Environment', 'Env'
]
```

#### Method B: ASG Name Parsing
```python
# Parse ASG name patterns like: company-prod-fortigate-asg
parts = asg_name.split('-')
if len(parts) >= 4 and parts[-1] == 'asg':
    customer_prefix = parts[0]    # 'company' 
    environment = parts[1]        # 'prod'
```

#### Method C: VPC Name Analysis
```python
# Discover VPC via ASG subnets, analyze VPC name
# company-prod-inspection-vpc → cp='company', env='prod'
```

### 2. Automatic Resource Discovery

Once CP and ENV are identified, the system automatically discovers:

```python
# Generate expected resource names
inspection_vpc_name = f"{cp}-{env}-inspection-vpc"
east_vpc_name = f"{cp}-{env}-east-vpc"
west_vpc_name = f"{cp}-{env}-west-vpc"

# Discover via tag filters
vpc_response = ec2.describe_vpcs(
    Filters=[
        {'Name': 'tag:Name', 'Values': [inspection_vpc_name]},
        {'Name': 'state', 'Values': ['available']}
    ]
)
```

### 3. Subnet Classification

Subnets are automatically classified based on Fortinet naming patterns:

```python
def classify_subnet(subnet_name):
    if 'public' in subnet_name:
        return 'public'     # NAT Gateway subnets
    elif 'private' in subnet_name:
        return 'private'    # FortiGate data interfaces
    elif 'gwlbe' in subnet_name:
        return 'gwlbe'      # GWLB Endpoint subnets
    elif 'management' in subnet_name:
        return 'management' # FortiGate management interfaces
```

### 4. Transit Gateway Discovery

```python
# Find TGW attachment for inspection VPC
attachments = ec2.describe_transit_gateway_vpc_attachments(
    Filters=[
        {'Name': 'vpc-id', 'Values': [inspection_vpc_id]},
        {'Name': 'state', 'Values': ['available']}
    ]
)

# Extract TGW ID and discover route table associations
tgw_id = attachment['TransitGatewayId']
```

### 5. Customer VPC Discovery

```python
# Method 1: Look for East/West VPCs (common in Fortinet template)
for vpc_type in ['east_vpc', 'west_vpc']:
    vpc_name = f"{cp}-{env}-{vpc_type.replace('_vpc', '')}-vpc"
    # Discover via tag name filter

# Method 2: Find all VPCs attached to same TGW
all_attachments = ec2.describe_transit_gateway_vpc_attachments(
    Filters=[
        {'Name': 'transit-gateway-id', 'Values': [tgw_id]},
        {'Name': 'state', 'Values': ['available']}
    ]
)
# Filter out inspection VPC to get customer VPCs
```

## Configuration Examples

### Discovered Infrastructure Output
```json
{
  "discovery_metadata": {
    "source": "fortinet_autoscale_template",
    "customer_prefix": "company",
    "environment": "prod",
    "source_asg": "company-prod-fortigate-asg"
  },
  "blue_environment": {
    "vpc_id": "vpc-12345",
    "vpc_cidr": "10.100.0.0/16", 
    "asg_name": "company-prod-fortigate-asg",
    "production_eips": {
      "eipalloc-123": {
        "public_ip": "203.0.113.10",
        "availability_zone": "us-east-1a"
      }
    }
  },
  "transit_gateway": {
    "tgw_id": "tgw-abcdef123",
    "inspection_attachment_id": "tgw-attach-12345"
  },
  "customer_vpcs": [
    {
      "vpc_id": "vpc-customer-east",
      "vpc_name": "company-prod-east-vpc",
      "vpc_type": "east",
      "priority": "high"
    }
  ]
}
```

### Generated Green Deployment Config
```json
{
  "green_deployment_config": {
    "vpc_name": "security-green-vpc",
    "vpc_cidr": "10.100.0.0/16",
    "terraform_module_source": "../terraform-aws-cloud-modules/modules/fortigate/fgt_asg",
    "reuse_blue_parameters": {
      "customer_prefix": "company",
      "environment": "green",
      "instance_type": "c6i.xlarge",
      "network_configuration": "identical_to_blue"
    }
  }
}
```

## Terraform Integration

### Blue Environment Reference
```hcl
# Reference existing Blue infrastructure
data "aws_autoscaling_group" "blue_asg" {
  name = var.blue_asg_name
}

data "aws_vpc" "blue_inspection_vpc" {
  filter {
    name   = "tag:Name"
    values = ["${var.customer_prefix}-${var.environment}-inspection-vpc"]
  }
}

data "aws_subnets" "blue_private_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.blue_inspection_vpc.id]
  }
  filter {
    name   = "tag:Name"
    values = ["${var.customer_prefix}-${var.environment}-inspection-private-*"]
  }
}
```

### Green Environment Deployment
```hcl
# Deploy identical Green environment with new AMI
module "green_security_vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${var.customer_prefix}-green-inspection-vpc"
  cidr = data.aws_vpc.blue_inspection_vpc.cidr_block  # Same CIDR
  
  # Identical subnet layout to Blue
  azs             = data.aws_availability_zones.available.names
  private_subnets = [for subnet in data.aws_subnets.blue_private_subnets.cidr_blocks : subnet]
  public_subnets  = [for subnet in data.aws_subnets.blue_public_subnets.cidr_blocks : subnet]
}

module "green_fortigate_asg" {
  source = "../../terraform-aws-cloud-modules/modules/fortigate/fgt_asg"
  
  # Same configuration as Blue except AMI
  vpc_id          = module.green_security_vpc.vpc_id
  ami_id          = var.target_fortigate_ami  # NEW AMI
  instance_type   = var.fortigate_instance_type
  asg_name        = "${var.customer_prefix}-green-fortigate-asg"
  
  # Copy network configuration from Blue
  network_interfaces = data.terraform_remote_state.blue.outputs.network_interfaces
}
```

## CLI Usage Examples

### Basic Discovery
```bash
# Discover infrastructure from ASG name
./scripts/intelligent-upgrade-cli.py discover \
  --asg-name company-prod-fortigate-asg \
  --region us-east-1 \
  --output discovered-infrastructure.json
```

### Full Upgrade Workflow
```bash
# Complete zero-downtime upgrade
./scripts/intelligent-upgrade-cli.py upgrade \
  --asg-name company-prod-fortigate-asg \
  --target-ami ami-fortigate-7.4.5 \
  --region us-east-1 \
  --upgrade-id company-prod-upgrade-001
```

### Validation Only
```bash
# Validate discovered infrastructure
./scripts/intelligent-upgrade-cli.py validate \
  --config-file discovered-infrastructure.json
```

## Fallback Discovery

If Fortinet template patterns are not detected, the system falls back to generic discovery:

```python
def _fallback_generic_discovery(self, asg_name):
    """
    Fallback to generic AWS resource discovery
    """
    # Discover via ASG → VPC → TGW relationships
    # Use generic naming pattern analysis
    # Prompt for manual configuration if needed
    
    return generic_infrastructure_config
```

## Benefits of Template Integration

### 1. **Zero Configuration**
- Automatic discovery from single ASG name
- No manual infrastructure mapping required
- Leverages known Fortinet deployment patterns

### 2. **Accurate Resource Identification**
- Understands Fortinet-specific resource relationships
- Correctly identifies FortiGate vs customer infrastructure
- Proper subnet classification (public, private, GWLB, management)

### 3. **Intelligent Migration Planning**
- Prioritizes VPCs based on naming conventions
- Estimates validation times based on VPC types
- Generates appropriate rollback strategies

### 4. **Seamless Green Deployment**
- Reuses exact Blue configuration with new AMI
- Maintains identical network layout and IP addressing
- Ensures configuration compatibility

## Troubleshooting Discovery Issues

### Issue: CP/ENV Not Detected
```bash
# Check ASG tags
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names your-asg-name \
  --query 'AutoScalingGroups[0].Tags'

# Check VPC tags
aws ec2 describe-vpcs \
  --vpc-ids vpc-12345 \
  --query 'Vpcs[0].Tags'
```

### Issue: No Customer VPCs Found  
```bash
# Check TGW attachments
aws ec2 describe-transit-gateway-vpc-attachments \
  --filters Name=transit-gateway-id,Values=tgw-12345 \
  --query 'TransitGatewayVpcAttachments[].VpcId'
```

### Issue: GWLB Not Discovered
```bash
# Check for Gateway Load Balancers
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?Type==`gateway`]'
```

This intelligent discovery system eliminates the complexity of manual infrastructure mapping while ensuring compatibility with existing Fortinet deployments.