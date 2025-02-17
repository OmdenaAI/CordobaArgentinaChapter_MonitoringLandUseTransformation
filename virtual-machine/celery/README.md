# Celery Instance

## Requirements

Celery library has a Redis flavor that can be installed locally:

```bash
pip install celery[redis]
pip freeze > requirements.txt
```

This installs Celery plus the needed dependencies, and `pip freeze` prepares the file for the Dockerfile to use.

## Application

The application has 2 modules:

- celery_app.py: Connection to the REDIS instance for broker database and results database. General Celery application config + logging config.
- tasks.py: All the application registered tasks.

## Dockerfile

The Celery instance requires connection to the Redis instance, which acts as broker; so in this case, we need a custom Dockerfile to instruct Docker on how to build the application. The setup is very simple, includes files transfer into the container, installing the requirements from the requirements file and the command to launch the Celery workers. 

## Deployment using Docker Compose

The compose for this is part of the main docker-compose.yaml file present in the Redis dir, and the Dockerfile present in this dir is referenced there, so is the .env file.

## Useful commands