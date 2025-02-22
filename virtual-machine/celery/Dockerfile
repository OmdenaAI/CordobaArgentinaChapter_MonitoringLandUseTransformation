FROM python:3.11.8-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*
# Copy application files (including requirements.txt) into the container
COPY app /app

# Set working directory inside the container
WORKDIR /app

# Upgrade pip and install dependencies from requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Command
CMD [ "celery", "-A", "celery_app.celery_app", "worker", "--loglevel=info" ]

