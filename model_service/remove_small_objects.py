import ee

def remove_small_objects(
    binary_img: ee.Image, 
    min_size: int, 
    connectivity: int = 8
) -> ee.Image:
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
