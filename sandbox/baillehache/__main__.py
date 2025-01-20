from PIL import Image

# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Create a preprocessor instance
preprocessor = CordobaDataPreprocessor()
# Select the data source
preprocessor.select_source(CordobaDataSource.SENTINEL2)
#preprocessor.max_cloud_coverage = 100.0

print(f"data source: {preprocessor.data_source}")
print(f"image resolution: {preprocessor.resolution}m/px")

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
day_1 = "2019-08-01"
day_2 = "2023-08-01"
days = [day_1, day_2]

# Loop on pair of area of interest and day of interest
for i_area, area in enumerate(areas):
    print(f"=== {area_lbls[i_area]}")

    # Get the images
    images = preprocessor.get_registered_images(days, area)
    print(f"downloaded:\n{images[0]}\n{images[1]}\n")

    # For each image
    for i_image in range(2):

        # Save the RGB bands to a png file
        rgb = images[i_image].toRGB(gamma=0.66)
        path_rgb = f"./Data/{area_lbls[i_area]}_{days[i_image]}_rgb.png"
        print(f"save image to {path_rgb}")
        Image.fromarray(rgb).save(path_rgb)

        # Save the NDVI band to a png file
        ndvi = images[i_image].toNDVI()
        path_ndvi = f"./Data/{area_lbls[i_area]}_{days[i_image]}_ndvi.png"
        print(f"save image to {path_ndvi}")
        Image.fromarray(ndvi).save(path_ndvi)

        # Save the EVI band to a png file
        evi = images[i_image].toEVI()
        path_evi = f"./Data/{area_lbls[i_area]}_{days[i_image]}_evi.png"
        print(f"save image to {path_evi}")
        Image.fromarray(evi).save(path_evi)
