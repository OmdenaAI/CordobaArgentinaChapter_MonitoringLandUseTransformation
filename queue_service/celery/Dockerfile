# Use Python 3.11.8 base image
FROM python:3.11.8

# Copy application files (including requirements.txt) into the container
COPY app /app

# Set working directory inside the container
WORKDIR /app

# Upgrade pip and install dependencies from requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Command
CMD [ "celery", "-A", "celery_app.celery_app", "worker", "--autoscale=10,2", "--loglevel=info" ]

