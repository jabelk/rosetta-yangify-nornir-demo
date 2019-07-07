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
- Make a Change to the Data Model and Push It to the Device
    - Add VLAN 10 and 20 to each device's data model (`rosetta_parsed_config`), merging in the changes
    - Use NTC-Rosetta to generate the new `native_config` needed based on the updated data model (ios, junos, eos)
    - Use Napalm to push the changes to the devices
