# import numpy as np
# import cv2
# import rasterio
# import pyproj
# from rasterio.features import rasterize
# from shapely.geometry import shape, Polygon
# from typing import Tuple, List

# from skimage.morphology import remove_small_objects
# from shapely.geometry import Polygon, MultiPolygon

# class cordobaPostProcessor:
#     """
#     Class implementing various mask processing functions.
#     """

#     def __init__(self):
#         pass

#     def apply_spectral_threshold(self, spectral_array: np.ndarray, threshold: float, greater_than: bool=True) -> np.ndarray:
#         """
#         Returns a binary mask based on the threshold.

#         Args:
#         spectral_array (np.ndarray): The input spectral array.
#         threshold (float): The threshold value.
#         greater_than (bool): If True, values above the threshold will become 1; otherwise, values below the threshold become 1.

#         Returns:
#         np.ndarray: The resulting binary mask.
#         """
#         if greater_than:
#             return (spectral_array > threshold).astype(np.uint8)
#         else:
#             return (spectral_array < threshold).astype(np.uint8)

#     def dilate_mask(self, mask: np.ndarray, iterations: int=1) -> np.ndarray:
#         """
#         Applies dilation to the mask.

#         Args:
#         mask (np.ndarray): The input binary mask.
#         iterations (int): The number of dilation iterations.

#         Returns:
#         np.ndarray: The dilated mask.
#         """
#         kernel = np.ones((3, 3), np.uint8)
#         return cv2.dilate(mask, kernel, iterations=iterations)

#     def erode_mask(self, mask: np.ndarray, iterations: int=1) -> np.ndarray:
#         """
#         Applies erosion to the mask.

#         Args:
#         mask (np.ndarray): The input binary mask.
#         iterations (int): The number of erosion iterations.

#         Returns:
#         np.ndarray: The eroded mask.
#         """
#         kernel = np.ones((3, 3), np.uint8)
#         return cv2.erode(mask, kernel, iterations=iterations)

#     def remove_small_objects(self, mask: np.ndarray, min_size: int=16) -> np.ndarray:
#         """
#         Removes small objects (components) in the mask.

#         Args:
#         mask (np.ndarray): The input binary mask.
#         min_size (int): The minimum size of objects to keep.

#         Returns:
#         np.ndarray: The mask with small objects removed.
#         """
#         return remove_small_objects(mask.astype(bool), min_size=min_size).astype(np.uint8)

#     def majority_vote(self, masks: list, min_votes: int=2) -> np.ndarray:
#         """
#         Takes multiple binary masks and generates a new one by majority vote.

#         Args:
#         masks (list): List of binary masks.
#         min_votes (int): Minimum number of votes required for a pixel to be set to 1.

#         Returns:
#         np.ndarray: The resulting binary mask.
#         """
#         stacked = np.stack(masks, axis=-1)
#         vote_sum = np.sum(stacked, axis=-1)
#         return (vote_sum >= min_votes).astype(np.uint8)

#     def create_area_mask(self, shape: Tuple[int, int], area_of_interest: ee.Geometry.Polygon) -> numpy.ndarray:
#             """
#             Create a binary mask from the area of interest coordinates.
#             shape: the shape of the mask (height, width)
#             area_of_interest: the area of interest as an ee.Geometry.Polygon
#             resolution: the resolution of the mask in meters
#             Return the binary mask
#             """
#             # Convert the coordinates of the area of interest to UTM
#             coords = area_of_interest.coordinates().getInfo()[0]
#             lat_from, lon_from, lat_to, lon_to = coords[0][1], coords[0][0], coords[2][1], coords[2][0]
#             utm_code = query_utm_crs_info(datum_name='WGS 84', area_of_interest=AreaOfInterest(lon_from, lat_from, lon_to, lat_to))
#             utm_zone = utm_code[0].code
            
