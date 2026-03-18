# Zero-Downtime FortiGate Upgrade System - Implementation Guide

## Project Overview

This implementation creates a **zero-downtime FortiGate upgrade system** using parallel VPC deployment, Transit Gateway route orchestration, and Elastic IP preservation. The system eliminates maintenance windows by deploying complete parallel infrastructure and using atomic route switching to migrate traffic seamlessly.

**Revolutionary Approach:**
- ✅ **Zero Downtime**: No service interruption during upgrades
- ✅ **Parallel VPCs**: Complete infrastructure isolation between Blue and Green
- ✅ **Route Orchestration**: Atomic traffic switching via Transit Gateway
- ✅ **EIP Preservation**: Maintain existing public IPs and external configurations
- ✅ **Instant Rollback**: Sub-minute recovery via route restoration

## Implementation Architecture

```
Customer VPCs ←→ Transit Gateway ←→ Blue Security VPC (Current)
Customer VPCs ←→ Transit Gateway ←→ Green Security VPC (Parallel)

Control Mechanism: Transit Gateway Route Table Switching
EIP Management: Migration between Blue/Green NAT Gateways
State Management: Step Functions + DynamoDB + CloudWatch
```

---

## Getting Started with Claude Code

### 1. Project Structure Setup

Create the complete directory structure:

```bash
~/github/40netse/aws-autoscale-fortios-upgrade/
├── terraform/
│   ├── shared-infrastructure/        # TGW, Customer VPCs (unchanged)
│   ├── blue-security-vpc/           # Current FortiGate environment
│   └── green-security-vpc/          # Parallel deployment
├── lambda/
│   ├── parallel-deployer/           # Deploy Green environment
│   ├── tgw-orchestrator/           # Transit Gateway route management
│   ├── eip-migrator/               # Elastic IP migration
│   ├── validation-engine/          # Environment validation
│   └── cleanup-manager/            # Blue environment cleanup
├── step-functions/
│   ├── upgrade-orchestrator.json   # Main workflow
│   └── emergency-rollback.json     # Emergency procedures
├── scripts/
│   ├── deploy.sh                   # Deployment automation
│   ├── upgrade-cli.py             # Command-line interface
│   └── monitoring-setup.py        # CloudWatch configuration
├── docs/
│   ├── runbook.md                 # Operational procedures
│   └── troubleshooting.md         # Common issues and solutions
└── examples/
    ├── basic-upgrade-config.json  # Simple upgrade scenario
    └── multi-vpc-upgrade.json     # Complex environment
```

### 2. Core Implementation Tasks

Execute these Claude Code tasks in sequence to build the complete system, **starting with intelligent discovery**.

---

## Task 1: Intelligent Infrastructure Discovery System

### Build Fortinet Template-Aware Discovery Engine
```bash
claude create lambda/infrastructure-discovery/main.py \
  --function intelligent_infrastructure_discovery \
  --inputs asg_name,region,discovery_options \
  --outputs complete_infrastructure_map,validation_results,migration_plan \
  --features fortinet_template_patterns,multi_method_extraction,comprehensive_mapping
```

**Prompt for Infrastructure Discovery Engine:**
> Create intelligent infrastructure discovery Lambda function for FortiGate environments:
>
> **Core Discovery Capabilities:**
> - **Fortinet Template Recognition**: Understand Autoscale Simplified Template naming conventions
> - **Multi-Method Extraction**: Extract customer prefix and environment from ASG names, tags, and VPC analysis
> - **Comprehensive Resource Discovery**: Automatically find VPCs, TGW, customer VPCs, production EIPs, GWLB infrastructure
> - **Intelligent Migration Planning**: Generate smart migration order based on VPC priority and complexity
>
> **Discovery Methods:**
> 1. **ASG Tag Analysis**: Extract from Customer_Prefix and Environment tags
> 2. **Name Pattern Recognition**: Parse "cp-env-description-asg" patterns
> 3. **VPC Name Analysis**: Trace ASG → Subnets → VPC → Extract from VPC names
> 4. **Fortinet Pattern Mapping**: Use "{cp}-{env}-{resource-type}" patterns for resource discovery
>
> **Resource Discovery Process:**
> - **VPC Discovery**: inspection-vpc, east-vpc, west-vpc using Fortinet patterns
> - **TGW Mapping**: Find TGW attachments and route table associations
> - **Customer VPC Identification**: Discover all VPCs attached to same TGW (excluding security VPC)
> - **EIP Discovery**: Extract production EIPs from NAT Gateways in security VPC
> - **GWLB Mapping**: Discover GWLB, target groups, and VPC endpoints
> - **Subnet Classification**: Categorize subnets (public, private, gwlbe, management)
>
> **Migration Planning Intelligence:**
> - **VPC Prioritization**: Analyze names/tags to determine migration order (dev → staging → prod)
> - **Validation Time Estimation**: Estimate required testing time based on VPC criticality
> - **Dependency Mapping**: Understand relationships between customer VPCs and security infrastructure
>
> **Output Structure:**
> ```json
> {
>   "discovery_metadata": {
>     "source": "fortinet_autoscale_template",
>     "customer_prefix": "extracted_cp",
>     "environment": "extracted_env"
>   },
>   "blue_environment": {
>     "vpc_id": "discovered_security_vpc",
>     "production_eips": {...},
>     "gwlb_config": {...}
>   },
>   "transit_gateway": {
>     "tgw_id": "discovered_tgw",
>     "route_table_associations": [...]
>   },
>   "customer_vpcs": [...],
>   "migration_plan": {...}
> }
> ```
>
> **Error Handling:**
> - Fallback to generic discovery when Fortinet patterns not detected
> - Graceful handling of partial discovery results
> - Detailed validation of discovered infrastructure
> - Manual override capability for complex environments

