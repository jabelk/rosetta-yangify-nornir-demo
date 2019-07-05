#!/usr/bin/env python
# thanks to Nick R and dmfigol examples:

"""
Nornir runbook to run arbitrary commands on network devices
"""

import os
import logging
from nornir import InitNornir
from nornir.core.task import Task
from nornir.plugins.tasks.networking import napalm_cli
from nornir.plugins.tasks.files import write_file
from nornir.plugins.functions.text import print_result
from nornir.core.filter import F
from nornir.plugins.tasks.networking import napalm_get

# rest api
import json
import yaml
from copy import deepcopy
import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()
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

# def temp(task):
#     ios = get_driver("ios", "openconfig")
#     ios_driver = ios()
#     parsed_vlans = ios_driver.parse(
#     native={"dev_conf": native_config_from_disk(task)},
#     validate=False,
#     include=[
#          "/openconfig-network-instance:network-instances/network-instance/name",
#         "/openconfig-network-instance:network-instances/network-instance/config",
#         "/openconfig-network-instance:network-instances/network-instance/vlans",
#         ]
#     )
#     print(json.dumps(parsed_vlans.raw_value(), indent=4))

def native_config_from_disk(task):
    with open("config/backed_up_from_device/{}_napalm_backup.conf".format(task.host.name), "r") as f:
        native_config = f.read()
    # Save the compiled configuration into a host variable
    task.host["native_config"] = native_config
    # ios_devices.inventory.hosts.get("csr1kv").data["native_config"] = config_from_disk

def parsed_config_from_disk(task):
    with open("config/data_models_from_parsing/{}_rosetta.json".format(task.host.name), "r") as f:
        ntc_rosetta_json = f.read()
    task.host["rosetta_parsed_config"] = ntc_rosetta_json

def rosetta_parse_native_to_data_model(task):
    ios = get_driver("ios", "openconfig")
    ios_driver = ios()
    ntc_rosetta_data = ios_driver.parse(native={"dev_conf": task.host["native_config"]})
    ntc_rosetta_dict = ntc_rosetta_data.raw_value()
    task.host["rosetta_parsed_config"] = ntc_rosetta_data.raw_value()

def rosetta_merge_new_config_from_data_model(task):
    ios = get_driver("ios", "openconfig")
    ios_processor = ios()
    new_vlans = {'openconfig-network-instance:network-instances': 
    {'network-instance': [{'name': 'default', 'config': {'name': 'default'}, 
    'vlans': {'vlan': [{'vlan-id': 10, 'config': {'vlan-id': 10, 'name': 'prod', 'status': 'ACTIVE'}}, 
    {'vlan-id': 20, 'config': {'vlan-id': 20, 'name': 'dev', 'status': 'SUSPENDED'}}]}}]}}
    print("New Vlans Data Model")
    print(json.dumps(new_vlans, indent=4))
    running_config = task.host["rosetta_parsed_config"]
    print("running config is ")
    print(running_config)
    merged_config = ios_processor.merge(candidate=new_vlans, running=running_config)
    # print("merged config is ")
    # print(merged_config)

def backup(task, path):
    r = task.run(
        task=napalm_get,
        getters=["config"],
        severity_level=logging.DEBUG,
    )
    task.run(
        task=write_file,
        filename=f"{path}/{task.host}_napalm_backup.conf",
        content=r.result["config"]["running"],
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

def main() -> None:
    nornir = InitNornir()
    # Get Openconfig Interface Data from CSR1000v from Restconf
    ios_devices = nornir.filter(F(platform="ios"))
    # result = ios_devices.run(task=temp)
    # print_result(result, severity_level=logging.INFO)

    # back up to disk using napalm getter 
    result = ios_devices.run(task=backup, path="config/backed_up_from_device")
    # print_result(result, severity_level=logging.INFO)
    
    # read backup from disk - assign to nornir inventory host attribute
    ios_devices.run(task=native_config_from_disk)
    # ios_devices.inventory.hosts.get("csr1kv").data["native_config"] = config_from_disk["csr1kv"].result

    # parse config into data model using rosetta / yangify, put yaml / json to file for reference
    result = ios_devices.run(task=rosetta_parse_native_to_data_model)
    print_result(result, severity_level=logging.INFO)

    print("rosetta dict\n\n")
    print(ios_devices.inventory.hosts["csr1kv"]["rosetta_parsed_config"])
    path = "config/data_models_from_parsing"
    ntc_rosetta_dict = ios_devices.inventory.hosts["csr1kv"]["rosetta_parsed_config"]
    native_config = ios_devices.inventory.hosts["csr1kv"]["native_config"]
    ios_devices.run(task=create_json_file, python_object_input=ntc_rosetta_dict, filename=f"{path}/csr1kv_rosetta.json")
    ios_devices.run(task=create_yaml_file, python_object_input=ntc_rosetta_dict, filename=f"{path}/csr1kv_rosetta.yml")
    # rosetta_parsed_config
    result = ios_devices.run(task=parsed_config_from_disk)
    print_result(result, severity_level=logging.INFO)

    inventory_dict = ios_devices.inventory.hosts["csr1kv"]["rosetta_parsed_config"]
    print(ios_devices.inventory.hosts["csr1kv"]["rosetta_parsed_config"])
    # Build New Inventory File with Config / Parsed Config in memory Inventory
    current_inventory = load_inventory()
    current_inventory["csr1kv"]["data"]["rosetta_parsed_config"] = ntc_rosetta_dict
    current_inventory["csr1kv"]["data"]["native_config"] = native_config
    result = ios_devices.run(task=create_yaml_file, python_object_input=current_inventory)
    print_result(result, severity_level=logging.INFO)

    # merge new config into running parsed
    result = ios_devices.run(task=rosetta_merge_new_config_from_data_model)
    print_result(result, severity_level=logging.INFO)
    # result = ios_devices.run(task=get_restconf_all_interfaces, model="openconfig")
    # print_result(result["csr1kv"], severity_level=logging.INFO)



if __name__ == "__main__":
    main()