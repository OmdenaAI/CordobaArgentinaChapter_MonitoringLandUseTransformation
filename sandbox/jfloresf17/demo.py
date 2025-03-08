# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Import the CordobaPredictor module
from cordobaPredictor import *

# Login info to GEE
gee_account = "cordoba@ee-baillehachepascal.iam.gserviceaccount.com"
gee_credentials_path = "../../../earthengine_api_key.json"

# The area of interest, here goes the conversion ee.Geometry -> LongLatBBox
# when Julieta will have done it
area_of_interest = LongLatBBox(-63.42803671537233,-63.34916140311282,-30.42050193711671,-30.339391209687783)

# The dates T1 and T2
days = ["2021-01-01", "2022-12-31"]

# Create a preprocessor instance
preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)

# Get the satellite images using sentinel-2 data and compositing over
# one window of 30 days around the requested dates
preprocessor.nb_max_step_search = 1
preprocessor.step_search_image = 30
preprocessor.data_source = CordobaDataSource.SENTINEL2
images = preprocessor.get_satellite_data(days, area_of_interest)

# Create a predictor instance
predictor = CordobaPredictor()

# Predict the deforestation using dynamic world only with a denoising
# threshold of 0.5
threshold_denoising = 0.5
deforest_mask = predictor.predict_dynamic_world(images, "trees", threshold_denoising)

# Here goes the conversion binary mask -> ee.geometry when Julieta will have
# done it

# To get the mask as an image if necessary
# from PIL import Image
# img = Image.fromarray((deforest_mask*255.0).astype(numpy.uint8))