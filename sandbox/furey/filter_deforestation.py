import os
import ee
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def initialize_gee(credentials_path: str) -> None:
    """Initialize Google Earth Engine with service account credentials."""
    credentials = ee.ServiceAccountCredentials(
        '',
        credentials_path
    )
    ee.Initialize(credentials)

def get_tree_coverage(
    lat: float,
    lon: float,
    date: datetime,
    buffer_size: int = 30
) -> Optional[float]:
    """
    Get tree coverage probability for a location at a specific date.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        date (datetime): Date to analyze
        buffer_size (int): Buffer size in meters around the point
        
    Returns:
        Optional[float]: Average tree probability or None if no data available
    """
    # Create point and buffer
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(buffer_size)
    
    # Calculate date range (30 days before and after)
    start_date = date - timedelta(days=30)
    end_date = date + timedelta(days=30)
    
    # Get Dynamic World collection
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
        .filterBounds(area) \
        .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    # Check if we have images
    if dw.size().getInfo() == 0:
        return None
    
    # Get tree probability band and compute mean
    tree_prob = dw.select('trees').mean()
    
    try:
        # Get mean probability for the area
        tree_coverage = tree_prob.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=area,
            scale=10
        ).get('trees').getInfo()
        
        return tree_coverage
    except:
        return None

def filter_deforestation_data(
    input_csv: str,
    output_csv: str,
    year: int = 2023,
    tree_threshold: float = 0.5
) -> None:
    """
    Filter deforestation data based on previous year's tree coverage.
    
    Args:
        input_csv (str): Path to input CSV file
        output_csv (str): Path to output CSV file
        year (int): Current year of deforestation data
        tree_threshold (float): Minimum tree probability threshold
    """
    # Read CSV
    df = pd.read_csv(input_csv)
    print(f"Read {len(df)} records from {input_csv}")
    
    # Check previous year's tree coverage for each point
    results = []
    
    for idx, row in df.iterrows():
        try:
            # Get tree coverage from previous year
            prev_year_date = datetime(year-1, 9, 1)  # September of previous year
            tree_coverage = get_tree_coverage(
                lat=row['centroid_lat'],
                lon=row['centroid_lon'],
                date=prev_year_date
            )
            
            if tree_coverage is not None and tree_coverage >= tree_threshold:
                results.append({
                    **row.to_dict(),
                    'prev_year_tree_coverage': tree_coverage
                })
                
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1} records...")
                
        except Exception as e:
            print(f"Error processing record {idx}: {str(e)}")
            continue
    
    if results:
        # Create new DataFrame and save
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv, index=False)
        print(f"\nSaved {len(results_df)} records to {output_csv}")
        print(f"Filtered out {len(df) - len(results_df)} records with insufficient tree coverage")
    else:
        print("No records met the tree coverage threshold criteria")

def process_multiple_years(
    start_year: int,
    end_year: int,
    input_dir: str,
    output_dir: str,
    tree_threshold: float = 0.5
) -> None:
    """
    Process deforestation data for multiple years.
    
    Args:
        start_year (int): First year to process
        end_year (int): Last year to process
        input_dir (str): Directory containing input CSV files
        output_dir (str): Directory to save filtered CSV files
        tree_threshold (float): Minimum tree probability threshold
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for year in range(start_year, end_year + 1):
        input_csv = os.path.join(input_dir, f'cordoba_{year}.csv')
        output_csv = os.path.join(output_dir, f'cordoba_{year}_filtered.csv')
        
        if os.path.exists(input_csv):
            print(f"\nProcessing year {year}...")
            filter_deforestation_data(
                input_csv=input_csv,
                output_csv=output_csv,
                year=year,
                tree_threshold=tree_threshold
            )
        else:
            print(f"\nSkipping year {year} - file not found: {input_csv}")

if __name__ == "__main__":
    # Get the absolute path to the project root
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Initialize Earth Engine
    GEE_CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'data', 'climatech-426614-3aa74ba1de08.json')
    initialize_gee(GEE_CREDENTIALS_PATH)
    
    # Define directories
    input_dir = os.path.join(PROJECT_ROOT, 'data', 'cordoba_por_anio')
    output_dir = os.path.join(PROJECT_ROOT, 'data', 'cordoba_por_anio_filtered')
    
    # Process all years from 2010 to 2023
    process_multiple_years(
        start_year=2010,
        end_year=2023,
        input_dir=input_dir,
        output_dir=output_dir,
        tree_threshold=0.5
    )
