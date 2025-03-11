from celery import Celery, chain
import ee
import logging

# Import the CordobaDataPreprocessor class
# Needs to be adjusted based on the actual implementation
from sandbox.baillehache.cordobaDataPreprocessor import *
from sandbox.baillehache.cordobaPredictor import *

# Imports related to the database
# Needs to be adjusted based on the actual implementation
from models import RequestData, Result
from sqlalchemy.orm import Session


# Initialize Celery and set Redis as the broker
celery_app = Celery(
    'cordoba_data_preprocessor', 
    broker='redis://localhost:6379/0',  # Use Redis as the message broker
    backend='redis://localhost:6379/0', # Use Redis as the result backend
)

# Optional: Define more configuration, like retries, time limits, etc.
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
    )

# Task 1: Preprocess the request and get satellite images
@celery_app.task(name="preprocess_images")
def preprocess_images(gee_account, gee_credentials_path, days, roi_coords):
    """
    Task to preprocess the image data by fetching satellite images for the given dates and area of interest (ROI).
    This task interacts with the CordobaDataPreprocessor to fetch images from Sentinel-2.
    """
    try:
        # Logging for debugging purposes
        logging.info(f"Starting image preprocessing for dates: {days} and ROI coordinates: {roi_coords}")

        # Create a preprocessor instance
        preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)

        # Define the area of interest
        roi = ee.Geometry.Polygon(roi_coords)
        area_of_interest = LongLatBBox.from_ee_geometry(roi)

        # Get the satellite images using Sentinel-2 data
        preprocessor.nb_max_step_search = 1
        preprocessor.step_search_image = 30
        preprocessor.data_source = CordobaDataSource.SENTINEL2
        images = preprocessor.get_satellite_data(days, area_of_interest)

        # Logging for debugging purposes
        logging.info(f"Successfully fetched images.")

        # Return images to be used in prediction
        return images
    
    except Exception as e:
        # Logging for debugging purposes
        logging.error(f"Error during image preprocessing: {e}")
        raise Exception(f"Error during image preprocessing: {e}")

# Task 2: Predict deforestation using the preprocessed images and save the result
@celery_app.task(name="predict_deforestation")
def predict_deforestation(images, db_session, days, roi_coords):
    """
    Task to predict deforestation using the preprocessed images.
    This task uses the CordobaPredictor module to analyze the images and detect deforestation.
    It then saves the result to the database for the requested days and roi_coords.
    """
    try:
        # Logging for debugging purposes
        logging.info(f"Starting deforestation prediction using preprocessed images.")

        # Create a predictor instance
        predictor = CordobaPredictor()

        # Predict the deforestation using dynamic world with a denoising
        # threshold of 0.5
        threshold_denoising = 0.5
        deforest_mask = predictor.predict_dynamic_world(images, "trees", threshold_denoising)

        # Convert the binary mask to ee.Geometry
        # `deforest_rois` is a list of ee.Geometry, each one is a detected area of
        # deforestation and should be displayed in the UI
        deforest_rois = predictor.get_ee_geometry_from_mask(images[1], deforest_mask)

        # Logging for debugging purposes
        logging.info(f"Successfully predicted deforestation.")

        # Needs to be adjusted based on the implementation of the database
        # Generate a hash from the request_data (could be a specific identifier like a UUID)
        request_hash = str(days, roi_coords)

        # Save the deforestation result to the database
        new_result = Result(request_hash=request_hash, result=deforest_rois)
        db_session.add(new_result)
        db_session.commit()

        # Update the status of the request in the database
        db_session.query(RequestData).filter(RequestData.request_hash == request_hash).update({"status": "completed"})
        db_session.commit()

        # Logging for debugging purposes
        logging.info(f"Successfully saved the result for the predicted deforestation in the database.")

        # Return messahe that the task is completed and result saved
        return {"status": "success", "message": "Deforestation prediction completed and result saved"}
    
    except Exception as e:
        # Update the status of the request in the database
        db_session.query(RequestData).filter(RequestData.request_hash == request_hash).update({"status": "failed"})
        db_session.commit()

        # Logging for debugging purposes
        logging.error(f"Error during deforestation prediction and saving of the result: {e}")

        raise Exception(f"Error during deforestation prediction and saving of the result: {e}")