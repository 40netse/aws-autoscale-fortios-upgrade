# Zero-Downtime FortiGate Upgrade System - Technical Design

## Architecture Overview

This system achieves zero-downtime FortiGate upgrades through **intelligent infrastructure discovery**, **parallel VPC deployment**, **Transit Gateway route orchestration**, and **Elastic IP preservation**. The approach automatically understands existing infrastructure, deploys complete parallel environments, and uses atomic route switching to seamlessly migrate traffic.

## Core Innovation: Intelligent Discovery + Parallel Security VPCs

### Discovery-Driven Architecture Pattern
```
Step 1: Intelligent Discovery
FortiGate ASG Name → Complete Infrastructure Map

Step 2: Parallel Deployment  
                    ┌─ Security VPC Blue (Current: 10.100.0.0/16)
Customer VPCs ─ TGW ─┤
                    └─ Security VPC Green (Parallel: 10.100.0.0/16)

Step 3: Route Orchestration
Customer VPCs ─ TGW ─→ Security VPC Green (Atomic Switch)
```

### Key Design Principles

#### 1. **Intelligent Infrastructure Discovery**
- **Fortinet Template Awareness**: Leverages Autoscale Simplified Template naming conventions
- **Automatic Resource Mapping**: Single ASG name discovers complete environment
- **Multi-Method Extraction**: Customer prefix and environment from ASG names/tags/VPC analysis
- **Comprehensive Discovery**: TGW, customer VPCs, production EIPs, GWLB configuration
- **Smart Migration Planning**: Automatic VPC prioritization and validation time estimation

#### 2. **Complete Infrastructure Isolation**
- **Separate VPCs**: Blue and Green environments in completely isolated VPCs
- **Identical Configuration**: Same CIDRs, IPs, and network layout
- **Independent Lifecycle**: Green deployed, tested, and cleaned up independently
- **No Shared Resources**: Zero dependencies between Blue and Green

#### 2. **Transit Gateway Route Orchestration**  
- **Centralized Control**: Single point for traffic routing decisions
- **Atomic Switching**: Route changes take effect in 2-5 seconds
- **Instant Rollback**: Single API call restores traffic to Blue
- **Gradual Migration**: Optional phased migration by customer VPC

#### 3. **Elastic IP Preservation**
- **Production IP Migration**: Move existing EIPs from Blue to Green
- **Whitelist Compatibility**: No external configuration changes required
- **Brief Migration Window**: 10-20 seconds per EIP during migration
- **Transparent to External Systems**: Partners and SaaS providers see no change

---

## Intelligent Infrastructure Discovery System

### Discovery Engine Architecture

The system includes a sophisticated discovery engine that automatically maps existing FortiGate infrastructure using Fortinet Autoscale Template patterns.

#### Discovery Workflow
```python
def intelligent_discovery_workflow(asg_name):
    """Complete infrastructure discovery from single ASG name"""
    
    # Step 1: Extract deployment patterns
    customer_prefix, environment = extract_cp_env_from_asg(asg_name)
    # Example: "company-prod-fortigate-asg" → cp="company", env="prod"
    
    # Step 2: Generate expected resource names using Fortinet patterns
    expected_resources = generate_fortinet_resource_names(cp, env)
    # Example: "company-prod-inspection-vpc", "company-prod-east-vpc"
    
    # Step 3: Discover infrastructure using AWS APIs
    infrastructure = discover_aws_resources(expected_resources)
    
    # Step 4: Map relationships and dependencies
    relationships = map_resource_relationships(infrastructure)
    
    # Step 5: Generate intelligent migration plan
    migration_plan = generate_migration_strategy(relationships)
    
    return complete_infrastructure_map
```

### Multi-Method Extraction Strategy

#### Method 1: ASG Tag Analysis (Preferred)
```python
# Extract from standardized tags
tags = {
    'Customer_Prefix': 'company',
    'Environment': 'prod',
    'Purpose': 'fortigate-security'
}
```

#### Method 2: ASG Name Pattern Recognition
```python
# Parse common patterns: cp-env-description-asg
asg_name = "company-prod-fortigate-asg"
parts = asg_name.split('-')
customer_prefix = parts[0]  # "company"
environment = parts[1]      # "prod"
```

