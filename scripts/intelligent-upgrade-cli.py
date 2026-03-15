#!/usr/bin/env python3
"""
Intelligent FortiGate Upgrade CLI
Leverages Fortinet Autoscale Template discovery for zero-downtime upgrades
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add lambda directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'lambda' / 'infrastructure-discovery'))

from fortinet_template_discovery import FortinetTemplateDiscovery

class IntelligentUpgradeCLI:
    def __init__(self):
        self.discoverer = None
        
    def discover_infrastructure(self, asg_name: str, region: str) -> dict:
        """
        Intelligent infrastructure discovery using Fortinet template patterns
        """
        print("🚀 Starting Intelligent Infrastructure Discovery")
        print("=" * 60)
        
        self.discoverer = FortinetTemplateDiscovery(region)
        infrastructure = self.discoverer.discover_from_asg_name(asg_name)
        
        # Display discovery results
        self._display_discovery_results(infrastructure)
        
        return infrastructure
    
    def _display_discovery_results(self, infrastructure: dict):
        """Display formatted discovery results"""
        metadata = infrastructure.get('discovery_metadata', {})
        
        print(f"\n📋 Discovery Summary")
        print("-" * 40)
        print(f"Source Method: {metadata.get('source', 'unknown')}")
        print(f"Customer Prefix: {metadata.get('customer_prefix', 'unknown')}")
        print(f"Environment: {metadata.get('environment', 'unknown')}")
        print(f"Source ASG: {metadata.get('source_asg', 'unknown')}")
        print(f"Discovery Time: {metadata.get('discovered_at', 'unknown')}")
        
        # Display Blue Environment
        blue_env = infrastructure.get('blue_environment', {})
        if blue_env:
            print(f"\n🔵 Blue Environment (Current)")
            print("-" * 40)
            print(f"VPC: {blue_env.get('vpc_id')} ({blue_env.get('vpc_cidr')})")
            print(f"ASG: {blue_env.get('asg_name')}")
            print(f"Production EIPs: {len(blue_env.get('production_eips', {}))}")
            print(f"NAT Gateways: {len(blue_env.get('nat_gateways', []))}")
            print(f"Subnets: {len(blue_env.get('subnets', {}))}")
            
            # Display EIPs
            eips = blue_env.get('production_eips', {})
            if eips:
                print(f"\n💫 Production EIPs:")
                for eip_id, eip_details in eips.items():
                    print(f"  • {eip_details.get('public_ip')} ({eip_id}) - AZ: {eip_details.get('availability_zone')}")
        
        # Display Transit Gateway
        tgw_config = infrastructure.get('transit_gateway', {})
        if tgw_config:
            print(f"\n🌐 Transit Gateway Configuration")
            print("-" * 40)
            print(f"TGW ID: {tgw_config.get('tgw_id')}")
            print(f"Inspection Attachment: {tgw_config.get('inspection_attachment_id')}")
            
            route_tables = tgw_config.get('route_table_associations', [])
            if route_tables:
                print(f"Route Tables:")
                for rt in route_tables:
                    print(f"  • {rt.get('route_table_name', 'Unnamed')} ({rt.get('route_table_id')})")
        
        # Display Customer VPCs
        customer_vpcs = infrastructure.get('customer_vpcs', [])
        if customer_vpcs:
            print(f"\n👥 Customer VPCs ({len(customer_vpcs)} found)")
            print("-" * 40)
            for vpc in customer_vpcs:
                print(f"• {vpc.get('vpc_name')} ({vpc.get('vpc_id')})")
                print(f"  CIDR: {vpc.get('cidr_block')}, Priority: {vpc.get('priority')}, Type: {vpc.get('vpc_type')}")
        
        # Display Migration Plan
        migration_plan = infrastructure.get('migration_plan', {})
        if migration_plan:
            print(f"\n📅 Migration Plan")
            print("-" * 40)
            print(f"Strategy: {migration_plan.get('migration_strategy')}")
            print(f"Total VPCs: {migration_plan.get('total_vpcs')}")
            
            migration_order = migration_plan.get('migration_order', [])
            if migration_order:
                print(f"Migration Order:")
                for item in migration_order:
                    print(f"  {item.get('order')}. {item.get('vpc_name')} (Priority: {item.get('priority')}, Est. {item.get('estimated_validation_time')}min)")
    
    def validate_infrastructure(self, infrastructure: dict) -> bool:
        """Validate discovered infrastructure for upgrade readiness"""
        print(f"\n🔍 Validating Infrastructure for Upgrade Readiness")
        print("-" * 50)
        
        validation_results = []
        
        # Check Blue environment
        blue_env = infrastructure.get('blue_environment', {})
        if not blue_env:
            validation_results.append(("❌", "Blue environment not discovered"))
        else:
            validation_results.append(("✅", f"Blue environment found: {blue_env.get('vpc_id')}"))
            
            # Check ASG
            asg_details = blue_env.get('asg_details', {})
            if asg_details:
                desired = asg_details.get('desired_capacity', 0)
                instances = len(asg_details.get('instance_ids', []))
                if desired == instances:
                    validation_results.append(("✅", f"ASG healthy: {instances}/{desired} instances"))
                else:
                    validation_results.append(("⚠️", f"ASG capacity mismatch: {instances}/{desired} instances"))
            
            # Check EIPs
            eips = blue_env.get('production_eips', {})
            if eips:
                validation_results.append(("✅", f"Production EIPs found: {len(eips)}"))
            else:
                validation_results.append(("⚠️", "No production EIPs found"))
        
        # Check Transit Gateway
        tgw_config = infrastructure.get('transit_gateway', {})
        if tgw_config:
            validation_results.append(("✅", f"Transit Gateway found: {tgw_config.get('tgw_id')}"))
        else:
            validation_results.append(("❌", "Transit Gateway configuration not found"))
        
        # Check Customer VPCs
        customer_vpcs = infrastructure.get('customer_vpcs', [])
        if customer_vpcs:
            validation_results.append(("✅", f"Customer VPCs found: {len(customer_vpcs)}"))
        else:
            validation_results.append(("⚠️", "No customer VPCs found"))
        
        # Display validation results
        for status, message in validation_results:
            print(f"{status} {message}")
        
        # Determine overall readiness
        errors = sum(1 for status, _ in validation_results if status == "❌")
        warnings = sum(1 for status, _ in validation_results if status == "⚠️")
        
        if errors == 0:
            print(f"\n✅ Infrastructure validation PASSED")
            if warnings > 0:
                print(f"⚠️  {warnings} warnings - review before proceeding")
            return True
        else:
            print(f"\n❌ Infrastructure validation FAILED ({errors} errors, {warnings} warnings)")
            return False
    
    def generate_upgrade_config(self, infrastructure: dict, target_ami: str, upgrade_id: str) -> dict:
        """Generate upgrade configuration from discovered infrastructure"""
        print(f"\n⚙️  Generating Upgrade Configuration")
        print("-" * 40)
        
        blue_env = infrastructure.get('blue_environment', {})
        tgw_config = infrastructure.get('transit_gateway', {})
        customer_vpcs = infrastructure.get('customer_vpcs', [])
        metadata = infrastructure.get('discovery_metadata', {})
        
        upgrade_config = {
            "upgrade_config": {
                "upgrade_id": upgrade_id,
                "upgrade_type": "zero_downtime_parallel_vpc",
                "target_ami": target_ami,
                "source_template": "fortinet_autoscale_simplified",
                "customer_prefix": metadata.get('customer_prefix'),
                "environment": metadata.get('environment'),
                "discovery_source": metadata.get('source')
            },
            "blue_environment": {
                "vpc_id": blue_env.get('vpc_id'),
                "vpc_cidr": blue_env.get('vpc_cidr'),
                "asg_name": blue_env.get('asg_name'),
                "production_eips": blue_env.get('production_eips', {}),
                "nat_gateways": blue_env.get('nat_gateways', []),
                "gwlb_config": blue_env.get('gwlb_config', {}),
                "tgw_attachment_id": tgw_config.get('inspection_attachment_id')
            },
            "green_deployment_config": {
                "vpc_name": f"security-green-vpc",
                "vpc_cidr": blue_env.get('vpc_cidr'),  # Same CIDR
                "reuse_blue_configuration": True,
                "target_ami": target_ami,
                "deployment_strategy": "identical_parallel",
                "initial_eip_strategy": "temporary_eips"
            },
            "transit_gateway": {
                "tgw_id": tgw_config.get('tgw_id'),
                "inspection_attachment_id": tgw_config.get('inspection_attachment_id'),
                "route_table_associations": tgw_config.get('route_table_associations', [])
            },
            "customer_vpcs": customer_vpcs,
            "migration_strategy": infrastructure.get('migration_plan', {}),
            "rollback_configuration": {
                "automatic_rollback_triggers": [
                    {
                        "condition": "connectivity_failure",
                        "threshold": "any_customer_vpc_loses_internet",
                        "action": "immediate_emergency_rollback"
                    },
                    {
                        "condition": "eip_migration_failure", 
                        "threshold": "any_eip_association_fails",
                        "action": "rollback_eips_continue_upgrade"
                    }
                ]
            }
        }
        
        print(f"✅ Generated upgrade configuration for {len(customer_vpcs)} customer VPCs")
        print(f"📋 Target AMI: {target_ami}")
        print(f"🆔 Upgrade ID: {upgrade_id}")
        
        return upgrade_config
    
    def start_upgrade(self, config_file: str):
        """Start the upgrade process using generated configuration"""
        print(f"\n🚀 Starting Zero-Downtime Upgrade")
        print("=" * 50)
        
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            return False
        
        with open(config_file, 'r') as f:
            upgrade_config = json.load(f)
        
        upgrade_id = upgrade_config.get('upgrade_config', {}).get('upgrade_id')
        target_ami = upgrade_config.get('upgrade_config', {}).get('target_ami')
        
        print(f"📋 Upgrade ID: {upgrade_id}")
        print(f"🎯 Target AMI: {target_ami}")
        print(f"🔵 Blue ASG: {upgrade_config.get('blue_environment', {}).get('asg_name')}")
        print(f"👥 Customer VPCs: {len(upgrade_config.get('customer_vpcs', []))}")
        
        # In a real implementation, this would trigger the Step Function
        print(f"\n🔄 Upgrade process would be initiated here via Step Functions")
        print(f"📊 Monitor progress: ./intelligent-upgrade-cli.py status --upgrade-id {upgrade_id}")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Intelligent FortiGate Zero-Downtime Upgrade CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover infrastructure
  %(prog)s discover --asg-name company-prod-fortigate-asg --region us-east-1
  
  # Start upgrade
  %(prog)s upgrade --asg-name company-prod-fortigate-asg --target-ami ami-12345 
  
  # Full workflow
  %(prog)s discover --asg-name company-prod-fgt-asg --region us-east-1
  %(prog)s validate --config-file discovered-infrastructure.json
  %(prog)s upgrade --config-file upgrade-config.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover infrastructure')
    discover_parser.add_argument('--asg-name', required=True, 
                               help='FortiGate ASG name (e.g., company-prod-fortigate-asg)')
    discover_parser.add_argument('--region', default='us-east-1', help='AWS region')
    discover_parser.add_argument('--output', default='discovered-infrastructure.json', 
                               help='Output file for discovery results')
    
    # Validate command  
    validate_parser = subparsers.add_parser('validate', help='Validate discovered infrastructure')
    validate_parser.add_argument('--config-file', required=True,
                                help='Infrastructure configuration file')
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Start zero-downtime upgrade')
    upgrade_parser.add_argument('--asg-name', help='FortiGate ASG name')
    upgrade_parser.add_argument('--target-ami', help='Target FortiGate AMI ID')
    upgrade_parser.add_argument('--region', default='us-east-1', help='AWS region')
    upgrade_parser.add_argument('--config-file', help='Pre-generated upgrade configuration file')
    upgrade_parser.add_argument('--upgrade-id', help='Custom upgrade ID')
    upgrade_parser.add_argument('--dry-run', action='store_true', help='Generate config without starting upgrade')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check upgrade status')
    status_parser.add_argument('--upgrade-id', required=True, help='Upgrade ID to check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = IntelligentUpgradeCLI()
    
    if args.command == 'discover':
        # Discover infrastructure
        infrastructure = cli.discover_infrastructure(args.asg_name, args.region)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(infrastructure, f, indent=2)
        
        print(f"\n💾 Discovery results saved to: {args.output}")
        
        # Auto-validate
        validation_passed = cli.validate_infrastructure(infrastructure)
        if validation_passed:
            print(f"✅ Infrastructure ready for upgrade!")
        else:
            print(f"❌ Infrastructure validation failed - resolve issues before upgrade")
            return 1
    
    elif args.command == 'validate':
        # Load and validate infrastructure
        try:
            with open(args.config_file, 'r') as f:
                infrastructure = json.load(f)
            
            validation_passed = cli.validate_infrastructure(infrastructure)
            return 0 if validation_passed else 1
            
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {args.config_file}")
            return 1
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in configuration file: {args.config_file}")
            return 1
    
    elif args.command == 'upgrade':
        if args.config_file:
            # Use existing configuration file
            success = cli.start_upgrade(args.config_file)
            return 0 if success else 1
        
        elif args.asg_name and args.target_ami:
            # Full workflow: discover + generate config + upgrade
            print(f"🔄 Running full upgrade workflow")
            
            # Step 1: Discover
            infrastructure = cli.discover_infrastructure(args.asg_name, args.region)
            
            # Step 2: Validate
            if not cli.validate_infrastructure(infrastructure):
                print(f"❌ Infrastructure validation failed")
                return 1
            
            # Step 3: Generate upgrade config
            upgrade_id = args.upgrade_id or f"upgrade-{args.asg_name}-{int(datetime.now().timestamp())}"
            upgrade_config = cli.generate_upgrade_config(infrastructure, args.target_ami, upgrade_id)
            
            # Save upgrade config
            config_file = f"upgrade-config-{upgrade_id}.json"
            with open(config_file, 'w') as f:
                json.dump(upgrade_config, f, indent=2)
            
            print(f"💾 Upgrade configuration saved to: {config_file}")
            
            # Step 4: Start upgrade (unless dry-run)
            if args.dry_run:
                print(f"🧪 Dry run complete - configuration generated but upgrade not started")
                return 0
            else:
                success = cli.start_upgrade(config_file)
                return 0 if success else 1
        
        else:
            print(f"❌ Either --config-file or both --asg-name and --target-ami are required")
            return 1
    
    elif args.command == 'status':
        # Check upgrade status
        print(f"📊 Checking status for upgrade: {args.upgrade_id}")
        print(f"🔄 This would query Step Functions execution status")
        print(f"📋 Integration with monitoring dashboards would show real-time progress")
        return 0
    
    return 0

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())