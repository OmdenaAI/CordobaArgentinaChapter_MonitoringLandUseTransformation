# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Import the CordobaPredictor module
from cordobaPredictor import *

# Login info to GEE
gee_account = "cordoba@ee-baillehachepascal.iam.gserviceaccount.com"
gee_credentials_path = "../../../earthengine_api_key.json"

# Create a preprocessor instance
preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)

# The area of interest
# below I use the variable `roi` as an example but this should be the area
# selected by the user in the UI
roi=ee.Geometry.Polygon(
        [[[-63.42803671537233, -30.42050193711671],
          [-63.42803671537233, -30.339391209687783],
          [-63.34916140311282, -30.339391209687783],
          [-63.34916140311282, -30.339391209687783]]]);
area_of_interest = LongLatBBox.from_ee_geometry(roi)

# The dates T1 and T2, should also be the one selected by the user
days = ["2021-01-01", "2022-12-31"]

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

# Convert the binary mask to a ee.Geometry
# `deforest_rois` is a list of ee.Geometry, each one is a detected area of
# deforestation and should be displayed in the UI
deforest_rois = predictor.get_ee_geometry_from_mask(images[1], deforest_mask)