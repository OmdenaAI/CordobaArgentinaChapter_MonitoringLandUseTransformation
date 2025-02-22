import ee

from datetime import datetime, timedelta


def create_composite_S2(roi, date, range_days, clear_threshold=0.6):
    """
    Create a cloud-masked Sentinel-2 composite image.
    """
    start_date = datetime.strptime(date, '%Y-%m-%d')
    end_date = start_date + timedelta(days=range_days)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

    def apply_cloudscore(img):
        cloud_score = ee.Image(img.get('cloud_score'))
        return img.updateMask(cloud_score.select('cs_cdf').gte(clear_threshold))

    BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
    s2_filtered = s2.filterBounds(roi).filterDate(start_date_str, end_date_str).filter(
        ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60)).select(BANDS)
    csPlus_filtered = csPlus.filterBounds(
        roi).filterDate(start_date_str, end_date_str)

    s2_with_cloud_score = ee.Join.saveFirst('cloud_score').apply(
        primary=s2_filtered, secondary=csPlus_filtered, condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))
    s2_with_cloud_score = ee.ImageCollection(s2_with_cloud_score)
    return s2_with_cloud_score.map(apply_cloudscore).median()