#### Method 3: VPC Name Analysis via ASG Subnets
```python
# Trace ASG → Subnets → VPC → VPC Name → Extract CP/ENV
vpc_name = "company-prod-inspection-vpc"
# Parse to extract customer_prefix="company", environment="prod"
```

### Fortinet Template Pattern Recognition

#### Resource Name Patterns
```python
fortinet_patterns = {
    'inspection_vpc': '{cp}-{env}-inspection-vpc',
    'east_vpc': '{cp}-{env}-east-vpc',
    'west_vpc': '{cp}-{env}-west-vpc',
    'public_subnet_az1': '{cp}-{env}-inspection-public-az1-subnet',
    'private_subnet_az1': '{cp}-{env}-inspection-private-az1-subnet',
    'gwlbe_subnet_az1': '{cp}-{env}-inspection-gwlbe-az1-subnet'
}
```

#### Resource Discovery Process
```python
def discover_fortinet_resources(cp, env):
    """Discover resources using Fortinet naming patterns"""
    
    # Discover VPCs
    inspection_vpc = find_vpc(f"{cp}-{env}-inspection-vpc")
    customer_vpcs = [
        find_vpc(f"{cp}-{env}-east-vpc"),
        find_vpc(f"{cp}-{env}-west-vpc")
    ]
    
    # Discover TGW configuration
    tgw_config = discover_tgw_from_vpc(inspection_vpc)
    
    # Discover production EIPs
    nat_gateways = find_nat_gateways(inspection_vpc)
    production_eips = extract_eips_from_nat_gateways(nat_gateways)
    
    # Discover GWLB infrastructure
    gwlb_config = discover_gwlb_infrastructure(inspection_vpc)
    
    return comprehensive_infrastructure_map
```

### Discovery Output Structure
```json
{
  "discovery_metadata": {
    "source": "fortinet_autoscale_template",
    "customer_prefix": "company",
    "environment": "prod", 
    "discovery_method": "asg_name_parsing",
    "discovered_at": "2024-03-15T10:00:00Z"
  },
  "blue_environment": {
    "vpc_id": "vpc-blue-123",
    "asg_name": "company-prod-fortigate-asg",
    "production_eips": {...},
    "gwlb_config": {...}
  },
  "transit_gateway": {
    "tgw_id": "tgw-12345",
    "inspection_attachment_id": "tgw-attach-blue"
  },
  "customer_vpcs": [...],
  "migration_plan": {
    "strategy": "gradual_by_vpc_priority",
    "migration_order": [...]
  }
}
```

### Fallback Discovery Mechanisms

#### Generic AWS Discovery
When Fortinet patterns are not detected:
```python
def fallback_generic_discovery(asg_name):
    """Generic AWS resource discovery as fallback"""
    # Discover via ASG → VPC → TGW relationships
    # Use AWS resource tags and naming analysis
    # Prompt for manual configuration if needed
    return generic_infrastructure_map
```

#### Manual Override Capability
```json
{
  "discovery_override": {
    "manual_configuration": true,
    "blue_environment": {...},
    "customer_vpcs": [...],
    "production_eips": [...]
  }
}
```

---

## Infrastructure Components

### Blue Environment (Existing)
```
Security VPC Blue (vpc-blue-123): 10.100.0.0/16
├── Management Subnets
│   ├── subnet-blue-mgmt-1a: 10.100.1.0/24
│   ├── subnet-blue-mgmt-1b: 10.100.2.0/24
│   └── subnet-blue-mgmt-1c: 10.100.3.0/24
├── Private Subnets  
│   ├── subnet-blue-priv-1a: 10.100.11.0/24
│   ├── subnet-blue-priv-1b: 10.100.12.0/24
│   └── subnet-blue-priv-1c: 10.100.13.0/24
├── Public Subnets (NAT Gateways)
│   ├── subnet-blue-pub-1a: 10.100.21.0/24 → EIP-PROD-1
│   ├── subnet-blue-pub-1b: 10.100.22.0/24 → EIP-PROD-2  
│   └── subnet-blue-pub-1c: 10.100.23.0/24 → EIP-PROD-3
├── FortiGate ASG
│   ├── Instance 1a: mgmt=10.100.1.10, data=10.100.11.10
│   ├── Instance 1b: mgmt=10.100.2.10, data=10.100.12.10
│   └── Instance 1c: mgmt=10.100.3.10, data=10.100.13.10
├── GWLB Infrastructure
│   ├── GWLB: blue-gwlb
│   ├── Target Group: blue-fortigate-tg
│   └── Endpoints: vpce-blue-1a, vpce-blue-1b, vpce-blue-1c
└── TGW Attachment: tgw-attach-blue-security
```

