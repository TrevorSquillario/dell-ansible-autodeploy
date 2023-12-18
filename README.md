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