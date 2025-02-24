import ee
from datetime import datetime, timedelta

def create_composite_DW(date: str, range_days: int, roi: ee.Geometry.Polygon) -> ee.Image:
    """
    Create a composite image from the Dynamic World collection.
    
    This function retrieves Sentinel-2 and Dynamic World images for a specified date range 
    and region of interest (ROI), filters out cloudy images, joins the two collections using 
    the 'system:index' property, and computes a median composite from the merged collection.
    
    Args:
      date (str): The start date for filtering images in 'YYYY-MM-DD' format.
      range_days (int): The number of days from the start date to include in the filter.
      roi (ee.Geometry.Polygon): The region of interest as an Earth Engine polygon.
    
    Returns:
      ee.Image: A composite image computed as the median of merged Dynamic World images.
    """
    # Convert the input date to a datetime object and compute the end date.
    start_date = datetime.strptime(date, '%Y-%m-%d')
    end_date = start_date + timedelta(days=range_days)
    
    # Format the start and end dates as strings.
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Define the Sentinel-2 and Dynamic World image collections.
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    dynamic = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
    
    # Filter the Sentinel-2 collection by ROI, date range, and cloud percentage.
    s2_filtered = s2.filterBounds(roi).filterDate(start_date_str, end_date_str) \
                    .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
    
    # Define the class bands used in the Dynamic World collection.
    class_bands = [
        'water', 'trees', 'grass', 'flooded_vegetation', 'crops',
        'shrub_and_scrub', 'built', 'bare', 'snow_and_ice'
    ]
    
    # Filter the Dynamic World collection by ROI and date range, selecting only the class bands.
    dynamic_filtered = dynamic.filterBounds(roi).filterDate(start_date_str, end_date_str) \
                              .select(class_bands)
    
    print(f"Dynamic World available images: {dynamic_filtered.size().getInfo()}")
    
    # Join the Dynamic World collection with the Sentinel-2 collection using 'system:index'.
    dynamic_merged = ee.Join.saveFirst('dynamic').apply(
        primary=dynamic_filtered,
        secondary=s2_filtered,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index')
    )
    
    # Convert the joined results to an ImageCollection and compute the median composite.
    dynamic_merged = ee.ImageCollection(dynamic_merged)
    composite = dynamic_merged.median()
    
    return composite  


def create_composite_S2(date: str, range_days: int, roi: ee.Geometry.Polygon, clear_threshold: float = 0.6) -> ee.Image:
    """
    Create a composite Sentinel-2 image using cloud masking.
    
    This function retrieves Sentinel-2 images and corresponding Cloud Score Plus images for a specified 
    date range and ROI. It applies a cloud mask based on a clear pixel threshold and computes the median 
    composite from the cloud-masked images.
    
    Args:
      date (str): The start date for filtering images in 'YYYY-MM-DD' format.
      range_days (int): The number of days from the start date to include in the filter.
      roi (ee.Geometry.Polygon): The region of interest as an Earth Engine polygon.
      clear_threshold (float): The threshold value to consider a pixel as cloud-free (default is 0.6).
    
    Returns:
      ee.Image: A composite Sentinel-2 image computed from cloud-masked images.
    """
    # Define the Sentinel-2 and Cloud Score Plus image collections.
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
    
    # Define a function to apply the cloud score mask to an image.
    def apply_cloudscore(img):
        # Retrieve the cloud score image from the image's properties.
        cloud_score = ee.Image(img.get('cloud_score'))
        # Update the image mask using the cloud score's 'cs_cdf' band and the clear threshold.
        return img.updateMask(cloud_score.select('cs_cdf').gte(clear_threshold))
    
    # Convert the input date to a datetime object and compute the end date.
    start_date = datetime.strptime(date, '%Y-%m-%d')
    end_date = start_date + timedelta(days=range_days)
    
    # Format the start and end dates as strings.
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Define the Sentinel-2 bands to be used.
    BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
    
    # Filter the Sentinel-2 collection by ROI, date range, and cloudiness; select the specified bands.
    s2_filtered = s2.filterBounds(roi).filterDate(start_date_str, end_date_str) \
                    .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60)) \
                    .select(BANDS)
    
    # Filter the Cloud Score Plus collection by ROI and date range.
    csPlus_filtered = csPlus.filterBounds(roi).filterDate(start_date_str, end_date_str)
    print(f"Sentinel-2 available images: {s2_filtered.size().getInfo()}")
    
    # Join the Sentinel-2 collection with the Cloud Score Plus collection using 'system:index'.
    s2_with_cloud_score = ee.Join.saveFirst('cloud_score').apply(
        primary=s2_filtered,
        secondary=csPlus_filtered,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index')
    )
    
    # Convert the joined collection to an ImageCollection.
    s2_with_cloud_score = ee.ImageCollection(s2_with_cloud_score)
    
    # Apply the cloud score mask to each image and compute the median composite.
    composite = s2_with_cloud_score.map(apply_cloudscore).median()
    return composite