### Green Environment (Parallel Deployment)
```
Security VPC Green (vpc-green-456): 10.100.0.0/16  ← SAME CIDR
├── Management Subnets (IDENTICAL)
│   ├── subnet-green-mgmt-1a: 10.100.1.0/24
│   ├── subnet-green-mgmt-1b: 10.100.2.0/24
│   └── subnet-green-mgmt-1c: 10.100.3.0/24
├── Private Subnets (IDENTICAL)
│   ├── subnet-green-priv-1a: 10.100.11.0/24
│   ├── subnet-green-priv-1b: 10.100.12.0/24
│   └── subnet-green-priv-1c: 10.100.13.0/24
├── Public Subnets (IDENTICAL)
│   ├── subnet-green-pub-1a: 10.100.21.0/24 → EIP-TEMP-1 (initially)
│   ├── subnet-green-pub-1b: 10.100.22.0/24 → EIP-TEMP-2 (initially)
│   └── subnet-green-pub-1c: 10.100.23.0/24 → EIP-TEMP-3 (initially)
├── FortiGate ASG (NEW AMI)
│   ├── Instance 1a: mgmt=10.100.1.10, data=10.100.11.10 ← SAME IPs
│   ├── Instance 1b: mgmt=10.100.2.10, data=10.100.12.10 ← SAME IPs
│   └── Instance 1c: mgmt=10.100.3.10, data=10.100.13.10 ← SAME IPs
├── GWLB Infrastructure (PARALLEL)
│   ├── GWLB: green-gwlb  
│   ├── Target Group: green-fortigate-tg
│   └── Endpoints: vpce-green-1a, vpce-green-1b, vpce-green-1c
└── TGW Attachment: tgw-attach-green-security
```

### Customer VPCs (Unchanged)
```
Customer VPC A (vpc-customer-a): 10.1.0.0/16
Customer VPC B (vpc-customer-b): 10.2.0.0/16  
Customer VPC C (vpc-customer-c): 10.3.0.0/16
├── Application instances (UNCHANGED)
├── Subnets and security groups (UNCHANGED)  
├── Route tables (UNCHANGED)
└── TGW Attachments (UNCHANGED)

Traffic routing controlled by TGW Route Tables ONLY
```

---

## Upgrade Workflow

### Phase 0: Intelligent Infrastructure Discovery
```python
def phase_0_intelligent_discovery(asg_name):
    """
    Comprehensive infrastructure discovery and validation
    """
    print(f"🔍 Starting intelligent discovery from ASG: {asg_name}")
    
    # 1. Initialize discovery engine
    discoverer = FortinetTemplateDiscovery(region)
    
    # 2. Execute comprehensive discovery
    infrastructure = discoverer.discover_from_asg_name(asg_name)
    
    # 3. Validate infrastructure readiness
    validation_results = validate_upgrade_readiness(infrastructure)
    
    # 4. Generate upgrade configuration
    upgrade_config = generate_upgrade_config(
        infrastructure=infrastructure,
        target_ami=target_ami_id
    )
    
    # 5. Create migration plan
    migration_plan = create_intelligent_migration_plan(
        customer_vpcs=infrastructure['customer_vpcs']
    )
    
    return {
        'infrastructure': infrastructure,
        'upgrade_config': upgrade_config,
        'migration_plan': migration_plan,
        'validation_passed': validation_results.success
    }
```

