from PIL import Image

# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Import the CordobaPredictor module
from cordobaPredictor import *

# Login info to GEE
gee_account = "cordoba@ee-baillehachepascal.iam.gserviceaccount.com"
gee_credentials_path = "../../../earthengine_api_key.json"

# Create a preprocessor instance
preprocessor = \
    CordobaDataPreprocessor(gee_account, gee_credentials_path, online=True)

roi=ee.Geometry.Polygon(
        [[[-63.42803671537233, -30.42050193711671],
          [-63.42803671537233, -30.339391209687783],
          [-63.34916140311282, -30.339391209687783],
          [-63.34916140311282, -30.339391209687783]]]);
area_jair_01 = LongLatBBox.from_ee_geometry(roi)
days_jair_01 = ["2021-01-01", "2022-12-31"]
area_jair_02 = LongLatBBox(-63.02341479977622,-62.940716720052535,-29.87713676641895,-29.800596170529722)
days_jair_02 = ["2021-01-01", "2022-12-31"]
area_jair_03 = LongLatBBox(-64.81480548517165,-64.68969201848563,-32.50300566653878,-32.43805824301178)
days_jair_03 = ["2020-03-01", "2021-06-01"]
area_jair_04 = LongLatBBox(-65.61138831755882,-65.53888985559803,-31.99645556588706,-31.89978610318753)
days_jair_04 = ["2022-06-01", "2023-06-01"]
area_jair_05 = LongLatBBox(-65.50593631546242,-65.4372014448094,-30.76559346086256,-30.701248739138492)
days_jair_05 = ["2022-06-01", "2023-06-01"]
area_jair_06 = LongLatBBox(-63.59617395125423,-63.564204443287736,-30.096382481502957,-30.049102375439773)
days_jair_06 = ["2022-06-01", "2023-06-01"]
area_jair_07 = LongLatBBox(-65.10065502652814,-65.04464262987477,-31.704045563926357,-31.66390090800001)
days_jair_07 = ["2019-01-01", "2020-01-01"]
areas = [area_jair_01, area_jair_02, area_jair_03, area_jair_04, area_jair_05, area_jair_06, area_jair_07]
area_lbls = ["jair_01", "jair_02", "jair_03", "jair_04", "jair_05", "jair_06", "jair_07"]
days = [days_jair_01, days_jair_02, days_jair_03, days_jair_04, days_jair_05, days_jair_06, days_jair_07]

areas = [area_jair_01]
area_lbls = ["jair_01"]
days = [days_jair_01]

# Create a predictor
predictor = CordobaPredictor()

# Loop on areas of interest
for i_area, area in enumerate(areas):
    print(f"=== {area_lbls[i_area]}")

    # Default is 35, Jair uses 60
    #preprocessor.max_cloud_coverage = 60

    # Get the satellite images
    preprocessor.nb_max_step_search = 1
    preprocessor.step_search_image = 30
    preprocessor.data_source = CordobaDataSource.SENTINEL2
    images = preprocessor.get_satellite_data(days[i_area], area)

    # Threhsold confidence for the "trees" mask
    threshold_mask = 0.5

    # For each image
    for i_image in range(len(images)):
        print(f"{images[i_image]}")

        # Save the RGB bands to a png file
        rgb = images[i_image].to_rgb(gamma=0.66)
        path_rgb = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_rgb.png"
        print(f"save image to {path_rgb}")
        Image.fromarray(rgb).save(path_rgb)

        # Save the 'trees' mask to a png file
        threshold = [threshold_mask, 0.0][i_image]
        tree_mask = (images[i_image].to_dynamic_world_mask("trees", threshold)*255.0).astype(numpy.uint8)
        path_tree_mask = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_tree_mask.png"
        print(f"save image to {path_tree_mask}")
        Image.fromarray(tree_mask).save(path_tree_mask)

        # From the second image
        if i_image > 0:

            # Predict the deforestation relative to the previous image
            # using dynamic world only
            deforest_mask = predictor.predict_dynamic_world(
                [images[i_image-1], images[i_image]],
                "trees", threshold_mask)
            img = Image.fromarray((deforest_mask*255.0).astype(numpy.uint8))
            path_deforest = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_deforest_dw.png"
            print(f"save image to {path_deforest}")
            img.save(path_deforest)
            
            # Convert to ee.Geometry
            rois = predictor.get_ee_geometry_from_mask(images[i_image], deforest_mask)
            for roi in rois:
                print(f"{roi.getInfo()}")