def threshold_optimization(magnitude, class_t1, class_t2, roi, scale, 
                           step_coarse=0.1, step_fine=0.01, tolerance=1e-3, max_iterations=10):
    """
    Optimize the change detection threshold to maximize the Lk metric.
    
    This function iteratively searches for the optimal threshold value that maximizes Lk.
    It performs a coarse search over the range of magnitude values followed by a fine search 
    around the best threshold found during the coarse search. The process is repeated until
    no significant improvement (greater than the tolerance) is observed or the maximum number 
    of iterations is reached.
    
    Args:
      magnitude (ee.Image): Image representing the magnitude of change.
      class_t1 (ee.Image): Image representing the class labels at time t1.
      class_t2 (ee.Image): Image representing the class labels at time t2.
      roi (ee.Geometry): Region of interest over which the computation is performed.
      scale (int): Spatial resolution (in meters) for the reduction.
      step_coarse (float): Step size for the coarse search. Default is 0.1.
      step_fine (float): Step size for the fine search. Default is 0.01.
      tolerance (float): Minimum improvement in Lk required to update the threshold. Default is 1e-3.
      max_iterations (int): Maximum number of iterations for the optimization. Default is 10.
      
    Returns:
      tuple: A tuple (best_threshold, best_Lk) where:
             - best_threshold (float) is the optimal threshold value found.
             - best_Lk (float) is the corresponding Lk metric value.
    """
    # Get the minimum and maximum magnitude values over the ROI
    vmin = magnitude.reduceRegion(ee.Reducer.min(), roi, scale).values().get(0).getInfo()
    vmax = magnitude.reduceRegion(ee.Reducer.max(), roi, scale).values().get(0).getInfo()
    
    # Initialize the best threshold and best Lk value
    best_threshold = vmin
    best_Lk = -9999.0
    
    iteration = 0
    improved = True
    
    # Iteratively search for an improved threshold
    while iteration < max_iterations and improved:
        iteration += 1
        improved = False
        
        # Coarse search: create a list of candidate thresholds from vmin to vmax with step_coarse increments
        coarse_candidates = ee.List.sequence(vmin, vmax, step_coarse)
        local_best_thr = best_threshold
        local_best_Lk = best_Lk
        
        # Function to evaluate each candidate threshold in the coarse search.
        # It returns a list [Lk_current, T] if Lk_current is greater than the current local best,
        # otherwise it returns the current best values.
        def coarse_step(T):
            Lk_current = compute_Lk(magnitude, class_t1, class_t2, T, roi, scale)
            return ee.Algorithms.If(Lk_current.gt(local_best_Lk), [Lk_current, T],
                                    [local_best_Lk, local_best_thr])
        
        # Map the coarse search function over all candidate thresholds and get the results
        coarse_results = coarse_candidates.map(coarse_step)
        coarse_results = ee.List(coarse_results).getInfo()
        # Extract the best Lk and corresponding threshold from coarse search results
        local_best_Lk, local_best_thr = max(coarse_results)
        
        # If the improvement is significant, update the best values
        if local_best_Lk - best_Lk > tolerance:
            best_Lk = local_best_Lk
            best_threshold = local_best_thr
            improved = True
        
        # Define bounds for the fine search around the current best threshold
        low_bound = max(best_threshold - step_coarse, vmin)
        high_bound = min(best_threshold + step_coarse, vmax)
        
        # Fine search: create a list of candidate thresholds within the fine search bounds
        fine_candidates = ee.List.sequence(low_bound, high_bound, step_fine)
        
        # Function to evaluate each candidate threshold in the fine search.
        def fine_step(T):
            Lk_current = compute_Lk(magnitude, class_t1, class_t2, T, roi, scale)
            return ee.Algorithms.If(Lk_current.gt(local_best_Lk), [Lk_current, T],
                                    [local_best_Lk, local_best_thr])
        
        # Map the fine search function over all fine candidates and get the results
        fine_results = fine_candidates.map(fine_step)
        fine_results = ee.List(fine_results).getInfo()
        local_best_Lk, local_best_thr = max(fine_results)
        
        # Update best values if the fine search yields an improvement greater than the tolerance
        if local_best_Lk - best_Lk > tolerance:
            best_Lk = local_best_Lk
            best_threshold = local_best_thr
            improved = True
    
    return best_threshold, best_Lk


