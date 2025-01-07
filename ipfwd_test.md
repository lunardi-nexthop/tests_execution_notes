# How to: tests/ipfwd/test_mtu.py

## Command:
`~/sonic-mgmt/tests$ sudo ./run_tests.sh -a False -c ipfwd/test_mtu.py -d usschq-nswdut-t002 -f ../ansible/testbed.yaml -i ../ansible/lab -k debug -n poc-lab-t0-16 -t t1 -u -x -e "--skip_sanity --neighbor_type=sonic" -I . -p /tmp
`
### Problem 1:
Can’t run `test_mtu.py` due to test topology is ‘t0’.

### Reason:
Script: `ipfwd/test_mtu.py` defines marker to skip test 

```
pytestmark = [
     pytest.mark.topology('t1', 't2'),
     pytest.mark.device_type('vs')
]
```

### Fix:

Script: `ipfwd/test_mtu.py` - redefine marker:

```
pytestmark = [
    pytest.mark.topology('t0', 't1', 't2'),
    pytest.mark.device_type('vs')
]
```

File: `tests_mark_conditions.yaml` - include ‘t0’ condition or else test will exit

`~/sonic-mgmt/tests$ vim ./common/plugins/conditional_mark/tests_mark_conditions.yaml
`

```
#######################################
#####            ipfwd            #####
#######################################
...
ipfwd/test_mtu.py:
  skip:
    reason: "Unsupported topology."
    conditions:
      - "topo_type not in ['t0', 't1', 't2']"
...    
```

### FAILED TEST LOG:

```
ipfwd/test_mtu.py::test_mtu[usschq-nswdut-t002-None-1514] SKIPPED (Unsupported topology.)                                                                                          [ 50%]
ipfwd/test_mtu.py::test_mtu[usschq-nswdut-t002-None-9114] SKIPPED (Unsupported topology.)                                                                                          [100%]

==================================================================================== warnings summary ====================================================================================
../../../../usr/local/lib/python3.8/dist-packages/paramiko/transport.py:236
  /usr/local/lib/python3.8/dist-packages/paramiko/transport.py:236: CryptographyDeprecationWarning: Blowfish has been deprecated
    "class": algorithms.Blowfish,

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
------------------------------------------------------------- generated xml file: /var/AzDevOps/sonic-mgmt/tests/logs/tr.xml -------------------------------------------------------------
================================================================================ short test summary info =================================================================================
SKIPPED [2] ipfwd/test_mtu.py:15: Unsupported topology.
============================================================================= 2 skipped, 1 warning in 7.14s ==============================================================================
```

### Successful run LOG:

```
...
...
callback   = <pytest_ansible.module_dispatcher.v213.ResultAccumulator object at 0x7ffbaacffc10>
complex_args = {'path': '/root/ptftests', 'state': 'absent'}
extra_hosts = []
hosts      = [ptf_vms1-4]
kwargs     = {'inventory': <ansible.inventory.manager.InventoryManager object at 0x7ffbaadb9a60>, 'loader': <ansible.parsing.datalo...ss': None}, 'stdout_callback': <pytest_ansible.module_dispatcher.v213.ResultAccumulator object at 0x7ffbaacffc10>, ...}
kwargs_extra = {}
module_args = ()
no_hosts   = False
play       = pytest-ansible
play_ds    = {'become': True, 'become_user': 'root', 'gather_facts': 'no', 'hosts': 'ptf_vms1-4', ...}
play_extra = None
self       = <pytest_ansible.module_dispatcher.v213.ModuleDispatcherV213 object at 0x7ffbaadc0c70>
tqm        = <ansible.executor.task_queue_manager.TaskQueueManager object at 0x7ffbaa6cf310>
verbosity  = None
verbosity_syntax = '-vvvvv'

/usr/local/lib/python3.8/dist-packages/pytest_ansible/module_dispatcher/v213.py:232: AnsibleConnectionFailure
==================================================================================== warnings summary ====================================================================================
../../../../usr/local/lib/python3.8/dist-packages/paramiko/transport.py:236
  /usr/local/lib/python3.8/dist-packages/paramiko/transport.py:236: CryptographyDeprecationWarning: Blowfish has been deprecated
    "class": algorithms.Blowfish,

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
---------------------------------------------------------------------------- generated xml file: /tmp/tr.xml -----------------------------------------------------------------------------
================================================================================ short test summary info =================================================================================
ERROR ipfwd/test_mtu.py::test_mtu[usschq-nswdut-t002-None-1514] - Failed: ARP table is not rebuilt in given time
ERROR ipfwd/test_mtu.py::test_mtu[usschq-nswdut-t002-None-9114] - Failed: ARP table is not rebuilt in given time
ERROR ipfwd/test_mtu.py::test_mtu[usschq-nswdut-t002-None-9114] - pytest_ansible.errors.AnsibleConnectionFailure: Host unreachable in the inventory
======================================================================== 1 warning, 3 errors in 309.94s (0:05:09) ========================================================================
INFO:root:Can not get Allure report URL. Please check logs
+ RC=1
+ [[ xgroup != x\d\e\b\u\g ]]
+ [[ xTrue == x\F\a\l\s\e ]]
+ exit 1
```
