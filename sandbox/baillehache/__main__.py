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


def test_analyse_period(areas, area_lbls, days):

    # Select the data source
    preprocessor.data_source = CordobaDataSource.AUTO
    #preprocessor.max_cloud_coverage = 50.0
    #preprocessor.flag_cloud_filtering = True
    print(f"image resolution: {preprocessor.resolution}m/px")

    # Create a predictor
    predictor = CordobaPredictor()

    # Loop on areas of interest
    for i_area, area in enumerate(areas):
        print(f"=== {area_lbls[i_area]}")

        # Get the images
        images = preprocessor.get_satellite_data(days, area)

        # For each image
        for i_image in range(len(images)):
            print(f"{images[i_image]}")

            # Save the RGB bands to a png file
            rgb = images[i_image].to_rgb(gamma=0.66)
            path_rgb = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_rgb.png"
            print(f"save image to {path_rgb}")
            Image.fromarray(rgb).save(path_rgb)

            # Save the NDVI band to a png file
            ndvi = images[i_image].to_ndvi()
            path_ndvi = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_ndvi.png"
            print(f"save image to {path_ndvi}")
            Image.fromarray(ndvi).save(path_ndvi)

            # Save the EVI band to a png file
            evi = images[i_image].to_evi()
            path_evi = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_evi.png"
            print(f"save image to {path_evi}")
            Image.fromarray(evi).save(path_evi)

            # Save the NDBI band to a png file
            ndbi = images[i_image].to_ndbi()
            path_ndbi = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_ndbi.png"
            print(f"save image to {path_ndbi}")
            Image.fromarray(ndbi).save(path_ndbi)

            # Save the NDMI band to a png file
            ndmi = images[i_image].to_ndmi()
            path_ndmi = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_ndmi.png"
            print(f"save image to {path_ndmi}")
            Image.fromarray(ndmi).save(path_ndmi)

            # From the second image
            if i_image > 0:

                # If the NDVI index is high enough (i.e. the image contains
                # vegetation)
                if images[i_image].mean_ndvi > 0.0:

                    # Predict the deforestation relative to the previous image
                    # using PCA/KMeans
                    deforest_image = predictor.predictPcaKMeanClustering(
                        [images[i_image-1], images[i_image]])
                    path_deforest = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_deforest_pca_kmeans.png"
                    print(f"save image to {path_deforest}")
                    Image.fromarray(deforest_image).save(path_deforest)

                    # Predict the deforestation relative to the previous image
                    # using FCCDN
                    """
                    deforest_image = predictor.predictFCCDN(
                        [images[i_image-1], images[i_image]])
                    path_deforest = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_deforest_fccdn.png"
                    print(f"save image to {path_deforest}")
                    Image.fromarray(deforest_image).save(path_deforest)
                    """


def test_search_period(areas, area_lbls, days, min_interval):

    # Select the data source
    preprocessor.data_source = CordobaDataSource.AUTO

    # Loop on areas of interest
    for i_area, area in enumerate(areas):
        print(f"=== {area_lbls[i_area]}")

        # Search the best dates
        dates = preprocessor.get_best_acquisition_dates(days[0], days[1], area, min_interval)
        print(f"{dates}")


def test_dynamic_world(areas, area_lbls, days):

    # Select the data source
    preprocessor.data_source = CordobaDataSource.DYNAMIC_WORLD

    # Loop on areas of interest
    for i_area, area in enumerate(areas):
        print(f"=== {area_lbls[i_area]}")

        # Get the images
        images = preprocessor.get_satellite_data(days, area)

        # For each image
        for i_image in range(len(images)):
            print(f"{images[i_image]}")

            # Save the mask for forest to a png file
            rgb = images[i_image].to_dynamic_world_mask("trees")
            path_trees = f"./Data/{images[i_image].source}_{area_lbls[i_area]}_{images[i_image].date}_trees.png"
            print(f"save image to {path_trees}")
            Image.fromarray(rgb).save(path_trees)

# Areas of interest
area_cordoba_city = LongLatBBox(-64.3, -64.2, -31.4, -31.3)
area_los_medanitos = LongLatBBox(-65.7, -65.6, -31.6, -31.5)
area_calmayo = LongLatBBox(-64.53518510984365, -64.36758169478006, -32.09793491720308, -31.98599080824592)
area_las_penas = LongLatBBox(-64.19504913677835, -63.92899759153784, -30.67255559541076, -30.43974550819874)
area_villa_alpina = LongLatBBox(-64.8501456212574, -64.70773302600543, -32.06252532553296, -31.93373503424498)
area_peru_deforest_01 = LongLatBBox(-75.085, -75.035, -8.295, -8.245)
area_chaco_deforest_01 = LongLatBBox(-61.15,-61.051,-21.8,-21.701)
area_chaco_deforest_02 = LongLatBBox(-62.28,-62.15,-21.8,-21.7)
area_chaco_deforest_03 = LongLatBBox(-62.30,-62.11,-21.84,-21.65)
all_areas = [area_cordoba_city, area_los_medanitos, area_calmayo, area_las_penas, area_villa_alpina, area_peru_deforest_01, area_chaco_deforest_01, area_chaco_deforest_02]
all_area_lbls = ["cordoba", "los_medanitos", "calmayo", "las_penas", "villa_alpina", "peru_deforest_01", "chaco_deforest_01", "chaco_deforest_02", "chaco_deforest_03"]

# Days of interests
# Recommended time windows:
# Summer Time: 21 Dec - 21 March
# Winter Time: 21 June - 21 Sept
#days = ["2019-08-01", "2020-08-01", "2021-08-01"]
days = ["2014-12-01", "2024-12-01"]
days_peru_deforest_01 = ["2015-08-04", "2015-09-10"]
days_chaco_deforest_01 = ["2018-01-24", "2019-12-24"]
days_chaco_deforest_02 = ["2019-01-24", "2019-12-24"]
days_chaco_deforest_03 = ["2019-01-24", "2019-12-24"]

areas = [area_chaco_deforest_01]
area_lbls = ["chaco_deforest_01"]
period_of_interest = days_chaco_deforest_01
min_interval = 90
preprocessor.nb_max_step_search = 1
preprocessor.step_search_image = min_interval / 4
preprocessor.max_cloud_coverage = 25.0
#dates_of_interest = preprocessor.get_best_acquisition_dates(period_of_interest[0], period_of_interest[1], areas[0], min_interval)
dates_of_interest = days_chaco_deforest_01
test_analyse_period(areas, area_lbls, dates_of_interest)

#dates_of_interest = days_chaco_deforest_01
#test_dynamic_world(areas, area_lbls, dates_of_interest)