def compute_Lk(magnitude, class_t1, class_t2, threshold, roi, scale):
    """
    Compute the Lk metric to evaluate the performance of a change detection threshold.
    
    The metric is defined as:
    
        Lk = ((Ak1 - Ak2) * 100) / A
        
    where:
      - Ak1: Number of pixels that truly changed (class_t1 != class_t2) and were detected as changed 
      (magnitude >= threshold).
      - Ak2: Number of pixels that did not change (class_t1 == class_t2) but were falsely detected 
      as changed.
      - A: Total number of pixels that truly changed.
      
    Args:
      magnitude (ee.Image): Image representing the magnitude of change.
      class_t1 (ee.Image): Image representing the class labels at time t1.
      class_t2 (ee.Image): Image representing the class labels at time t2.
      threshold (float): Threshold value to determine if a pixel is considered changed.
      roi (ee.Geometry): Region of interest over which the computation is performed.
      scale (int): Spatial resolution (in meters) for the reduction.
      
    Returns:
      ee.Number: The computed Lk value (as an Earth Engine Number).
    """
    # Create a binary image where pixels with magnitude greater than or equal to threshold are 1 (changed)
    detected_change = magnitude.gte(ee.Image.constant(threshold))
    
    # Create a binary image where pixels with different classes between t1 and t2 are 1 (true change)
    true_change = class_t1.neq(class_t2)
    
    # Create a binary image where pixels with the same class are 1 (no true change)
    true_no_change = true_change.Not()
    
    # Ak1: Pixels that truly changed and were detected as changed
    Ak1 = detected_change.And(true_change).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=scale
    ).values().get(0)
    
    # Ak2: Pixels that did not change but were detected as changed
    Ak2 = detected_change.And(true_no_change).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=scale
    ).values().get(0)
    
    # A: Total number of pixels that truly changed
    A = true_change.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=scale
    ).values().get(0)
    
    # Compute the Lk value: ((Ak1 - Ak2) * 100) / A
    Lk_value = ee.Number(Ak1).subtract(Ak2).multiply(100).divide(A)
    
    return Lk_value

