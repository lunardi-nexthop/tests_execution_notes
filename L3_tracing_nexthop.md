# Redis Commands for Tracing SONiC Route Nexthops

This guide provides the Redis CLI commands to manually trace nexthops for route entries in SONiC ASIC DB.

## Database Numbers
- ASIC_DB: Database 1 (`-n 1`)
- STATE_DB: Database 6 (`-n 6`)

## Step-by-Step Nexthop Tracing

### 1. Get Route Entries
```bash
# Get all route entries
redis-cli -n 1 keys "*ROUTE_ENTRY*"

# Get specific route entries (first 10 as in your example)
redis-cli -n 1 keys "*ROUTE_ENTRY*" | head -10

# Search for specific destination
redis-cli -n 1 keys "*ROUTE_ENTRY*" | grep "20.3.10.100/31"
```

### 2. Get Route Attributes
For each route entry key, get its attributes:
```bash
# Example for one of your routes
redis-cli -n 1 hgetall 'ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"20.3.10.100/31","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000103"}'

# Get just the nexthop ID
redis-cli -n 1 hget 'ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"20.3.10.100/31","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000103"}' SAI_ROUTE_ENTRY_ATTR_NEXT_HOP_ID
```

### 3. Trace Nexthop Based on OID Type

#### A. Individual Nexthop (OID starts with 0x4)
```bash
# Get nexthop attributes
redis-cli -n 1 hgetall "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP:oid:0x40000000001234"

# Common attributes to look for:
# - SAI_NEXT_HOP_ATTR_TYPE
# - SAI_NEXT_HOP_ATTR_IP
# - SAI_NEXT_HOP_ATTR_ROUTER_INTERFACE_ID
```

#### B. Nexthop Group (OID starts with 0x5)
```bash
# Get nexthop group attributes
redis-cli -n 1 hgetall "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP:oid:0x50000000001234"

# Get all nexthop group members
redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER:*"

# For each member, check if it belongs to your nexthop group
redis-cli -n 1 hget "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER:oid:0x1700000000abcd" SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_GROUP_ID

# Get the actual nexthop ID from the member
redis-cli -n 1 hget "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER:oid:0x1700000000abcd" SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_ID
```

#### C. Router Interface (OID starts with 0x6)
```bash
# Get router interface attributes
redis-cli -n 1 hgetall "ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:oid:0x60000000001234"

# Common attributes to look for:
# - SAI_ROUTER_INTERFACE_ATTR_PORT_ID
# - SAI_ROUTER_INTERFACE_ATTR_VLAN_ID
# - SAI_ROUTER_INTERFACE_ATTR_TYPE
```

## Example Tracing Session

Let's trace one of your route entries step by step:

### Route: 20.3.10.100/31

```bash
# 1. Get the route attributes
ROUTE_KEY='ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"20.3.10.100/31","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000103"}'
redis-cli -n 1 hgetall "$ROUTE_KEY"

# 2. Get the nexthop ID
NEXTHOP_ID=$(redis-cli -n 1 hget "$ROUTE_KEY" SAI_ROUTE_ENTRY_ATTR_NEXT_HOP_ID)
echo "Nexthop ID: $NEXTHOP_ID"

# 3. Determine nexthop type and get details
if [[ $NEXTHOP_ID == oid:0x5* ]]; then
    echo "This is a nexthop group"
    redis-cli -n 1 hgetall "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP:$NEXTHOP_ID"
    
    # Get group members
    redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER:*" | while read member_key; do
        group_id=$(redis-cli -n 1 hget "$member_key" SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_GROUP_ID)
        if [ "$group_id" = "$NEXTHOP_ID" ]; then
            echo "Member: $member_key"
            redis-cli -n 1 hgetall "$member_key"
        fi
    done
    
elif [[ $NEXTHOP_ID == oid:0x4* ]]; then
    echo "This is an individual nexthop"
    redis-cli -n 1 hgetall "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP:$NEXTHOP_ID"
    
elif [[ $NEXTHOP_ID == oid:0x6* ]]; then
    echo "This is a router interface"
    redis-cli -n 1 hgetall "ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:$NEXTHOP_ID"
fi
```

## Useful One-Liners

### Get all nexthop groups and their member counts
```bash
redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP:*" | while read nhg; do
    nhg_id=$(echo $nhg | cut -d: -f4)
    member_count=$(redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER:*" | xargs -I {} redis-cli -n 1 hget {} SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_GROUP_ID | grep -c "$nhg_id")
    echo "$nhg_id: $member_count members"
done
```

### Get all individual nexthops with their IPs
```bash
redis-cli -n 1 keys "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP:*" | while read nh; do
    nh_id=$(echo $nh | cut -d: -f4)
    nh_ip=$(redis-cli -n 1 hget "$nh" SAI_NEXT_HOP_ATTR_IP)
    echo "$nh_id: $nh_ip"
done
```

### Find routes using a specific nexthop
```bash
NEXTHOP_ID="oid:0x40000000001234"
redis-cli -n 1 keys "*ROUTE_ENTRY*" | while read route; do
    route_nh=$(redis-cli -n 1 hget "$route" SAI_ROUTE_ENTRY_ATTR_NEXT_HOP_ID)
    if [ "$route_nh" = "$NEXTHOP_ID" ]; then
        echo "Route using nexthop $NEXTHOP_ID: $route"
    fi
done
```

## OID Prefixes Reference

- `oid:0x10*` - Ports
- `oid:0x21*` - Switch
- `oid:0x30*` - Virtual Router
- `oid:0x40*` - Next Hop
- `oid:0x50*` - Next Hop Group
- `oid:0x60*` - Router Interface
- `oid:0x17*` - Next Hop Group Member

## Common SAI Attributes

### Route Entry Attributes
- `SAI_ROUTE_ENTRY_ATTR_NEXT_HOP_ID` - The nexthop or nexthop group ID
- `SAI_ROUTE_ENTRY_ATTR_PACKET_ACTION` - Forward, drop, etc.

### Next Hop Attributes
- `SAI_NEXT_HOP_ATTR_TYPE` - IP, MPLS, etc.
- `SAI_NEXT_HOP_ATTR_IP` - Next hop IP address
- `SAI_NEXT_HOP_ATTR_ROUTER_INTERFACE_ID` - Associated router interface

### Next Hop Group Attributes
- `SAI_NEXT_HOP_GROUP_ATTR_TYPE` - ECMP, etc.
- `SAI_NEXT_HOP_GROUP_ATTR_NEXT_HOP_COUNT` - Number of members

### Router Interface Attributes
- `SAI_ROUTER_INTERFACE_ATTR_TYPE` - Port, VLAN, etc.
- `SAI_ROUTER_INTERFACE_ATTR_PORT_ID` - Associated port
- `SAI_ROUTER_INTERFACE_ATTR_VLAN_ID` - Associated VLAN
