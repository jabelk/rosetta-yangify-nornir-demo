#!/usr/bin/env python

"""
Nornir runbook to run arbitrary commands on network devices
"""
import json
import yaml
import os
import logging
from copy import deepcopy
import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()
from nornir import InitNornir
from nornir.core.task import Task
from nornir.plugins.tasks.files import write_file
from nornir.plugins.functions.text import print_result
from nornir.core.filter import F
from nornir.plugins.tasks.networking import napalm_get, napalm_configure, napalm_cli, netmiko_send_command
auth = HTTPBasicAuth('vagrant', 'vagrant')
headers = {
    "Content-Type": "application/yang-data+json", 
    "Accept": "application/yang-data+json"
}

# rosetta / yangify
from ntc_rosetta import get_driver
from yangson.exceptions import SemanticError

def get_restconf_single_interface(task, model="native", port="2225",int_id="3"):
    if model == "native":
        url = 'https://{}:{}/restconf/data/Cisco-IOS-XE-native:native/interface=GigabitEthernet/{}'.format(task.host.hostname,port,int_id)
    elif model == "ietf":
        url = 'https://{}:{}/restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet{}'.format(task.host.hostname,port,int_id)
    elif model == "openconfig":
        url = 'https://{}:{}/restconf/data/openconfig-interfaces:interfaces/interface=GigabitEthernet{}'.format(task.host.hostname,port,int_id)

    # url = 'https://127.0.0.1:2225/restconf/data/Cisco-IOS-XE-native:native/interface'
    response = requests.get(url, headers=headers, auth=auth, verify=False)
    return response.text

def get_restconf_all_interfaces(task, model="native", port="2225"):
    if model == "native":
        url = 'https://{}:{}/restconf/data/Cisco-IOS-XE-native:native/interface'.format(task.host.hostname,port)
    elif model == "ietf":
        url = 'https://{}:{}/restconf/data/ietf-interfaces:interfaces'.format(task.host.hostname,port)
    elif model == "openconfig":
        url = 'https://{}:{}/restconf/data/openconfig-interfaces:interfaces'.format(task.host.hostname,port)

    # url = 'https://127.0.0.1:2225/restconf/data/Cisco-IOS-XE-native:native/interface'
    response = requests.get(url, headers=headers, auth=auth, verify=False)
    return response.text

def native_config_from_disk(task):
    with open("config/backed_up_from_device/{}_napalm_backup.conf".format(task.host.name), "r") as f:
        native_config = f.read()
    # Save the compiled configuration into a host variable
    task.host["native_config"] = native_config

def transfer_parsed_json_to_host_vars_memory(task):
    with open("config/data_models_from_parsing/{}_rosetta.json".format(task.host.name), "r") as f:
        ntc_rosetta_json = f.read()
    task.host["rosetta_parsed_config"] = ntc_rosetta_json

def rosetta_get_driver(platform):
    if platform == "ios" or "eos":
         # eos not a platform in rosetta https://github.com/networktocode/ntc-rosetta/blob/develop/ntc_rosetta/__init__.py#L13
        ios = get_driver("ios", "openconfig")
        rosetta_device_driver = ios()
    if platform == "junos":
        junos = get_driver("junos", "openconfig")
        rosetta_device_driver = junos()
    return rosetta_device_driver

def rosetta_parse_native_to_data_model(task):
    rosetta_device_driver = rosetta_get_driver(task.host.platform)
    # adding validate=False since not all of the running config can be parsed yet
    ntc_rosetta_data = rosetta_device_driver.parse(native={"dev_conf": task.host["native_config"]},validate=False)
    ntc_rosetta_dict = ntc_rosetta_data.raw_value()
    task.host["rosetta_parsed_config"] = ntc_rosetta_data.raw_value()

