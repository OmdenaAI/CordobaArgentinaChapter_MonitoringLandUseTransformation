# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Import the CordobaPredictor module
from cordobaPredictor import *

def process(roi, days):
    """
    Process the deforestation prediction with dynamic ROI and date range.
    :param roi: The area of interest as an ee.Geometry object
    :param days: List of two dates [start_date, end_date]
    """
    # Login info to GEE
    gee_account = "cordoba@ee-baillehachepascal.iam.gserviceaccount.com"
    gee_credentials_path = "../../../earthengine_api_key.json"

    # Create a preprocessor instance
    preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)

    # Convert the input roi to a LongLatBBox
    area_of_interest = LongLatBBox.from_ee_geometry(roi)

    # Get the satellite images using sentinel-2 data
    preprocessor.nb_max_step_search = 1
    preprocessor.step_search_image = 30
    preprocessor.data_source = CordobaDataSource.SENTINEL2
    images = preprocessor.get_satellite_data(days, area_of_interest)

    # Create a predictor instance
    predictor = CordobaPredictor()

    # Predict the deforestation using dynamic world only with a denoising
    threshold_denoising = 0.5
    deforest_mask = predictor.predict_dynamic_world(images, "trees", threshold_denoising)

    # Convert the binary mask to ee.Geometry
    deforest_rois = predictor.get_ee_geometry_from_mask(images[1], deforest_mask)

    return deforest_rois
