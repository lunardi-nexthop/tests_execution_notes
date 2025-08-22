#!/usr/bin/env python3

"""
Script to trace nexthops for route entries in SONiC ASIC DB and State DB.
This script takes route entries and traces their nexthop information through
the SAI object hierarchy.

Usage: python3 trace_route_nexthops.py [options]
"""

import json
import re
import sys
import argparse
from swsscommon import swsscommon

class RouteNexthopTracer:
    def __init__(self, namespace=""):
        self.namespace = namespace
        self.asic_db = swsscommon.DBConnector('ASIC_DB', 0, True, namespace)
        self.state_db = swsscommon.DBConnector('STATE_DB', 0, True, namespace)
        
    def get_route_entries(self, pattern="*ROUTE_ENTRY*"):
        """Get all route entries matching the pattern"""
        table = swsscommon.Table(self.asic_db, 'ASIC_STATE')
        keys = table.getKeys()
        route_keys = [key for key in keys if 'SAI_OBJECT_TYPE_ROUTE_ENTRY' in key and pattern.replace('*', '') in key]
        return route_keys
    
    def parse_route_key(self, route_key):
        """Parse route key to extract destination, switch_id, and vr"""
        # Extract JSON part from route key
        match = re.search(r'\{.*\}', route_key)
        if match:
            try:
                route_info = json.loads(match.group())
                return route_info
            except json.JSONDecodeError:
                return None
        return None
    
    def get_route_attributes(self, route_key):
        """Get route attributes including nexthop ID"""
        table = swsscommon.Table(self.asic_db, 'ASIC_STATE')
        (status, fvs) = table.get(route_key)
        if status:
            attrs = dict(fvs)
            return attrs
        return {}
    
    def get_nexthop_info(self, nexthop_id):
        """Get nexthop information from ASIC DB"""
        if not nexthop_id or nexthop_id == "SAI_NULL_OBJECT_ID":
            return None
            
        # Check if it's a nexthop group or individual nexthop
        if nexthop_id.startswith('oid:0x5'):  # Nexthop group
            return self.get_nexthop_group_info(nexthop_id)
        elif nexthop_id.startswith('oid:0x4'):  # Individual nexthop
            return self.get_individual_nexthop_info(nexthop_id)
        elif nexthop_id.startswith('oid:0x6'):  # Router interface
            return self.get_router_interface_info(nexthop_id)
        else:
            return {"type": "unknown", "id": nexthop_id}
    
    def get_nexthop_group_info(self, nhg_id):
        """Get nexthop group information and its members"""
        table = swsscommon.Table(self.asic_db, 'ASIC_STATE')
        nhg_key = f"SAI_OBJECT_TYPE_NEXT_HOP_GROUP:{nhg_id}"
        
        (status, fvs) = table.get(nhg_key)
        nhg_info = {"type": "nexthop_group", "id": nhg_id, "attributes": {}, "members": []}
        
        if status:
            nhg_info["attributes"] = dict(fvs)
        
        # Get nexthop group members
        all_keys = table.getKeys()
        member_keys = [key for key in all_keys if 'SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER' in key]
        
        for member_key in member_keys:
            (status, fvs) = table.get(member_key)
            if status:
                member_attrs = dict(fvs)
                if member_attrs.get('SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_GROUP_ID') == nhg_id:
                    member_nh_id = member_attrs.get('SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_ID')
                    member_info = self.get_individual_nexthop_info(member_nh_id)
                    nhg_info["members"].append({
                        "member_id": member_key.split(':')[-1],
                        "nexthop_id": member_nh_id,
                        "nexthop_info": member_info
                    })
        
        return nhg_info
    
    def get_individual_nexthop_info(self, nh_id):
        """Get individual nexthop information"""
        table = swsscommon.Table(self.asic_db, 'ASIC_STATE')
        nh_key = f"SAI_OBJECT_TYPE_NEXT_HOP:{nh_id}"
        
        (status, fvs) = table.get(nh_key)
        nh_info = {"type": "nexthop", "id": nh_id, "attributes": {}}
        
        if status:
            attrs = dict(fvs)
            nh_info["attributes"] = attrs
            
            # Get router interface info if present
            rif_id = attrs.get('SAI_NEXT_HOP_ATTR_ROUTER_INTERFACE_ID')
            if rif_id:
                nh_info["router_interface"] = self.get_router_interface_info(rif_id)
        
        return nh_info
    
    def get_router_interface_info(self, rif_id):
        """Get router interface information"""
        table = swsscommon.Table(self.asic_db, 'ASIC_STATE')
        rif_key = f"SAI_OBJECT_TYPE_ROUTER_INTERFACE:{rif_id}"
        
        (status, fvs) = table.get(rif_key)
        rif_info = {"type": "router_interface", "id": rif_id, "attributes": {}}
        
        if status:
            rif_info["attributes"] = dict(fvs)
        
        return rif_info
    
    def trace_route_nexthops(self, route_destinations=None):
        """Main function to trace nexthops for given route destinations"""
        if route_destinations:
            # Filter for specific destinations
            all_routes = []
            for dest in route_destinations:
                pattern = f"*{dest}*"
                routes = self.get_route_entries(pattern)
                all_routes.extend(routes)
        else:
            # Get all route entries
            all_routes = self.get_route_entries()
        
        results = []
        
        for route_key in all_routes:
            route_info = self.parse_route_key(route_key)
            if not route_info:
                continue
                
            route_attrs = self.get_route_attributes(route_key)
            nexthop_id = route_attrs.get('SAI_ROUTE_ENTRY_ATTR_NEXT_HOP_ID')
            
            nexthop_info = self.get_nexthop_info(nexthop_id) if nexthop_id else None
            
            result = {
                "route_key": route_key,
                "destination": route_info.get('dest'),
                "vr": route_info.get('vr'),
                "switch_id": route_info.get('switch_id'),
                "route_attributes": route_attrs,
                "nexthop_info": nexthop_info
            }
            
            results.append(result)
        
        return results
    
    def print_results(self, results, verbose=False):
        """Print the traced nexthop results"""
        for i, result in enumerate(results, 1):
            print(f"\n{'='*80}")
            print(f"Route #{i}: {result['destination']}")
            print(f"{'='*80}")
            print(f"VR: {result['vr']}")
            print(f"Switch ID: {result['switch_id']}")
            
            if verbose:
                print(f"Route Key: {result['route_key']}")
                print(f"Route Attributes: {json.dumps(result['route_attributes'], indent=2)}")
            
            nexthop_info = result['nexthop_info']
            if nexthop_info:
                self.print_nexthop_info(nexthop_info, verbose)
            else:
                print("No nexthop information found")
    
    def print_nexthop_info(self, nexthop_info, verbose=False):
        """Print nexthop information recursively"""
        if nexthop_info['type'] == 'nexthop_group':
            print(f"\nNexthop Group: {nexthop_info['id']}")
            if verbose and nexthop_info['attributes']:
                print(f"  Attributes: {json.dumps(nexthop_info['attributes'], indent=4)}")
            
            print(f"  Members ({len(nexthop_info['members'])}):")
            for member in nexthop_info['members']:
                print(f"    Member ID: {member['member_id']}")
                print(f"    Nexthop ID: {member['nexthop_id']}")
                if member['nexthop_info']:
                    self.print_individual_nexthop(member['nexthop_info'], indent="      ", verbose=verbose)
        
        elif nexthop_info['type'] == 'nexthop':
            print(f"\nNexthop: {nexthop_info['id']}")
            self.print_individual_nexthop(nexthop_info, verbose=verbose)
        
        elif nexthop_info['type'] == 'router_interface':
            print(f"\nRouter Interface: {nexthop_info['id']}")
            if verbose and nexthop_info['attributes']:
                print(f"  Attributes: {json.dumps(nexthop_info['attributes'], indent=4)}")
    
    def print_individual_nexthop(self, nh_info, indent="  ", verbose=False):
        """Print individual nexthop details"""
        attrs = nh_info.get('attributes', {})
        
        nh_type = attrs.get('SAI_NEXT_HOP_ATTR_TYPE', 'Unknown')
        nh_ip = attrs.get('SAI_NEXT_HOP_ATTR_IP', 'Unknown')
        
        print(f"{indent}Type: {nh_type}")
        print(f"{indent}IP: {nh_ip}")
        
        if 'router_interface' in nh_info:
            rif_info = nh_info['router_interface']
            print(f"{indent}Router Interface: {rif_info['id']}")
            
            rif_attrs = rif_info.get('attributes', {})
            port_id = rif_attrs.get('SAI_ROUTER_INTERFACE_ATTR_PORT_ID')
            vlan_id = rif_attrs.get('SAI_ROUTER_INTERFACE_ATTR_VLAN_ID')
            
            if port_id:
                print(f"{indent}  Port ID: {port_id}")
            if vlan_id:
                print(f"{indent}  VLAN ID: {vlan_id}")
        
        if verbose and attrs:
            print(f"{indent}All Attributes: {json.dumps(attrs, indent=len(indent)+2)}")

def main():
    parser = argparse.ArgumentParser(description='Trace nexthops for SONiC route entries')
    parser.add_argument('-d', '--destinations', nargs='+', 
                       help='Specific route destinations to trace (e.g., 20.3.10.100/31)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed attribute information')
    parser.add_argument('-n', '--namespace', default='',
                       help='Namespace to query (default: global)')
    
    args = parser.parse_args()
    
    tracer = RouteNexthopTracer(args.namespace)
    
    try:
        results = tracer.trace_route_nexthops(args.destinations)
        tracer.print_results(results, args.verbose)
        
        print(f"\n{'='*80}")
        print(f"Total routes traced: {len(results)}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
