import ee
import os
import pyproj
import pathlib
import numpy as np

from dotenv import load_dotenv
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

def get_credentials():
    """
    Get the credentials to access Google Earth Engine.
    Returns:
    ee.ServiceAccountCredentials: The credentials to access Google Earth Engine.
    """
    try: 
        # Get the notebook directory
        NOTEBOOK_DIR = os.getcwd()

        # Get the project root directory (two levels up)
        PROJECT_ROOT = os.path.abspath(os.path.join(NOTEBOOK_DIR, '../..'))

        # Load environment variables
        load_dotenv()

        # Get credentials path and ensure it's relative to PROJECT_ROOT
        GEE_CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, os.getenv('GEE_CREDENTIALS_PATH'))
        GEE_PROJECT_ID = os.getenv('GEE_PROJECT_ID')

        # Initialize GEE
        credentials = ee.ServiceAccountCredentials(
            '',
            GEE_CREDENTIALS_PATH,
            GEE_PROJECT_ID
        )
        ee.Initialize(credentials, opt_url="https://earthengine-highvolume.googleapis.com")
        return credentials
    
    except Exception as e:
        print(e)


## Generate a cloud-free composite for a given year and location
def generate_cloudfree_composite(lat: float, 
                                 lon: float, 
                                 start_date: str,
                                 end_date: str, 
                                 clear_threshold: float) -> ee.Image:
    """
    Generate a cloud-free composite for a given year and location.

    Args:
    lat (float): Latitude of the location.
    lon (float): Longitude of the location.
    start_date (str): Start date of the time range. Format: 'YYYY-MM-DD'
    end_date (str): End date of the time range. Format: 'YYYY-MM-DD'
    clear_threshold (float): Threshold to consider a pixel as cloud-free. From 0 to 1.

    Returns:
    ee.Image: The cloud-free composite.
    """

    # Define the collections: Sentinel-2 and Cloud Score+
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

    # Region of interest by coordinates
    roi = ee.Geometry.Point([lon, lat])

    # Define the update mask with cloud-free pixels by threshold
    def apply_cloudscore(img):
        cloud_score = ee.Image(img.get('cloud_score'))
        return img.updateMask(cloud_score.select('cs_cdf').gte(clear_threshold))


    # Filter collections by region and date
    s2_filtered = s2.filterBounds(roi).filterDate(start_date, end_date) \
                  .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
    
    csPlus_filtered = csPlus.filterBounds(roi).filterDate(start_date, end_date)
    print(f"Sentinel-2 available images: {s2_filtered.size().getInfo()}")

    # Join collections and generate the composite
    s2_with_cloud_score = ee.Join.saveFirst('cloud_score').apply(**{
        "primary": s2_filtered,
        "secondary": csPlus_filtered,
        "condition": ee.Filter.equals(**{
            "leftField": 'system:index',
            "rightField": 'system:index'
        })
    })

    # Apply the cloud score mask
    s2_with_cloud_score = ee.ImageCollection(s2_with_cloud_score)
    composite = s2_with_cloud_score.map(apply_cloudscore).median()

    return composite 


## Dwonload the image composite by coordinates, edge size, resolution, and time range
def download_composite(lat: float, 
                       lon: float, 
                       filename: str, 
                       edge_size: int,
                       resolution: int,
                       start_date: str,
                       end_date: str,
                       clear_threshold: float) -> None:

    """
    Download a cloud-free composite for a given year and location in a square area.

    Args:
    lat (float): Latitude of the location.
    lon (float): Longitude of the location.
    composite (float): Cloud-free composite.
    filename (str): Filepath to save the image.
    edge_size (int): Size of the image edge in meters.
    resolution (int): Resolution of the image in meters.
    start_date (str): Start date of the time range. Format: 'YYYY-MM-DD'
    end_date (str): End date of the time range. Format: 'YYYY-MM-DD'
    clear_threshold (float): Threshold to consider a pixel as cloud-free
    """

    # Generate the cloud-free composite
    composite = generate_cloudfree_composite(lat, lon, start_date, end_date, clear_threshold)

    # Get the center coordinates
    utm_crs = query_utm_crs_info(datum_name="WGS84", area_of_interest=AreaOfInterest(lon, lat, lon, lat))
    epsg_code = utm_crs[0].code
    transformer = pyproj.Transformer.from_crs(f'epsg:4326', f'epsg:{epsg_code}', always_xy=True)
    center_x, center_y = transformer.transform(lon, lat)

    # Get the upper left coordinates
    ul_x = center_x - (edge_size * resolution / 2)
    ul_y = center_y + (edge_size * resolution / 2)

    # Define the request
    request = {
        "expression": composite,
        "fileFormat": "GEO_TIFF",
        "bandIds": ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12'],
        "grid": {
            "dimensions": {
                "width": edge_size,
                "height": edge_size
            },
        
        "affineTransform": {
            "scaleX": resolution,
            "shearX": 0,
            "translateX": ul_x,
            "shearY": 0,
            "scaleY": -resolution,        
            "translateY": ul_y  
            },
        "crsCode": f"EPSG:{epsg_code}",
        },    
    }

    # Compute the pixels and save the image
    filename = pathlib.Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the image
    image = ee.data.computePixels(request)
    with open(filename, 'wb') as file:
        file.write(image)
    
    print(f"Image saved in {filename}")    


## Convert the S2 image to RGB
def sentinel_l2a_to_rgb(image: np.ndarray) -> np.ndarray:
    """
    Convert the Sentinel-2 image to RGB (0-255).

    Args:
    image (np.ndarray): Sentinel-2 image composite from Test Data. In the C, H, W dimension order.

    Returns:
    The RGB image in the H, W, C dimension order.
    """
    min_val = 0.0
    max_val = 0.3

    # Get only RGB bands from the image
    # B2: Blue, B3: Green, B4: Red     
    rgb_image = (image[[2,1,0]] / 10000 - min_val) / (max_val - min_val)
    rgb_image[rgb_image < 0] = 0
    rgb_image[rgb_image > 1] = 1

    # Convert to 8-bit
    rgb_image = (rgb_image * 255).astype(np.uint8)
    return rgb_image # C, H, W


## Convert the ground truth image to 0-255
def gt_to_0_255(gt: np.ndarray) -> np.ndarray:
    """
    Convert the ground truth image to 0-255.

    Args:
    gt (np.ndarray): Ground truth image.

    Returns:
    np.ndarray: The ground truth image in 0-255.
    """
    gt_converted = (gt * 255).astype(np.uint8)
    return gt_converted