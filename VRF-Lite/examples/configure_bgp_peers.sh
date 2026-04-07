#!/bin/bash
# Complete BGP Peering Configuration Script
# This script configures both the sub-interfaces and BGP peering
#
# Usage:
#   1. First, run the VRF sub-interface configuration script
#   2. Then, run this script to configure BGP
#
# Example:
#   python3 configure_vrf_subinterfaces.py --config examples/bgp_peers.yaml --output-cli setup_interfaces.sh
#   bash setup_interfaces.sh
#   bash examples/configure_bgp_peers.sh

# Local AS Number
LOCAL_ASN=65000

echo "Configuring BGP for VRF-based peering..."

# Configure BGP using vtysh
vtysh << EOF

configure terminal

! ============================================================
! ISP Uplinks
! ============================================================

! ISP_A - Ethernet0.100
router bgp ${LOCAL_ASN} vrf ISP_A
  neighbor 10.1.1.1 remote-as 65001
  neighbor 10.1.1.1 description ISP_A-IPv4
  neighbor 2001:db8:1::1 remote-as 65001
  neighbor 2001:db8:1::1 description ISP_A-IPv6
  !
  address-family ipv4 unicast
    neighbor 10.1.1.1 activate
    neighbor 10.1.1.1 soft-reconfiguration inbound
    neighbor 10.1.1.1 prefix-list ISP_A_IN in
    neighbor 10.1.1.1 prefix-list ISP_A_OUT out
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor 2001:db8:1::1 activate
    neighbor 2001:db8:1::1 soft-reconfiguration inbound
  exit-address-family
exit

! ISP_B - Ethernet0.101
router bgp ${LOCAL_ASN} vrf ISP_B
  neighbor 10.1.1.3 remote-as 65002
  neighbor 10.1.1.3 description ISP_B-IPv4
  neighbor 2001:db8:1::3 remote-as 65002
  neighbor 2001:db8:1::3 description ISP_B-IPv6
  !
  address-family ipv4 unicast
    neighbor 10.1.1.3 activate
    neighbor 10.1.1.3 soft-reconfiguration inbound
    neighbor 10.1.1.3 prefix-list ISP_B_IN in
    neighbor 10.1.1.3 prefix-list ISP_B_OUT out
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor 2001:db8:1::3 activate
    neighbor 2001:db8:1::3 soft-reconfiguration inbound
  exit-address-family
exit

! ============================================================
! Customer Peering
! ============================================================

! Customer_Alpha - Ethernet1.200
router bgp ${LOCAL_ASN} vrf Customer_Alpha
  neighbor 10.2.1.1 remote-as 65100
  neighbor 10.2.1.1 description Customer_Alpha-IPv4
  neighbor 2001:db8:2::1 remote-as 65100
  neighbor 2001:db8:2::1 description Customer_Alpha-IPv6
  !
  address-family ipv4 unicast
    neighbor 10.2.1.1 activate
    neighbor 10.2.1.1 soft-reconfiguration inbound
    neighbor 10.2.1.1 route-map CUSTOMER_IN in
    neighbor 10.2.1.1 route-map CUSTOMER_OUT out
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor 2001:db8:2::1 activate
    neighbor 2001:db8:2::1 soft-reconfiguration inbound
  exit-address-family
exit

! Customer_Beta - Ethernet1.201
router bgp ${LOCAL_ASN} vrf Customer_Beta
  neighbor 10.2.1.3 remote-as 65101
  neighbor 10.2.1.3 description Customer_Beta-IPv4
  neighbor 2001:db8:2::3 remote-as 65101
  neighbor 2001:db8:2::3 description Customer_Beta-IPv6
  !
  address-family ipv4 unicast
    neighbor 10.2.1.3 activate
    neighbor 10.2.1.3 soft-reconfiguration inbound
    neighbor 10.2.1.3 route-map CUSTOMER_IN in
    neighbor 10.2.1.3 route-map CUSTOMER_OUT out
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor 2001:db8:2::3 activate
    neighbor 2001:db8:2::3 soft-reconfiguration inbound
  exit-address-family
exit

! Customer_Gamma - Ethernet1.202
router bgp ${LOCAL_ASN} vrf Customer_Gamma
  neighbor 10.2.1.5 remote-as 65102
  neighbor 10.2.1.5 description Customer_Gamma-IPv4
  neighbor 2001:db8:2::5 remote-as 65102
  neighbor 2001:db8:2::5 description Customer_Gamma-IPv6
  !
  address-family ipv4 unicast
    neighbor 10.2.1.5 activate
    neighbor 10.2.1.5 soft-reconfiguration inbound
    neighbor 10.2.1.5 route-map CUSTOMER_IN in
    neighbor 10.2.1.5 route-map CUSTOMER_OUT out
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor 2001:db8:2::5 activate
    neighbor 2001:db8:2::5 soft-reconfiguration inbound
  exit-address-family
exit

! ============================================================
! Transit Providers
! ============================================================

! Transit_1 - Po10.300
router bgp ${LOCAL_ASN} vrf Transit_1
  neighbor 172.16.0.1 remote-as 65200
  neighbor 172.16.0.1 description Transit_1-IPv4
  neighbor fc00::1 remote-as 65200
  neighbor fc00::1 description Transit_1-IPv6
  !
  address-family ipv4 unicast
    neighbor 172.16.0.1 activate
    neighbor 172.16.0.1 soft-reconfiguration inbound
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor fc00::1 activate
    neighbor fc00::1 soft-reconfiguration inbound
  exit-address-family
exit

! Transit_2 - Po10.301
router bgp ${LOCAL_ASN} vrf Transit_2
  neighbor 172.16.0.3 remote-as 65201
  neighbor 172.16.0.3 description Transit_2-IPv4
  neighbor fc00::3 remote-as 65201
  neighbor fc00::3 description Transit_2-IPv6
  !
  address-family ipv4 unicast
    neighbor 172.16.0.3 activate
    neighbor 172.16.0.3 soft-reconfiguration inbound
  exit-address-family
  !
  address-family ipv6 unicast
    neighbor fc00::3 activate
    neighbor fc00::3 soft-reconfiguration inbound
  exit-address-family
exit

end
write memory
EOF

echo "BGP configuration completed!"
echo ""
echo "To verify BGP neighbors, run:"
echo "  vtysh -c 'show bgp vrf all summary'"
echo ""
echo "To check specific VRF:"
echo "  vtysh -c 'show bgp vrf ISP_A summary'"
echo "  vtysh -c 'show bgp vrf Customer_Alpha neighbors'"

