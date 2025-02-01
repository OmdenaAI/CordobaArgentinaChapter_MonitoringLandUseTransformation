import ee
import os
import geemap
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from sentinel_analysis import get_sentinel_image
from land_composition_analysis import get_dynamic_world_visualization

def analyze_site(
    site_index: int = 0,
    start_year: int = 2023,
    end_year: int = 2023,
    period: str = 'monthly',
    images_per_year: int = 12,
    csv_year: int = None
) -> geemap.Map:
    """
    Analyzes a specific deforestation site with images at different time periods.
    
    Args:
        site_index (int): Index of the site in the CSV (0-based). Default 0 (first site)
        start_year (int): Initial year of analysis
        end_year (int): Final year of analysis
        period (str): Analysis period ('yearly', 'biannual', 'quarterly', 'monthly', 'custom')
        images_per_year (int): Number of images per year when period='custom'
        csv_year (int, optional): Year of CSV to use. If not specified, uses start_year
    
    Returns:
        geemap.Map: Map with added image layers
    
    Examples:
        # Yearly analysis (one image per year) for 2018-2023 using 2023 CSV data
        >>> map = analyze_site(
        ...     site_index=0,
        ...     start_year=2018,
        ...     end_year=2023,
        ...     period='yearly',
        ...     csv_year=2023
        ... )
        >>> display(map)  # In Jupyter Notebook
        # Or
        >>> map  # In Jupyter Lab

        # Biannual analysis using default initial year CSV
        >>> map = analyze_site(
        ...     site_index=0,
        ...     start_year=2023,
        ...     end_year=2023,
        ...     period='biannual'
        ... )
        >>> display(map)  # Show the map

        # Quarterly analysis (four images per year) for 2022-2023
        >>> map = analyze_site(
        ...     site_index=0,
        ...     start_year=2022,
        ...     end_year=2023,
        ...     period='quarterly'
        ... )

        # Monthly analysis (twelve images per year) for 2023
        >>> map = analyze_site(
        ...     site_index=0,
        ...     start_year=2023,
        ...     end_year=2023,
        ...     period='monthly'
        ... )

        # Custom analysis (6 images per year) for 2021-2023
        >>> map = analyze_site(
        ...     site_index=0,
        ...     start_year=2021,
        ...     end_year=2023,
        ...     period='custom',
        ...     images_per_year=6
        ... )
    """
    # Validate parameters
    if end_year < start_year:
        raise ValueError("End year must be greater than or equal to start year")
    
    # Configure periods according to the period parameter
    period_configs = {
        'yearly': 1,      # 1 image per year
        'biannual': 2,    # 2 images per year
        'quarterly': 4,   # 4 images per year
        'monthly': 12,    # 12 images per year
        'custom': images_per_year
    }
    
    if period not in period_configs:
        raise ValueError(f"Invalid period. Options: {', '.join(period_configs.keys())}")
    
    images_per_year = period_configs[period]
    days_between_images = 365 // images_per_year

    if csv_year is None:
        csv_year = start_year
    
    # Get path to CSV
    current_dir = Path().absolute()
    csv_path = (current_dir.parent.parent /  # Only go up two levels to reach root
                'data' / 'cordoba_por_anio_filtered' / f'cordoba_{csv_year}_filtered.csv')

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
        print(f"\nProcessing: {row['DEPARTAM']} ({row['SUPERF_HA']:.2f} ha)")
        print(f"Coordinates: {row['centroid_lat']}, {row['centroid_lon']}")
        print(f"Period: {period} ({images_per_year} images per year)")
        print(f"Year range: {start_year}-{end_year}")
        
        # Iterate over years
        for year in range(start_year, end_year + 1):
            # Iterate over periods within the year
            for period_index in range(images_per_year):
                # Calculate dates for each period
                start_date = datetime(year, 1, 1) + timedelta(days=days_between_images * period_index)
                end_date = start_date + timedelta(days=days_between_images)
                
                # Format dates for GEE
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')
                
                # Get image for the period
                image, metadata = get_sentinel_image(
                    lat=row['centroid_lat'],
                    lon=row['centroid_lon'],
                    start_date=start_str,
                    end_date=end_str,
                    # buffer_size=1000,  # 1km buffer
                    cloud_threshold=20
                )
                
                # Add layer to map
                if period == 'yearly':
                    layer_name = f"{year}"
                else:
                    layer_name = f"{start_date.strftime('%B %Y')}"
                map_display.addLayer(image, vis_params, layer_name)
                
                # Get and add Dynamic World layer
                try:
                    s2_image, dw_vis = get_dynamic_world_visualization(
                        start_date,
                        row['centroid_lat'],
                        row['centroid_lon']
                    )
                    
                    # Add Dynamic World layers
                    map_display.addLayer(
                        dw_vis,
                        {'min': 0, 'max': 0.65},
                        f"{layer_name} - Land Cover",
                        False  # Initially hidden
                    )
                except Exception as e:
                    print(f"  Error processing Dynamic World for {layer_name}: {str(e)}")
                
                print(f"  {layer_name}: {metadata['image_count']} images found")
        
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
        
        # Center map on site
        map_display.center_object(
            ee.Geometry.Point([row['centroid_lon'], row['centroid_lat']]), 
            zoom=14
        )
        
        return map_display
        
    except Exception as e:
        print(f"Error processing site {site_index}: {str(e)}")
        print(f"Site coordinates: lat={row['centroid_lat']}, lon={row['centroid_lon']}")
        return None