### Phase 1: Green Environment Deployment
```python
def deploy_green_environment():
    """
    Deploy complete parallel FortiGate infrastructure
    """
    # 1. Deploy Green Security VPC (identical to Blue)
    green_vpc = create_security_vpc(
        cidr="10.100.0.0/16",  # SAME as Blue
        name="security-green-vpc"
    )
    
    # 2. Deploy FortiGate ASG with new AMI
    green_asg = deploy_fortigate_asg(
        vpc_id=green_vpc.id,
        ami_id=new_fortigate_ami,
        instance_config=blue_instance_config  # SAME config
    )
    
    # 3. Deploy GWLB infrastructure  
    green_gwlb = deploy_gwlb_infrastructure(
        vpc_id=green_vpc.id,
        target_instances=green_asg.instances
    )
    
    # 4. Attach to Transit Gateway
    green_tgw_attachment = attach_to_transit_gateway(
        vpc_id=green_vpc.id,
        tgw_id=existing_tgw.id
    )
    
    return green_environment_details
```

### Phase 2: Canary Validation
```python
def validate_green_environment():
    """
    Test Green environment with controlled traffic
    """
    # 1. Create temporary TGW route table for testing
    test_route_table = create_tgw_route_table("green-canary-test")
    
    # 2. Route test traffic to Green environment
    add_route(test_route_table, "0.0.0.0/0", green_tgw_attachment)
    associate_test_vpc_with_route_table(test_vpc, test_route_table)
    
    # 3. Execute validation tests
    validation_results = run_validation_suite([
        connectivity_test(),
        security_policy_test(),
        performance_baseline_test(),
        fortigate_health_test()
    ])
    
    # 4. Cleanup test routing
    disassociate_test_vpc(test_vpc)
    delete_tgw_route_table(test_route_table)
    
    return validation_results
```

### Phase 3: Production Traffic Migration
```python
def migrate_production_traffic():
    """
    Atomic migration of production traffic to Green
    """
    # 1. Create Green production route table
    green_route_table = create_tgw_route_table("green-production")
    add_route(green_route_table, "0.0.0.0/0", green_tgw_attachment)
    
    # 2. Migrate customer VPC associations (can be gradual)
    customer_vpcs = get_customer_vpc_attachments()
    
    for vpc_attachment in customer_vpcs:
        # Switch TGW route table association
        migrate_vpc_to_green_routes(vpc_attachment, green_route_table)
        
        # Validate traffic flow through Green
        validate_vpc_connectivity(vpc_attachment)
        
        # Brief pause between migrations (optional)
        sleep(30)
    
    # 3. All traffic now flowing through Green environment
    return migration_complete
```

### Phase 4: EIP Migration  
```python
def migrate_production_eips():
    """
    Migrate production EIPs from Blue to Green NAT Gateways
    """
    blue_eips = get_production_eips_from_blue()
    green_nat_gateways = get_green_nat_gateways()
    
    for eip_id, blue_nat_id in blue_eips.items():
        # Get corresponding Green NAT Gateway
        az = get_az_for_nat_gateway(blue_nat_id)
        green_nat_id = get_green_nat_gateway_for_az(az)
        
        # Atomic EIP migration
        migrate_eip_atomic(eip_id, blue_nat_id, green_nat_id)
        
        # Validate EIP association
        validate_eip_migration(eip_id, green_nat_id)
    
    return eip_migration_complete
```

### Phase 5: Blue Environment Cleanup
```python
def cleanup_blue_environment():
    """
    Remove Blue environment after stability period
    """
    # 1. Validate Green environment stability
    monitor_green_stability(duration="24h")
    
    # 2. Clean up Blue TGW route table  
    delete_tgw_route_table(blue_route_table)
    
    # 3. Detach Blue VPC from TGW
    detach_vpc_from_tgw(blue_vpc_attachment)
    
    # 4. Destroy Blue Security VPC (via Terraform)
    terraform_destroy(blue_security_vpc_state)
    
    return cleanup_complete
```

---

## State Management & Rollback

