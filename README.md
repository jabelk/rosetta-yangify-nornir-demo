# ntc-yangify-rosetta-demo

This demo is meant to illustrate the Yangify + NTC-Rosetta functionality in action.

The Vagrantfile includes 1 IOS, 1 EOS, 1 Junos device. 

The workflow is as follows (all using Nornir tasks and inventory):
- Gather Existing Config from Devices
    - Gather existing running-config from each device: use Napalm getters (ios/eos) / Netmiko (Junos XML style configuration)
    - Write the config of each device to a file in `config/backed_up_from_device/`
    - Read the config from each device's file and store it in that device's host associated inventory variable called `native_config`
- Use NTC-Rosetta to parse each device's configuration into a Vendor Neutral Data Model
    - Create a rosetta driver based on the Nornir inventory platform for each device
    - Use the rosetta driver to parse the native configuration in the inventory variable `native_config` and storing the results 
    into the `rosetta_parsed_config` inventory variable (per device). These results are a vendor neutral data model, based on the underlying Yang models (OpenConfig in this case) and the data taken from the device. The structure / keys are from the Yang Model, the data values are from the device. 
    - Write the Data Models to a YAML and a JSON file under `config/data_models_from_parsing` 
- Update the Inventory to include the Config Data Models
    - For each device in the `hosts.yaml`, take the inventory variables of `native_config` and `rosetta_parsed_config` which had been updated in memory at runtime and write the updates to a new hosts file called `hosts_new.yaml` to be used in a future run. 
- Make a Change to the Data Model and Generate New Native Config
    - Add VLAN 10 and 20 to each device's data model (`rosetta_parsed_config`), merging in the changes
    - Use NTC-Rosetta to generate the new `native_config` needed based on the updated data model (ios, junos, eos)
    - Write the proposed configuration to a file per device in `config/config_rendered_from_data`. 

### Native config
#### IOS
```
! IOS
interface GigabitEthernet1
 ip address dhcp
 negotiation auto
 no mop enabled
 no mop sysid
!
interface GigabitEthernet2
 no ip address
 shutdown
 negotiation auto
 no mop enabled
 no mop sysid
!
interface GigabitEthernet3
 no ip address
 shutdown
 negotiation auto
 no mop enabled
 no mop sysid
```
#### EOS
```

interface Ethernet1
!
interface Ethernet2
!
interface Management1
   ip address 10.0.2.15/24
```

```xml
           <interfaces>
                <interface>
                    <name>ge-0/0/0</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <dhcp>
                                </dhcp>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/1</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <address>
                                    <name>192.168.33.10/22</name>
                                </address>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/2</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <dhcp>
                                </dhcp>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/3</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <address>
                                    <name>192.168.34.10/24</name>
                                </address>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/4</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <dhcp>
                                </dhcp>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/5</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <address>
                                    <name>192.168.35.10/24</name>
                                </address>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/6</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <dhcp>
                                </dhcp>
                            </inet>
                        </family>
                    </unit>
                </interface>
                <interface>
                    <name>ge-0/0/7</name>
                    <unit>
                        <name>0</name>
                        <family>
                            <inet>
                                <address>
                                    <name>192.168.36.10/24</name>
                                </address>
                            </inet>
                        </family>
                    </unit>
                </interface>
            </interface
```
### Data Models Parsed from Native Config Using NTC-Rosetta 


#### IOS

```json
{
    "openconfig-interfaces:interfaces": {
        "interface": [
            {
                "name": "GigabitEthernet1",
                "config": {
                    "name": "GigabitEthernet1",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": true
                }
            },
            {
                "name": "GigabitEthernet2",
                "config": {
                    "name": "GigabitEthernet2",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": false
                }
            },
            {
                "name": "GigabitEthernet3",
                "config": {
                    "name": "GigabitEthernet3",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": false
                }
            }
        ]
    },
    "openconfig-network-instance:network-instances": {
        "network-instance": [
            {
                "name": "default",
                "config": {
                    "name": "default"
                }
            }
        ]
    }
}
```