### Build CLI Interface for Discovery
```bash
claude create scripts/intelligent-upgrade-cli.py \
  --cli discovery_driven_upgrades \
  --commands discover,validate,upgrade,status \
  --features interactive_discovery,automatic_config_generation,progress_tracking
```

**Prompt for Discovery CLI:**
> Create command-line interface for discovery-driven FortiGate upgrades:
>
> **Commands:**
> - **discover**: Intelligent infrastructure discovery from ASG name
> - **validate**: Validate discovered infrastructure for upgrade readiness
> - **upgrade**: Execute complete zero-downtime upgrade (discovery + deployment)
> - **status**: Monitor upgrade progress and show real-time status
>
> **Discovery Command Features:**
> - Input: Single FortiGate ASG name
> - Output: Complete infrastructure map with visualization
> - Automatic validation and readiness assessment
> - Save results for subsequent upgrade operations
>
> **Upgrade Command Features:**
> - Full workflow: discovery → validation → parallel deployment → traffic migration
> - Progress tracking with real-time updates
> - Interactive approval gates for critical operations
> - Automatic rollback on any failures
>
> **Example Usage:**
> ```bash
> # Complete discovery and upgrade in one command
> ./intelligent-upgrade-cli.py upgrade \
>   --asg-name company-prod-fortigate-asg \
>   --target-ami ami-fortigate-7.4.5 \
>   --region us-east-1
>
> # Discovery only for investigation
> ./intelligent-upgrade-cli.py discover \
>   --asg-name company-prod-fortigate-asg \
>   --output discovered-infrastructure.json
>
> # Validate existing discovery results
> ./intelligent-upgrade-cli.py validate \
>   --config-file discovered-infrastructure.json
> ```

### Create Discovery Integration Documentation
```bash
claude create docs/discovery-integration-guide.md \
  --documentation discovery_system_integration \
  --topics fortinet_template_patterns,cli_usage,troubleshooting \
  --examples real_world_scenarios
```

**Prompt for Discovery Documentation:**
> Create comprehensive guide for intelligent discovery system integration:
>
> **Documentation Sections:**
> 1. **Fortinet Template Integration**: How the system leverages Autoscale Simplified Template patterns
> 2. **Discovery Methods**: Technical details of multi-method extraction and resource mapping
> 3. **CLI Usage Guide**: Complete examples for all discovery and upgrade scenarios
> 4. **Troubleshooting**: Common issues and resolution steps
> 5. **Configuration Examples**: Real-world discovery outputs and upgrade configurations
>
> **Integration Patterns:**
> - How to use with existing Fortinet deployments
> - Integration with monitoring and alerting systems
> - Terraform state management and resource relationships
> - Custom naming convention support and fallback discovery

---

## Task 2: Enhanced Terraform Infrastructure with Discovery Integration

### Create Shared Infrastructure (Unchanged)
```bash
claude create terraform/shared-infrastructure/main.tf \
  --template transit_gateway_hub_spoke \
  --components customer_vpcs,transit_gateway,route_tables \
  --note "This represents existing infrastructure - never modified during upgrades"
```

**Prompt for Shared Infrastructure:**
> Create Terraform configuration for existing hub-and-spoke infrastructure:
> - **Transit Gateway**: Central routing hub for all VPCs
> - **Customer VPCs**: Application workload VPCs (multiple)
> - **TGW Route Tables**: Current routing configuration
> - **TGW Attachments**: Customer VPC attachments to TGW
> 
> This infrastructure is **never modified** during upgrades - only route table associations change.
> Export all necessary data sources for Blue/Green deployments.

### Create Blue Security VPC (Current Environment)
```bash
claude create terraform/blue-security-vpc/main.tf \
  --template fortigate_security_vpc \
  --components vpc,subnets,nat_gateways,fortigate_asg,gwlb,tgw_attachment \
  --features eip_management,identical_green_config
```

**Prompt for Blue Security VPC:**
> Create Terraform for existing FortiGate security VPC infrastructure:
> - **VPC**: 10.100.0.0/16 CIDR
> - **Subnets**: Management (10.100.1-3.0/24), Private (10.100.11-13.0/24), Public (10.100.21-23.0/24)
> - **NAT Gateways**: With production Elastic IPs for internet egress
> - **FortiGate ASG**: Using existing terraform-aws-cloud-modules/modules/fortigate/fgt_asg
> - **GWLB Infrastructure**: Load balancer, target groups, VPC endpoints
> - **TGW Attachment**: Connect security VPC to existing Transit Gateway
> 
> **Key Requirements:**
> - Export all configuration details for Green environment replication
> - Tag all resources with Environment=blue for identification
> - Use data sources to reference shared infrastructure (TGW, etc.)
> - Output EIP mappings for migration planning

### Create Green Security VPC (Parallel Deployment)
```bash
claude create terraform/green-security-vpc/main.tf \
  --template fortigate_security_vpc \
  --components identical_to_blue,new_ami_support,temp_eip_management \
  --features parallel_deployment,eip_migration_ready
```