### Upgrade State Tracking
```python
@dataclass
class UpgradeState:
    upgrade_id: str
    phase: str  # DEPLOYING_GREEN, VALIDATING, MIGRATING, MIGRATING_EIPS, COMPLETE
    blue_environment: BlueEnvironmentConfig
    green_environment: GreenEnvironmentConfig
    migration_progress: MigrationProgress
    rollback_data: RollbackData
    started_at: datetime
    
class BlueEnvironmentConfig:
    vpc_id: str
    tgw_attachment_id: str
    route_table_id: str
    eip_mappings: Dict[str, str]  # eip_id -> nat_gateway_id
    
class GreenEnvironmentConfig:  
    vpc_id: str
    tgw_attachment_id: str
    route_table_id: str
    temp_eip_mappings: Dict[str, str]
    
class MigrationProgress:
    completed_customer_vpcs: List[str]
    remaining_customer_vpcs: List[str]
    migrated_eips: List[str]
    
class RollbackData:
    original_vpc_route_associations: Dict[str, str]
    original_eip_associations: Dict[str, str]
```

### Emergency Rollback System
```python
def emergency_rollback(upgrade_id: str):
    """
    Immediate rollback to Blue environment (<60 seconds)
    """
    state = get_upgrade_state(upgrade_id)
    
    # 1. Restore TGW route table associations
    for vpc_attachment, blue_route_table in state.rollback_data.original_vpc_route_associations.items():
        associate_vpc_with_route_table(vpc_attachment, blue_route_table)
    
    # 2. Restore EIP associations (if EIPs were migrated)
    for eip_id, blue_nat_id in state.rollback_data.original_eip_associations.items():
        migrate_eip_atomic(eip_id, current_nat_id, blue_nat_id)
    
    # 3. Validate Blue environment health
    validate_blue_environment_connectivity()
    
    # 4. Update state and alert
    update_upgrade_state(upgrade_id, "ROLLED_BACK")
    send_rollback_notification(upgrade_id, rollback_reason)
    
    return "Rollback complete - traffic restored to Blue environment"
```

### Rollback Triggers
```python
class AutomaticRollbackTriggers:
    connectivity_failure = "any_customer_vpc_loses_internet"
    performance_degradation = "latency_increase_over_50_percent"  
    security_policy_violation = "blocked_traffic_passes_through"
    fortigate_health_failure = "any_fortigate_instance_unhealthy"
    eip_migration_failure = "eip_association_fails"
```

---

## Terraform Architecture

### Directory Structure
```
terraform/
├── shared-infrastructure/           # TGW, Customer VPCs (unchanged)
│   ├── main.tf
│   ├── outputs.tf
│   └── terraform.tfstate           # Shared resources - never touched
├── blue-security-vpc/              # Current FortiGate deployment
│   ├── main.tf                     
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfstate           # Blue environment state
└── green-security-vpc/             # Parallel deployment
    ├── main.tf                     # IDENTICAL to Blue (different AMI)
    ├── variables.tf
    ├── outputs.tf
    └── terraform.tfstate           # Independent Green state
```

### Blue Security VPC Configuration
```hcl
# terraform/blue-security-vpc/main.tf
module "security_vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "security-blue-vpc"
  cidr = "10.100.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.100.11.0/24", "10.100.12.0/24", "10.100.13.0/24"]
  public_subnets  = ["10.100.21.0/24", "10.100.22.0/24", "10.100.23.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Environment = "blue"
    Purpose     = "fortigate-security"
  }
}

module "fortigate_asg" {
  source = "../../terraform-aws-cloud-modules/modules/fortigate/fgt_asg"
  
  vpc_id          = module.security_vpc.vpc_id
  ami_id          = var.fortigate_ami_id
  instance_type   = "c6i.xlarge"
  asg_name        = "blue-fortigate-asg"
  
  # Network configuration
  network_interfaces = {
    mgmt = {
      device_index     = 0
      subnet_ids       = module.security_vpc.private_subnets
      security_groups  = [aws_security_group.fortigate_mgmt.id]
    }
    data = {
      device_index     = 1  
      subnet_ids       = module.security_vpc.private_subnets
      security_groups  = [aws_security_group.fortigate_data.id]
    }
  }
}

# TGW Attachment
resource "aws_ec2_transit_gateway_vpc_attachment" "blue_security" {
  transit_gateway_id = data.aws_ec2_transit_gateway.main.id
  vpc_id            = module.security_vpc.vpc_id
  subnet_ids        = module.security_vpc.private_subnets
  
  tags = {
    Name = "blue-security-attachment"
  }
}
```

