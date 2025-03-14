# Queue Service - Celery Worker for Deforestation Prediction

This is a Celery-based asynchronous service for deforestation prediction. It uses satellite imagery from the Google Earth Engine (GEE) to process and predict deforestation in a specified area of interest (ROI) over a given period. The results from the prediction are saved in a database. The service is built using Python, Celery, and Redis for task management and queuing.

## General File Structure

    celery_app.py: Initializes the Celery app and configures the Celery worker.
    tasks.py: Defines two Celery tasks:
        preprocess_images: Preprocesses satellite images from Google Earth Engine for a given area and time range.
        predict_deforestation: Uses preprocessed images to predict deforestation and stores the results in a database.

## Prerequisites

To run this project, ensure you have installed the required dependencies for the Land Use Change Detection Project and have Google Earth Engine credentials (for satellite data). Set up a Redis server. Ensure that Redis is running on the default port (6379).
    
## Configuration

    Celery Broker & Backend: The project uses Redis as both the broker and backend for Celery.
        Broker URL: redis://localhost:6379/0
        Backend URL: redis://localhost:6379/0

    Celery Settings: Celery is configured with:
        Task serialization format set to JSON.
        Task acknowledgment and retries enabled.
        Task retries set to 3, with a delay of 10 seconds between retries.
        Task routing for queue_service.tasks.* set to the "default" queue.
        The timezone is set to UTC.

These settings may be adjusted based on your environment.

## Running the Service

    Start Celery Worker: To process tasks, run the Celery worker in the terminal:
    ```
    celery -A celery_app.celery_app worker --loglevel=info
    ```
    Run the application: To start processing tasks, call the tasks from within your application code, or trigger the tasks via an API.

## Tasks
#### preprocess_images

This task fetches satellite images from Google Earth Engine for a given set of days and coordinates (ROI). It processes the images using the CordobaDataPreprocessor class and returns the images for further prediction.

Parameters:
    gee_account: Google Earth Engine account.
    gee_credentials_path: Path to the credentials file for Google Earth Engine.
    days: List of days for which images should be fetched.
    roi_coords: Coordinates defining the area of interest (ROI).

#### predict_deforestation

This task uses preprocessed satellite images to predict deforestation in the provided area and time range. It analyzes the images using the CordobaPredictor class and saves the result in the database (configured in the models.py file). The status of the task is also updated in the database.

Parameters:
    images: Preprocessed images for analysis.
    db_session: Active database session (SQLAlchemy).
    days: List of days for which images should be fetched.
    roi_coords: Coordinates defining the area of interest (ROI).

## Running the Application
#### Ensure Redis is running

#### Starting Celery Worker

To start the Celery worker, run the following command:
```
celery -A celery_app.celery_app worker --loglevel=info
```
This will start the Celery worker and it will begin processing tasks from the Redis queue.

#### Running the Task

To enqueue tasks, you can import and call the tasks from tasks.py. Here's an example of how you might trigger a task:

```
from tasks import preprocess_images, predict_deforestation

# Example values for parameters
gee_account = 'your_gee_account'
gee_credentials_path = '/path/to/credentials.json'
days = ['2025-01-01', '2025-01-02']
roi_coords = [[-122.6, 37.4], [-122.6, 37.5], [-122.5, 37.5], [-122.5, 37.4]]

# Call the task to preprocess images
images = preprocess_images.apply_async((gee_account, gee_credentials_path, days, roi_coords))

# Once images are preprocessed, the next task can be triggered
predict_deforestation.apply_async((images.result, db_session, days, roi_coords))
```

Tasks will run asynchronously, and the results will be saved to the database.