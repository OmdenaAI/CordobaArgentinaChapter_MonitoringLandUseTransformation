import ee

def change_type_discrimination(
    prob_t1: ee.Image, 
    prob_t2: ee.Image, 
    changed_mask: ee.Image, 
    n_classes: int
) -> ee.Image:
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
      prob_t2 (ee.Image): Multiband image of class probabilities at time t2.
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