**Prompt for Green Security VPC:**
> Create Terraform for parallel Green security VPC - **IDENTICAL to Blue except**:
> - **Same CIDR**: 10.100.0.0/16 (identical IP addressing)
> - **Same Subnet Layout**: Exact same subnet CIDRs and AZ distribution
> - **New AMI**: Variable for target FortiGate AMI version
> - **Temporary EIPs**: Initial deployment with temp EIPs, prepare for production EIP migration
> - **Parallel GWLB**: Complete GWLB infrastructure independent of Blue
> - **Independent TGW Attachment**: Separate attachment to same Transit Gateway
> 
> **Implementation Notes:**
> - Reuse Blue configuration with minimal changes (AMI + naming)
> - Support conditional EIP usage (temp vs production after migration)
> - Export all details for traffic migration planning
> - Tag resources with Environment=green

### Create Terraform Outputs and Data Sources
```bash
claude create terraform/shared-infrastructure/outputs.tf \
  --exports tgw_id,customer_vpc_attachments,existing_route_tables

claude create terraform/blue-security-vpc/outputs.tf \
  --exports vpc_config,eip_mappings,gwlb_details,tgw_attachment_id

claude create terraform/green-security-vpc/outputs.tf \
  --exports vpc_config,temp_eip_mappings,gwlb_details,tgw_attachment_id
```

---

## Task 3: Lambda Functions - Core Automation

### Parallel Deployer Lambda
```bash
claude create lambda/parallel-deployer/main.py \
  --function deploy_green_environment \
  --inputs blue_environment_config,target_ami_id,deployment_options \
  --outputs green_environment_details,deployment_status
```

**Prompt for Parallel Deployer:**
> Create Lambda function to deploy Green security VPC in parallel to Blue:
> 
> **Core Functionality:**
> - **Terraform Execution**: Run terraform apply for green-security-vpc directory
> - **Configuration Cloning**: Copy Blue network/security configuration to Green
> - **Health Validation**: Wait for Green FortiGate ASG to become healthy
> - **Readiness Check**: Validate Green environment ready for traffic testing
> 
> **Implementation Details:**
> - Use boto3 to interact with AWS APIs for status checking
> - Run terraform commands via subprocess with proper error handling
> - Monitor ASG instance health and FortiGate API responses
> - Return comprehensive Green environment configuration
> 
> **Error Handling:**
> - Cleanup partial deployments on failure
> - Detailed logging of deployment progress
> - Timeout handling for long-running operations
> - Export deployment details for rollback if needed

### TGW Orchestrator Lambda
```bash
claude create lambda/tgw-orchestrator/main.py \
  --function orchestrate_traffic_migration \
  --inputs action,customer_vpcs,blue_green_attachments \
  --outputs migration_results,updated_route_associations
```

**Prompt for TGW Orchestrator:**
> Create Lambda function for Transit Gateway route orchestration:
> 
> **Core Actions:**
> - **migrate**: Move customer VPC associations from Blue to Green route tables
> - **rollback**: Restore customer VPC associations to Blue route tables
> - **gradual_migrate**: Migrate customer VPCs one at a time with validation
> 
> **Implementation:**
> - **Route Table Management**: Create/delete TGW route tables for Blue/Green
> - **VPC Association Migration**: Atomic switching of customer VPC associations
> - **Progress Tracking**: Monitor migration progress and log each step
> - **Validation Integration**: Test connectivity after each migration step
> 
> **Safety Features:**
> - Store original associations before any changes (for rollback)
> - Validate route propagation before proceeding to next VPC
> - Immediate rollback on any connectivity failures
> - Comprehensive logging of all route table changes

### EIP Migrator Lambda
```bash
claude create lambda/eip-migrator/main.py \
  --function migrate_production_eips \
  --inputs blue_eip_mappings,green_nat_gateways,migration_strategy \
  --outputs eip_migration_results,rollback_data
```

**Prompt for EIP Migrator:**
> Create Lambda function for Elastic IP migration between Blue and Green:
> 
> **Core Functionality:**
> - **EIP Discovery**: Identify production EIPs currently associated with Blue NAT Gateways
> - **Mapping Logic**: Match Blue NAT Gateways to corresponding Green NAT Gateways by AZ
> - **Atomic Migration**: Disassociate from Blue, immediately associate with Green
> - **Validation**: Verify EIP associations successful and routing working
> 
> **Migration Process:**
> - Support both parallel and sequential EIP migration strategies
> - Brief connectivity window (~10-20 seconds per EIP)
> - Immediate validation of new EIP associations
> - Store original associations for emergency rollback
> 
> **Error Handling:**
> - Rollback any partially migrated EIPs on failure
> - Detailed timing logs for migration windows
> - Health checks post-migration to ensure connectivity
> - Integration with monitoring for migration progress

### Validation Engine Lambda
```bash
claude create lambda/validation-engine/main.py \
  --function comprehensive_environment_validation \
  --inputs environment_config,test_scenarios,validation_criteria \
  --outputs validation_results,detailed_test_reports
```

**Prompt for Validation Engine:**
> Create comprehensive validation Lambda for Green environment testing:
> 
> **Validation Categories:**
> 1. **Connectivity Tests**:
>    - Ping tests from customer VPCs through Green environment
>    - Traceroute validation to ensure proper path through Green FortiGates
>    - Application-layer connectivity (HTTP/HTTPS/SSH/custom protocols)
> 
> 2. **Security Policy Tests**:
>    - Verify blocked traffic remains blocked (security policy enforcement)
>    - Confirm allowed traffic flows correctly through Green
>    - Test threat detection and prevention capabilities
>    - Validate logging and monitoring functionality
> 
> 3. **Performance Tests**:
>    - Latency comparison between Blue and Green environments
>    - Throughput validation under load
>    - Connection capacity testing
>    - Resource utilization monitoring
> 
> 4. **FortiGate Health Tests**:
>    - FortiGate API responsiveness
>    - HA status validation (if applicable)
>    - System resource usage
>    - Configuration consistency checks
> 
> **Implementation:**
> - Use test instances in customer VPCs for realistic testing
> - Generate both legitimate and blocked traffic for security validation
> - Detailed test reporting with pass/fail status for each test
> - Integration with existing monitoring tools and baselines