### Green Security VPC Configuration  
```hcl
# terraform/green-security-vpc/main.tf
# IDENTICAL to Blue except for naming and AMI
module "security_vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "security-green-vpc"
  cidr = "10.100.0.0/16"              # SAME CIDR as Blue
  
  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.100.11.0/24", "10.100.12.0/24", "10.100.13.0/24"]  # SAME
  public_subnets  = ["10.100.21.0/24", "10.100.22.0/24", "10.100.23.0/24"]  # SAME
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Environment = "green"
    Purpose     = "fortigate-security"
  }
}

module "fortigate_asg" {
  source = "../../terraform-aws-cloud-modules/modules/fortigate/fgt_asg"
  
  vpc_id          = module.security_vpc.vpc_id
  ami_id          = var.new_fortigate_ami_id      # ONLY CHANGE: New AMI
  instance_type   = "c6i.xlarge"                  # SAME
  asg_name        = "green-fortigate-asg"
  
  # Network configuration (IDENTICAL to Blue)
  network_interfaces = {
    mgmt = {
      device_index     = 0
      subnet_ids       = module.security_vpc.private_subnets
      security_groups  = [aws_security_group.fortigate_mgmt.id]
    }
    data = {
      device_index     = 1
      subnet_ids       = module.security_vpc.private_subnets  
      security_groups  = [aws_security_group.fortigate_data.id]
    }
  }
}
```

---

## Lambda Functions

### 1. Infrastructure Discovery Engine
```python
# lambda/infrastructure-discovery/main.py
def lambda_handler(event, context):
    """
    Intelligent infrastructure discovery from FortiGate ASG name
    """
    asg_name = event['asg_name']
    region = event.get('region', 'us-east-1')
    
    # Initialize Fortinet-aware discovery engine
    discoverer = FortinetTemplateDiscovery(region)
    
    # Execute comprehensive discovery
    infrastructure = discoverer.discover_from_asg_name(asg_name)
    
    # Validate discovery results
    validation = validate_discovered_infrastructure(infrastructure)
    
    # Generate migration strategy
    migration_plan = generate_intelligent_migration_plan(infrastructure)
    
    return {
        'statusCode': 200,
        'discovered_infrastructure': infrastructure,
        'validation_results': validation,
        'migration_plan': migration_plan
    }
```

### 2. Parallel Deployer
```python
# lambda/parallel-deployer/main.py
def lambda_handler(event, context):
    """
    Deploy Green environment in parallel to Blue
    """
    blue_config = event['blue_environment_config']
    target_ami = event['target_fortigate_ami']
    
    # Deploy Green Security VPC
    green_deployment = deploy_green_security_vpc(
        blue_config=blue_config,
        target_ami=target_ami
    )
    
    # Wait for deployment completion
    wait_for_deployment_ready(green_deployment)
    
    # Validate Green environment health
    health_check = validate_green_environment(green_deployment)
    
    return {
        'statusCode': 200,
        'green_environment': green_deployment,
        'health_status': health_check
    }
```

### 2. TGW Orchestrator
```python
# lambda/tgw-orchestrator/main.py  
def lambda_handler(event, context):
    """
    Orchestrate Transit Gateway route changes
    """
    action = event['action']  # 'migrate', 'rollback'
    upgrade_state = event['upgrade_state']
    
    if action == 'migrate':
        result = migrate_customer_vpcs_to_green(upgrade_state)
    elif action == 'rollback':
        result = rollback_customer_vpcs_to_blue(upgrade_state)
    
    return {
        'statusCode': 200,
        'migration_result': result,
        'updated_state': upgrade_state
    }
```

### 3. EIP Migrator
```python
# lambda/eip-migrator/main.py
def lambda_handler(event, context):
    """
    Migrate production EIPs from Blue to Green NAT Gateways
    """
    blue_eips = event['blue_eip_mappings']
    green_nat_gateways = event['green_nat_gateways']
    
    migration_results = []
    
    for eip_id, blue_nat_id in blue_eips.items():
        # Find corresponding Green NAT Gateway
        green_nat_id = find_green_nat_for_blue_nat(blue_nat_id, green_nat_gateways)
        
        # Perform atomic migration
        migration_result = migrate_eip_atomic(eip_id, blue_nat_id, green_nat_id)
        migration_results.append(migration_result)
    
    return {
        'statusCode': 200,
        'eip_migrations': migration_results
    }
```

