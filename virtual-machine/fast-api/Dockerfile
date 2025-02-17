# Use Python 3.11.8 base image
FROM python:3.11.8

# Copy application files (including requirements.txt) into the container
COPY app /app

# Set working directory inside the container
WORKDIR /app

# Upgrade pip and install dependencies from requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]