def rosetta_merge_new_config_from_data_model(task):
    rosetta_device_driver = rosetta_get_driver(task.host.platform)
    new_vlans = {'openconfig-network-instance:network-instances': 
    {'network-instance': [{'name': 'default', 'config': {'name': 'default'}, 
    'vlans': {'vlan': [{'vlan-id': 10, 'config': {'vlan-id': 10, 'name': 'prod', 'status': 'ACTIVE'}}, 
    {'vlan-id': 20, 'config': {'vlan-id': 20, 'name': 'dev', 'status': 'SUSPENDED'}}]}}]}}
    native = rosetta_device_driver.translate(candidate=new_vlans)
    try:
        running_config = json.load(task.host["rosetta_parsed_config"])
    except AttributeError: # fixing for AttributeError: 'str' object has no attribute 'read'
        running_config = json.loads(task.host["rosetta_parsed_config"])
    merged_config = rosetta_device_driver.merge(candidate=new_vlans, running=running_config)
    print("Proposed New Native config from Rosetta is ")
    print(merged_config)
    # syntax errors for merge config need to be fixed 
    # task.run(
    #     name="Loading Rosetta Generated Configuration on the device",
    #     task=napalm_configure,
    #     replace=False,
    #     configuration=merged_config,
    # )

def backup(task, path):
    if task.host.platform == "ios" or "eos":
        r = task.run(
            task=napalm_get,
            getters=["config"],
            severity_level=logging.DEBUG,
        )
        task.run(
            task=write_file,
            filename=f"{path}/{task.host}_napalm_backup.conf",
            content=r.result["config"]["running"])
    if task.host.platform == "junos":
        r = task.run(
            task=netmiko_send_command,
            command_string=task.host["backup_command"],
            severity_level=logging.DEBUG,
        )
        
        native_config = r[0].result
        task.run(
            task=write_file,
            filename=f"{path}/{task.host}_napalm_backup.conf",
            content=native_config,
        )


def load_inventory():
    with open("hosts.yaml", "r") as f:
        inventory_dict = yaml.safe_load(f.read())
    return inventory_dict

def create_yaml_file(task, python_object_input, filename="hosts_new.yaml"):
    print(python_object_input)
    yaml_file = yaml.dump(python_object_input, default_flow_style=False)
    print("yaml file\n\n")
    print(yaml_file)
    task.run(
        task=write_file,
        filename=filename,
        content=yaml_file,
    )

def create_json_file(task, python_object_input, filename="hosts_new.yaml"):
    json_file = json.dumps(python_object_input, indent=4)
    task.run(
        task=write_file,
        filename=filename,
        content=json_file,
    ) 

def export_vars_to_yaml_standalone(task, path="config/data_models_from_parsing"):
    ntc_rosetta_dict = task.host["rosetta_parsed_config"]
    native_config = task.host["native_config"]
    # create json / yaml files from parsed config
    task.run(task=create_json_file, python_object_input=ntc_rosetta_dict, filename=f"{path}/{task.host.platform}_device_rosetta.json")
    task.run(task=create_yaml_file, python_object_input=ntc_rosetta_dict, filename=f"{path}/{task.host.platform}_device_rosetta.yml")

def main():
    nornir = InitNornir()
    # back up to disk using napalm getter 
    result = nornir.run(task=backup, path="config/backed_up_from_device")
    print_result(result, severity_level=logging.INFO)
    
    # read backup from disk - assign to nornir inventory host attribute
    nornir.run(task=native_config_from_disk)

    # parse config into data model using rosetta / yangify, put yaml / json to file for reference
    result = nornir.run(task=rosetta_parse_native_to_data_model)
    print_result(result, severity_level=logging.INFO)
    result = nornir.run(task=export_vars_to_yaml_standalone)
    print_result(result, severity_level=logging.INFO)

    current_inventory = load_inventory()
    for device_name in nornir.inventory.hosts.keys():
        ntc_rosetta_dict = nornir.inventory.hosts[device_name]["rosetta_parsed_config"]
        native_config = nornir.inventory.hosts[device_name]["native_config"]
        # rosetta_parsed_config
        result = nornir.run(task=transfer_parsed_json_to_host_vars_memory)
        inventory_dict = nornir.inventory.hosts[device_name]["rosetta_parsed_config"]
        # Build New Inventory File with Config / Parsed Config in memory Inventory
        current_inventory[device_name]["data"]["rosetta_parsed_config"] = ntc_rosetta_dict
        current_inventory[device_name]["data"]["native_config"] = native_config
    # write new inventory to file
    result = nornir.run(task=create_yaml_file, python_object_input=current_inventory)
    print_result(result, severity_level=logging.INFO)
    # merge new config for each os type from common openconfig data model 
    result = nornir.run(task=rosetta_merge_new_config_from_data_model)
    print_result(result, severity_level=logging.INFO)

if __name__ == "__main__":
    main()