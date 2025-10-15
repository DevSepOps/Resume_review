# Bootstrapping docker swarm
docker swarm init --advertise-addr <ip-address>

# Creating network
docker network create -d overlay resume_network

# Creating volumes
docker volume create postgres_data
docker volume create es_data
docker volume create grafana-data
docker volume create portainer_data
docker volume create traefik-logs
docker volume create traefik-letsencrypt
docker volume create traefik-certs
docker volume create logstash_pipeline
docker volume create grafana-provisioning

# Deploying the stack
docker stack deploy -c docker-compose.swarm.yml resume

# Checking services
docker stack services resume

# Checking logs
docker service logs resume_traefik