def change_type_discrimination(prob_t1, prob_t2, changed_mask, n_classes):
    """
    Compute the change type (class transition) for each pixel that changed.
    
    For each pixel with change (changed_mask == 1), this function calculates the change vector:
      δ = prob_t2 - prob_t1
    and then computes the cosine similarity between δ and the theoretical transition vector 
      (P[b] - P[a])
    for each candidate transition (a, b) with a != b, where P[i] is the one-hot vector for class i.
    
    The cosine is computed as:
      cos = (δ · (P[b] - P[a])) / (||δ|| * sqrt(2))
    
    For each pixel, the transition with the maximum cosine similarity is selected and its 
    corresponding code (a*100 + b) is assigned. Pixels with no change (changed_mask == 0) are 
    assigned a value of 0.
    
    Args:
      prob_t1 (ee.Image): Multiband image of class probabilities at time t1.
      prob_t2 (ee.Image): Multiband imagex of class probabilities at time t2.
      changed_mask (ee.Image): Binary image (1 for changed pixels, 0 for unchanged).
      n_classes (int): Number of classes.
    
    Returns:
      ee.Image: An image where each pixel is assigned the transition code (a*100 + b) corresponding 
                to the change type with the highest cosine similarity. Unchanged pixels are set to 0.
    """
    # sqrt2 is used to normalize the theoretical transition vector, whose norm is sqrt(2)
    sqrt2 = ee.Number(2).sqrt()
    
    # Compute the change vector delta = prob_t2 - prob_t1
    delta = prob_t2.subtract(prob_t1)

    # Compute the Euclidean norm of delta (pixel-wise)
    norm_delta = delta.pow(2).reduce(ee.Reducer.sum()).sqrt()
    
    # Lists to store cosine similarity images and corresponding transition codes
    candidate_cos_list = []
    candidate_code_list = []
    
    # Loop over all possible transitions (a, b) where a != b
    for a in range(n_classes):
        for b in range(n_classes):
            if a == b:
                continue
            # Create the theoretical transition vector:
            # A list of length n_classes with 1 at position b, -1 at position a, and 0 elsewhere.
            candidate_vector = [0] * n_classes
            candidate_vector[b] = 1
            candidate_vector[a] = -1
    
            # Convert the candidate vector to an image constant and rename its bands to match prob_t1
            candidate_vector_img = ee.Image.constant(candidate_vector).rename(prob_t1.bandNames())
            
            # Compute the dot product between delta and the candidate vector image
            dot = delta.multiply(candidate_vector_img).reduce(ee.Reducer.sum())
    
            # Compute the cosine similarity:
            candidate_cos = dot.divide(norm_delta.multiply(sqrt2))
            candidate_cos_list.append(candidate_cos)
            
            # Create the transition code (a*100 + b) and convert it to int32 for homogeneity
            candidate_code = ee.Image.constant(a * 100 + b).toInt32()
            candidate_code_list.append(candidate_code)
    
    # Compute the pixel-wise maximum cosine similarity across all candidate transitions
    max_cos = ee.ImageCollection(candidate_cos_list).max()
    tolerance = 1e-6  # Tolerance to account for floating-point precision
    
    # For each candidate, create an image of its code only where its cosine is close to the maximum
    candidate_code_images = []
    for candidate_cos, candidate_code in zip(candidate_cos_list, candidate_code_list):        
        # Create a mask where the candidate's cosine is within the tolerance of the maximum
        mask = candidate_cos.subtract(max_cos).abs().lte(tolerance)
        candidate_code_img = candidate_code.updateMask(mask)
        candidate_code_images.append(candidate_code_img)
    
    # Combine the candidate code images into one image; at each pixel, only the best candidate's code remains
    change_map = ee.ImageCollection(candidate_code_images).sum().rename('change_map')
    # For pixels with no detected change, force the change code to 0
    change_map = change_map.where(changed_mask.Not(), 0)
    
    return change_map


