#!/bin/bash

# Script to trace nexthops for SONiC route entries using redis-cli
# Usage: ./trace_nexthops_redis.sh [route_destination]
#
# This script will trace the nexthop information for the route entries you provided:
# - 20.3.10.100/31, 107.7.102.0/28, 20.3.6.164/31, etc.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Database numbers
ASIC_DB=1
STATE_DB=6

echo -e "${CYAN}SONiC Route Nexthop Tracer${NC}"
echo -e "${CYAN}===========================${NC}"

# Function to extract destination from route key
extract_destination() {
    local route_key="$1"
    echo "$route_key" | grep -o '"dest":"[^"]*"' | cut -d'"' -f4
}

# Function to extract VR from route key
extract_vr() {
    local route_key="$1"
    echo "$route_key" | grep -o '"vr":"[^"]*"' | cut -d'"' -f4
}

# Function to get route attributes
get_route_attributes() {
    local route_key="$1"
    echo -e "${YELLOW}Route Attributes:${NC}"
    redis-cli -n $ASIC_DB hgetall "$route_key" | while read -r key; do
        read -r value
        echo "  $key: $value"
    done
}

# Function to get nexthop group information
get_nexthop_group_info() {
    local nhg_id="$1"
    local nhg_key="ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP:$nhg_id"

    echo -e "${GREEN}Nexthop Group: $nhg_id${NC}"

    # Get nexthop group attributes
    echo -e "${YELLOW}  Group Attributes:${NC}"
    redis-cli -n $ASIC_DB hgetall "$nhg_key" | while read -r key; do
        read -r value
        echo "    $key: $value"
    done

    # Get nexthop group members
    echo -e "${YELLOW}  Group Members:${NC}"
    local members=$(redis-cli -n $ASIC_DB keys "ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER:*")

    local member_count=0
    for member_key in $members; do
        local member_nhg_id=$(redis-cli -n $ASIC_DB hget "$member_key" "SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_GROUP_ID")
        if [ "$member_nhg_id" = "$nhg_id" ]; then
            member_count=$((member_count + 1))
            local member_nh_id=$(redis-cli -n $ASIC_DB hget "$member_key" "SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_ID")
            echo -e "${PURPLE}    Member $member_count:${NC}"
            echo "      Member Key: $member_key"
            echo "      Nexthop ID: $member_nh_id"

            # Get individual nexthop info for this member
            get_individual_nexthop_info "$member_nh_id" "      "
        fi
    done

    if [ $member_count -eq 0 ]; then
        echo "    No members found for this nexthop group"
    fi
}

# Function to get individual nexthop information
get_individual_nexthop_info() {
    local nh_id="$1"
    local indent="${2:-  }"
    local nh_key="ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP:$nh_id"

    echo -e "${indent}${BLUE}Nexthop Details:${NC}"

    # Get nexthop attributes
    local nh_attrs=$(redis-cli -n $ASIC_DB hgetall "$nh_key")
    if [ -n "$nh_attrs" ]; then
        echo "$nh_attrs" | while read -r key; do
            read -r value
            echo "${indent}  $key: $value"

            # If this is a router interface ID, get more details
            if [ "$key" = "SAI_NEXT_HOP_ATTR_ROUTER_INTERFACE_ID" ]; then
                get_router_interface_info "$value" "${indent}    "
            fi
        done
    else
        echo "${indent}  No nexthop attributes found"
    fi
}

# Function to get router interface information
get_router_interface_info() {
    local rif_id="$1"
    local indent="${2:-    }"
    local rif_key="ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:$rif_id"

    echo -e "${indent}${CYAN}Router Interface ($rif_id):${NC}"

    # Get router interface attributes
    local rif_attrs=$(redis-cli -n $ASIC_DB hgetall "$rif_key")
    if [ -n "$rif_attrs" ]; then
        echo "$rif_attrs" | while read -r key; do
            read -r value
            echo "${indent}  $key: $value"
        done
    else
        echo "${indent}  No router interface attributes found"
    fi
}

# Function to trace nexthop for a single route
trace_route_nexthop() {
    local route_key="$1"
    local destination=$(extract_destination "$route_key")
    local vr=$(extract_vr "$route_key")

    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}Tracing Route: $destination${NC}"
    echo -e "${GREEN}VR: $vr${NC}"
    echo -e "${GREEN}================================================${NC}"

    # Get route attributes
    get_route_attributes "$route_key"

    # Get nexthop ID from route
    local nexthop_id=$(redis-cli -n $ASIC_DB hget "$route_key" "SAI_ROUTE_ENTRY_ATTR_NEXT_HOP_ID")

    if [ -z "$nexthop_id" ] || [ "$nexthop_id" = "SAI_NULL_OBJECT_ID" ]; then
        echo -e "${RED}No nexthop ID found for this route${NC}"
        return
    fi

    echo -e "\n${YELLOW}Nexthop ID: $nexthop_id${NC}"

    # Determine nexthop type based on OID prefix
    if [[ $nexthop_id == oid:0x5* ]]; then
        # Nexthop group
        get_nexthop_group_info "$nexthop_id"
    elif [[ $nexthop_id == oid:0x4* ]]; then
        # Individual nexthop
        echo -e "${GREEN}Individual Nexthop: $nexthop_id${NC}"
        get_individual_nexthop_info "$nexthop_id"
    elif [[ $nexthop_id == oid:0x6* ]]; then
        # Router interface
        echo -e "${GREEN}Router Interface: $nexthop_id${NC}"
        get_router_interface_info "$nexthop_id"
    else
        echo -e "${RED}Unknown nexthop type: $nexthop_id${NC}"
    fi
}

# Main execution
if [ $# -eq 1 ]; then
    # Trace specific destination
    destination="$1"
    echo "Searching for routes with destination: $destination"

    # Find route keys matching the destination
    route_keys=$(redis-cli -n $ASIC_DB keys "*ROUTE_ENTRY*" | grep "$destination")

    if [ -z "$route_keys" ]; then
        echo -e "${RED}No routes found for destination: $destination${NC}"
        exit 1
    fi

    for route_key in $route_keys; do
        trace_route_nexthop "$route_key"
    done
else
    # Trace the specific routes from your example
    echo "Tracing the route entries from your example..."

    # Get the first 10 route entries as shown in your example
    route_keys=$(redis-cli -n $ASIC_DB keys "*ROUTE_ENTRY*" | head -10)

    route_count=0
    for route_key in $route_keys; do
        route_count=$((route_count + 1))
        trace_route_nexthop "$route_key"

        # Add separator between routes
        if [ $route_count -lt 10 ]; then
            echo -e "\n${CYAN}---${NC}"
        fi
    done
fi

echo -e "\n${CYAN}Nexthop tracing completed!${NC}"

