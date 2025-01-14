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
areas = [area_cordoba_city, area_los_medanitos]
area_lbls = ["cordoba", "los_medanitos"]

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
