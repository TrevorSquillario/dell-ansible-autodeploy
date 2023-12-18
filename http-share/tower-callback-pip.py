import json
import time
import os
import socket
import tower_cli

# use the undocumented API client from the tower-cli tool
group_resource = tower_cli.get_resource('group')
host_resource = tower_cli.get_resource('host')

CREATE_TOWER_GROUPS = True
DEFAULT_INVENTORY = 1

def get_tower_group(group_name, create=True):
    """
    Given a group name, find or optionally create a corresponding Tower group.
    """
    groups = group_resource.list(all_pages=True)['results']
    matching_groups = [g for g in groups if g['name'] == group_name]

    if not matching_groups:
        # no matching group
        if create:
            tower_group = group_resource.create(name=group_name,
                                        inventory=DEFAULT_INVENTORY,
                                        description="auto created ASG group")
        else:
            raise RuntimeError("no matching group")
    else:
        tower_group = matching_groups[0]
    return tower_group


def get_tower_host(host_name_or_ip, inventory=1):
    hosts = host_resource.list(inventory=inventory, all_pages=True)['results']
    matching_hosts = [h for h in hosts if h['name'] == host_name_or_ip]
    if matching_hosts:
        return matching_hosts[0]
    return None


def add_host_to_inventory(hostname, ip):
    tower_group = get_tower_group("TestServers",
                                  create=CREATE_TOWER_GROUPS)

    new_host = host_resource.create(
                    name=ip,
                    description=hostname,
                    inventory=1
                    )

    host_resource.associate(new_host['id'], tower_group['id'])


def remove_host_from_inventory(ip):
    # get group
    tower_group = get_tower_group("TestServers",
                                  create=CREATE_TOWER_GROUPS)

    host = get_tower_host(ip)

    # The Tower API does not allow the removal or disabling of a host
    # so the best we can do for now is dissociate it from the group
    # dissacociate? or does it cascade delete?

    if host:
        host_resource.disassociate(host['id'], tower_group['id'])

def launch_job(job_template, extra_vars, limit):
    host_resource.launch(
        job_template=job_template,
        monitor=False,
        wait=False,
        timeout=1500,
        extra_vars=None,
        limit=limit
    )

def get_server_hostname():
    hostname = os.uname()[1]
    return hostname

def get_server_ip():
    hostname = socket.gethostname()    
    ip = socket.gethostbyname(hostname)    
    return ip

def main():
    while True:
        hostname = get_server_hostname()
        ip = get_server_ip()
        if hostname and ip:
            try:
                add_host_to_inventory(hostname, ip)
                launch_job(job_template="Test", extra_vars=None, limit=hostname)
            except Exception as e:
                # TODO handle more specific errors
                print(e)
        else:
            print("Hostname or IP now found")
            print(hostname)
            print(ip)

if __name__ == "__main__":
    main()