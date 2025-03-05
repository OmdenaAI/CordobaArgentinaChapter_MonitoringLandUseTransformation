from celery import Celery
from typing import Dict, Any

# Import the CordobaDataPreprocessor class
# Needs to be adjusted based on the actual implementation
from sandbox.baillehache.cordobaDataPreprocessor import CordobaDataPreprocessor
from sandbox.baillehache.cordobaDataPreprocessor import LongLatBBox, CordobaImage

# Initialize Celery and set Redis as the broker
celery_app = Celery(
    'cordoba_data_preprocessor', 
    broker='redis://localhost:6379/0',  # Use Redis as the message broker
    backend='redis://localhost:6379/0', # Use Redis as the result backend
)

# Process image using the model
celery_app.conf.update(
    task_routes = {
        'cordoba_tasks.process_image': {'queue': 'image_processing'},
        'cordoba_tasks.preprocess_ndvi': {'queue': 'preprocessing'},
        'cordoba_tasks.radiometric_registration': {'queue': 'registration'},
        'cordoba_tasks.get_ee_image_registered': {'queue': 'registration'},
        'cordoba_tasks.get_satellite_data': {'queue': 'data_retrieval'},
        'cordoba_tasks.cvt_ee_image_to_cordoba_image': {'queue': 'conversion'},
        'cordoba_tasks.download_numpy_data': {'queue': 'data_retrieval'},
        'cordoba_tasks.get_best_acquisition_dates': {'queue': 'data_retrieval'},
        'cordoba_tasks.preprocess_ndbi': {'queue': 'preprocessing'},
        'cordoba_tasks.preprocess_evi': {'queue': 'preprocessing'},
        'cordoba_tasks.preprocess_gaussian_blur': {'queue': 'preprocessing'},   
    }
)

# Celery task for processing image
@celery_app.task(name="processing image")
def process_image_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    result = preprocessor.get_ee_image(date, area, source)
    return result

# Celery task for NDVI preprocessing
@celery_app.task(name = "preprocess_ndvi")
def preprocess_ndvi_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)
    result = preprocessor.preprocess_ndvi(image)
    return result

# Celery task for NDBI preprocessing
@celery_app.task(name = "preprocess_ndbi")
def preprocess_ndbi_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)
    result = preprocessor.preprocess_ndbi(image)
    return result

# Celery task for EVI preprocessing
@celery_app.task(name = "preprocess_evi")
def preprocess_evi_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)
    result = preprocessor.preprocess_evi(image)
    return result

# Celery task for Gaussian Blur preprocessing
@celery_app.task(name = "preprocess_gaussian_blur")
def preprocess_gaussian_blur_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)
    result = preprocessor.preprocess_gaussian_blur(image)
    return result

# Celery task for radiometric registration
@celery_app.task(name = "radiometric_registration")
def radiometric_registration_task(gee_account, gee_credentials_path, date, area, source, ee_image_ref):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)
    result = preprocessor.radiometric_registration(ee_image_ref, image, area)
    return result

# Celery task for image registration
@celery_app.task(name = "get_ee_image_registered")
def get_ee_image_registered_task(gee_account, gee_credentials_path, date, area, ee_image_ref):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image, actual_source = preprocessor.get_ee_image_registered(date, area, ee_image_ref)
    return {"image": image, "actual_source": actual_source}

# Celery task for downloading satellite data
@celery_app.task(name = "get_satellite_data")
def get_satellite_data_task(gee_account, gee_credentials_path, dates, area):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    images = preprocessor.get_satellite_data(dates, area)
    return images

# Celery task for converting EE image to Cordoba image
@celery_app.task(name = "cvt_ee_image_to_cordoba_image")
def cvt_ee_image_to_cordoba_image_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)  # Assume source is passed correctly
    result = preprocessor.cvt_ee_image_to_cordoba_image(image)
    return result

# Celery task for downloading numpy data from EE image
@celery_app.task(name = "download_numpy_data")
def download_numpy_data_task(gee_account, gee_credentials_path, date, area, source):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    image = preprocessor.get_ee_image(date, area, source)  # Assume source is passed correctly
    result = preprocessor.download_numpy_data(image, area)
    return result

# Celery task for getting best acquisition dates
@celery_app.task(name = "get_best_acquisition_dates")
def get_best_acquisition_dates_task(gee_account, gee_credentials_path, date_from, date_to, area, min_interval):
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
    best_dates = preprocessor.get_best_acquisition_dates(date_from, date_to, area, min_interval)
    return best_dates