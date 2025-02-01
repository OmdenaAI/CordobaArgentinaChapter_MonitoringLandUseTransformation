import ee
import os
import geemap
import pandas as pd
from pathlib import Path
from typing import Union, Tuple
from datetime import datetime, timedelta

def mask_s2_clouds(image: ee.Image) -> ee.Image:
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

def get_sentinel_image(
    lat: float,
    lon: float,
    start_date: str, 
    end_date: str,
    buffer_size: int = 5000,
    cloud_threshold: int = 20,
    date_expansion_days: int = 30,
    composite_method: str = 'median'
) -> Tuple[ee.Image, dict]:
    """
    Obtains a composite Sentinel-2 image for the specified location and date range.

    Args:
        lat (float): Latitude of the center point
        lon (float): Longitude of the center point
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
        buffer_size (int, optional): Size of buffer around point in meters. Defaults to 5000.
        cloud_threshold (int, optional): Maximum cloud coverage percentage. Defaults to 20.
        date_expansion_days (int, optional): Days to expand search if no images found. Defaults to 30.
        composite_method (str, optional): Method to create composite ('median' or 'mean'). Defaults to 'median'.

    Returns:
        Tuple[ee.Image, dict]: Composite image and metadata dictionary containing:
            - 'original_dates': Original date range requested
            - 'actual_dates': Actual date range used
            - 'image_count': Number of images in collection
            - 'cloud_threshold': Cloud threshold used
            - 'composite_method': Method used for composite
            - 'coordinates': Center point coordinates
            - 'buffer_size': Buffer size used in meters

    Raises:
        ValueError: If dates are invalid, coordinates are out of range, or composite_method is not supported
    """
    # Validate coordinates
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError(f"Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180. But got {lat} and {lon}")

    # Create geometry from coordinates
    geometry = ee.Geometry.Point([lon, lat]).buffer(buffer_size)

    # Validate dates
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Dates must be in 'YYYY-MM-DD' format")

    if composite_method not in ['median', 'mean']:
        raise ValueError("composite_method must be either 'median' or 'mean'")

    # Ensure start_date is earlier than end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # If dates are the same, adjust end_date to have a 1-day range
    if start_date == end_date:
        end_date = ee.Date(end_date).advance(1, 'day').format('YYYY-MM-dd').getInfo()

    original_dates = {'start': start_date, 'end': end_date}

    def get_collection(start: str, end: str) -> ee.ImageCollection:
        return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(geometry)
                .filterDate(start, end)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_threshold))
                .map(mask_s2_clouds))

    # Get the initial collection
    s2_collection = get_collection(start_date, end_date)
    collection_size = s2_collection.size().getInfo()

    # If the collection is empty, expand the date range
    if collection_size == 0:
        start_date = ee.Date(start_date).advance(-date_expansion_days, 'day').format('YYYY-MM-dd').getInfo()
        end_date = ee.Date(end_date).advance(date_expansion_days, 'day').format('YYYY-MM-dd').getInfo()
        s2_collection = get_collection(start_date, end_date)
        collection_size = s2_collection.size().getInfo()

        if collection_size == 0:
            raise ValueError(f"No images found even after expanding date range to {start_date} - {end_date}")

    # Create a composite image
    composite = s2_collection.median() if composite_method == 'median' else s2_collection.mean()

    # Prepare metadata
    metadata = {
        'original_dates': original_dates,
        'actual_dates': {'start': start_date, 'end': end_date},
        'image_count': collection_size,
        'cloud_threshold': cloud_threshold,
        'composite_method': composite_method,
        'coordinates': {'lat': lat, 'lon': lon},
        'buffer_size': buffer_size
    }

    return composite, metadata

def analyze_site_monthly(year: int = 2023, site_index: int = 0):
    """
    Analyzes a specific deforestation site with monthly images throughout a complete year.
    
    Args:
        year (int): Base year for analysis
        site_index (int): Index of the site in the CSV (0-based). Default 0 (first site)
    """
    # Get path to CSV
    current_dir = Path().absolute()
    csv_path = (current_dir.parent.parent.parent.parent / 
                'CordobaArgentinaChapter_MonitoringLandUseTransformation' / 
                'data' / 'cordoba_por_anio' / f'cordoba_{year}.csv')

    if not csv_path.exists():
        raise FileNotFoundError(f"File not found at: {csv_path}")

    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Verify index is valid
    if site_index >= len(df):
        raise ValueError(f"Index {site_index} is greater than the number of available sites ({len(df)})")
    
    # Get specific row
    row = df.iloc[site_index]
    
    # Create base map
    map_display = geemap.Map()
    
    # Configure visualization for Sentinel-2
    vis_params = {
        'min': 0.0,
        'max': 0.3,
        'bands': ['B4', 'B3', 'B2'],
    }
    
    try:
        site_name = f"Site {site_index} - {row['DEPARTAM']} ({row['SUPERF_HA']:.2f} ha)"
        print(f"\nProcessing: {site_name}")
        print(f"Coordinates: {row['centroid_lat']}, {row['centroid_lon']}")
        
        # Generate 13 monthly periods
        for month in range(13):
            # Calculate dates for each month
            start_date = datetime(year, 1, 1) + timedelta(days=30*month)
            end_date = start_date + timedelta(days=30)
            
            # Format dates for GEE
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Get image for the period
            image, metadata = get_sentinel_image(
                lat=row['centroid_lat'],
                lon=row['centroid_lon'],
                start_date=start_str,
                end_date=end_str,
                buffer_size=1000,  # 1km buffer
                cloud_threshold=20
            )
            
            # Add layer to map
            layer_name = f"{start_date.strftime('%B %Y')}"
            map_display.addLayer(image, vis_params, layer_name)
            
            print(f"  {layer_name}: {metadata['image_count']} images found")
        
        # Create point for marker
        point = ee.Geometry.Point([row['centroid_lon'], row['centroid_lat']])
        
        # Convert WKT polygon to Earth Engine geometry
        polygon_wkt = row['polygon_geometry_wgs84']
        
        # Extract coordinates from WKT and convert to Earth Engine expected format
        coords_text = polygon_wkt[polygon_wkt.find("((") + 2:polygon_wkt.find("))")]
        coords_pairs = [x.strip().split(" ")[:2] for x in coords_text.split(",")]
        coords_list = [[float(pair[0]), float(pair[1])] for pair in coords_pairs]
        
        # Create polygon with processed coordinates
        polygon = ee.Geometry.Polygon([coords_list])
        
        # Add polygon as layer
        map_display.addLayer(
            polygon,
            {'color': 'red'},  # Polygon style
            f"Site Polygon {site_index}",
            opacity=0.5,
            shown=True
        )
        
        # Add center point marker
        map_display.addLayer(
            point,
            {},
            f"Site Center {site_index}",
            opacity=0.8,
            shown=True
        )
        
    except Exception as e:
        print(f"Error processing site {site_index}: {str(e)}")
        print(f"Site coordinates: lat={row['centroid_lat']}, lon={row['centroid_lon']}")
    
    # Center map on site
    map_display.center_object(
        ee.Geometry.Point([row['centroid_lon'], row['centroid_lat']]), 
        zoom=12
    )
    
    return map_display