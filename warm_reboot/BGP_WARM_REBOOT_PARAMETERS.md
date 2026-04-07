# BGP Warm-Reboot Parameters and Behavior Matrix

## Test Results

| Test # | establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | bgp_eoiu | EOR Received | Result | Notes |
|--------|----------------|-----------|-----------------|----------------------|-----------|----------|--------------|--------|-------|
| 1 | not configured | 360 | 480 | 480 | 240 | true | ~6 min | NSF (Non-Stop Forwarding) |  |
