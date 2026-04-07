#!/usr/bin/env python3
"""
Test script to demonstrate point-to-point neighbor detection for /31 and /127 networks.
"""

import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configure_vrf_subinterfaces import (
    get_point_to_point_neighbor,
    is_point_to_point_network,
    get_network_base_ip,
    SubInterfaceConfig
)


def test_ipv4_p2p():
    """Test IPv4 /31 point-to-point networks."""
    print("="*60)
    print("Testing IPv4 /31 Point-to-Point Networks")
    print("="*60)
    
    test_cases = [
        "10.0.0.0/31",
        "10.0.0.1/31",
        "192.168.1.0/31",
        "192.168.1.1/31",
        "172.16.0.100/31",
        "172.16.0.101/31",
        "10.0.0.0/24",  # Not a /31
    ]
    
    for ip in test_cases:
        is_p2p = is_point_to_point_network(ip)
        neighbor = get_point_to_point_neighbor(ip)
        base_ip = get_network_base_ip(ip)
        
        print(f"\nIP: {ip}")
        print(f"  Is P2P (/31): {is_p2p}")
        if neighbor:
            print(f"  Neighbor: {neighbor}")
        print(f"  Base IP: {base_ip}")


def test_ipv6_p2p():
    """Test IPv6 /127 point-to-point networks."""
    print("\n" + "="*60)
    print("Testing IPv6 /127 Point-to-Point Networks")
    print("="*60)
    
    test_cases = [
        "fc00::0/127",
        "fc00::1/127",
        "fc00:0:0::0/127",
        "fc00:0:0::1/127",
        "2001:db8::0/127",
        "2001:db8::1/127",
        "fc00::0/64",  # Not a /127
    ]
    
    for ip in test_cases:
        is_p2p = is_point_to_point_network(ip)
        neighbor = get_point_to_point_neighbor(ip)
        base_ip = get_network_base_ip(ip)
        
        print(f"\nIPv6: {ip}")
        print(f"  Is P2P (/127): {is_p2p}")
        if neighbor:
            print(f"  Neighbor: {neighbor}")
        print(f"  Base IP: {base_ip}")


def test_subinterface_methods():
    """Test SubInterfaceConfig methods for neighbor detection."""
    print("\n" + "="*60)
    print("Testing SubInterfaceConfig Neighbor Methods")
    print("="*60)
    
    # Test with /31 IPv4
    sub_int1 = SubInterfaceConfig(
        parent_interface="Ethernet0",
        vlan_id=100,
        ip_address="10.0.0.0/31",
        ipv6_address="fc00::0/127",
        vrf_name="Vrf1"
    )
    
    print(f"\nSub-interface: {sub_int1.name}")
    print(f"  IPv4: {sub_int1.ip_address}")
    print(f"  Is IPv4 P2P: {sub_int1.is_ipv4_point_to_point()}")
    print(f"  IPv4 Neighbor: {sub_int1.get_neighbor_ipv4()}")
    print(f"  IPv6: {sub_int1.ipv6_address}")
    print(f"  Is IPv6 P2P: {sub_int1.is_ipv6_point_to_point()}")
    print(f"  IPv6 Neighbor: {sub_int1.get_neighbor_ipv6()}")
    
    # Test with non-P2P networks
    sub_int2 = SubInterfaceConfig(
        parent_interface="Ethernet1",
        vlan_id=200,
        ip_address="10.0.0.1/24",
        ipv6_address="fc00::1/64",
        vrf_name="Vrf2"
    )
    
    print(f"\nSub-interface: {sub_int2.name}")
    print(f"  IPv4: {sub_int2.ip_address}")
    print(f"  Is IPv4 P2P: {sub_int2.is_ipv4_point_to_point()}")
    print(f"  IPv4 Neighbor: {sub_int2.get_neighbor_ipv4()}")
    print(f"  IPv6: {sub_int2.ipv6_address}")
    print(f"  Is IPv6 P2P: {sub_int2.is_ipv6_point_to_point()}")
    print(f"  IPv6 Neighbor: {sub_int2.get_neighbor_ipv6()}")


if __name__ == "__main__":
    test_ipv4_p2p()
    test_ipv6_p2p()
    test_subinterface_methods()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)