### Cleanup Manager Lambda
```bash
claude create lambda/cleanup-manager/main.py \
  --function manage_environment_cleanup \
  --inputs cleanup_target,stability_requirements,safety_checks \
  --outputs cleanup_results,preserved_resources
```

**Prompt for Cleanup Manager:**
> Create Lambda function for safe environment cleanup:
> 
> **Cleanup Operations:**
> - **Blue Environment Cleanup**: Remove Blue security VPC after successful migration
> - **Failed Green Cleanup**: Clean up Green environment if deployment/testing fails
> - **Temporary Resource Cleanup**: Remove temporary EIPs, test resources, etc.
> 
> **Safety Mechanisms:**
> - **Stability Period**: Ensure Green environment stable before Blue cleanup
> - **Health Validation**: Verify Green environment health before destroying Blue
> - **Gradual Cleanup**: Remove resources in proper dependency order
> - **Preservation Options**: Keep specific resources for audit/debugging
> 
> **Implementation:**
> - Execute terraform destroy for target environment
> - Handle cleanup failures gracefully (partial cleanup recovery)
> - Preserve audit logs and configuration backups
> - Integration with change management and compliance requirements

### Blue Cleanup Safety Protocol

**Critical Warning**: Never run `terraform destroy` on the Blue state without first auditing the state file. The customer's Blue state file is the ground truth — **it may not match current templates**. Deployments from older versions of the Autoscale-Simplified-Template may have different resource layouts, module structures, or state organization. Always discover what is actually in the state before taking any action.

The core risk: if the Transit Gateway (TGW) was created as part of the Blue terraform state, `terraform destroy` will destroy it — taking down the GREEN environment too.

#### Step 1: Audit the Actual Blue State (Read-Only)

```bash
# From the customer's Blue terraform directory (wherever their state backend points)
terraform state list
```

Scan the output for any TGW-related resources:
```
# Resources to look for:
module.vpc-transit-gateway[0].aws_ec2_transit_gateway.main
module.vpc-transit-gateway-attachment-east[0].aws_ec2_transit_gateway_vpc_attachment.main
aws_ec2_transit_gateway_route_table.*
aws_ec2_transit_gateway_route.*
```

#### Step 2: Preview the Full Blast Radius (Read-Only)

```bash
terraform plan -destroy
```

This is a dry run — nothing changes. Read the full output carefully. You are specifically checking for:
- `aws_ec2_transit_gateway`
- `aws_ec2_transit_gateway_vpc_attachment`
- `aws_ec2_transit_gateway_route_table`
- `aws_ec2_transit_gateway_route`

If any of these appear and GREEN depends on them, stop and use `terraform state rm` before proceeding.

#### Step 3: Detach Shared Resources from Blue State (Non-Destructive)

`terraform state rm` removes a resource from the state file **without destroying it in AWS**. The physical TGW stays intact. After this command, `terraform destroy` has no knowledge of the TGW and will not touch it.

```bash
# Remove TGW itself
terraform state rm 'module.vpc-transit-gateway[0].aws_ec2_transit_gateway.main'

# Remove TGW attachments
terraform state rm 'module.vpc-transit-gateway-attachment-east[0].aws_ec2_transit_gateway_vpc_attachment.main'
terraform state rm 'module.vpc-transit-gateway-attachment-west[0].aws_ec2_transit_gateway_vpc_attachment.main'

# Remove TGW routes and route tables that GREEN now owns
terraform state rm 'aws_ec2_transit_gateway_route.east-default-route-to-inspection'
terraform state rm 'aws_ec2_transit_gateway_route.west-default-route-to-inspection'
```

Exact resource addresses depend on the customer's actual state — use the `terraform state list` output from Step 1 as your reference, not any template file.

#### Step 4: Confirm Remaining Resources Are Blue-Only

```bash
# Run plan -destroy again to verify only Blue-specific resources remain
terraform plan -destroy
```

Review: only the Blue Security VPC, its subnets, NAT gateways, FortiGate ASG, GWLB, and related resources should be listed now.

#### Step 5: Safe Destroy

```bash
terraform destroy
```

#### Why Not `terraform state mv`?

`terraform state mv` moves a resource between two state files — useful if you want Green's Terraform to start managing the TGW. However, this requires:
- Both state files accessible simultaneously
- Matching resource address structure between Blue and Green states
- The module hierarchy to be compatible

Since GREEN discovers TGW via `Fortinet-Role` tags (data sources) rather than managing it via state, there is nothing to transfer. `terraform state rm` is simpler and lower risk.

#### Summary

| Command | What It Does | Risk |
|---------|-------------|------|
| `terraform state list` | List all resources in Blue state | None — read only |
| `terraform plan -destroy` | Preview every resource that would be destroyed | None — read only |
| `terraform state rm <addr>` | Detach a resource from state (AWS resource unchanged) | Low — reversible with `terraform import` |
| `terraform destroy` | Destroy everything remaining in state | Permanent — only run after audit + state rm |

