# BGP Warm-Reboot Parameters and Behavior Matrix

## Parameter Definitions

| Parameter | Scope | What It Controls | Valid Range |
|-----------|-------|------------------|-------------|
| **establish_wait** | Local (gold219) | How long BGP waits before establishing sessions after restart | 1-3600s |
| **max_delay** | Local (gold219) | Maximum time to defer best path selection during GR | 1-3600s |
| **gr_restart_time** | Local (gold219) | What gold219 advertises to peers: "Keep my routes for this long if I restart" | 1-3600s |
| **gr_stale_routes_time** | Peers (gold226/307) | How long peers actually hold stale routes from restarting neighbors | 1-3600s |
| **bgp_timer** | Local (gold219) | How long fpmsyncd waits before reconciling routes (hard timeout) | 1-3600s |
| **eoiu** | Local (gold219) | Enable smart signaling - reconcile when BGP signals "done" instead of timer | true/false |

---

## Timeline Explanation

### On gold219 (Restarting Router):
1. **T=0**: Warm-reboot starts
2. **T=0 to establish_wait**: BGP waits before starting to establish sessions
3. **T=establish_wait to convergence**: BGP establishes sessions, learns routes
4. **T=convergence**: BGP has all routes, sends EOIU signal (if eoiu=true)
5. **T=bgp_timer OR EOIU**: fpmsyncd reconciles (whichever comes first)
6. **After reconciliation**: gold219 starts advertising routes to peers

### On gold226/307 (Peer Routers):
1. **T=0**: Receive GR notification, mark gold219's routes as stale
2. **T=0 to gr_stale_routes_time**: Keep stale routes, keep sending traffic to gold219
3. **T=gr_stale_routes_time**: Delete stale routes if no update from gold219

---

## Behavior Scenarios

### Scenario 1: EOIU Working, Timers Properly Aligned ✅ IDEAL

| establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | eoiu | Behavior |
|----------------|-----------|-----------------|----------------------|-----------|------|----------|
| 60 | 360 | 480 | 480 | 420 | true | **Perfect!** BGP converges at ~200s, EOIU signals fpmsyncd, reconciliation at 200s, routes advertised at ~210s, peers refresh routes. No traffic loss. bgp_timer (420s) is backup only. |

**Timeline:**
```
T=0s:    Reboot
T=60s:   BGP starts establishing sessions (establish_wait)
T=200s:  BGP converges, sends EOIU signal
T=200s:  fpmsyncd reconciles (triggered by EOIU)
T=210s:  gold219 advertises routes to peers
T=220s:  Peers receive routes, replace stale with fresh
Result:  ✅ Total convergence: 220s, No traffic loss
```

---

### Scenario 2: EOIU Disabled, Proper Timer ✅ SAFE

| establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | eoiu | Behavior |
|----------------|-----------|-----------------|----------------------|-----------|------|----------|
| 60 | 360 | 480 | 480 | 420 | false | **Safe but slower.** BGP converges at ~200s but fpmsyncd waits until bgp_timer (420s) expires. Routes advertised at 420s. No traffic loss but 200s slower than EOIU. |

**Timeline:**
```
T=0s:    Reboot
T=60s:   BGP starts (establish_wait)
T=200s:  BGP converges (but no EOIU signal)
T=420s:  bgp_timer expires, fpmsyncd reconciles
T=430s:  gold219 advertises routes
T=440s:  Peers receive routes
Result:  ✅ No traffic loss, but 220s slower than EOIU
```

---

### Scenario 3: bgp_timer Too Short ❌ TRAFFIC LOSS

| establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | eoiu | Behavior |
|----------------|-----------|-----------------|----------------------|-----------|------|----------|
| 120 | 360 | 480 | 480 | 180 | false | **Traffic loss!** bgp_timer (180s) expires before BGP finishes learning routes (~300s). fpmsyncd deletes routes that haven't been re-learned. Outbound traffic from gold219 drops. |

**Timeline:**
```
T=0s:    Reboot
T=120s:  BGP starts (establish_wait)
T=180s:  bgp_timer expires (BGP only 20% converged!)
T=180s:  fpmsyncd reconciles with incomplete routes
         ❌ 80% of routes DELETED from ASIC
T=180s+: Outbound traffic from gold219 BLACK HOLES
T=300s:  BGP finally converges, but damage done
Result:  ❌ 120s of traffic loss (T=180s to T=300s)
```

---

