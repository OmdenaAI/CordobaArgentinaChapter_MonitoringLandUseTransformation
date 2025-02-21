import ee
import os
import pyproj
import pathlib
import numpy as np

from dotenv import load_dotenv
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

def get_credentials():
    """
    Get the credentials to access Google Earth Engine.
    Returns:
    
    """
    try: 
        # Get the notebook directory
        NOTEBOOK_DIR = os.getcwd()

        # Get the project root directory (two levels up)
        PROJECT_ROOT = os.path.abspath(os.path.join(NOTEBOOK_DIR, '../..'))

        # Load environment variables
        load_dotenv()

        # Get credentials path and ensure it's relative to PROJECT_ROOT
        GEE_CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, os.getenv('GEE_CREDENTIALS_PATH'))
        GEE_PROJECT_ID = os.getenv('GEE_PROJECT_ID')

        # Initialize GEE
        credentials = ee.ServiceAccountCredentials(
            '',
            GEE_CREDENTIALS_PATH,
            GEE_PROJECT_ID
        )
        ee.Initialize(credentials, opt_url="https://earthengine-highvolume.googleapis.com")
        return credentials
    
    except Exception as e:
        print(e)


## Generate a cloud-free composite for a given year and location
def generate_cloudfree_composite(lat: float, 
                                 lon: float, 
                                 start_date: str,
                                 end_date: str, 
                                 clear_threshold: float,
                                 compose_by: str) -> ee.Image:
    """
    Generate a cloud-free composite for a given year and location.

    Args:
    lat (float): Latitude of the location.
    lon (float): Longitude of the location.
    start_date (str): Start date of the time range. Format: 'YYYY-MM-DD'
    end_date (str): End date of the time range. Format: 'YYYY-MM-DD'
    clear_threshold (float): Threshold to consider a pixel as cloud-free. From 0 to 1.
    compose_by (str): The method to compose the images. Options: 'mean', 'median', 'max', 'min'

    Returns:
    ee.Image: The cloud-free composite.
    """

    # Define the collections: Sentinel-2 and Cloud Score+
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

    # Region of interest by coordinates
    roi = ee.Geometry.Point([lon, lat])

    # Define the update mask with cloud-free pixels by threshold
    def apply_cloudscore(img):
        cloud_score = ee.Image(img.get('cloud_score'))
        return img.updateMask(cloud_score.select('cs_cdf').gte(clear_threshold))


    # Filter collections by region and date
    s2_filtered = s2.filterBounds(roi).filterDate(start_date, end_date) \
                  .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
    
    csPlus_filtered = csPlus.filterBounds(roi).filterDate(start_date, end_date)
    print(f"Sentinel-2 available images: {s2_filtered.size().getInfo()}")

    # Join collections and generate the composite
    s2_with_cloud_score = ee.Join.saveFirst('cloud_score').apply(**{
        "primary": s2_filtered,
        "secondary": csPlus_filtered,
        "condition": ee.Filter.equals(**{
            "leftField": 'system:index',
            "rightField": 'system:index'
        })
    })

    # Apply the cloud score mask
    s2_with_cloud_score = ee.ImageCollection(s2_with_cloud_score)
    
    if compose_by == 'mean':
        composite = s2_with_cloud_score.map(apply_cloudscore).mean()
    elif compose_by == 'median':
        composite = s2_with_cloud_score.map(apply_cloudscore).median()
    elif compose_by == 'max':
        composite = s2_with_cloud_score.map(apply_cloudscore).max()
    elif compose_by == 'min':
        composite = s2_with_cloud_score.map(apply_cloudscore).min()
    else:
        raise ValueError("Invalid compose_by option. Use 'mean', 'median', 'max', or 'min'")

    return composite 


