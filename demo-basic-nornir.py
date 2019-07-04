#!/usr/bin/env python
# thanks to Nick R example:
# https://github.com/nickrusso42518/ansible2nornir/tree/master/getter/nornir
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

# rest api
import json
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

def parse_config(task):
    ios = get_driver("ios", "openconfig")
    ios_driver = ios()
    with open("data/ios/config.txt", "r") as f:
        config = f.read()
    parsed = ios_driver.parse(native={"dev_conf": config})
    print("printing ntc_rosetta parsed config")
    print(json.dumps(parsed.raw_value(), indent=4))

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

def main() -> None:
    nornir = InitNornir()
    # Get Openconfig Interface Data from CSR1000v from Restconf
    result = nornir.run(task=get_restconf_all_interfaces, model="openconfig")
    # print_result(result["csr1kv"], severity_level=logging.INFO)
    # Get Openconfig Interface Data parsed from native CLI on disk
    result = nornir.run(task=parse_config)
    print_result(result, severity_level=logging.INFO)


if __name__ == "__main__":
    main()