import ee

def compute_Lk(magnitude, class_t1, class_t2, threshold, roi, scale):
    """
    Compute the Lk metric for a given threshold.
    """
    detected_change = magnitude.gte(ee.Image.constant(threshold))
    true_change = class_t1.neq(class_t2)
    true_no_change = true_change.Not()
    Ak1 = detected_change.And(true_change).reduceRegion(reducer=ee.Reducer.sum(), geometry=roi, scale=scale).values().get(0)
    Ak2 = detected_change.And(true_no_change).reduceRegion(reducer=ee.Reducer.sum(), geometry=roi, scale=scale).values().get(0)
    A = true_change.reduceRegion(reducer=ee.Reducer.sum(), geometry=roi, scale=scale).values().get(0)
    Lk_value = ee.Number(Ak1).subtract(Ak2).multiply(100).divide(A)
    return Lk_value