def generate_dynamic_composite(lat: float,
                               lon: float, 
                               start_date: str,
                               end_date: str,
                               compose_by: str) -> ee.Image:
    """
    Generate a cloud-free composite for a given year and location.

    Args:
    lat (float): Latitude of the location.
    lon (float): Longitude of the location.
    start_date (str): Start date of the time range. Format: 'YYYY-MM-DD'
    end_date (str): End date of the time range. Format: 'YYYY-MM-DD'
    compose_by (str): The method to compose the images. Options: 'mean', 'median', 'max', 'min'

    Returns:
    ee.Image: The cloud-free composite.
    """

    # Define the collections: Sentinel-2 and Cloud Score+
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    dynamic = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')

    # Region of interest by coordinates
    roi = ee.Geometry.Point([lon, lat])
   
    # Filter collections by region and date
    s2_filtered = s2.filterBounds(roi).filterDate(start_date, end_date) \
                  .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 60))
        
    class_bands = ['water',
    'trees',
    'grass',
    'flooded_vegetation',
    'crops',
    'shrub_and_scrub',
    'built',
    'bare',
    'snow_and_ice'
    ]
    
    dynamic_filtered = dynamic.filterBounds(roi) \
                              .filterDate(start_date, end_date) \
                              .select(class_bands)

    print(f"Dynamic World available images: {dynamic_filtered.size().getInfo()}")

    # Join collections and generate the composite
    dynamic_merged = ee.Join.saveFirst('dynamic').apply(**{
        "primary": dynamic_filtered,
        "secondary": s2_filtered,
        "condition": ee.Filter.equals(**{
            "leftField": 'system:index',
            "rightField": 'system:index'
        })
    })
    # Merge the images from the Dynamic World
    dynamic_merged = ee.ImageCollection(dynamic_merged)
    if compose_by == 'mean':
        composite = dynamic_merged.mean()
    elif compose_by == 'median':
        composite = dynamic_merged.median()
    elif compose_by == 'max':
        composite = dynamic_merged.max()
    elif compose_by == 'min':
        composite = dynamic_merged.min()
    else:
        raise ValueError("Invalid compose_by option. Use 'mean', 'median', 'max', or 'min'")

    return composite 
                               

## Dwonload the image composite by coordinates, edge size, resolution, and time range
def get_composite(lat: float, 
                lon: float,                        
                edge_size: int,
                start_date: str,
                end_date: str,
                product: str = 'S2_SR_HARMONIZED',                               
                resolution: int = 10,                                     
                save_file: bool = False,
                filename: str = None,
                clear_threshold: float=0.6
                ) -> np.ndarray:

    """
    Download a cloud-free composite for a given year and location in a square area.

    Args:
    lat (float): Latitude of the location.
    lon (float): Longitude of the location.
    composite (float): Cloud-free composite.
    edge_size (int): Size of the image edge in meters.
    resolution (int): Resolution of the image in meters.
    start_date (str): Start date of the time range. Format: 'YYYY-MM-DD'
    end_date (str): End date of the time range. Format: 'YYYY-MM-DD'    
    product (str): Product to use. Default: 'S2_SR_HARMONIZED'. Other option is 'DYNAMIC_WORLD'
    save_file (bool): Save the image to disk. Default: False.    
    filename (str): Filepath to save the image. Default: None.
    clear_threshold (float): Threshold to consider a pixel as cloud-free. From 0 to 1, default: 0.6.

    Returns:
    np.ndarray: The composite product for the given location.
    """

    if product == 'S2_SR_HARMONIZED':
        # Generate the cloud-free composite
        composite = generate_cloudfree_composite(lat, lon, start_date, end_date, clear_threshold, 
                                                 compose_by='mean')
        BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']

    elif product == 'DYNAMIC_WORLD':
        composite = generate_dynamic_composite(lat, lon, start_date, end_date, compose_by='median')
        BANDS = ['water', 'trees', 'grass', 'flooded_vegetation', 'crops', 'shrub_and_scrub', 
                 'built', 'bare', 'snow_and_ice']

    # Get the center coordinates
    utm_crs = query_utm_crs_info(datum_name="WGS84", area_of_interest=AreaOfInterest(lon, lat, lon, lat))
    epsg_code = utm_crs[0].code
    transformer = pyproj.Transformer.from_crs(f'epsg:4326', f'epsg:{epsg_code}', always_xy=True)
    center_x, center_y = transformer.transform(lon, lat)

    # Get the upper left coordinates
    ul_x = center_x - (edge_size * resolution / 2)
    ul_y = center_y + (edge_size * resolution / 2)

    # Define the request
    request = {
        "expression": composite,
        "fileFormat": "GEO_TIFF",
        "bandIds": BANDS,
        "grid": {
            "dimensions": {
                "width": edge_size,
                "height": edge_size
            },
        
        "affineTransform": {
            "scaleX": resolution,
            "shearX": 0,
            "translateX": ul_x,
            "shearY": 0,
            "scaleY": -resolution,        
            "translateY": ul_y  
            },
        "crsCode": f"EPSG:{epsg_code}",
        },    
    }

    image = ee.data.computePixels(request)

    if save_file:
        # Compute the pixels and save the image
        filename = pathlib.Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the image
        
        with open(filename, 'wb') as file:
            file.write(image)
        
        print(f"Image saved in {filename}")    

    else:
        return image

# ------------------------------
# UTIL FUNCTIONS FOR SVC + DFPS
# ------------------------------

