import ee
from typing import Tuple
from datetime import datetime

# Dynamic World constants
CLASS_NAMES = [
    'water',
    'trees',
    'grass',
    'flooded_vegetation',
    'crops',
    'shrub_and_scrub',
    'built',
    'bare',
    'snow_and_ice',
]

VIS_PALETTE = [
    '419bdf',  # water
    '397d49',  # trees
    '88b053',  # grass
    '7a87c6',  # flooded_vegetation
    'e49635',  # crops
    'dfc35a',  # shrub_and_scrub
    'c4281b',  # built
    'a59b8f',  # bare
    'b39fe1',  # snow_and_ice
]

def get_dynamic_world_visualization(image_date: datetime, lat: float, lon: float) -> Tuple[ee.Image, ee.Image]:
    """
    Get Dynamic World visualization for a specific date and location.
    
    Args:
        image_date (datetime): Date for the image
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        Tuple[ee.Image, ee.Image]: Sentinel-2 image and Dynamic World visualization
    """
    # Use a 30-day range centered on the requested date
    START = ee.Date(image_date.strftime('%Y-%m-%d')).advance(-15, 'day')
    END = ee.Date(image_date.strftime('%Y-%m-%d')).advance(15, 'day')
    
    # Filter collections
    col_filter = ee.Filter.And(
        ee.Filter.bounds(ee.Geometry.Point(lon, lat)),
        ee.Filter.date(START, END),
    )
    
    dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filter(col_filter)
    
    # Check if there are available images
    if dw_col.size().getInfo() == 0:
        raise ValueError(f"No Dynamic World images found between {START.format('YYYY-MM-dd').getInfo()} and {END.format('YYYY-MM-dd').getInfo()}")
    
    s2_col = ee.ImageCollection('COPERNICUS/S2_HARMONIZED').filter(col_filter)
    
    # Link DW and S2 source images
    linked_col = dw_col.linkCollection(s2_col, s2_col.first().bandNames())
    
    # Get example DW image with linked S2 image
    linked_image = ee.Image(linked_col.first())
    
    # Create RGB image of the label
    dw_rgb = (
        linked_image.select('label')
        .visualize(min=0, max=8, palette=VIS_PALETTE)
        .divide(255)
    )
    
    # Get most likely class probability
    top1_prob = linked_image.select(CLASS_NAMES).reduce(ee.Reducer.max())
    
    # Create hillshade
    top1_prob_hillshade = ee.Terrain.hillshade(top1_prob.multiply(100)).divide(255)
    
    # Combine RGB with hillshade
    dw_rgb_hillshade = dw_rgb.multiply(top1_prob_hillshade)
    
    return linked_image, dw_rgb_hillshade