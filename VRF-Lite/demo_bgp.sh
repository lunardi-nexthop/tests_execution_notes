#!/bin/bash
# Auto-generated BGP configuration
# Local ASN: 65000

vtysh << 'EOF'
configure terminal

! ============================================================
! VRF: ISP1
! ============================================================
router bgp 65000 vrf ISP1
  neighbor 192.168.1.1 remote-as 65100
  neighbor 192.168.1.1 description ISP1-Ethernet0.100-IPv4
  !
  address-family ipv4 unicast
    neighbor 192.168.1.1 activate
    neighbor 192.168.1.1 soft-reconfiguration inbound
  exit-address-family
  !
exit

! ============================================================
! VRF: ISP2
! ============================================================
router bgp 65000 vrf ISP2
  neighbor 192.168.1.3 remote-as 65101
  neighbor 192.168.1.3 description ISP2-Ethernet0.101-IPv4
  !
  address-family ipv4 unicast
    neighbor 192.168.1.3 activate
    neighbor 192.168.1.3 soft-reconfiguration inbound
  exit-address-family
  !
exit

! ============================================================
! VRF: ISP3
! ============================================================
router bgp 65000 vrf ISP3
  neighbor 192.168.1.5 remote-as 65102
  neighbor 192.168.1.5 description ISP3-Ethernet0.102-IPv4
  !
  address-family ipv4 unicast
    neighbor 192.168.1.5 activate
    neighbor 192.168.1.5 soft-reconfiguration inbound
  exit-address-family
  !
exit

end
write memory
EOF

echo "BGP configuration completed!"
echo ""
echo "Verify with: vtysh -c 'show bgp vrf all summary'"