```yaml
openconfig-interfaces:interfaces:
  interface:
  - config:
      enabled: true
      name: GigabitEthernet1
      type: iana-if-type:ethernetCsmacd
    name: GigabitEthernet1
  - config:
      enabled: false
      name: GigabitEthernet2
      type: iana-if-type:ethernetCsmacd
    name: GigabitEthernet2
  - config:
      enabled: false
      name: GigabitEthernet3
      type: iana-if-type:ethernetCsmacd
    name: GigabitEthernet3
openconfig-network-instance:network-instances:
  network-instance:
  - config:
      name: default
    name: default
```

#### EOS
```json
{
    "openconfig-interfaces:interfaces": {
        "interface": [
            {
                "name": "Ethernet1",
                "config": {
                    "name": "Ethernet1",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": true
                }
            },
            {
                "name": "Ethernet2",
                "config": {
                    "name": "Ethernet2",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": true
                }
            },
            {
                "name": "Management1",
                "config": {
                    "name": "Management1",
                    "enabled": true
                }
            }
        ]
    },
    "openconfig-network-instance:network-instances": {
        "network-instance": [
            {
                "name": "default",
                "config": {
                    "name": "default"
                }
            }
        ]
    }
}
```

#### Junos
```yaml
openconfig-interfaces:interfaces:
  interface:
  - config:
      enabled: true
      name: Ethernet1
      type: iana-if-type:ethernetCsmacd
    name: Ethernet1
  - config:
      enabled: true
      name: Ethernet2
      type: iana-if-type:ethernetCsmacd
    name: Ethernet2
  - config:
      enabled: true
      name: Management1
    name: Management1
openconfig-network-instance:network-instances:
  network-instance:
  - config:
      name: default
    name: default
```
#### Junos
```json
{
    "openconfig-network-instance:network-instances": {
        "network-instance": [
            {
                "name": "default",
                "config": {
                    "name": "default"
                }
            }
        ]
    }
}
```

```yaml
openconfig-network-instance:network-instances:
  network-instance:
  - config:
      name: default
    name: default
```
### Rendered Config

```
rosetta_merge_new_config_from_data_model****************************************
* csr1kv ** changed : True *****************************************************
vvvv rosetta_merge_new_config_from_data_model ** changed : False vvvvvvvvvvvvvvv INFO
---- write_file ** changed : True ---------------------------------------------- INFO
--- config/config_rendered_from_data/csr1kv_rosetta_proposed_merge_config.conf

+++ new

@@ -0,0 +1,13 @@

+default interface GigabitEthernet1
+default interface GigabitEthernet2
+default interface GigabitEthernet3
+vlan 10
+   name prod
+   no shutdown
+   exit
+!
+vlan 20
+   name dev
+   shutdown
+   exit
+!
^^^^ END rosetta_merge_new_config_from_data_model ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* eos_device ** changed : True *************************************************
vvvv rosetta_merge_new_config_from_data_model ** changed : False vvvvvvvvvvvvvvv INFO
---- write_file ** changed : True ---------------------------------------------- INFO
--- config/config_rendered_from_data/eos_device_rosetta_proposed_merge_config.conf

+++ new

@@ -0,0 +1,13 @@

+default interface Ethernet1
+default interface Ethernet2
+default interface Management1
+vlan 10
+   name prod
+   no shutdown
+   exit
+!
+vlan 20
+   name dev
+   shutdown
+   exit
+!
^^^^ END rosetta_merge_new_config_from_data_model ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* junos_device ** changed : True ***********************************************
vvvv rosetta_merge_new_config_from_data_model ** changed : False vvvvvvvvvvvvvvv INFO
---- write_file ** changed : True ---------------------------------------------- INFO
--- config/config_rendered_from_data/junos_device_rosetta_proposed_merge_config.conf

+++ new

@@ -0,0 +1,14 @@

+<configuration>
+  <vlans>
+    <vlan>
+      <vlan-id>10</vlan-id>
+      <name>prod</name>
+      <disable delete="delete"/>
+    </vlan>
+    <vlan>
+      <vlan-id>20</vlan-id>
+      <name>dev</name>
+      <disable/>
+    </vlan>
+  </vlans>
+</configuration>
```