### 4. Validation Engine
```python
# lambda/validation-engine/main.py
def lambda_handler(event, context):
    """
    Comprehensive validation of Green environment
    """
    green_environment = event['green_environment']
    validation_config = event['validation_config']
    
    validation_results = run_validation_suite([
        connectivity_validation(green_environment),
        security_policy_validation(green_environment),
        performance_validation(green_environment),
        fortigate_health_validation(green_environment)
    ])
    
    # Determine if validation passed
    overall_status = all(test.passed for test in validation_results)
    
    return {
        'statusCode': 200,
        'validation_passed': overall_status,
        'detailed_results': validation_results
    }
```

### 5. Cleanup Manager
```python
# lambda/cleanup-manager/main.py
def lambda_handler(event, context):
    """
    Clean up Blue environment after successful migration
    """
    blue_environment = event['blue_environment']
    cleanup_delay = event.get('cleanup_delay', '24h')
    
    # Wait for stability period
    if not stability_period_elapsed(cleanup_delay):
        return schedule_cleanup_retry(event)
    
    # Validate Green environment still healthy
    green_health = validate_green_environment_health()
    if not green_health.healthy:
        return abort_cleanup("Green environment unhealthy")
    
    # Perform cleanup
    cleanup_result = cleanup_blue_infrastructure(blue_environment)
    
    return {
        'statusCode': 200, 
        'cleanup_result': cleanup_result
    }
```

---

## Step Function Workflows

### Main Upgrade Orchestrator
```json
{
  "Comment": "Zero-downtime FortiGate upgrade orchestrator with intelligent discovery",
  "StartAt": "IntelligentInfrastructureDiscovery",
  "States": {
    "IntelligentInfrastructureDiscovery": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:infrastructure-discovery",
      "Next": "ValidateDiscoveredInfrastructure",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "DiscoveryFailed"
      }]
    },
    "ValidateDiscoveredInfrastructure": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.validation_results.passed",
        "BooleanEquals": true,
        "Next": "DeployGreenEnvironment"
      }],
      "Default": "InfrastructureValidationFailed"
    },
    "DeployGreenEnvironment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:parallel-deployer",
      "Next": "ValidateGreenEnvironment",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "CleanupFailedGreen"
      }]
    },
    "ValidateGreenEnvironment": {
      "Type": "Task", 
      "Resource": "arn:aws:lambda:region:account:function:validation-engine",
      "Next": "ValidationApproval",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "CleanupFailedGreen"  
      }]
    },
    "ValidationApproval": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.validation_passed",
        "BooleanEquals": true,
        "Next": "MigrateTrafficToGreen"
      }],
      "Default": "CleanupFailedGreen"
    },
    "MigrateTrafficToGreen": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:tgw-orchestrator", 
      "Parameters": {
        "action": "migrate"
      },
      "Next": "MigrateProductionEIPs",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "EmergencyRollback"
      }]
    },
    "MigrateProductionEIPs": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:eip-migrator",
      "Next": "ValidateProductionTraffic",
      "Catch": [{
        "ErrorEquals": ["States.ALL"], 
        "Next": "EmergencyRollback"
      }]
    },
    "ValidateProductionTraffic": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:validation-engine",
      "Next": "ProductionValidationCheck",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "EmergencyRollback"
      }]
    },
    "ProductionValidationCheck": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.validation_passed",
        "BooleanEquals": true,
        "Next": "ScheduleBlueCleanup"
      }],
      "Default": "EmergencyRollback"
    },
    "ScheduleBlueCleanup": {
      "Type": "Wait",
      "Seconds": 86400,
      "Next": "CleanupBlueEnvironment"
    },
    "CleanupBlueEnvironment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:cleanup-manager",
      "Next": "UpgradeComplete"
    },
    "UpgradeComplete": {
      "Type": "Succeed"
    },
    "EmergencyRollback": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:tgw-orchestrator",
      "Parameters": {
        "action": "rollback"
      },
      "Next": "RollbackComplete"
    },
    "RollbackComplete": {
      "Type": "Fail",
      "Cause": "Upgrade failed - rolled back to Blue environment"
    },
    "CleanupFailedGreen": {
      "Type": "Task", 
      "Resource": "arn:aws:lambda:region:account:function:cleanup-manager",
      "Next": "UpgradeFailed"
    },
    "UpgradeFailed": {
      "Type": "Fail",
      "Cause": "Upgrade failed during deployment or validation"
    },
    "DiscoveryFailed": {
      "Type": "Fail", 
      "Cause": "Infrastructure discovery failed - check ASG name and permissions"
    },
    "InfrastructureValidationFailed": {
      "Type": "Fail",
      "Cause": "Discovered infrastructure failed readiness validation - resolve issues before retry"
    }
  }
}
```

