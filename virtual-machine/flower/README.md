# Flower Instance

## Purpose

Flower is an open-source framework for monitoring and managing Celery clusters (it allows scaling and pooling). It provides real-time information about the status of Celery workers and tasks providing a fully featured GUI, and can be easily integrated to general purpose monitoring applications like Grafana, though it also provides a CLI.

## Deployment using Docker Compose

The Flower image used is pulled directly from Docker Hub, using `mher/flower`, which resulted in Flower v=2.0.0. In order to enable custom settings being saved, the instance got associated to a `volume` in the deployment.

Deployed with the main [Docker Compose](virtual-machine\docker-compose.yaml) file.

Once deployed, it can be accessed from its GUI at http://localhost:5555/broker.