## Compute the metric to evaluate the threshold
def compute_Lk(magnitude: np.ndarray,
               class_t1: np.ndarray,
               class_t2: np.ndarray,
               threshold: float) -> float:
    """
    Calculate Lk for a given threshold:
     
        Lk = ((Ak1 - Ak2) * 100) / A
     
     where:
        - Ak1 = # of pixels that (according to ground truth) changed and
                  (according to our threshold) were classified as changed
        - Ak2 = # of pixels that (according to ground truth) did NOT change but
                  (according to our threshold) were classified as changed
        - A   = total # of pixels that (according to ground truth) changed

    Args:
    magnitude (np.ndarray): Magnitude of the change 
    class_t1 (np.ndarray): Land cover class at time t1.
    class_t2 (np.ndarray): Land cover class at time t2.
    threshold (float): Threshold to consider a pixel as changed.

    Returns:
    float: Lk value. Between 0 and 100.
    """
    
    # Change detected given the threshold
    detected_change = (magnitude >= threshold)
    
    # A pixel changes if the class changes
    true_change = (class_t1 != class_t2)

    # A pixel does not change if the class remains the same
    true_no_change = ~true_change
    
    # Calculate Ak1, Ak2, and A
    # Ak1: pixels that changed (true_change) and were correctly detected
    Ak1 = np.count_nonzero(true_change & detected_change)
    
    # Ak2: pixels that did not change (true_no_change) but were detected as changed
    Ak2 = np.count_nonzero(true_no_change & detected_change)
    
    # A: total de píxeles que cambiaron en la realidad
    A = np.count_nonzero(true_change)
    
    if A == 0:
        # Evitar división por cero (caso extremo de dataset)
        return -9999.0
    
    Lk_value = ((Ak1 - Ak2) * 100.0) / A

    return Lk_value


## Implement a simple threshold optimization
def threshold_optimization(
    magnitude: np.ndarray,
    class_t1: np.ndarray,
    class_t2: np.ndarray,
    step_coarse: float = 0.1,
    step_fine: float = 0.01,
    tolerance: float = 1e-3,
    max_iterations: int = 10
) -> tuple[float, float]:
    """
    Threshold optimization using a simple search algorithm to maximize Lk.

    Parameters:
    magnitude (np.ndarray): Magnitude of the change vector.
    class_t1 (np.ndarray): Land cover class at time t1.
    class_t2 (np.ndarray): Land cover class at time t2.
    step_coarse (float): Coarse step for the global search. Default: 0.1.
    step_fine (float): Fine step for the local search. Default: 0.01.
    tolerance (float): Minimum improvement in Lk to continue iterating. Default: 1e-3.
    max_iterations (int): Maximum number of iterations. Default: 10.

    Returns:
    tuple[float, float]: The best threshold and the best Lk value.
    """

    # 1) Determine the range of magnitude
    vmin, vmax = np.min(magnitude), np.max(magnitude)
    
    best_threshold = vmin
    best_Lk = -9999.0
    
    iteration = 0
    improved = True
    
    while iteration < max_iterations and improved:
        iteration += 1
        improved = False
        
        # --------------------------
        # (A) COARSE STEP
        # --------------------------
        coarse_candidates = np.arange(vmin, vmax + step_coarse, step_coarse)
        local_best_thr = best_threshold
        local_best_Lk = best_Lk
        
        for T in coarse_candidates:
            Lk_current = compute_Lk(magnitude, class_t1, class_t2, T)
            if Lk_current > local_best_Lk:
                local_best_Lk = Lk_current
                local_best_thr = T
        
        # CHECK IF THE COARSE SEARCH IMPROVED
        if (local_best_Lk - best_Lk) > tolerance:
            best_Lk = local_best_Lk
            best_threshold = local_best_thr
            improved = True
        
        # --------------------------
        # (B) FINE STEP
        # --------------------------
        # Define the range for the fine search
        low_bound = max(vmin, best_threshold - step_coarse)
        high_bound = min(vmax, best_threshold + step_coarse)
        
        fine_candidates = np.arange(low_bound, high_bound + step_fine, step_fine)
        
        local_best_thr = best_threshold
        local_best_Lk = best_Lk
        
        for T in fine_candidates:
            Lk_current = compute_Lk(magnitude, class_t1, class_t2, T)
            if Lk_current > local_best_Lk:
                local_best_Lk = Lk_current
                local_best_thr = T
        
        # CHECK IF THE FINE SEARCH IMPROVED
        if (local_best_Lk - best_Lk) > tolerance:
            best_Lk = local_best_Lk
            best_threshold = local_best_thr
            improved = True
    
    return best_threshold, best_Lk


