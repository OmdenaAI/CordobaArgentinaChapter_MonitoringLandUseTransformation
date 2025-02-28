from celery import Celery
from queue_service.celery.app.celery_app import celery_app
from sandbox.baillehache.cordobaDataPreprocessor import CordobaDataPreprocessor
from typing import List
from sandbox.baillehache.cordobaDataPreprocessor import LongLatBBox, CordobaImage  # Ensure these are correctly imported

@celery_app.task(name="run_get_satellite_data")
def run_get_satellite_data(data):
    """
    Celery task to run the get_satellite_data function from the CordobaDataPreprocessor class.

    Args:
        data (dict): Contains:
            - dates: List[str]: List of dates for images
            - area: dict: Bounding box for the area of interest
            - source: str: Data source (e.g., 'SENTINEL2')

    Returns:
        dict: Task status and list of processed image data.
    """
    try:
        pre_processor = CordobaDataPreprocessor()  # Instantiate inside task

        # Ensure dates is a list
        dates = data["date"] if isinstance(data["date"], list) else [data["date"]]

        # Convert area dict to LongLatBBox object (adjust based on actual structure)
        area = LongLatBBox(**data["area"])

        # Run the satellite data retrieval
        result_images: List[CordobaImage] = pre_processor.get_satellite_data(dates, area)

        # Convert CordobaImage objects to a returnable format
        processed_images = [image.to_dict() for image in result_images]  # Assuming CordobaImage has a `to_dict()` method

        return {"status": "success", "result": processed_images}

    except Exception as e:
        return {"status": "error", "message": str(e)}