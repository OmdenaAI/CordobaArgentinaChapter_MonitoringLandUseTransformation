import os
from celery import Celery


# Create Celery app
celery_app = Celery(
    "tasks",
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND'),
    include=["tasks"] # Module where tasks are registered
)

celery_app.conf.update(
    # Timezone & UTC Settings
    timezone="UTC",  # Set a timezone
    enable_utc=True,  # Enable UTC mode

    # Worker Concurrency & Performance
    worker_concurrency=2,  # Adjust based on CPU cores (Example: 4)
    worker_prefetch_multiplier=1,  # Prevents one worker from grabbing too many tasks at once
    worker_autoscale=(1, 2),
    worker_max_tasks_per_child=100,  # Restart worker after processing 100 tasks (Prevent memory leaks)
    
    # Broker Settings
    broker_heartbeat=30,  # Avoids long-running connections breaking
    broker_pool_limit=None,  # Prevents connection pool exhaustion
    broker_connection_retry_on_startup=True,  # Ensures Celery retries broker connection if it fails at startup

    # Task Acknowledgment & Result Expiry
    task_acks_late=True,  # Ensure tasks are acknowledged only after execution (Prevents losing tasks on worker crash)
    task_reject_on_worker_lost=True,  # Ensures task is re-queued if a worker dies before finishing it
    result_expires=86400,  # 24 hours in seconds, cleanup old results

    # Rate Limiting
    worker_disable_rate_limits=False,  # Enable per-task rate limiting

    # Task Retry Settings
    task_default_retry_delay=10,  # Wait 10 sec before retrying a failed task
    task_max_retries=5,  # Maximum retries before task is marked as failed
    task_acks_on_failure_or_timeout=False,  # Prevents lost tasks due to crashes

    # Task Timeouts
    task_time_limit=300,  # Hard limit (Kill task if it exceeds 5 min)
    task_soft_time_limit=280,  # Graceful limit (Warn before killing task)

    # Error Handling & Monitoring
    task_track_started=True,  # Track when a task starts
    worker_send_task_events=True,  # Enable task monitoring in Flower
    
    # Logging (Optional)
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
)
