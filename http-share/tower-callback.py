import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
# from pprint import pprint
import time
import sys
import json
import yaml
import socket
import os

def import_variables_from_file():
    variables_file=open('tower-config.yml', 'r')
    variables_in_string=variables_file.read()
    # print variables_in_string
    variables_in_yaml=yaml.safe_load(variables_in_string)
    # print variables_in_yaml
    # print variables_in_yaml['awx']['ip']
    variables_file.close()
    return variables_in_yaml

def tower_request(url, payload, request_type):
    config=import_variables_from_file()

    authuser = config['user']['username']
    authpass = config['user']['password']
    towerhost = config['awx']['ip']
    towerport = config['awx']['port']

    headers = { 'content-type' : 'application/json' }
    if towerport != 443:
        base_url = 'https://' + towerhost + ':' + str(towerport) + '/api/v2/'
    else: 
        base_url = 'https://' + towerhost + '/api/v2/'
    url = base_url + url

    if request_type == 'POST':
        try:
            response = requests.post(url, headers=headers, auth=(authuser, authpass), data=json.dumps(payload), verify=False)
            print(response.json())
        except HTTPError as e:
            print(e.response.text)

def launch_job(extra_vars, limit, template_id=1):
    payload = {
        "limit": limit,
        "verbosity": 3,
        "extra_vars": extra_vars
    }
    url = 'job_templates/' + str(template_id) + '/launch/'
    request = tower_request(url=url, payload=payload, request_type="POST")

def add_host_to_inventory(hostname, ip, inventory_id=1):
    payload = {
        "name": ip,
        "description": hostname,
        "variables": None
    }
    url = 'inventories/' + str(inventory_id) + '/hosts/'
    request = tower_request(url=url, payload=payload, request_type="POST")

def get_server_hostname():
    hostname = os.uname()[1]
    return hostname

def get_server_ip():
    hostname = socket.gethostname()    
    ip = socket.gethostbyname(hostname)    
    return ip

def main():
    
    hostname = get_server_hostname()
    ip = get_server_ip()
    if hostname and ip:
        try:
            add_host_to_inventory(hostname=hostname, ip=ip)
            launch_job(extra_vars={}, limit=ip, template_id=9)
        except Exception as e:
            # TODO handle more specific errors
            print(e)
    else:
        print("Hostname or IP now found")
        print(hostname)
        print(ip)

if __name__ == "__main__":
    main()