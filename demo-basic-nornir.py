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


def native_config_from_disk(task):
    with open("config/backed_up_from_device/{}_napalm_backup.conf".format(task.host.name), "r") as f:
        native_config = f.read()
    return native_config

def rosetta_parse_native_to_data_model(task):
    ios = get_driver("ios", "openconfig")
    ios_driver = ios()
    ntc_rosetta_data = ios_driver.parse(native={"dev_conf": native_config_from_disk(task)})
    url = 'https://127.0.0.1:2225/restconf/data/Cisco-IOS-XE-native:native/interface'
    response = requests.get(url, headers=headers, auth=auth, verify=False)
    device_api = json.loads(response.text)
    device_api = yaml.dump(device_api, default_flow_style=False)
    ntc_rosetta_json = ntc_rosetta_data.raw_value()
    ntc_rosetta_yaml = yaml.dump(ntc_rosetta_data.raw_value(), default_flow_style=False)
    return ntc_rosetta_json, ntc_rosetta_yaml

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

def parse_config_to_json(task, path):
    ntc_rosetta_json, ntc_rosetta_yaml = rosetta_parse_native_to_data_model(task)
    ntc_rosetta_json = json.dumps(ntc_rosetta_json)
    task.run(
        task=write_file,
        filename=f"{path}/{task.host}_rosetta.json",
        content=ntc_rosetta_json,
    )
    task.run(
        task=write_file,
        filename=f"{path}/{task.host}_rosetta.yml",
        content=ntc_rosetta_yaml,
    )

def main() -> None:
    nornir = InitNornir()
    # Get Openconfig Interface Data from CSR1000v from Restconf
    ios_devices = nornir.filter(F(platform="ios"))
    # print(ios_devices.inventory.hosts.get("csr1kv").get("candidate_config_model"))
    result = ios_devices.run(task=backup, path="config/backed_up_from_device")
    print_result(result, severity_level=logging.INFO)

    result = ios_devices.run(task=parse_config_to_json, path="config/backed_up_from_device")
    print_result(result, severity_level=logging.INFO)


    # result = ios_devices.run(task=native_config_from_disk("ios","config.txt"))
    # print_result(result)

    # result = ios_devices.run(task=get_restconf_all_interfaces, model="openconfig")
    # print_result(result["csr1kv"], severity_level=logging.INFO)

    # # Get Openconfig Interface Data parsed from native CLI on disk

    # result = ios_devices.run(task=parse_config)
    # print_result(result, severity_level=logging.INFO)


if __name__ == "__main__":
    main()