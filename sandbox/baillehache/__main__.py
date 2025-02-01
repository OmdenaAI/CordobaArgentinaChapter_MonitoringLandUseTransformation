from PIL import Image

# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Import the CordobaPredictor module
from cordobaPredictor import *

# Create a preprocessor instance
preprocessor = CordobaDataPreprocessor()
# Select the data source
preprocessor.select_source(CordobaDataSource.SENTINEL2)
#preprocessor.select_source(CordobaDataSource.LANDSAT8)
if preprocessor.data_source == CordobaDataSource.LANDSAT8:
    preprocessor.step_search_image = 10
    preprocessor.nb_median_composite = 1

print(f"data source: {preprocessor.data_source}")
print(f"image resolution: {preprocessor.resolution}m/px")

# Create a predictor
predictor = CordobaPredictor()

def test_analyse_period(areas, area_lbls, days):

    # Loop on pair of area of interest and day of interest
    for i_area, area in enumerate(areas):
        print(f"=== {area_lbls[i_area]}")

        # Get the images
        images = preprocessor.get_registered_images(days, area)

        # For each image
        for i_image in range(len(images)):
            print(f"{images[i_image]}")

            # Save the RGB bands to a png file
            rgb = images[i_image].toRGB(gamma=0.66)
            path_rgb = f"./Data/{preprocessor.data_source}_{area_lbls[i_area]}_{images[i_image].date}_rgb.png"
            print(f"save image to {path_rgb}")
            Image.fromarray(rgb).save(path_rgb)

            # Save the NDVI band to a png file
            ndvi = images[i_image].toNDVI()
            path_ndvi = f"./Data/{preprocessor.data_source}_{area_lbls[i_area]}_{images[i_image].date}_ndvi.png"
            print(f"save image to {path_ndvi}")
            Image.fromarray(ndvi).save(path_ndvi)

            # Save the EVI band to a png file
            evi = images[i_image].toEVI()
            path_evi = f"./Data/{preprocessor.data_source}_{area_lbls[i_area]}_{images[i_image].date}_evi.png"
            print(f"save image to {path_evi}")
            Image.fromarray(evi).save(path_evi)

            # Save the NDBI band to a png file
            ndbi = images[i_image].toNDBI()
            path_ndbi = f"./Data/{preprocessor.data_source}_{area_lbls[i_area]}_{images[i_image].date}_ndbi.png"
            print(f"save image to {path_ndbi}")
            Image.fromarray(ndbi).save(path_ndbi)

            # From the second image
            if i_image > 0:
                # If the NDVI index is high enough
                if images[i_image].mean_ndvi > 0.0:

                    # Predict the deforestation relative to the previous image
                    # using PCA/KMeans
                    deforest_image = predictor.predictPcaKMeanClustering(
                        [images[i_image-1], images[i_image]])
                    path_deforest = f"./Data/{preprocessor.data_source}_{area_lbls[i_area]}_{images[i_image].date}_deforest_pca_kmeans.png"
                    print(f"save image to {path_deforest}")
                    Image.fromarray(deforest_image).save(path_deforest)

                    # Predict the deforestation relative to the previous image
                    # using FCCDN
                    deforest_image = predictor.predictFCCDN(
                        [images[i_image-1], images[i_image]])
                    path_deforest = f"./Data/{preprocessor.data_source}_{area_lbls[i_area]}_{images[i_image].date}_deforest_fccdn.png"
                    print(f"save image to {path_deforest}")
                    Image.fromarray(deforest_image).save(path_deforest)

# Areas of interest
area_cordoba_city = LongLatBBox(-64.3, -64.2, -31.4, -31.3)
area_los_medanitos = LongLatBBox(-65.7, -65.6, -31.6, -31.5)
area_calmayo = LongLatBBox(-64.53518510984365, -64.36758169478006, -32.09793491720308, -31.98599080824592)
area_las_penas = LongLatBBox(-64.19504913677835, -63.92899759153784, -30.67255559541076, -30.43974550819874)
area_villa_alpina = LongLatBBox(-64.8501456212574, -64.70773302600543, -32.06252532553296, -31.93373503424498)
all_areas = [area_cordoba_city, area_los_medanitos, area_calmayo, area_las_penas, area_villa_alpina]
all_area_lbls = ["cordoba", "los_medanitos", "calmayo", "las_penas", "villa_alpina"]
areas = [area_calmayo, area_las_penas, area_villa_alpina]
area_lbls = ["calmayo", "las_penas", "villa_alpina"]

# Days of interests
# Recommended time windows:
# Summer Time: 21 Dec - 21 March
# Winter Time: 21 June - 21 Sept
days = ["2019-08-01", "2020-08-01", "2021-08-01"]
#days = ["2023-12-01", "2024-12-01"]

test_analyse_period(areas, area_lbls, days)