---

## Task 4: Step Functions - Workflow Orchestration

### Main Upgrade Orchestrator
```bash
claude create step-functions/upgrade-orchestrator.json \
  --workflow zero_downtime_upgrade \
  --steps deploy_green,validate_green,migrate_traffic,migrate_eips,cleanup \
  --features error_handling,rollback_on_failure,progress_tracking
```

**Prompt for Upgrade Orchestrator:**
> Create Step Function for complete zero-downtime upgrade workflow:
> 
> **Workflow Steps:**
> 1. **DeployGreenEnvironment**: Call parallel-deployer Lambda
> 2. **ValidateGreenEnvironment**: Run comprehensive validation tests
> 3. **ApprovalGate**: Optional manual approval before production migration
> 4. **MigrateTrafficToGreen**: Switch TGW routes to Green environment
> 5. **ValidateTrafficMigration**: Confirm all customer VPCs have connectivity
> 6. **MigrateProductionEIPs**: Move production EIPs from Blue to Green
> 7. **FinalValidation**: Comprehensive validation with production EIPs
> 8. **ScheduleBlueCleanup**: Wait stability period, then cleanup Blue
> 
> **Error Handling:**
> - Comprehensive catch blocks for each step
> - Automatic rollback to Blue on any critical failure
> - Choice states for validation results (pass/fail branching)
> - Parallel execution where safe (e.g., multiple validation tests)
> 
> **State Management:**
> - DynamoDB integration for persistent state tracking
> - Progress updates and notifications via SNS
> - Detailed execution history for debugging and audit
> - Support for pause/resume functionality

### Emergency Rollback Workflow
```bash
claude create step-functions/emergency-rollback.json \
  --workflow emergency_rollback \
  --steps detect_failure,restore_tgw_routes,restore_eips,validate_blue \
  --optimization speed_over_safety \
  --target_time under_60_seconds
```

**Prompt for Emergency Rollback:**
> Create high-speed emergency rollback Step Function:
> 
> **Rollback Steps:**
> 1. **RestoreTGWRoutes**: Immediately switch customer VPCs back to Blue routes
> 2. **RestoreProductionEIPs**: Move EIPs back to Blue NAT Gateways (if migrated)
> 3. **ValidateBlueConnectivity**: Verify all customer VPCs can reach internet via Blue
> 4. **NotifyOperations**: Alert operations team of rollback event
> 5. **ScheduleGreenCleanup**: Plan Green environment cleanup
> 
> **Optimization for Speed:**
> - Parallel execution of independent rollback steps
> - Minimal validation during rollback (speed over perfection)
> - Direct Lambda invocations (skip Step Function overhead where possible)
> - Aggressive timeouts to prevent hanging
> 
> **Monitoring Integration:**
> - Real-time progress updates via CloudWatch events
> - Integration with alerting systems for immediate notification
> - Detailed logging for post-incident analysis

---

## Task 5: Monitoring and Alerting

### CloudWatch Dashboards
```bash
claude create scripts/monitoring-setup.py \
  --dashboards upgrade_progress,environment_health,traffic_metrics \
  --alarms rollback_triggers,performance_degradation,connectivity_failures \
  --notifications sns_integration
```

**Prompt for Monitoring Setup:**
> Create comprehensive monitoring for zero-downtime upgrade system:
> 
> **Dashboards:**
> 1. **Upgrade Progress Dashboard**:
>    - Step Function execution status and progress
>    - Current upgrade phase and estimated completion
>    - Error rates and rollback events
>    - Historical upgrade success/failure rates
> 
> 2. **Environment Health Dashboard**:
>    - Blue/Green FortiGate instance health
>    - TGW route table associations and traffic flow
>    - EIP associations and NAT Gateway health
>    - Customer VPC connectivity status
> 
> 3. **Traffic Metrics Dashboard**:
>    - Network traffic volumes through Blue vs Green
>    - Latency and packet loss metrics
>    - Connection counts and session tables
>    - Bandwidth utilization and performance baselines
> 
> **Custom Metrics:**
> - Upgrade progress percentage
> - Environment health scores (0-100)
> - Traffic migration completion percentage
> - Validation test pass rates
> 
> **Automated Alerts:**
> - Immediate rollback triggers (connectivity failures, security violations)
> - Performance degradation warnings
> - Upgrade failure notifications
> - Operational status updates

### Custom Metrics Collection
```bash
claude create lambda/monitoring/metrics-collector.py \
  --function collect_upgrade_metrics \
  --sources step_functions,fortigate_apis,vpc_flow_logs,custom_tests \
  --outputs cloudwatch_metrics,operational_insights
```

**Prompt for Metrics Collector:**
> Create Lambda for collecting custom metrics during upgrades:
> 
> **Metric Sources:**
> - **Step Functions**: Execution progress, duration, success/failure rates
> - **FortiGate APIs**: Instance health, session counts, policy hit rates, CPU/memory
> - **VPC Flow Logs**: Traffic patterns, connection counts, geographical distribution
> - **Custom Tests**: Connectivity test results, latency measurements, throughput tests
> 
> **Metric Categories:**
> - **Operational Metrics**: Upgrade duration, success rates, rollback frequency
> - **Performance Metrics**: Latency, throughput, connection capacity
> - **Security Metrics**: Policy enforcement rates, threat detection events
> - **Business Metrics**: Uptime percentage, customer impact measurements

---

## Task 6: Command Line Interface and Automation

