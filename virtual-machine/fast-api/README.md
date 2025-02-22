# FastAPI App

## Requirements

FastAPI and Uvicorn server were installed locally, together with the Celery library ready to work with Redis:

On windows
```powershell
py -3.11 -m venv venv
```

```powershell
.\venv\Scripts\Activate
```

```bash
pip install fastapi uvicorn celery[redis]
pip freeze > requirements.txt
```

This installed all the needed dependencies, and `pip freeze` prepares the file for the Dockerfile to use.

## Application

The application has 2 modules:

- celery_config.py: Celery connector.
- main.py: Fast API configuration + endpoints.

Endpoints can be tested from the Swagger docs interface at /docs

## Dockerfile

Including the needed files and installs for the FastAPI app to connect to Celery/Redis + the launch command.

## Deployment using Docker Compose

Deployed with the main [Docker Compose](virtual-machine\docker-compose.yaml) file.



