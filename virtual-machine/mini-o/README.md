# MiniO Instance

## Purpose

MinIO is an object storage solution that provides an Amazon Web Services S3-compatible API and supports all core S3 features. MinIO is built to deploy anywhere - public or private cloud, baremetal infrastructure, orchestrated environments, and edge infrastructure.

In this project's case, this solution was deployed to store unserialisable data, like images.

## Deployment using Docker Compose

The MiniO image used is pulled directly from Docker Hub, using `quay.io/minio/minio:latest`, which resulted in version `RELEASE.2025-02-18T16-25-55Z (go1.23.6 linux/amd64)`. The instance gets an associated `volume` in the deployment in order to persist the files saved.

Deployed with the main [Docker Compose](virtual-machine\docker-compose.yaml) file. Notice that a MiniO Client container is built from image `minio/mc` pulled from the Docker Hub, in order to run an entrypoint script that makes sure a default bucket is set. The container is terminated after execution.

The storage instance can be interacted with using MiniO Console at http://localhost:9001.