### Upgrade CLI Tool
```bash
claude create scripts/upgrade-cli.py \
  --cli zero_downtime_upgrade \
  --commands start,status,pause,resume,rollback,cleanup \
  --features progress_tracking,interactive_approval,safety_checks
```

**Prompt for Upgrade CLI:**
> Create command-line interface for zero-downtime upgrade operations:
> 
> **Commands:**
> - **start**: Initiate new upgrade with target AMI and configuration
> - **status**: Show current upgrade progress and detailed status
> - **pause**: Pause upgrade at safe checkpoint (after validation)
> - **resume**: Resume paused upgrade from last checkpoint
> - **rollback**: Initiate emergency rollback to Blue environment
> - **cleanup**: Clean up completed or failed upgrade resources
> - **list**: Show all active and recent upgrade executions
> 
> **Features:**
> - Interactive configuration with validation
> - Real-time progress updates with color coding
> - Safety confirmations for destructive operations
> - Integration with Step Functions for execution control
> - Detailed logging and audit trail
> 
> **Usage Examples:**
> ```bash
> ./upgrade-cli.py start --target-ami ami-12345 --environment prod
> ./upgrade-cli.py status --upgrade-id upgrade-20241215-001
> ./upgrade-cli.py rollback --upgrade-id upgrade-20241215-001 --emergency
> ```

### Deployment Automation
```bash
claude create scripts/deploy.sh \
  --script automated_deployment \
  --environments dev,staging,production \
  --features safety_checks,rollback_capability,monitoring_integration
```

**Prompt for Deployment Script:**
> Create automated deployment script for the upgrade system itself:
> 
> **Deployment Steps:**
> 1. **Infrastructure Validation**: Verify prerequisites (TGW, VPCs, IAM roles)
> 2. **Lambda Deployment**: Package and deploy all Lambda functions
> 3. **Step Function Deployment**: Create/update workflow definitions
> 4. **Monitoring Setup**: Deploy CloudWatch dashboards and alarms
> 5. **Testing**: Run basic functionality tests
> 6. **Documentation**: Generate deployment report and configuration summary
> 
> **Safety Features:**
> - Dry-run mode for testing deployment without changes
> - Rollback capability to previous version on deployment failure
> - Environment-specific configuration management
> - Integration testing before marking deployment successful
> 
> **Environments:**
> - **dev**: Minimal setup for development testing
> - **staging**: Full setup for integration testing
> - **production**: Full setup with enhanced monitoring and alerting

---

## Task 7: Testing and Validation Framework

### Integration Tests
```bash
claude create tests/integration/test_complete_upgrade.py \
  --test_scenarios basic_upgrade,complex_multi_vpc,failure_recovery \
  --mock_services aws_apis,fortigate_responses \
  --validation zero_downtime,eip_preservation,rollback_capability
```

**Prompt for Integration Testing:**
> Create comprehensive integration test suite:
> 
> **Test Scenarios:**
> 1. **Basic Upgrade**: Single customer VPC, simple network topology
> 2. **Multi-VPC Complex**: Multiple customer VPCs, complex routing
> 3. **Failure Recovery**: Test failure injection and rollback capabilities
> 4. **EIP Migration**: Validate production EIP preservation
> 5. **Performance Impact**: Measure upgrade impact on traffic
> 
> **Validation Areas:**
> - **Zero Downtime**: Continuous ping/connectivity tests during upgrade
> - **EIP Preservation**: Verify same public IPs before/after upgrade
> - **Security Policy**: Confirm blocked traffic remains blocked
> - **Performance**: Measure latency/throughput impact during migration
> - **Rollback Speed**: Validate sub-60-second rollback capability
> 
> **Mock Services:**
> - AWS API responses for consistent testing
> - FortiGate API responses for various health states
> - Network simulation for connectivity testing
> - Failure injection for resilience testing

### Chaos Engineering Tests
```bash
claude create tests/chaos/chaos_testing.py \
  --scenarios lambda_failures,network_partitions,aws_api_failures \
  --validate automatic_rollback,system_resilience,recovery_time
```

**Prompt for Chaos Testing:**
> Create chaos engineering tests for system resilience:
> 
> **Failure Scenarios:**
> 1. **Lambda Function Failures**: Random Lambda timeouts/errors during upgrade
> 2. **Network Partitions**: Temporary connectivity issues between components
> 3. **AWS API Failures**: Simulated AWS service degradations
> 4. **FortiGate Health Issues**: Instance failures during migration
> 5. **Partial EIP Migration Failures**: EIP association errors
> 
> **Resilience Validation:**
> - Automatic detection of failures and triggering of rollback
> - Recovery time measurement under various failure conditions
> - Data consistency validation after failures and recovery
> - Alert system effectiveness during failure scenarios
> 
> **Chaos Injection:**
> - Programmatic failure injection into running upgrade processes
> - Gradual failure escalation (single component → cascading failures)
> - Recovery validation and system state verification
> - Documentation of failure patterns and system responses

---

## Task 8: Documentation and Runbooks

### Operational Runbook
```bash
claude create docs/runbook.md \
  --procedures standard_upgrade,emergency_procedures,troubleshooting \
  --checklists pre_upgrade,post_upgrade,rollback_validation \
  --escalation_paths technical_issues,business_impact
```

