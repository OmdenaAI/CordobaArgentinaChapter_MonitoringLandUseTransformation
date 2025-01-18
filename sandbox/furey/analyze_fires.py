import ee
import geemap
import os
from datetime import datetime
from pathlib import Path

def mask_s2_clouds(image):
    """Masks clouds in a Sentinel-2 image using the QA band.

    Args:
        image (ee.Image): A Sentinel-2 image.

    Returns:
        ee.Image: A cloud-masked Sentinel-2 image.
    """
    qa = image.select('QA60')

    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    # Both flags should be set to zero, indicating clear conditions.
    mask = (
        qa.bitwiseAnd(cloud_bit_mask)
        .eq(0)
        .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    )

    return image.updateMask(mask).divide(10000)

def analyze_fires(
    start_date: str = '2019-01-01',
    end_date: str = '2019-12-31',
    latitude: float = -6.66,
    longitude: float = -55.36,
    zoom: int = 12,
    min_temp: float = 325.0,
    max_temp: float = 400.0
) -> geemap.Map:
    """
    Analyzes and visualizes fires over Brazil using FIRMS dataset and shows Sentinel-2 imagery.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        latitude (float): Center latitude (default: -6.66)
        longitude (float): Center longitude (default: -55.36)
        zoom (int): Zoom level (default: 12)
        min_temp (float): Minimum temperature for visualization
        max_temp (float): Maximum temperature for visualization
    
    Returns:
        geemap.Map: Map with fire visualization layers and Sentinel-2 imagery
    """
    # Create a map centered on specified coordinates
    map_display = geemap.Map(center=[latitude, longitude], zoom=zoom)
    
    # Create a region of interest (ROI) - 50km buffer around the point
    point = ee.Geometry.Point([longitude, latitude])
    roi = point.buffer(50000)  # 50km buffer
    
    # Get FIRMS dataset
    dataset = ee.ImageCollection('FIRMS').filter(
        ee.Filter.date(start_date, end_date)
    ).filter(
        ee.Filter.bounds(roi)
    )
    
    # Select thermal anomalies
    fires = dataset.select('T21')
    
    # Define visualization parameters for fires
    fire_vis_params = {
        'min': min_temp,
        'max': max_temp,
        'palette': ['red', 'orange', 'yellow']
    }
    
    # Add Sentinel-2 imagery for years 2018-2024
    s2_vis_params = {
        'min': 0.0,
        'max': 0.3,
        'bands': ['B4', 'B3', 'B2'],
    }
    
    years = [2017 ,2018, 2019, 2020, 2021, 2022, 2023, 2024]
    for year in years:
        # Skip future years
        if year > datetime.now().year:
            continue
            
        # Get Sentinel-2 imagery for August of each year (dry season)
        s2_dataset = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(f'{year}-08-01', f'{year}-08-31')
            .filterBounds(roi)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .map(mask_s2_clouds)
        )
        
        # Get the mean image for the month
        s2_image = s2_dataset.mean()
        
        # Add the layer to the map
        layer_name = f'Sentinel-2 {year}-08'
        if year == 2018:
            layer_name += ' (Pre-fire)'
        elif year == 2019:
            layer_name += ' (Fire year)'
        else:
            layer_name += ' (Post-fire)'
            
        map_display.addLayer(
            s2_image,
            s2_vis_params,
            layer_name
        )
    
    # Add ROI boundary
    roi_feature = ee.Feature(roi)
    map_display.addLayer(
        ee.FeatureCollection([roi_feature]),
        {'color': 'black', 'fillColor': '00000000'},
        'Region of Interest (50km radius)'
    )

    # Add fire layer to map
    map_display.addLayer(
        fires,
        fire_vis_params,
        f'Fires {start_date} to {end_date}'
    )
    
    return map_display

if __name__ == '__main__':
    # Example usage
    map = analyze_fires(
        start_date='2019-08-01',
        end_date='2019-08-31',
        latitude=-6.66,
        longitude=-55.36,
        zoom=12
    )
    
    # Display the map (when running in Jupyter)
    display(map) 