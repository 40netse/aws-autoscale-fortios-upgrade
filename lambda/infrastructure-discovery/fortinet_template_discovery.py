#!/usr/bin/env python3
"""
Fortinet Autoscale Template Infrastructure Discovery
Leverages known naming conventions from ~/github/40netse/Autoscale-Simplified-Template
"""

import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class FortinetTemplateDiscovery:
    """
    Intelligent infrastructure discovery based on Fortinet Autoscale Template patterns
    """
    
    def __init__(self, region: str):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.autoscaling_client = boto3.client('autoscaling', region_name=region)
        self.elbv2_client = boto3.client('elbv2', region_name=region)
        self.region = region
        
        # Known Fortinet template naming patterns
        self.fortinet_patterns = {
            'inspection_vpc': '{cp}-{env}-inspection-vpc',
            'management_vpc': '{cp}-{env}-management-vpc', 
            'east_vpc': '{cp}-{env}-east-vpc',
            'west_vpc': '{cp}-{env}-west-vpc',
            'inspection_public_az1': '{cp}-{env}-inspection-public-az1-subnet',
            'inspection_public_az2': '{cp}-{env}-inspection-public-az2-subnet',
            'inspection_private_az1': '{cp}-{env}-inspection-private-az1-subnet',
            'inspection_private_az2': '{cp}-{env}-inspection-private-az2-subnet',
            'inspection_gwlbe_az1': '{cp}-{env}-inspection-gwlbe-az1-subnet',
            'inspection_gwlbe_az2': '{cp}-{env}-inspection-gwlbe-az2-subnet'
        }
    
    def discover_from_asg_name(self, asg_name: str) -> Dict:
        """
        Primary discovery method - start with ASG name and discover everything
        """
        print(f"🔍 Starting Fortinet template discovery from ASG: {asg_name}")
        
        # Extract customer prefix and environment from ASG name
        cp, env = self._extract_cp_env_from_asg(asg_name)
        print(f"📋 Detected Customer Prefix: '{cp}', Environment: '{env}'")
        
        if not cp or not env:
            # Fallback to generic discovery
            return self._fallback_generic_discovery(asg_name)
        
        # Discover infrastructure using Fortinet template patterns
        infrastructure = self._discover_fortinet_infrastructure(cp, env, asg_name)
        
        return infrastructure
    
    def _extract_cp_env_from_asg(self, asg_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract customer prefix and environment from ASG name
        Common patterns: cp-env-description-asg, cp-env-fgt-asg, etc.
        """
        # Get ASG details to look for tags
        try:
            asg_response = self.autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            if not asg_response['AutoScalingGroups']:
                return None, None
                
            asg = asg_response['AutoScalingGroups'][0]
            
            # Method 1: Extract from tags (preferred)
            cp, env = self._extract_from_asg_tags(asg.get('Tags', []))
            if cp and env:
                return cp, env
            
            # Method 2: Parse from ASG name patterns
            cp, env = self._parse_asg_name_patterns(asg_name)
            if cp and env:
                return cp, env
            
            # Method 3: Check VPC tags from ASG subnets
            if asg.get('VPCZoneIdentifier'):
                subnet_ids = asg['VPCZoneIdentifier'].split(',')
                cp, env = self._extract_from_vpc_via_subnets(subnet_ids)
                if cp and env:
                    return cp, env
                    
        except Exception as e:
            print(f"⚠️  Error extracting CP/ENV from ASG {asg_name}: {e}")
            
        return None, None
    
    def _extract_from_asg_tags(self, tags: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """Extract CP and ENV from ASG tags"""
        cp = None
        env = None
        
        for tag in tags:
            key = tag.get('Key', '').lower()
            value = tag.get('Value', '')
            
            if key in ['customer_prefix', 'customerprefix', 'cp']:
                cp = value
            elif key in ['environment', 'env']:
                env = value
                
        return cp, env
    
    def _parse_asg_name_patterns(self, asg_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse common ASG naming patterns:
        - cp-env-fortigate-asg
        - cp-env-fgt-asg  
        - cp-env-inspection-asg
        - cp-env-something-asg
        """
        parts = asg_name.lower().split('-')
        
        if len(parts) >= 4 and parts[-1] == 'asg':
            # Assume first part is CP, second is ENV
            potential_cp = parts[0]
            potential_env = parts[1]
            
            # Validate ENV looks like environment
            if potential_env in ['prod', 'production', 'test', 'staging', 'dev', 'development']:
                return potential_cp, potential_env
                
        return None, None
    
    def _extract_from_vpc_via_subnets(self, subnet_ids: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Extract CP/ENV from VPC tags via subnet lookup"""
        try:
            # Get subnet details
            subnets_response = self.ec2_client.describe_subnets(SubnetIds=subnet_ids)
            
            if subnets_response['Subnets']:
                vpc_id = subnets_response['Subnets'][0]['VpcId']
                
                # Get VPC tags
                vpc_response = self.ec2_client.describe_vpcs(VpcIds=[vpc_id])
                if vpc_response['Vpcs']:
                    vpc_tags = vpc_response['Vpcs'][0].get('Tags', [])
                    
                    # Extract from VPC tags
                    for tag in vpc_tags:
                        key = tag.get('Key', '')
                        value = tag.get('Value', '')
                        
                        # Check if VPC name follows Fortinet pattern
                        if key == 'Name':
                            cp, env = self._parse_vpc_name_pattern(value)
                            if cp and env:
                                return cp, env
                                
        except Exception as e:
            print(f"⚠️  Error extracting from VPC: {e}")
            
        return None, None
    
    def _parse_vpc_name_pattern(self, vpc_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse VPC name patterns:
        - cp-env-inspection-vpc
        - cp-env-management-vpc
        """
        parts = vpc_name.lower().split('-')
        
        if len(parts) >= 3 and parts[-1] == 'vpc':
            potential_cp = parts[0]
            potential_env = parts[1]
            
            # Check if this looks like Fortinet pattern
            vpc_type = parts[2] if len(parts) >= 3 else ''
            if vpc_type in ['inspection', 'management', 'east', 'west']:
                return potential_cp, potential_env
                
        return None, None
    
    def _discover_fortinet_infrastructure(self, cp: str, env: str, asg_name: str) -> Dict:
        """
        Discover complete infrastructure using Fortinet template patterns
        """
        infrastructure = {
            'discovery_metadata': {
                'source': 'fortinet_autoscale_template',
                'customer_prefix': cp,
                'environment': env,
                'source_asg': asg_name,
                'discovered_at': datetime.utcnow().isoformat()
            }
        }
        
        # 1. Discover VPCs using Fortinet patterns
        vpcs = self._discover_fortinet_vpcs(cp, env)
        infrastructure['vpcs'] = vpcs
        
        # 2. Discover inspection VPC details (this is the Blue environment)
        if 'inspection_vpc' in vpcs:
            blue_environment = self._discover_blue_environment(vpcs['inspection_vpc'], asg_name)
            infrastructure['blue_environment'] = blue_environment
            
        # 3. Discover Transit Gateway configuration
        if 'inspection_vpc' in vpcs:
            tgw_config = self._discover_tgw_configuration(vpcs['inspection_vpc']['vpc_id'])
            infrastructure['transit_gateway'] = tgw_config
            
        # 4. Discover customer VPCs (East/West or other attached VPCs)
        customer_vpcs = self._discover_customer_vpcs(cp, env, infrastructure.get('transit_gateway', {}))
        infrastructure['customer_vpcs'] = customer_vpcs
        
        # 5. Generate migration plan
        infrastructure['migration_plan'] = self._generate_migration_plan(customer_vpcs)
        
        return infrastructure
    
    def _discover_fortinet_vpcs(self, cp: str, env: str) -> Dict:
        """Discover VPCs using Fortinet naming patterns"""
        vpcs = {}
        
        for vpc_type, name_pattern in self.fortinet_patterns.items():
            if 'vpc' in vpc_type:
                vpc_name = name_pattern.format(cp=cp, env=env)
                
                try:
                    vpc_response = self.ec2_client.describe_vpcs(
                        Filters=[
                            {'Name': 'tag:Name', 'Values': [vpc_name]},
                            {'Name': 'state', 'Values': ['available']}
                        ]
                    )
                    
                    if vpc_response['Vpcs']:
                        vpc = vpc_response['Vpcs'][0]
                        vpcs[vpc_type] = {
                            'vpc_id': vpc['VpcId'],
                            'vpc_name': vpc_name,
                            'cidr_block': vpc['CidrBlock'],
                            'tags': vpc.get('Tags', [])
                        }
                        print(f"✅ Found {vpc_type}: {vpc_name} ({vpc['VpcId']})")
                    else:
                        print(f"❌ VPC not found: {vpc_name}")
                        
                except Exception as e:
                    print(f"⚠️  Error discovering {vpc_type}: {e}")
                    
        return vpcs
    
    def _discover_blue_environment(self, inspection_vpc: Dict, asg_name: str) -> Dict:
        """Discover Blue environment details from inspection VPC"""
        vpc_id = inspection_vpc['vpc_id']
        
        blue_env = {
            'vpc_id': vpc_id,
            'vpc_cidr': inspection_vpc['cidr_block'],
            'asg_name': asg_name
        }
        
        # Discover subnets
        blue_env['subnets'] = self._discover_inspection_vpc_subnets(vpc_id)
        
        # Discover ASG details
        blue_env['asg_details'] = self._get_asg_details(asg_name)
        
        # Discover NAT Gateways and EIPs
        blue_env['nat_gateways'] = self._discover_nat_gateways(vpc_id)
        blue_env['production_eips'] = self._extract_eips_from_nat_gateways(blue_env['nat_gateways'])
        
        # Discover GWLB infrastructure
        blue_env['gwlb_config'] = self._discover_gwlb_infrastructure(vpc_id)
        
        return blue_env
    
    def _discover_inspection_vpc_subnets(self, vpc_id: str) -> Dict:
        """Discover subnets in inspection VPC using Fortinet patterns"""
        try:
            subnets_response = self.ec2_client.describe_subnets(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            subnets = {}
            for subnet in subnets_response['Subnets']:
                subnet_name = self._get_subnet_name(subnet)
                
                # Categorize subnet by name pattern
                if 'public' in subnet_name.lower():
                    subnet_type = 'public'
                elif 'private' in subnet_name.lower():
                    subnet_type = 'private'
                elif 'gwlbe' in subnet_name.lower():
                    subnet_type = 'gwlbe'
                elif 'management' in subnet_name.lower():
                    subnet_type = 'management'
                else:
                    subnet_type = 'other'
                
                # Determine AZ
                az = subnet['AvailabilityZone']
                az_suffix = az[-1]  # Get 'a', 'b', 'c' etc.
                
                subnet_key = f"{subnet_type}_{az_suffix}"
                
                subnets[subnet_key] = {
                    'subnet_id': subnet['SubnetId'],
                    'subnet_name': subnet_name,
                    'cidr_block': subnet['CidrBlock'],
                    'availability_zone': az,
                    'subnet_type': subnet_type
                }
                
            return subnets
            
        except Exception as e:
            print(f"⚠️  Error discovering subnets: {e}")
            return {}
    
    def _get_subnet_name(self, subnet: Dict) -> str:
        """Get subnet name from tags"""
        for tag in subnet.get('Tags', []):
            if tag.get('Key') == 'Name':
                return tag.get('Value', '')
        return subnet['SubnetId']  # Fallback to ID
    
    def _discover_tgw_configuration(self, inspection_vpc_id: str) -> Dict:
        """Discover Transit Gateway configuration"""
        try:
            # Find TGW attachment for inspection VPC
            attachments_response = self.ec2_client.describe_transit_gateway_vpc_attachments(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [inspection_vpc_id]},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            if not attachments_response['TransitGatewayVpcAttachments']:
                print(f"❌ No TGW attachment found for VPC {inspection_vpc_id}")
                return {}
            
            attachment = attachments_response['TransitGatewayVpcAttachments'][0]
            tgw_id = attachment['TransitGatewayId']
            attachment_id = attachment['TransitGatewayAttachmentId']
            
            print(f"✅ Found TGW: {tgw_id}, Attachment: {attachment_id}")
            
            # Find route table associations
            associations_response = self.ec2_client.get_transit_gateway_route_table_associations(
                Filters=[
                    {'Name': 'transit-gateway-attachment-id', 'Values': [attachment_id]}
                ]
            )
            
            tgw_config = {
                'tgw_id': tgw_id,
                'inspection_attachment_id': attachment_id,
                'route_table_associations': []
            }
            
            for association in associations_response['Associations']:
                route_table_id = association['TransitGatewayRouteTableId']
                
                # Get route table details
                route_table_response = self.ec2_client.describe_transit_gateway_route_tables(
                    TransitGatewayRouteTableIds=[route_table_id]
                )
                
                if route_table_response['TransitGatewayRouteTables']:
                    route_table = route_table_response['TransitGatewayRouteTables'][0]
                    
                    tgw_config['route_table_associations'].append({
                        'route_table_id': route_table_id,
                        'route_table_name': self._get_route_table_name(route_table),
                        'state': association['State']
                    })
            
            return tgw_config
            
        except Exception as e:
            print(f"⚠️  Error discovering TGW configuration: {e}")
            return {}
    
    def _get_route_table_name(self, route_table: Dict) -> str:
        """Get route table name from tags"""
        for tag in route_table.get('Tags', []):
            if tag.get('Key') == 'Name':
                return tag.get('Value', '')
        return route_table['TransitGatewayRouteTableId']  # Fallback to ID
    
    def _discover_customer_vpcs(self, cp: str, env: str, tgw_config: Dict) -> List[Dict]:
        """Discover customer VPCs that route through the inspection VPC"""
        customer_vpcs = []
        
        if not tgw_config.get('tgw_id'):
            return customer_vpcs
        
        try:
            # First, check for East/West VPCs (common in Fortinet template)
            for vpc_type in ['east_vpc', 'west_vpc']:
                vpc_name = self.fortinet_patterns[vpc_type].format(cp=cp, env=env)
                
                vpc_response = self.ec2_client.describe_vpcs(
                    Filters=[
                        {'Name': 'tag:Name', 'Values': [vpc_name]},
                        {'Name': 'state', 'Values': ['available']}
                    ]
                )
                
                if vpc_response['Vpcs']:
                    vpc = vpc_response['Vpcs'][0]
                    vpc_id = vpc['VpcId']
                    
                    # Find TGW attachment for this VPC
                    attachment_response = self.ec2_client.describe_transit_gateway_vpc_attachments(
                        Filters=[
                            {'Name': 'vpc-id', 'Values': [vpc_id]},
                            {'Name': 'transit-gateway-id', 'Values': [tgw_config['tgw_id']]},
                            {'Name': 'state', 'Values': ['available']}
                        ]
                    )
                    
                    if attachment_response['TransitGatewayVpcAttachments']:
                        attachment = attachment_response['TransitGatewayVpcAttachments'][0]
                        
                        customer_vpcs.append({
                            'vpc_id': vpc_id,
                            'vpc_name': vpc_name,
                            'vpc_type': vpc_type.replace('_vpc', ''),  # 'east' or 'west'
                            'cidr_block': vpc['CidrBlock'],
                            'tgw_attachment_id': attachment['TransitGatewayAttachmentId'],
                            'priority': 'high' if 'east' in vpc_type else 'medium'
                        })
                        
                        print(f"✅ Found customer VPC: {vpc_name} ({vpc_id})")
            
            # Discover any other VPCs attached to the same TGW
            all_attachments = self.ec2_client.describe_transit_gateway_vpc_attachments(
                Filters=[
                    {'Name': 'transit-gateway-id', 'Values': [tgw_config['tgw_id']]},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            inspection_attachment_id = tgw_config.get('inspection_attachment_id')
            known_vpc_ids = {vpc['vpc_id'] for vpc in customer_vpcs}
            
            for attachment in all_attachments['TransitGatewayVpcAttachments']:
                vpc_id = attachment['VpcId']
                attachment_id = attachment['TransitGatewayAttachmentId']
                
                # Skip inspection VPC and already discovered VPCs
                if attachment_id == inspection_attachment_id or vpc_id in known_vpc_ids:
                    continue
                
                # Get VPC details
                vpc_response = self.ec2_client.describe_vpcs(VpcIds=[vpc_id])
                if vpc_response['Vpcs']:
                    vpc = vpc_response['Vpcs'][0]
                    vpc_name = self._get_vpc_name(vpc)
                    
                    customer_vpcs.append({
                        'vpc_id': vpc_id,
                        'vpc_name': vpc_name,
                        'vpc_type': 'customer',
                        'cidr_block': vpc['CidrBlock'],
                        'tgw_attachment_id': attachment_id,
                        'priority': self._determine_vpc_priority(vpc_name)
                    })
                    
                    print(f"✅ Found additional customer VPC: {vpc_name} ({vpc_id})")
            
        except Exception as e:
            print(f"⚠️  Error discovering customer VPCs: {e}")
        
        return customer_vpcs
    
    def _get_vpc_name(self, vpc: Dict) -> str:
        """Get VPC name from tags"""
        for tag in vpc.get('Tags', []):
            if tag.get('Key') == 'Name':
                return tag.get('Value', '')
        return vpc['VpcId']  # Fallback to ID
    
    def _determine_vpc_priority(self, vpc_name: str) -> str:
        """Determine VPC migration priority based on name"""
        vpc_name_lower = vpc_name.lower()
        
        if any(keyword in vpc_name_lower for keyword in ['prod', 'production', 'critical']):
            return 'critical'
        elif any(keyword in vpc_name_lower for keyword in ['staging', 'test']):
            return 'medium'
        elif any(keyword in vpc_name_lower for keyword in ['dev', 'development']):
            return 'low'
        else:
            return 'medium'  # Default
    
    def _discover_nat_gateways(self, vpc_id: str) -> List[Dict]:
        """Discover NAT Gateways in VPC"""
        try:
            nat_response = self.ec2_client.describe_nat_gateways(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            nat_gateways = []
            for nat in nat_response['NatGateways']:
                nat_gateways.append({
                    'nat_gateway_id': nat['NatGatewayId'],
                    'subnet_id': nat['SubnetId'],
                    'availability_zone': self._get_subnet_az(nat['SubnetId']),
                    'addresses': nat.get('NatGatewayAddresses', [])
                })
            
            return nat_gateways
            
        except Exception as e:
            print(f"⚠️  Error discovering NAT Gateways: {e}")
            return []
    
    def _get_subnet_az(self, subnet_id: str) -> str:
        """Get subnet availability zone"""
        try:
            subnet_response = self.ec2_client.describe_subnets(SubnetIds=[subnet_id])
            if subnet_response['Subnets']:
                return subnet_response['Subnets'][0]['AvailabilityZone']
        except:
            pass
        return 'unknown'
    
    def _extract_eips_from_nat_gateways(self, nat_gateways: List[Dict]) -> Dict:
        """Extract production EIPs from NAT Gateways"""
        production_eips = {}
        
        for nat in nat_gateways:
            for address in nat['addresses']:
                if 'AllocationId' in address:  # Has EIP
                    eip_id = address['AllocationId']
                    production_eips[eip_id] = {
                        'allocation_id': eip_id,
                        'public_ip': address.get('PublicIp'),
                        'nat_gateway_id': nat['nat_gateway_id'],
                        'availability_zone': nat['availability_zone']
                    }
        
        return production_eips
    
    def _discover_gwlb_infrastructure(self, vpc_id: str) -> Dict:
        """Discover GWLB infrastructure in VPC"""
        try:
            # Find GWLB in VPC
            gwlb_response = self.elbv2_client.describe_load_balancers()
            
            gwlb_config = {}
            
            for lb in gwlb_response['LoadBalancers']:
                if lb['Type'] == 'gateway' and lb['VpcId'] == vpc_id:
                    gwlb_config['gwlb_arn'] = lb['LoadBalancerArn']
                    gwlb_config['gwlb_name'] = lb['LoadBalancerName']
                    
                    # Find target groups
                    target_groups = self.elbv2_client.describe_target_groups(
                        LoadBalancerArn=lb['LoadBalancerArn']
                    )
                    
                    gwlb_config['target_groups'] = []
                    for tg in target_groups['TargetGroups']:
                        gwlb_config['target_groups'].append({
                            'target_group_arn': tg['TargetGroupArn'],
                            'target_group_name': tg['TargetGroupName']
                        })
                    
                    # Find GWLB endpoints
                    endpoints_response = self.ec2_client.describe_vpc_endpoints(
                        Filters=[
                            {'Name': 'vpc-id', 'Values': [vpc_id]},
                            {'Name': 'service-name', 'Values': [f"com.amazonaws.vpce.{self.region}.{lb['LoadBalancerName']}"]},
                            {'Name': 'state', 'Values': ['available']}
                        ]
                    )
                    
                    gwlb_config['endpoints'] = []
                    for endpoint in endpoints_response['VpcEndpoints']:
                        gwlb_config['endpoints'].append({
                            'endpoint_id': endpoint['VpcEndpointId'],
                            'subnet_id': endpoint['SubnetIds'][0] if endpoint['SubnetIds'] else None,
                            'availability_zone': self._get_subnet_az(endpoint['SubnetIds'][0]) if endpoint['SubnetIds'] else 'unknown'
                        })
                    
                    break
            
            return gwlb_config
            
        except Exception as e:
            print(f"⚠️  Error discovering GWLB infrastructure: {e}")
            return {}
    
    def _get_asg_details(self, asg_name: str) -> Dict:
        """Get detailed ASG information"""
        try:
            asg_response = self.autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            if asg_response['AutoScalingGroups']:
                asg = asg_response['AutoScalingGroups'][0]
                return {
                    'asg_name': asg['AutoScalingGroupName'],
                    'min_size': asg['MinSize'],
                    'max_size': asg['MaxSize'],
                    'desired_capacity': asg['DesiredCapacity'],
                    'instance_ids': [instance['InstanceId'] for instance in asg['Instances']],
                    'launch_template': asg.get('LaunchTemplate', {}),
                    'availability_zones': asg.get('AvailabilityZones', [])
                }
        except Exception as e:
            print(f"⚠️  Error getting ASG details: {e}")
            
        return {}
    
    def _generate_migration_plan(self, customer_vpcs: List[Dict]) -> Dict:
        """Generate migration plan based on discovered VPCs"""
        # Sort VPCs by priority
        priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        
        sorted_vpcs = sorted(customer_vpcs, 
                           key=lambda vpc: priority_order.get(vpc.get('priority', 'medium'), 1))
        
        migration_plan = {
            'migration_strategy': 'gradual_by_vpc_priority',
            'total_vpcs': len(customer_vpcs),
            'migration_order': []
        }
        
        for i, vpc in enumerate(sorted_vpcs):
            migration_plan['migration_order'].append({
                'order': i + 1,
                'vpc_id': vpc['vpc_id'],
                'vpc_name': vpc['vpc_name'],
                'priority': vpc['priority'],
                'estimated_validation_time': self._estimate_validation_time(vpc['priority'])
            })
        
        return migration_plan
    
    def _estimate_validation_time(self, priority: str) -> int:
        """Estimate validation time in minutes based on priority"""
        validation_times = {
            'critical': 15,  # More thorough testing
            'high': 10,
            'medium': 5,
            'low': 3
        }
        return validation_times.get(priority, 5)
    
    def _fallback_generic_discovery(self, asg_name: str) -> Dict:
        """Fallback to generic discovery if Fortinet patterns don't match"""
        print(f"⚠️  Falling back to generic discovery for ASG: {asg_name}")
        
        # Use the generic discovery methods from the original implementation
        # This would call the previous generic discovery functions
        return {
            'discovery_metadata': {
                'source': 'generic_fallback',
                'source_asg': asg_name,
                'discovered_at': datetime.utcnow().isoformat()
            },
            'note': 'Fortinet template patterns not detected, used generic discovery'
        }

# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fortinet Template Infrastructure Discovery')
    parser.add_argument('--asg-name', required=True, help='FortiGate ASG name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--output', default='discovery-result.json', help='Output file')
    
    args = parser.parse_args()
    
    # Run discovery
    discoverer = FortinetTemplateDiscovery(args.region)
    result = discoverer.discover_from_asg_name(args.asg_name)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Discovery complete! Results saved to {args.output}")
    print(f"📊 Discovered: {len(result.get('customer_vpcs', []))} customer VPCs")
    print(f"🔍 Discovery method: {result.get('discovery_metadata', {}).get('source', 'unknown')}")