**Prompt for Operational Runbook:**
> Create comprehensive operational runbook for production use:
> 
> **Standard Procedures:**
> 1. **Pre-Upgrade Checklist**: Environment validation, backup verification, team notification
> 2. **Upgrade Execution**: Step-by-step upgrade process with decision points
> 3. **Post-Upgrade Validation**: Comprehensive testing and sign-off procedures
> 4. **Cleanup Operations**: Blue environment cleanup and resource optimization
> 
> **Emergency Procedures:**
> 1. **Emergency Rollback**: When and how to trigger immediate rollback
> 2. **Partial Failure Recovery**: Handling partial deployment failures
> 3. **Communication Protocols**: Stakeholder notification during emergencies
> 4. **Post-Incident Procedures**: Analysis and lessons learned
> 
> **Troubleshooting Guide:**
> - Common error scenarios and resolution steps
> - Log analysis and debugging techniques
> - Performance troubleshooting during and after upgrades
> - Integration with existing operational procedures

### API Documentation
```bash
claude create docs/api-reference.md \
  --apis step_functions,lambda_functions,cli_interface \
  --formats openapi_specs,usage_examples,response_schemas \
  --integration existing_systems
```

**Prompt for API Documentation:**
> Create comprehensive API documentation for system integration:
> 
> **API Categories:**
> 1. **Step Functions APIs**: Execution control, status querying, parameter passing
> 2. **Lambda Function APIs**: Direct invocation, input schemas, output formats
> 3. **CLI Interface**: Command-line usage, scripting integration, automation hooks
> 4. **Monitoring APIs**: Metrics collection, alerting integration, dashboard queries
> 
> **Documentation Format:**
> - OpenAPI specifications for programmatic integration
> - Usage examples with real request/response data
> - Error codes and troubleshooting guides
> - Integration patterns with existing systems
> 
> **Integration Guides:**
> - CI/CD pipeline integration
> - Change management system integration
> - Monitoring and alerting system integration
> - Custom dashboard and reporting integration

---

## Task 9: Example Configurations and Use Cases

### Basic Upgrade Configuration
```bash
claude create examples/basic-upgrade-config.json \
  --scenario single_customer_vpc,standard_fortigate_deployment \
  --parameters minimal_required_config \
  --validation_tests basic_connectivity,security_policy_enforcement
```

**Example Configuration Prompt:**
> Create example configuration for basic upgrade scenario:
> 
> **Scenario Description:**
> - Single customer VPC with standard web application workload
> - FortiGate ASG with 2 instances across 2 AZs
> - Standard security policies (web filtering, antivirus, IPS)
> - Production EIPs for internet egress
> 
> **Configuration Structure:**
> ```json
> {
>   "upgrade_config": {
>     "upgrade_id": "basic-prod-upgrade-001",
>     "target_ami": "ami-fortigate-7.4.5",
>     "environment": "production"
>   },
>   "blue_environment": {
>     "vpc_id": "vpc-blue-security",
>     "asg_name": "fortigate-prod-asg",
>     "production_eips": ["eip-prod1", "eip-prod2"]
>   },
>   "validation_config": {
>     "tests": ["connectivity", "security_policies", "performance"],
>     "timeout_minutes": 15
>   },
>   "rollback_config": {
>     "automatic_triggers": ["connectivity_failure", "security_violation"],
>     "manual_approval_required": false
>   }
> }
> ```

### Complex Multi-VPC Scenario
```bash
claude create examples/multi-vpc-upgrade.json \
  --scenario multiple_customer_vpcs,complex_routing,compliance_requirements \
  --parameters advanced_configuration \
  --validation_tests comprehensive_suite
```

**Complex Configuration Prompt:**
> Create example for complex enterprise upgrade scenario:
> 
> **Scenario Description:**
> - Multiple customer VPCs (production, staging, development)
> - Complex routing with multiple security domains
> - Compliance requirements (PCI, HIPAA, SOX)
> - Advanced FortiGate features (ZTNA, CASB, advanced threat protection)
> - Multiple EIPs with external whitelist dependencies
> 
> **Advanced Features:**
> - Gradual migration by VPC priority (critical → non-critical)
> - Extended validation periods for compliance
> - Custom security policy validation
> - Integration with external monitoring systems
> - Audit trail and compliance reporting

---

## Implementation Sequence

### Phase 1: Intelligent Discovery Foundation
```bash
# 1. Build intelligent discovery system (PRIORITY)
claude create lambda/infrastructure-discovery/main.py --function intelligent_infrastructure_discovery
claude create scripts/intelligent-upgrade-cli.py --cli discovery_driven_upgrades
claude create docs/discovery-integration-guide.md --documentation discovery_system

# 2. Test discovery with existing infrastructure
./scripts/intelligent-upgrade-cli.py discover --asg-name test-asg --region us-east-1

# 3. Validate discovery accuracy and create fallback mechanisms
claude create lambda/infrastructure-discovery/fallback_discovery.py --function generic_discovery_fallback
```

### Phase 2: Core Infrastructure and Automation
```bash
# 4. Create Terraform infrastructure templates (using discovery outputs)
claude create terraform/shared-infrastructure/main.tf --template transit_gateway_hub_spoke
claude create terraform/blue-security-vpc/main.tf --template fortigate_security_vpc  
claude create terraform/green-security-vpc/main.tf --template parallel_fortigate_vpc

# 5. Build core Lambda functions (integrated with discovery)
claude create lambda/parallel-deployer/main.py --function deploy_green_environment
claude create lambda/tgw-orchestrator/main.py --function orchestrate_traffic_migration
claude create lambda/validation-engine/main.py --function comprehensive_validation

# 6. Create discovery-integrated workflow
claude create step-functions/upgrade-orchestrator.json --workflow discovery_driven_upgrade
```