### Scenario 4: gr_stale_routes_time Too Short ❌ TRAFFIC LOSS

| establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | eoiu | Behavior |
|----------------|-----------|-----------------|----------------------|-----------|------|----------|
| 60 | 360 | 480 | 240 | 420 | false | **Traffic loss!** Peers' gr_stale_routes_time (240s) expires before gold219 finishes reconciliation (420s). Peers delete stale routes to gold219. Inbound traffic to gold219 drops. |

**Timeline:**
```
T=0s:    Reboot
T=60s:   BGP starts
T=200s:  BGP converges at gold219
T=240s:  Peers' gr_stale_routes_time expires
         ❌ Peers DELETE stale routes to gold219
         ❌ Inbound traffic to gold219 BLACK HOLES
T=420s:  gold219 reconciles and advertises routes
T=430s:  Peers re-learn routes
Result:  ❌ 190s of traffic loss (T=240s to T=430s)
```

---

### Scenario 5: establish_wait Too High ⚠️ DELAY

| establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | eoiu | Behavior |
|----------------|-----------|-----------------|----------------------|-----------|------|----------|
| 300 | 360 | 480 | 480 | 420 | false | **Risk of timeout!** BGP doesn't start until T=300s, might not converge before bgp_timer (420s). Only 120s window for full route learning. |

**Timeline:**
```
T=0s:    Reboot
T=300s:  BGP starts (establish_wait delay)
T=420s:  bgp_timer expires (only 120s of BGP convergence)
         ⚠️ If BGP not done: partial routes, traffic loss
Result:  ❌ High risk of incomplete convergence
```

---

### Scenario 6: EOIU Broken (Current Bug) ❌ UNRELIABLE

| establish_wait | max_delay | gr_restart_time | gr_stale_routes_time | bgp_timer | eoiu | Behavior |
|----------------|-----------|-----------------|----------------------|-----------|------|----------|
| 60 | 360 | 480 | 480 | 300 | true | **Unreliable!** EOIU script crashes (Python syntax error), falls back to bgp_timer (300s). If BGP not converged by 300s, traffic loss. Same as Scenario 3. |

**Timeline:**
```
T=0s:    Reboot
T=0s:    EOIU script crashes (Python error)
T=60s:   BGP starts
T=200s:  BGP converges (no signal sent - EOIU broken)
T=300s:  bgp_timer expires (fallback)
         ⚠️ If routes still learning: deletion, traffic loss
Result:  ❌ Depends on whether BGP finishes before 300s
```

---

## Recommended Configurations

### For 900K Routes (Your Scale)

**Conservative (Safest):**
```bash
establish_wait:          60
max_delay:              360
gr_restart_time:        600
gr_stale_routes_time:   600  (on peers)
bgp_timer:              540
eoiu:                  true
```

**Moderate (Recommended):**
```bash
establish_wait:          60
max_delay:              360
gr_restart_time:        480
gr_stale_routes_time:   480  (on peers)
bgp_timer:              420
eoiu:                  true
```

**Aggressive (Fast but risky):**
```bash
establish_wait:          30
max_delay:              240
gr_restart_time:        360
gr_stale_routes_time:   360  (on peers)
bgp_timer:              300
eoiu:                  true
```

---

## Critical Rules

1. **gr_stale_routes_time (peers) ≥ gr_restart_time (local)**
   - Peers must wait at least as long as you advertise

2. **gr_restart_time > bgp_timer + 60s safety margin**
   - Time to advertise must exceed time to reconcile

3. **bgp_timer > (establish_wait + convergence_time)**
   - Timer must allow BGP to fully converge

4. **If eoiu=false: bgp_timer must be very conservative**
   - No smart signaling, must wait for worst case

5. **establish_wait should be minimal**
   - Don't waste precious time before BGP starts

---

## Your Current Configuration

```
establish_wait:        120  ⚠️ Too high, wastes time
max_delay:             360  ✅ OK
gr_restart_time:       480  ✅ Good
gr_stale_routes_time:  480  ✅ Good (on peers)
bgp_timer:             120  ❌ WAY TOO SHORT!
eoiu:                 true  ✅ Now fixed!
```

**Issues:**
- bgp_timer (120s) - establish_wait (120s) = 0s for BGP convergence ❌
- This will cause massive traffic loss

**Fix:**
```bash
sudo config warm_restart bgp_timer 420
sonic-db-cli CONFIG_DB hset "BGP_GLOBALS|default" establish_wait 60
sudo config save -y
```