#             # Convert the coordinates to UTM
#             utm_transformer = pyproj.Transformer.from_crs('epsg:4326', f"epsg:{utm_zone}", always_xy=True)
#             utm_coords = [utm_transformer.transform(lon, lat) for lon, lat in coords]

#             # Convert to shapely polygon
#             polygon = Polygon(utm_coords)

#             # Create a transformation of coordinates
#             x_min, y_min, x_max, y_max = polygon.bounds
#             transform = rasterio.transform.from_bounds(x_min, y_min, x_max, y_max, shape[1], shape[0])

#             # Rasterize the polygon
#             mask = rasterize([polygon], out_shape=shape, transform=transform, all_touched=True, fill=0, default_value=1, dtype=numpy.uint8)

#             return mask

#     def convert_mask_to_polygon(self, mask: np.ndarray, area_of_interest: LongLatBBox) -> List[List[Tuple[float, float]]]:
#             """
#             Convert a mask to a list of polygons.
#             mask: the mask to convert
#             area_of_interest: the area of interest as a LongLatBBox
#             resolution: the resolution of the mask in meters
#             Return the list of polygons
#             """
#             # Create a binary mask from the area of interest coordinates
#             area_mask = self.create_area_mask(mask.shape, area_of_interest.to_ee_polygon())
            
#             # Apply the area mask to the input mask
#             mask = mask * area_mask
            
#             # Vectorize the result using rasterio.features.shapes
#             transform = rasterio.transform.from_bounds(area_of_interest.long_from, area_of_interest.lat_from, area_of_interest.long_to, area_of_interest.lat_to, mask.shape[1], mask.shape[0])
#             shapes_gen = shapes(mask, transform=transform)
#             shapes = [(shape(s), v) for s, v in shapes_gen if v == 1]

#             # Convert shapes to polygons
#             polygons = [s for s, _ in shapes]
#             return polygons

#     def calculate_index_difference(self, images: list, index: str, threshold: float, greater_than: bool=True) -> np.ndarray:
#         """
#         Calculate the difference of a specified index between two images and apply a threshold.

#         Args:
#         images (list): List of CordobaImage instances.
#         index (str): The index to calculate (e.g., 'ndvi').
#         threshold (float): The threshold value.
#         greater_than (bool): If True, values above the threshold will become 1; otherwise, values below the threshold become 1.

#         Returns:
#         np.ndarray: The binary mask after applying the threshold.
#         """
#         image1 = images[0].bands[index]
#         image2 = images[1].bands[index]

#         index_diff = image2 - image1
#         return self.apply_spectral_threshold(index_diff, threshold, greater_than)

#     def process(self, images: list, index_thresholds: dict, 
#                 dilate_iterations: int=1, 
#                 erode_iterations: int=1, 
#                 min_size: int=16, 
#                 min_votes: int=3) -> MultiPolygon:
#         """
#         Full post-processing pipeline.

#         Args:
#         images (list): List of CordobaImage instances.
#         index_thresholds (dict): Dictionary with indices as keys and tuples of (threshold, greater_than) as values.
#         dilate_iterations (int): The number of dilation iterations.
#         erode_iterations (int): The number of erosion iterations.
#         min_size (int): The minimum size of objects to keep.
#         min_votes (int): Minimum number of votes required for a pixel to be set to 1.

#         Returns:
#         MultiPolygon: The resulting multipolygon after full post-processing.
#         """
#         index_masks = []
#         for index, (threshold, greater_than) in index_thresholds.items():
#             mask = self.calculate_index_difference(images, index, threshold, greater_than)
#             index_masks.append(mask)
        
#         final_mask = self.majority_vote(index_masks, min_votes)
#         final_mask = self.dilate_mask(final_mask, dilate_iterations)
#         final_mask = self.erode_mask(final_mask, erode_iterations)
#         final_mask = self.remove_small_objects(final_mask, min_size)
        
#         polygons = self.mask_to_polygons(final_mask)
#         return polygons