### Phase 3: Advanced Features
```bash
# 4. Add EIP migration and monitoring
claude create lambda/eip-migrator/main.py --function migrate_production_eips
claude create lambda/cleanup-manager/main.py --function manage_environment_cleanup
claude create scripts/monitoring-setup.py --dashboards upgrade_monitoring

# 5. Build CLI and automation
claude create scripts/upgrade-cli.py --cli zero_downtime_upgrade
claude create scripts/deploy.sh --script automated_deployment

# 6. Create emergency procedures
claude create step-functions/emergency-rollback.json --workflow emergency_rollback
```

### Phase 4: Testing and Documentation
```bash
# 7. Build test suites
claude create tests/integration/test_complete_upgrade.py --test_scenarios comprehensive
claude create tests/chaos/chaos_testing.py --scenarios failure_injection

# 8. Create documentation
claude create docs/runbook.md --procedures operational_guide
claude create docs/api-reference.md --apis system_integration

# 9. Example configurations
claude create examples/basic-upgrade-config.json --scenario standard_deployment
claude create examples/multi-vpc-upgrade.json --scenario enterprise_complex
```

---

## Deployment and Testing

### Initial Deployment
```bash
# Deploy to development environment
cd ~/github/40netse/aws-autoscale-fortios-upgrade
./scripts/deploy.sh --environment dev --validate

# Run integration tests
python -m pytest tests/integration/ --environment dev

# Deploy to production
./scripts/deploy.sh --environment production --dry-run
./scripts/deploy.sh --environment production --deploy
```

### First Upgrade Execution
```bash
# Execute first upgrade (with careful monitoring)
./scripts/upgrade-cli.py start \
  --target-ami ami-fortigate-7.4.5 \
  --environment production \
  --config examples/basic-upgrade-config.json \
  --dry-run

# If dry-run successful, execute actual upgrade
./scripts/upgrade-cli.py start \
  --target-ami ami-fortigate-7.4.5 \
  --environment production \
  --config examples/basic-upgrade-config.json

# Monitor progress
./scripts/upgrade-cli.py status --follow
```

---

## Success Validation

### Zero-Downtime Verification
```bash
# Run continuous connectivity tests during upgrade
claude create tests/continuous-monitoring.py \
  --tests ping_tests,application_connectivity,security_validation \
  --duration upgrade_window \
  --reporting real_time_dashboard
```

### EIP Preservation Validation
```bash
# Verify EIPs preserved throughout upgrade
claude create tests/eip-validation.py \
  --tests eip_consistency,whitelist_compatibility,external_connectivity \
  --validation before_during_after_upgrade
```

### Performance Impact Assessment
```bash
# Measure performance impact during upgrade
claude create tests/performance-validation.py \
  --metrics latency,throughput,connection_capacity \
  --baseline_comparison blue_vs_green_environments
```

---

## Quick Start Commands

```bash
# Initialize the intelligent zero-downtime upgrade system
cd ~/github/40netse/aws-autoscale-fortios-upgrade

# PRIORITY: Build intelligent discovery system FIRST
claude create lambda/infrastructure-discovery/main.py --function intelligent_infrastructure_discovery
claude create scripts/intelligent-upgrade-cli.py --cli discovery_driven_upgrades

# Test discovery with your existing infrastructure  
./scripts/intelligent-upgrade-cli.py discover \
  --asg-name your-company-prod-fortigate-asg \
  --region us-east-1

# Complete zero-downtime upgrade using discovery
./scripts/intelligent-upgrade-cli.py upgrade \
  --asg-name your-company-prod-fortigate-asg \
  --target-ami ami-fortigate-7.4.5

# Build remaining infrastructure templates (using discovery outputs)
claude create terraform/shared-infrastructure/main.tf --template hub_spoke_existing
claude create terraform/blue-security-vpc/main.tf --template current_fortigate_deployment  
claude create terraform/green-security-vpc/main.tf --template parallel_identical_deployment

# Build discovery-integrated automation functions
claude create lambda/parallel-deployer/main.py --function deploy_green_parallel
claude create lambda/tgw-orchestrator/main.py --function orchestrate_route_migration
claude create step-functions/upgrade-orchestrator.json --workflow discovery_driven_upgrade

# Monitor and validate
./scripts/intelligent-upgrade-cli.py status --upgrade-id upgrade-12345 --real-time
```

## Innovation Summary

This implementation provides a **revolutionary approach** to network security appliance upgrades:

1. **Intelligent Infrastructure Discovery**: Single ASG name discovers complete environment using Fortinet template patterns
2. **One-Command Operation**: Complete upgrade workflow from discovery to deployment in single CLI command
3. **True Zero Downtime**: Eliminates maintenance windows entirely through parallel infrastructure
4. **Risk Elimination**: Test new versions with real traffic before production deployment  
5. **Instant Recovery**: Sub-minute rollback capability via route restoration
6. **EIP Preservation**: Maintain external configurations and whitelist compatibility
7. **Operational Excellence**: Fully automated, auditable, repeatable upgrade process

**Key Differentiator**: The intelligent discovery system transforms FortiGate upgrades from a **complex, manual, multi-hour process** requiring extensive AWS infrastructure knowledge into a **simple, one-command operation** that any operations team member can execute safely.

The system represents a **paradigm shift** from "infrastructure complexity as a barrier" to "infrastructure intelligence as an enabler" - making zero-downtime FortiGate upgrades accessible to organizations regardless of their AWS expertise level.