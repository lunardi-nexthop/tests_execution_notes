# BGP Warm-Reboot Parameters and Behavior Matrix

## Test Results

| Test # | max_delay | establish_wait | gr_restart_time | gr_stale_routes_time | bgp_timer | bgp_eoiu | EOR Received | Result | Notes |
|--------|-----------|----------------|-----------------|----------------------|-----------|----------|--------------|--------|-------|
| 1 | 360 | not configured | 480 | 480 | 240 | true | ~6 min | NSF (Non-Stop Forwarding) |  |
| 2 | 360 | not configured | 480 | 480 | not configured (default=120) | not configured | ~6 min | LOSS at restarting router |  |
| 3 | 360 | not configured | 480 | 480 | 240 | not configured | ~6 min | NSF |  |
| 4 | 360 | 120 | 480 | 480 | 240 | true | ~120 sec | NSF but brief redirection to other ECMP paths | Peers flush out stale routes AND received routes at the time it receives EOR. |
