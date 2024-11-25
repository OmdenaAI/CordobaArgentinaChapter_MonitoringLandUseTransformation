from typing import Dict, Any
import ee
import os
from datetime import datetime

def test_gee_connection() -> Dict[str, Any]:
    """Test connection to Google Earth Engine.
    
    Returns:
        Dict with test results
    """
    try:
        ee.Initialize()
        
        # Get a test image collection
        collection = ee.ImageCollection('COPERNICUS/S2_SR')
        
        # Try a simple filter
        test_img = collection.filterDate(
            datetime(2023, 1, 1), 
            datetime(2023, 1, 2)
        ).first()
        
        return {
            "status": "success",
            "message": "Successfully connected to GEE",
            "test_image_id": test_img.id().getInfo()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect: {str(e)}"
        }

if __name__ == "__main__":
    result = test_gee_connection()
    print(f"Test result: {result}") 