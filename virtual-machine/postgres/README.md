# Postgres Instance

## Deployment using Docker Compose

The Postgres image used is pulled directly from Docker Hub, using `postgis/postgis:16-3.4`. This version maintains compatibility with code pushed to the api gateway development branch, together with the Postgis extension. In order to persist the data in the database beyond the container's life, the instance got associated to a `volume` in the deployment.

An entrypoint script was mounted to the corresponding location in the image to make sure the needed databases are created if they do not exist when the container starts, as well as checking the Postgis extension is up and running. If a database dump file is placed in the backup directory, the script also takes care of restoring the backup.

Deployed with the main [Docker Compose](virtual-machine\docker-compose.yaml) file.