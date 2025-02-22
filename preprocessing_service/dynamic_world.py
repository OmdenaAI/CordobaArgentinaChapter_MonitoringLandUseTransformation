import ee

from datetime import datetime, timedelta


def create_composite_DW(roi, date, range_days):
    """
    Create a median composite using the Dynamic World collection.
    """

    start_date = datetime.strptime(date, '%Y-%m-%d')
    end_date = start_date + timedelta(days=range_days)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    dynamic = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')

    # Filter Sentinel-2 and Dynamic World collections.
    s2_filtered = s2.filterBounds(roi).filterDate(start_date_str, end_date_str).filter(
        ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
    class_bands = ['water', 'trees', 'grass', 'flooded_vegetation',
                   'crops', 'shrub_and_scrub', 'built', 'bare', 'snow_and_ice']
    dynamic_filtered = dynamic.filterBounds(roi).filterDate(
        start_date_str, end_date_str).select(class_bands)

    # Merge collections by 'system:index'
    dynamic_merged = ee.Join.saveFirst('dynamic').apply(primary=dynamic_filtered, secondary=s2_filtered,
                                                        condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))
    dynamic_merged = ee.ImageCollection(dynamic_merged)
    return dynamic_merged.median()