def remove_small_objects(binary_img, min_size, connectivity=8):
    """
    Remove small objects from a binary image using connected components analysis.
    
    The function labels connected regions in the binary image, calculates the size (in pixels)
    of each region, and masks out regions with fewer than min_size pixels.
    
    Args:
      binary_img (ee.Image): A binary image (with values 0 and 1).
      min_size (int): The minimum number of pixels an object must have to be retained.
      connectivity (int): Connectivity for grouping pixels (4 or 8). Default is 8.
    
    Returns:
      ee.Image: A binary image with small objects removed.
    """
    # Define the kernel for connectivity: use a plus kernel for 8-connectivity,
    # or a square kernel for 4-connectivity.
    kernel = ee.Kernel.plus(1) if connectivity == 8 else ee.Kernel.square(1)
    
    # Label connected components in the binary image
    components = binary_img.connectedComponents(kernel, 256)
    
    # Calculate the size (in pixels) of each connected component using the label band "labels"
    component_size = components.reduceConnectedComponents(
        reducer=ee.Reducer.count(), 
        labelBand='labels', 
        maxSize=256
    )
    
    # Create a mask: only keep regions where the component size is greater or equal to min_size
    filtered = binary_img.updateMask(component_size.gte(min_size))
    return filtered

def create_index_mask(image1: ee.Image, 
                   image2: ee.Image, 
                   index: str="dNDVI", 
                   threshold: float=0,
                   greater_than: bool=False) -> ee.Image:
    """
    Create a binary mask to an image based on a threshold value of the difference of an index between two images.

    Args:
      image1 (ee.Image): The first input image.
      image2 (ee.Image): The second input image.
      index (str): The index to use for thresholding. Default is "NDVI". Other
                    options are "dNDWI", "dNBR", "dSAVI", "dNDMI".
      threshold (float): The threshold value for the index difference. Default is 0.
      greater_than (bool): If True, the mask will be True where the index difference is greater than the threshold.
                           If False, the mask will be True where the index difference is less than or equal to the threshold.
                           Default is False.
    
    Returns:
      ee.Image: A binary mask image based on the index difference threshold.
    """

    # Compute the index value for the first image
    if index == "dNDVI":
        index_value1 = image1.normalizedDifference(['B8', 'B4'])
        index_value2 = image2.normalizedDifference(['B8', 'B4'])

    elif index == "dNDWI":        
        index_value1 = image1.normalizedDifference(['B3', 'B8'])
        index_value2 = image2.normalizedDifference(['B3', 'B8'])
    
    elif index == "dNBR":
        index_value1 = image1.normalizedDifference(['B8', 'B12'])
        index_value2 = image2.normalizedDifference(['B8', 'B12'])
    
    elif index == "dSAVI":
        index_value1 = image1.expression(
            '1.5 * (NIR - RED) / (NIR + RED + 0.5)', 
            {'NIR': image1.select('B8'), 'RED': image1.select('B4')}
        )
        index_value2 = image2.expression(
            '1.5 * (NIR - RED) / (NIR + RED + 0.5)', 
            {'NIR': image2.select('B8'), 'RED': image2.select('B4')}
        )
    
    elif index == "dNDMI":
        index_value1 = image1.normalizedDifference(['B8', 'B11'])
        index_value2 = image2.normalizedDifference(['B8', 'B11'])
    
    else:
        raise ValueError(f"Invalid index: {index}")
    
    # Compute the difference of the index values
    index_diff = index_value2.subtract(index_value1)
    
    # Create a binary mask based on the index difference threshold
    if greater_than:
        mask = index_diff.gt(threshold).rename('index_mask')
    else:
        mask = index_diff.lte(threshold).rename('index_mask')

    return mask


def dilate_mask(mask: ee.Image, radius: int = 1) -> ee.Image:
    """
    Dilate a binary mask using a specified radius.

    Args:
      mask (ee.Image): The binary mask to dilate.
      radius (int): The radius for the dilation operation. Default is 1.
    
    Returns:
      ee.Image: The dilated binary mask.
    """
    return mask.focal_max(radius, 'square', 'pixels')


def erode_mask(mask: ee.Image, radius: int = 1) -> ee.Image:
    """
    Erode a binary mask using a specified radius.

    Args:
      mask (ee.Image): The binary mask to erode.
      radius (int): The radius for the erosion operation. Default is 1.
    
    Returns:
      ee.Image: The eroded binary mask.
    """
    return mask.focal_min(radius, 'square', 'pixels')
