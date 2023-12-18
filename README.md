# dell-ansible-autodeploy

# AWX
## Deploy AWX on Docker (for testing and development only)
```
git clone -b 23.5.1 https://github.com/ansible/awx.git
docker pull quay.io/ansible/receptor:latest
export RECEPTOR_IMAGE=quay.io/ansible/receptor:latest
make docker-compose-build
make docker-compose COMPOSE_UP_OPTS=-d
docker exec tools_awx_1 make clean-ui ui-devel
docker exec -ti tools_awx_1 awx-manage createsuperuser

https://<ip>:8043

sudo firewall-cmd --add-forward-port=port=443:proto=tcp:toport=8043 --permanent
sudo firewall-cmd --reload
https://<ip>
Username: awx
```

## Fresh Start
***Warning this will delete all containers, volumes and networks
```
docker stop $(docker ps -a -q)
docker system prune -a
docker volume prune -a
docker network prune
```

# Dell Ansible Execution Environment
## Build
```
pip install ansible-builder ansible-runner
ansible-builder build -f execution-environment.yml --container-runtime=docker -c build_context --tag dell-openmanage-ee:latest
```

## Test
```
ansible-runner run --process-isolation --process-isolation-executable docker --container-image dell-openmanage-ee:latest -p playbook.yml ./runner-example/ -v
```

# Container Registry
openssl req -x509 -out /opt/container-registry/certs/server.example.com.crt -keyout /opt/container-registry/certs/server.example.com.key -days 1825 \
  -newkey rsa:2048 -nodes -sha256 \
  -subj "/C=US/ST=CO/L=OSE/O=Dell/CN=server.example.com" -extensions EXT -config <( \
   printf "[dn]\nCN=server.example.com\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:server.example.com\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")

docker run -d --name container-registry \
-p 5000:5000 \
-v /opt/container-registry/data:/var/lib/registry:z \
-v /opt/container-registry/auth:/auth:z \
-e "REGISTRY_AUTH=htpasswd" \
-e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
-e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
-v /opt/container-registry/certs:/certs:z \
-e "REGISTRY_HTTP_TLS_CERTIFICATE=/certs/server.example.com.crt" \
-e "REGISTRY_HTTP_TLS_KEY=/certs/server.example.com.key" \
-d \
docker.io/library/registry:latest

docker run --entrypoint htpasswd httpd:2 -Bbn admin "Password@123" > /opt/container-registry/auth/htpasswd

## Push Dell Ansible Execution Environment to Container Registry
docker tag dell-openmanage-ee localhost:5000/dell-openmanage-ee:latest
docker push localhost:5000/dell-openmanage-ee:latest

# Dell OpenManage ZeroTouch
## Documentation Links
ZeroTouch Bare-Metal Configuration Guide
https://dl.dell.com/manuals/all-products/esuprt_software/esuprt_it_ops_datcentr_mgmt/dell-management-solution-resources_white-papers9_en-us.pdf
Using Server Configuration Profiles to Deploy Operating Systems
https://dl.dell.com/manuals/common/dell-emc-scp-os-deploy-poweredge.pdf

## Configure iDRAC
 Possible Values:
  - Disabled (0) — iDRAC does not perform DHCP configuration
  - Enable once (1) — iDRAC performs DHCP configuration once
  - Enable once after reset (2) — Performs configuration after iDRAC is reset

```
racacm -r <IP> -u root -p "calvin" set iDRAC.NIC.AutoConfig "Enable Once"
```

## Configure DHCP Options
### Option 43
Scope Option: 043 Vendor Specific Info
Value: <HTTP Share IP>

### Option 60
Scope Option: 060 Vendor Class
Name: iDRAC
Value: -f config.xml -i <HTTP Share IP> -s http