---

## Monitoring & Observability

### CloudWatch Dashboards
```python
upgrade_dashboard = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/StepFunctions", "ExecutionsSucceeded", "StateMachineArn", upgrade_state_machine_arn],
                    ["AWS/StepFunctions", "ExecutionsFailed", "StateMachineArn", upgrade_state_machine_arn]
                ],
                "title": "Upgrade Success Rate"
            }
        },
        {
            "type": "metric", 
            "properties": {
                "metrics": [
                    ["Custom/FortiGate", "Blue/InstanceHealth"],
                    ["Custom/FortiGate", "Green/InstanceHealth"]
                ],
                "title": "Environment Health"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/EC2/TransitGateway", "PacketDropCount"],
                    ["AWS/VPC", "PacketDropCount"]
                ],
                "title": "Network Health During Migration"
            }
        }
    ]
}
```

### Custom Metrics
```python
def publish_upgrade_metrics(upgrade_state):
    """
    Publish custom CloudWatch metrics during upgrade
    """
    cloudwatch.put_metric_data(
        Namespace='Custom/FortiGate/Upgrade',
        MetricData=[
            {
                'MetricName': 'UpgradeProgress',
                'Value': calculate_upgrade_progress(upgrade_state),
                'Unit': 'Percent'
            },
            {
                'MetricName': 'BlueEnvironmentHealth', 
                'Value': 1 if blue_environment_healthy() else 0,
                'Unit': 'Count'
            },
            {
                'MetricName': 'GreenEnvironmentHealth',
                'Value': 1 if green_environment_healthy() else 0, 
                'Unit': 'Count'
            }
        ]
    )
```

### Alarms & Notifications
```hcl
resource "aws_cloudwatch_metric_alarm" "upgrade_failure" {
  alarm_name          = "fortigate-upgrade-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/StepFunctions"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "FortiGate upgrade execution failed"
  
  alarm_actions = [aws_sns_topic.upgrade_alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "environment_health_degradation" {
  alarm_name          = "fortigate-environment-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "GreenEnvironmentHealth"
  namespace           = "Custom/FortiGate/Upgrade"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Green FortiGate environment became unhealthy"
  
  alarm_actions = [aws_sns_topic.emergency_rollback.arn]
}
```

---

## Success Metrics

### Upgrade Performance
- **Downtime**: Target 0 seconds (current manual process: 60-240 minutes)
- **Total Duration**: Complete upgrade in <60 minutes
- **Rollback Speed**: Recovery in <60 seconds
- **EIP Migration Window**: <20 seconds per EIP

### Reliability Metrics
- **Success Rate**: 99%+ successful upgrades without rollback
- **Validation Coverage**: 100% of critical paths tested before production
- **Rollback Effectiveness**: 100% successful rollbacks when triggered
- **Infrastructure Consistency**: Green environment identical to Blue

### Business Impact
- **SLA Maintenance**: 99.9%+ uptime during upgrade operations
- **Customer Impact**: Zero customer-facing service disruptions
- **Operational Efficiency**: 90%+ reduction in manual coordination
- **Change Management**: Standardized, auditable upgrade process

This technical design provides the foundation for a production-ready zero-downtime FortiGate upgrade system that can be implemented using the detailed Claude Code instructions in the implementation guide.