def direction_cosine(delta_m: np.ndarray,
                     delta_p: np.ndarray
    ) -> float:
    
    """
    Calculate the cosine of the angle between delta_m and delta_p.
    Returns a value in [-1, 1].
    The formula is:

        cos(theta) = (delta_m . delta_p) / (||delta_m|| * ||delta_p||)

    Args:
    delta_m (np.ndarray): Delta vector for the model.
    delta_p (np.ndarray): Delta vector for the probability.

    Returns:
    float: Cosine of the angle between delta_m and delta_p. Between -1 and 1.
    """
    norm_m = np.linalg.norm(delta_m)
    norm_p = np.linalg.norm(delta_p)
    
    # To avoid division by zero
    if norm_m < 1e-12 or norm_p < 1e-12:
        return -9999 
    
    return np.dot(delta_m, delta_p) / (norm_m * norm_p)


def change_type_discrimination(prob_t1: np.ndarray,
                               prob_t2: np.ndarray,
                               changed_mask: np.ndarray,
                               n_classes: int
    ) -> np.ndarray:
    """
    Assign the change type (class transition) for pixels that changed.

    Args:
    prob_t1 (np.ndarray): Array (n, height, width) with probabilities at t1.
    prob_t2 (np.ndarray): Array (n, height, width) with probabilities at t2.
    changed_mask (np.ndarray): Array (height, width) boolean (True = changed).
    n_classes (int): Number of classes (e.g., 9).

    Returns:
    np.ndarray: Change map (height, width), where each "changed" pixel has a code
                of transition a->b, and the unchanged pixels have 0.
    """
        
    # 1) Pre calculate the transition vectors
    # We use a dictionary with key=(a,b), value=delta_p_ab
    transition_vectors = {}
    
    # Generate "pure" vectors for each class
    # P_0 = (1, 0, 0, ...), P_1 = (0, 1, 0, ...) etc.
    P = np.eye(n_classes)
    
    for a in range(n_classes):
        for b in range(n_classes):
            if a != b:
                delta_ab = P[b] - P[a]
                transition_vectors[(a, b)] = delta_ab
            else:
                transition_vectors[(a, b)] = None  # No transition (a->a)
    
    # 2) Create an empty change map
    height, width = prob_t1.shape[1], prob_t1.shape[2]
    change_map = np.zeros((height, width), dtype=np.int32)
    
    # 3) For each changed pixel, calculate Delta M and find the transition with the highest cosine
    for i in range(height):
        for j in range(width):
            if changed_mask[i, j]:
                # Extract the probability vectors at t1 and t2
                p1 = prob_t1[:, i, j]  # shape (n_classes,)
                p2 = prob_t2[:, i, j]
                
                # Delta M
                delta_m = p2 - p1
                
                # Search for the transition (a->b) with the highest cosine
                best_cos = -9999
                best_transition = (0,0)
                
                for (a, b), delta_ab in transition_vectors.items():
                    if delta_ab is None:
                        continue
                    cos_val = direction_cosine(delta_m, delta_ab)
                    if cos_val > best_cos:
                        best_cos = cos_val
                        best_transition = (a, b)
                
                # Code the transition a->b as a number, e.g. a * 100 + b
                a, b = best_transition
                transition_code = a * 100 + b
                
                change_map[i, j] = transition_code
            else:
                # Unchanged pixel
                change_map[i, j] = 0 
    
    return change_map


## Convert the S2 image to RGB
def sentinel_l2a_to_rgb(image: np.ndarray) -> np.ndarray:
    """
    Convert the Sentinel-2 image to RGB (0-255).

    Args:
    image (np.ndarray): Sentinel-2 image composite from Test Data. In the C, H, W dimension order.

    Returns:
    The RGB image in the H, W, C dimension order.
    """
    min_val = 0.0
    max_val = 0.3

    # Get only RGB bands from the image
    # B2: Blue, B3: Green, B4: Red     
    rgb_image = (image[[2,1,0]] / 10000 - min_val) / (max_val - min_val)
    rgb_image[rgb_image < 0] = 0
    rgb_image[rgb_image > 1] = 1

    # Convert to 8-bit
    rgb_image = (rgb_image * 255).astype(np.uint8)
    return rgb_image # C, H, W


## Convert the ground truth image to 0-255
def gt_to_0_255(gt: np.ndarray) -> np.ndarray:
    """
    Convert the ground truth image to 0-255.

    Args:
    gt (np.ndarray): Ground truth image.

    Returns:
    np.ndarray: The ground truth image in 0-255.
    """
    gt_converted = (gt * 255).astype(np.uint8)
    return gt_converted