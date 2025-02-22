#!/bin/bash

# Start the first worker for high_priority queue
celery -A celery_app.celery_app worker --queue=high_priority --concurrency=2 --loglevel=info &

# Start the second worker for medium_priority and low_priority queues
celery -A celery_app.celery_app worker --queue=medium_priority,low_priority --concurrency=1 --loglevel=info &

# Wait for all background processes to finish
wait
