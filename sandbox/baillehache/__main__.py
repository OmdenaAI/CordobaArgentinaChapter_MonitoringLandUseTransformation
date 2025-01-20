from PIL import Image

# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Create a preprocessor instance
preprocessor = CordobaDataPreprocessor()
# Eventually set the resolution of the images with:
#preprocessor.resolution = 10.0

print(f"data source: {preprocessor.data_source}")
print(f"image resolution: {preprocessor.resolution}m/px")

# Areas of interest
area_cordoba_city = LongLatBBox(-64.3, -64.2, -31.4, -31.3)
area_los_medanitos = LongLatBBox(-65.7, -65.6, -31.6, -31.5)
area_calmayo = LongLatBBox(-64.53518510984365, -64.36758169478006, -32.09793491720308, -31.98599080824592)
area_las_penas = LongLatBBox(-64.19504913677835, -63.92899759153784, -30.67255559541076, -30.43974550819874)
area_villa_alpina = LongLatBBox(-64.8501456212574, -64.70773302600543, -32.06252532553296, -31.93373503424498)
areas = [area_cordoba_city, area_los_medanitos, area_calmayo, area_las_penas, area_villa_alpina]
area_lbls = ["cordoba", "los_medanitos", "calmayo", "las_penas", "villa_alpina"]

# Days of interests
day_1 = "2023-12-01"
day_2 = "2024-12-01"
days = [day_1, day_2]

# Loop on pair of area of interest and day of interest
for i_area, area in enumerate(areas):
    for day in days:

        # Get the image
        image = preprocessor.get_image(day, area)
        print(f"downloaded {image}")

        # Save the RGB bands to a png file
        rgb = image.toRGB()
        path_rgb = f"./Data/{area_lbls[i_area]}_{day}_rgb.png"
        print(f"save image to {path_rgb}")
        Image.fromarray(rgb).save(path_rgb)

        # Save the NDVI band to a png file
        ndvi = image.toNDVI()
        path_ndvi = f"./Data/{area_lbls[i_area]}_{day}_ndvi.png"
        print(f"save image to {path_ndvi}")
        Image.fromarray(ndvi).save(path_ndvi)
