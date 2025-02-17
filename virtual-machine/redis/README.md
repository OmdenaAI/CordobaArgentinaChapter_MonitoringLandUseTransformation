# Redis Instance

## Deployment using Docker Compose

The redis instance used is pulled directly from Docker Hub, using `redis:latest`, which resulted in Redis server v=7.4.2. This official image uses default settings that put 16 databases online. Notice that databases require associated `volumes` where to store the data, included in the compose file, besides the reference to the network. Environment variables can be easily added with a reference to a .env file.

Deployed with the main [Docker Compose](virtual-machine\docker-compose.yaml) file.

## Useful commands

### Access with Redis CLI from inside the container.
```bash
sudo docker exec -it redis-instance redis-cli
```

### Remember to auth to use the databases (if a password was set).
```bash
AUTH mysecretpassword
```

### Select database (by number).
```bash
SELECT 0
```

