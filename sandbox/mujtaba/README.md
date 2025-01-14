# Deforestation Analysis using Non-Deep Learning Methods

This code performs deforestation analysis using satellite imagery through traditional machine learning approaches. It analyzes changes in vegetation between two time periods using NDVI (Normalized Difference Vegetation Index) and applies dimensionality reduction (PCA) and clustering (K-means) to identify patterns of change.

## Features

- NDVI calculation from satellite imagery
- Change detection between two time periods
- Principal Component Analysis (PCA) for feature reduction
- K-means clustering for change pattern identification
- Visualization of results with matplotlib

## Requirements

```
numpy
matplotlib
pillow (PIL)
scikit-learn
```

## Input Data

The code expects two satellite images:
- `before.tif`: Satellite image from the earlier time period
- `after.tif`: Satellite image from the later time period

Images should be in GeoTIFF format with RGB bands.

## Output

The code generates several visualizations:
1. NDVI maps for both time periods
2. NDVI difference map
3. PCA components visualization
4. K-means clustering results

Output files:
- `analysis_results.png`: Combined visualization of all analysis steps
- `kmeans_clustered_diff.png`: Final clustering results showing change patterns

## Usage

1. Place your satellite images in the correct directory
2. Run the script:
```bash
python Non_deep_learning.py
```

## Analysis Components

1. **NDVI Calculation**
   - Uses red and near-infrared bands to calculate vegetation index
   - Values range from -1 to 1, where higher values indicate denser vegetation

2. **Change Detection**
   - Calculates difference in NDVI between two time periods
   - Identifies areas of vegetation loss and gain

3. **PCA Analysis**
   - Reduces dimensionality of the data
   - Helps identify major patterns of change

4. **K-means Clustering**
   - Groups similar patterns of change
   - Uses 3 clusters to categorize: stable, loss, and gain of vegetation

## Visualization Guide

- **NDVI Maps**: Red-Yellow-Green colormap where:
  - Green: High vegetation density
  - Yellow: Moderate vegetation
  - Red: Low vegetation/bare soil

- **Difference Map**: Shows changes where:
  - Positive values (green): Vegetation increase
  - Negative values (red): Vegetation loss

- **Clustering Results**: Different colors represent different change patterns

## Notes

- The code uses a simplified NDVI calculation using RGB bands
- For more accurate results, use proper multispectral imagery with NIR bands
- Adjust the number of clusters in K-means based on your specific needs 