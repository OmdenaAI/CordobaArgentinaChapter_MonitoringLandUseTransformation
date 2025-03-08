from typing import List
from enum import Enum
import numpy
import pyproj
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
# Install the Earth Engine Python API with
# pip install earthengine-api
import ee
import requests
import io
import sys
import datetime

# List of bands name in the dynamic world dataset
dynamic_world_bands = ["water", "trees", "grass", "flooded_vegetation", "crops","shrub_and_scrub", "built", "bare", "snow_and_ice"]

class CordobaDataSource(Enum):
    """
    Enumeration to identify the available image sources
    """
    # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
    SENTINEL2 = 0
    # https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
    LANDSAT8 = 1
    # https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LT05_C02_T1_L2
    LANDSAT5 = 2
    # Automatic selection of the source sentinel2 > landsat8 > landasat5
    AUTO = 3
    # https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
    DYNAMIC_WORLD = 4

    def __str__(self):
        """
        String representation
        """
        return str(self.name)

class LongLatBBox:
    """
    Longitude-latitude bounding box or irregular polygon
    """
    def __init__(self, coordinates: List[tuple]):
        """
        Constructor for an instance of LongLatBBox.
        coordinates: list of (longitude, latitude) tuples defining the polygon
        """
        self.coordinates = coordinates
        self.long_from = min(coord[0] for coord in coordinates)
        self.long_to = max(coord[0] for coord in coordinates)
        self.lat_from = min(coord[1] for coord in coordinates)
        self.lat_to = max(coord[1] for coord in coordinates)

    def to_ee_polygon(self) -> ee.Geometry.Polygon:
        """
        Convert a LongLatBBox to a ee.Geometry.Polygon
        """
        return ee.Geometry.Polygon([self.coordinates])
    
    def to_ee_rectangle(self) -> ee.Geometry.Rectangle:
        """
        Convert a LongLatBBox to a ee.Geometry.Rectangle
        """
        return ee.Geometry.Rectangle(
          [self.long_from, self.lat_from, self.long_to, self.lat_to]) 

    def __str__(self):
        """
        String representation
        """
        return f"Polygon with coordinates: {self.coordinates}"
    

class CordobaImage:
    """
    Class representing an image (raw data and extra data) ready to use by the
    other teams
    """
    def __init__(self,
        date: str,
        area: LongLatBBox,
        resolution: float,
        width: int,
        height: int):
        """
        Constructor for an instance of CordobaImage.
        date: the acquisition date and time (eg. "2022-12-01T00:01")
        area: the bounding longitudes and latitudes of the image
        resolution: the size in meter of one pixel
        width, height: dimensions of the image
        """
        self.date = date
        self.area = area
        self.resolution = resolution
        self.width = width
        self.height = height
        self.source = None

        # Contains image data per band, dictionary key is the band name,
        # dictionary value is a numpy array of the value of the band
        self.bands = {}

        # Contains classification data, dictionary key is the class name,
        # dictionary value is a numpy array of the probability in [0,1] of
        # the class
        self.classes = {}

    def __str__(self):
        """
        String representation
        """
        return f"acquisition date: {self.date}, area: {self.area}, \
                resolution: {self.resolution}m/px, width: {self.width}px, height: {self.height}px"

    def to_rgb(self, gamma=1.0) -> numpy.array:
        """
        Convert a CordobaImage into a RGB array
        Return the composite of red, green, blue bands as a numpy array.
        Pixel values in [0,255]. Red, gree, blue bands normalised.
        """
        
        # Get the max value over red, green, blue bands for normalisation
        max_val = max(self.bands["red"].max(), 
                      max(self.bands["green"].max(), 
                          self.bands["blue"].max()))
        if max_val == 0.0:
            max_val = 1.0

        # Create the result image
        image = numpy.zeros([self.height, self.width, 3], numpy.uint8)
        
        # Normalize and apply gamma correction
        red_normalized = ((self.bands["red"] / max_val) ** gamma) * 255.0 
        green_normalized = ((self.bands["green"] / max_val) ** gamma) * 255.0   
        blue_normalized = ((self.bands["blue"] / max_val) ** gamma) * 255.0 

        # Stack the bands to create the RGB image
        image = numpy.stack((red_normalized, green_normalized, blue_normalized), axis=-1).astype(numpy.uint8)

        # Return the result image
        return image


    def to_grey_scale(self, band) -> numpy.array:
        """
        Convert a CordobaImage into a numpy array
        band: the band to use
        Return the numpy array.
        Pixel values in [0,255]. Values normalised.
        """
        
        # Get the max value for normalisation
        max_val = self.bands[band].max()
        if max_val == 0.0:
            max_val = 1.0

        # Normalize the band
        normalized_band = ((self.bands[band] / max_val)) * 255.0

        # Stack the normalized band to create a 3-channel greyscale image
        image = numpy.stack((normalized_band,)*3, axis=-1)

        # Return the result image
        return image

    def to_dynamic_world_mask(self) -> numpy.ndarray:
        """
        Convert a CordobaImage into a mask for a given band
        threshold: minimum probability
        Return the mask as a boolean numpy array.
        """

        # If the image's source is a dynamic world
        if self.source == CordobaDataSource.DYNAMIC_WORLD:
            values = numpy.array(list(self.bands.values()))
        # Else, the image has a satellite source
        else:
            values = numpy.array(list(self.classes.values()))
        
        # Create a boolean mask of class values for which the highest
        # probability among classes is the one of the requested class
        mask = numpy.argmax(values, axis=0)
        
        # Return the mask
        return mask
    
    
    def get_bands_as_vectors(self, lbl_bands: List[str]=None) -> numpy.array:
        """
        Convert the CordobaImage into a numpy array of vectors. Each vector
        contains the values of bands for the respective pixel.
        lbl_bands: list of bands name used, if None all bands are used
        Return a numpy array.
        """
        # Set the bands to all bands if none were provided
        if lbl_bands is None:
            lbl_bands = self.bands.keys()
        # Return the concatenation of bands values
        bands = list(map(lambda x: self.bands[x], lbl_bands))
        return numpy.dstack(bands)
   
    def to_ndvi(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDVI array
        Return the NDVI as a numpy array.
        Pixel values in [0,255], 3 channels. NDVI band normalised.
        """
        return self.to_grey_scale("ndvi")

    def to_ndmi(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDMI array
        Return the NDMI as a numpy array.
        Pixel values in [0,255], 3 channels. NDMI band normalised.
        """
        return self.to_grey_scale("ndmi")

    def to_nbr(self) -> numpy.array:
        """
        Convert a CordobaImage into a NBR array
        Return the NBR as a numpy array.
        Pixel values in [0,255], 3 channels. NBR band normalised.
        """
        return self.to_grey_scale("nbr")

    def to_savi(self) -> numpy.array:
        """
        Convert a CordobaImage into a SAVI array
        Return the SAVI as a numpy array.
        Pixel values in [0,255], 3 channels. SAVI band normalised.
        """
        return self.to_grey_scale("savi")
    
    def to_ndwi(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDWI array
        Return the NDWI as a numpy array.
        Pixel values in [0,255], 3 channels. NDWI band normalised.
        """
        return self.to_grey_scale("ndwi")
    
    def dark_object_correction(self):
        """
        Apply dark object correction to  ee.Image
        image: the image to be preprocessed
        The image is updated.
        """
        # Loop on the bands
        for band in self.bands.keys():

            # Search for the minimum value
            min_value = self.bands[band].min()

            # Substract the minimum value to all values in the band
            self.bands[band] -= min_value


# Helper function to discard clouds when calculating the median of several
# images
def mask_clouds_sentinel(image: ee.Image) -> ee.Image:
    qa = image.select('QA60')
    cloud_bit_mask = 1 << 10  # Bit 10 represents clouds
    cirrus_bit_mask = 1 << 11  # Bit 11 represents cirrus clouds
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    return image.updateMask(mask)

def mask_clouds_landsat(image: ee.Image) -> ee.Image:
    qa = image.select('QA_PIXEL')
    cloud_mask = 1 << 4  # Bit 4 represents cloud presence
    mask = qa.bitwiseAnd(cloud_mask).eq(0)
    return image.updateMask(mask)


class CordobaDataPreprocessor:
    """
    Class implementing tasks of the team 'data preprocessing and analysis'
    """

    def __init__(self, gee_account, gee_credentials_path, online=True):
        """
        Constructor for an instance of CordobaDataPreprocessor
        gee_account: GEE login
        gee_credentials_path: path to the GEE credentials file
        online: online/offline mode
        """

        # Flag for online/offline mode (in offline mode avoid interacting with
        # GEE for test)
        self.online = online

        # Authentication to Google Earth Engine API
        if online:
            credentials = ee.ServiceAccountCredentials(
              gee_account, gee_credentials_path)
            # Can use
            # ee.Initialize(
            #    credentials,
            #    opt_url="https://earthengine-highvolume.googleapis.com")
            # to allow higher volume transaction
            ee.Initialize(credentials)

        # Set the data source to automatic by default
        self.data_source = CordobaDataSource.AUTO

        # Set the threshold for the cloud coverage to 35% by default to match
        # the one used by dynamic world
        # (percentage of image pixels; in [0.0, 100.0])
        self.max_cloud_coverage = 35.0

        # Resolution of the returned image (in meter per pixel)
        self.resolution = 10.0

        # Verbose mode
        self.flag_verbose = True

        # Gaussian blur parameters (if radius==0, no blur)
        self.gaussian_blur = {"radius": 3, "sigma": 0.5}

        # Step (in days) when searching an image around a given date
        self.step_search_image = 5

        # Max number of step when searching for data around a date
        self.nb_max_step_search = 2

        # Threshold for the area span in degrees (default: 0.1)
        # When downloading the data, if the reqested area is larger than the
        # threshold, divide the data into chunks of downloadable size
        self.max_area_angle = 0.1

        # Flag to control cloud filtering when compositing several images
        # Default is False because it creates dirty artefacts
        self.flag_cloud_filtering = False

    def search_dataset_range(self, date: str, area: LongLatBBox, source: CordobaDataSource) -> ee.ImageCollection:
        """
        Search dates around a given date for which an ee.ImageCollection
        containing at least one image for a given area
        date: the date (eg. "2024-12-01")
        area: the area of interest
        source: the data source to use
        Return the ImageCollection, or None if no images available
        """
        
        # Convert the area of interest to a ee.GeometryRectangle
        area_bounding = area.to_ee_rectangle()

        # Get the relevant image collection according to the data source
        if source == CordobaDataSource.SENTINEL2:
            dataset = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        elif source == CordobaDataSource.LANDSAT8:
            dataset = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        elif source == CordobaDataSource.LANDSAT5:
            dataset = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
        elif source == CordobaDataSource.DYNAMIC_WORLD:
            dataset = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
        else:
            return None, None

        # Filter the image collection over the area of interest
        dataset = dataset.filterBounds(area_bounding)

        # Filter the image collection to reject images with too many clouds
        if source == CordobaDataSource.SENTINEL2:
            filter_cloud = \
                ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.max_cloud_coverage)
            dataset = dataset.filter(filter_cloud)
        elif source == CordobaDataSource.LANDSAT8:
            filter_cloud = \
                ee.Filter.lt('CLOUD_COVER', self.max_cloud_coverage)
            dataset = dataset.filter(filter_cloud)
        elif source == CordobaDataSource.LANDSAT5:
            filter_cloud = \
                ee.Filter.lt('CLOUD_COVER', self.max_cloud_coverage)
            dataset = dataset.filter(filter_cloud)
        elif source == CordobaDataSource.DYNAMIC_WORLD:
            pass
        else:
          return None, None

        # Loop to search a date range around the required date which includes
        # at least one image
        shift_day = self.step_search_image
        date_from = ee.Date(date).advance(-shift_day, "day")
        date_to = ee.Date(date).advance(shift_day, "day")
        dataset_range = dataset.filterDate(date_from, date_to)
        nb_try = 0
        
        while dataset_range.size().getInfo() == 0 and nb_try < self.nb_max_step_search:
            if self.flag_verbose:
                print(f"no image in {date_from.format('yyyy-MM-dd', 'UTC').getInfo()} - {date_to.format('yyyy-MM-dd', 'UTC').getInfo()} for {source}")
                sys.stdout.flush()
            shift_day += self.step_search_image
            date_from = ee.Date(date).advance(-shift_day, "day")
            date_to = ee.Date(date).advance(shift_day, "day")
            dataset_range = dataset.filterDate(date_from, date_to)
            nb_try += 1

        # If we've failed to find a date range, stop here
        if nb_try >= self.nb_max_step_search:
            return None, None

        # If the data ssource is not dynamic world
        if source != CordobaDataSource.DYNAMIC_WORLD:
            # Join the dynamic world image collection data
            dataset_dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
            dataset_dw = dataset_dw.filterBounds(area_bounding)
            dataset_dw = dataset_dw.filterDate(date_from, date_to)
        else:
            dataset_dw = None

        # Return the ImageCollection for the result date range
        return dataset_range, dataset_dw

    def get_ee_image(self, date: str, area: LongLatBBox, source: CordobaDataSource, 
                     preprocessed_indices: List[str] = None) -> ee.Image:
        """
        Get the satellite image for a given date and area.
        date: the date (eg. "2024-12-01")
        area: the area of interest
        source: the data source to use
        Return the a composite image of the area with preprocessing.
        """

        if self.flag_verbose:
            print("image acquisition...")
            sys.stdout.flush()

        # Search for the date range with available image
        dataset_range, dataset_dw = self.search_dataset_range(date, area, source)
        
        # If no image is available, stop here
        if dataset_range is None:
            return None, None

        # Convert the area of interest to a ee.GeometryRectangle
        area_bounding = area.to_ee_rectangle()

        # If the source is dynamic world, use the most frequent class over
        # images
        if source == CordobaDataSource.DYNAMIC_WORLD:
            if self.flag_verbose:
                print(f"mode composite of {dataset_range.size().getInfo()} images...")
                sys.stdout.flush()
            ee_image = dataset_range.mode().clip(area_bounding)

        # Else, composite all images into a single one using the median of all
        # values. To improve results use a mask to exclude clouds when
        # calculating the median.
        
        elif dataset_range.size().getInfo() > 1:
            if self.flag_verbose:
                print(f"median composite of {dataset_range.size().getInfo()} images...")
                sys.stdout.flush()
            if self.flag_cloud_filtering:
                if source == CordobaDataSource.SENTINEL2:
                    ee_image = dataset_range.map(mask_clouds_sentinel).median()
                elif source == CordobaDataSource.LANDSAT8:
                    ee_image = dataset_range.map(mask_clouds_landsat).median()
                elif source == CordobaDataSource.LANDSAT5:
                    ee_image = dataset_range.map(mask_clouds_landsat).median()
            else:
                ee_image = dataset_range.median().clip(area_bounding)
        else:
            ee_image = dataset_range.first().clip(area_bounding)

        if dataset_dw != None:
            if self.flag_verbose:
                print(f"mode composite of {dataset_range.size().getInfo()} dynamic world images...")
                sys.stdout.flush()
            ee_image_dw = dataset_dw.mode().clip(area_bounding)
            ee_image_dw = ee_image_dw.select(dynamic_world_bands)
        else:
            ee_image_dw = None
        
        
        # Image properties get lost through the composition, put them back
        # by using those of the first image in the collection
        # (not necessary, left for reference)
        ee_image.copyProperties(
            dataset_range.first(), dataset_range.first().propertyNames())

        
        # Rename the bands to have common names independently of the source
        ee_image = ee_image.select(self.get_bands_name(preprocessed_indices))

        # Return the ee.Image
        return ee_image, ee_image_dw


    def radiometric_registration(self, ee_image_ref: ee.Image, ee_image: ee.Image, area: LongLatBBox) -> ee.Image:
        """
        Apply radiometric registration to an image
        ee_image_ref: the reference image
        ee_image: the image to be registered
        area: the area of interest
        Return the result of registration. As described in
        https://developers.google.com/earth-engine/tutorials/community/pseudo-invariant-feature-matching
        """

        # Convert the area of interest to a ee.GeometryRectangle
        area_bounding = area.to_ee_rectangle()

        # Calculate the spectral distance according to "spectral angle mapper"
        # method and all bands
        spectral_distance = ee_image_ref.spectralDistance(ee_image, "sid")
        
        # Get the threshold to select pixels with low spectral distance
        threshold = spectral_distance.reduceRegion(
            reducer=ee.Reducer.percentile([10]),
            geometry=area_bounding,
            scale=1,
            bestEffort=True,
            maxPixels=1e6,
        ).getNumber("distance")

        # Create a mask of pixels with low spectral distance
        pseudo_invariant_feature_mask = spectral_distance.lt(threshold)

        # For each relevant band in the image
        bands_name = self.get_bands_name()[:4]
        for band_name in bands_name:

            # Calculate a linear transformation for mapping the pseudo
            # invariant features
            from_data = \
                ee_image_ref.select([band_name]) \
                    .updateMask(pseudo_invariant_feature_mask)
            to_data = \
                ee_image.select([band_name]) \
                    .updateMask(pseudo_invariant_feature_mask)
            coeffs = \
                ee.Image.cat([to_data, from_data]).reduceRegion(
                    reducer=ee.Reducer.linearFit(),
                    geometry=area_bounding,
                    scale=1,
                    maxPixels=1e6,
                    bestEffort=True)

            # Apply the transformation to the registered image
            registered_band = ee_image \
              .select([band_name]) \
              .multiply(coeffs.getNumber('scale')) \
              .add(coeffs.getNumber('offset')) \
              .rename([band_name])

            # Replace the band data with the registered data
            ee_image = \
                ee_image.addBands(registered_band, [band_name], overwrite=True)

        # Return the registered image
        return ee_image


    def get_dummy_image(self, date: str, area: LongLatBBox) -> CordobaImage:
        """
        Create a dummy CordobaImage for a given area
        date: acquisition date (eg. "2024-11-01")
        area: the area of interest
        Return a CordobaImage with all values for all bands set to zero.
        Dimensions of the image approximately match those of the one that
        would have been retrieved from GEE
        """
        utm_codes = query_utm_crs_info(datum_name="WGS84", 
                                       area_of_interest=AreaOfInterest(area.long_from, 
                                                                       area.lat_from, 
                                                                       area.long_to, 
                                                                       area.lat_to))
        
        # Get the UTM zone
        utm_zone = utm_codes[0].code

        x_min, y_min = pyproj.transform('epsg:4326', 
                                        f'epsg:{utm_zone}',
                                        area.long_from, 
                                        area.lat_from)
        
        x_max, y_max = pyproj.transform('epsg:4326',
                                        'epsg:{utm_zone}',
                                        area.long_to, 
                                        area.lat_to)
        
        # Get the width and height of the image
        width = int((x_max - x_min) / self.resolution)
        height = int((y_max - y_min) / self.resolution)
        image = CordobaImage(date, area, self.resolution, width, height)
        band_names = self.get_bands_name(True)
        image.source = self.data_source

        for band_name in band_names:
            image.bands[band_name] = numpy.zeros((height, width))
        return image

    def get_ee_image_registered(self, date: str, area: LongLatBBox, ee_image_ref: ee.Image) -> ee.Image:
            """
            Get the satellite image for a given date and area and register it
            against a reference image.
            date: date (e.g. "2024-11-01")
            area: the area of interest
            ee_image_ref: reference image, if None then no registration occurs
            Return the registered image and its source.
            """

            # Variable to memorise the actual source of the image (may vary when
            # in auto mode)
            actual_source = self.data_source

            # Get the ee image according to the source
            # If the source is AUTO, try the sources in order of priority until
            # we find an image
            if self.data_source == CordobaDataSource.AUTO:
                ee_image = None
                sources = [CordobaDataSource.SENTINEL2, CordobaDataSource.LANDSAT8, CordobaDataSource.LANDSAT5]
                idx_source = 0
                while ee_image is None and idx_source < len(sources):
                    ee_image, ee_image_dw = \
                        self.get_ee_image(date, area, sources[idx_source])
                    if ee_image is not None:
                        actual_source = sources[idx_source]
                        print(f"data source: {sources[idx_source]}")
                    idx_source += 1
            else:
                print(f"data source: {self.data_source}")
                ee_image, ee_image_dw = \
                    self.get_ee_image(date, area, self.data_source)

            # If we could get the image and there is a reference image
            if ee_image is not None and ee_image_ref is not None:

                # Geometric registration
                if self.flag_verbose:
                    print("geometric registration...")
                    sys.stdout.flush()
                ee_image = ee_image.register(
                    referenceImage=ee_image_ref,
                    maxOffset=50.0,
                    patchWidth=100.0)

                # Radiometric registration
                """
                if self.flag_verbose:
                    print("radiometric registration...")
                    sys.stdout.flush()
                ee_image = \
                    self.radiometric_registration(ee_image_ref, ee_image, area)
                """

            # Return the image
            return ee_image, actual_source, ee_image_dw


    def get_satellite_data(self, dates: List[str], area: LongLatBBox, 
                        preprocessed_indices: List[str] = None) -> List[CordobaImage]:
        """
        Get the satellite images for an area and a list of dates
        dates: list of dates (eg. ["2024-11-01", "2024-12-01"])
        area: the area of interest
        preprocessed_indices: list of additional processed bands to include
        Return the available images fully covering the area of interest for
        each date.
        """
        # Array of result CordobaImage
        images = []

        # If in offline mode
        if self.online is False:
            # Create a dummy image instead of retrieving data from GEE
            for date in dates:
                image = self.get_dummy_image(date, area)
                images.append(image)

        # Else, we are in online normal mode
        else:
            # Reference image for registration (initially none)
            ee_image_ref = None

            # Loop on the requested dates
            for _, date in enumerate(dates):

                # Get the ee image for the date
                ee_image, actual_source, ee_image_dw = \
                    self.get_ee_image_registered(date, area, ee_image_ref)

                # If we could get the ee.Image
                if ee_image is not None:
                    # If we have no reference image yet
                    if ee_image_ref is None:
                        # Set the current image as the reference one
                        ee_image_ref = ee_image

                    # Apply the remote preprocessing
                    if self.flag_verbose:
                        print("remote preprocessing...")
                        sys.stdout.flush()

                    # Convert the ee.image into a CordobaImage
                    if self.flag_verbose:
                        print("converting to CordobaImage...")
                        sys.stdout.flush()
                    try:
                        image = self.cvt_ee_image_to_cordoba_image(
                            date, ee_image, area, ee_image_dw, preprocessed_indices)
                    
                    except ValueError as e:
                        print(f"Error converting ee.Image to CordobaImage: {e}")
                        image = self.get_dummy_image(date, area)

                    if preprocessed_indices is not None:
                        index_functions = {
                            "ndvi": self.preprocess_ndvi,
                            "ndbi": self.preprocess_ndbi,
                            "evi": self.preprocess_evi,
                            "ndmi": self.preprocess_ndmi,
                            "nbr": self.preprocess_nbr,
                            "savi": self.preprocess_savi,
                            "ndwi": self.preprocess_ndwi
                        }

                        # If preprocessed_indices is None, process all predefined indices
                        
                        preprocessed_indices = list(index_functions.keys())

                        # Process each index in the preprocessed_indices list
                        for index in preprocessed_indices:
                            if index in index_functions:
                                processed_image = index_functions[index](ee_image)
                                image.bands[index] = processed_image

                    # If we couldn't get the image, use a dummy one instead
                    if image is None:
                        image = self.get_dummy_image(date, area)

                    # Add the image to the list of result images
                    image.source = actual_source
                    images.append(image)

                # else we couldn't get the ee.Image
                else:
                    image = self.get_dummy_image(date, area)
                    image.source = actual_source
                    images.append(image)

        # Return the images
        return images

    # def get_ee_bands_name(self, source: CordobaDataSource, include_processed: bool) -> List[str]:
    #     """
    #     Return the list of relevant bands name in the ee.Image according to the
    #     current data source.
    #     source: the data source
    #     include_processed: if true, include the processed bands
    #     """
    #     bands = []
    #     if source == CordobaDataSource.SENTINEL2:
    #         bands = ["B4", "B3", "B2", "B8", "B11", "ndvi", "ndbi", "evi", "ndmi", "nbr", "savi", "ndwi"]
    #     elif source == CordobaDataSource.LANDSAT8:
    #         bands = ["SR_B4", "SR_B3", "SR_B2", "SR_B5", "SR_B6", "ndvi", "ndbi", "evi", "ndmi", "nbr", "savi", "ndwi"]
    #     elif source == CordobaDataSource.LANDSAT5:
    #         # No swir band, used the nir band instead
    #         bands = ["SR_B3", "SR_B2", "SR_B1", "SR_B4", "SR_B4", "ndvi", "ndbi", "evi", "ndmi", "nbr", "savi", "ndwi"]
    #     elif source == CordobaDataSource.DYNAMIC_WORLD:
    #         bands = dynamic_world_bands
    #     if include_processed:
    #         return bands
    #     else:
    #         if source == CordobaDataSource.DYNAMIC_WORLD:
    #             return bands
    #         else:
    #             return bands[:5]

    def get_bands_name(self, source: CordobaDataSource = None, 
                       include_processed: List[str] = None) -> List[str]:
        """
        Return the list of relevant bands name according to the data source.
        source: the data source (if None, use self.data_source)
        include_processed: list of additional processed bands to include
        """
        if source is None:
            source = self.data_source

        if source == CordobaDataSource.SENTINEL2:
            bands = ["B4", "B3", "B2", "B8", "B11"]
        elif source == CordobaDataSource.LANDSAT8:
            bands = ["SR_B4", "SR_B3", "SR_B2", "SR_B5", "SR_B6"]
        elif source == CordobaDataSource.LANDSAT5:
            bands = ["SR_B3", "SR_B2", "SR_B1", "SR_B4", "SR_B4"]
        elif source == CordobaDataSource.DYNAMIC_WORLD:
            bands = dynamic_world_bands
        else:
            bands = []

        if include_processed and source != CordobaDataSource.DYNAMIC_WORLD:
            bands += include_processed

        return bands


    def download_numpy_data(self, ee_image: ee.Image, area: LongLatBBox, bands_name: List[str], chunk_size: int = 128) -> numpy.ndarray:
        """
        Download the image data as numpy array in chunks of a predefined size.
        eeImage: the image to convert
        area: the requested area as a LongLatBBox
        bands_name: list of band names to download
        chunk_size: size of the chunks to download (default is 128)
        Return the image data as numpy array for the requested area
        """
        # Get the coordinates of the area
        area = area.to_ee_rectangle()
        coords = area.coordinates().getInfo()[0]
        long_from, lat_from = coords[0]
        long_to, lat_to = coords[2]

        # Get crs from longlat
        utm_codes = query_utm_crs_info(datum_name="WGS84",
                                        area_of_interest=AreaOfInterest(long_from,
                                                                        lat_from,
                                                                        long_to,
                                                                        lat_to))
        # Get the UTM zone
        utm_zone = utm_codes[0].code

        ## Convert to UTM
        geotransform = pyproj.Transformer.from_proj("epsg:4326", f"epsg:{utm_zone}", always_xy=True)
        x_min, y_min = geotransform.transform(long_from, lat_from)
        x_max, y_max = geotransform.transform(long_to, lat_to)

        # Get the dimensions of the area in pixels
        width = int((x_max - x_min) / self.resolution)
        height = int((y_max - y_min) / self.resolution)

        # Calculate the number of chunks needed
        num_chunks_x = (width + chunk_size - 1) // chunk_size
        num_chunks_y = (height + chunk_size - 1) // chunk_size

        # Initialize an empty array to store the image data
        data_bands = numpy.zeros((height, width, len(bands_name)), dtype=numpy.float32)

        for i in range(num_chunks_x):
            for j in range(num_chunks_y):
                # Calculate the coordinates of the current chunk in UTM
                x_min_chunk = x_min + i * chunk_size * self.resolution
                x_max_chunk = min(x_min + (i + 1) * chunk_size * self.resolution, x_max)
                y_min_chunk = y_min + j * chunk_size * self.resolution
                y_max_chunk = min(y_min + (j + 1) * chunk_size * self.resolution, y_max)

                # Convert the chunk coordinates back to lat/lon
                long_min_chunk, lat_min_chunk = geotransform.transform(x_min_chunk, y_min_chunk, direction="INVERSE")
                long_max_chunk, lat_max_chunk = geotransform.transform(x_max_chunk, y_max_chunk, direction="INVERSE")

                # Create a rectangle for the current chunk
                chunk_area = ee.Geometry.Rectangle([long_min_chunk, lat_min_chunk, long_max_chunk, lat_max_chunk])

                if self.flag_verbose:
                    print(f"Downloading chunk ({i}, {j})...")

                try:
                    # Download the data for the current chunk
                    url = ee_image.getDownloadUrl({
                        'bands': bands_name,
                        'region': chunk_area,
                        'format': 'NPY',
                        'crs': f"EPSG:{utm_zone}",
                        'scale': self.resolution
                    })
                    response = requests.get(url)
                    chunk_data = numpy.load(io.BytesIO(response.content))

                    # Convert the structured array to a regular numpy array
                    chunk_data = numpy.array([chunk_data[band] for band in bands_name]).transpose(1, 2, 0)

                    # Calculate the indices of the current chunk in the full image
                    x_start = i * chunk_size
                    x_end = x_start + chunk_data.shape[1]
                    y_start = j * chunk_size
                    y_end = y_start + chunk_data.shape[0]

                    # Adjust the dimensions of the chunk data if necessary
                    x_end = min(x_end, width)
                    y_end = min(y_end, height)
                    chunk_data = chunk_data[:y_end - y_start, :x_end - x_start, :]

                    # Store the chunk data in the full image array
                    data_bands[y_start:y_end, x_start:x_end, :] = chunk_data

                except Exception as exc:
                    if self.flag_verbose:
                        print(f"Image data download failed for chunk ({i}, {j})...\n{exc}")
                    return None

        if self.flag_verbose:
            print(f"Downloaded data shape: {data_bands.shape}")

        return data_bands


    def cvt_ee_image_to_cordoba_image(self,
        date: str, ee_image: ee.Image, 
        area: LongLatBBox, ee_image_dw: ee.Image,
        preprocessed_indices: List[str] = None) -> CordobaImage:
        """
        Convert an ee.Image to a CordobaImage
        date: date of the image (eg. "2024-11-01")
        eeImage: the image to convert
        area: the requested area as a LongLatBBox
        Return a CordobaImage
        """

        # Convert the area of interest to a ee.GeometryRectangle
        # area_bounding = area.to_ee_rectangle()

        # Try to get the acquisition date
        try:
            acquisition_date = \
                ee_image.date().format("yyyy-MM-dd", "UTC").getInfo()
        except:
            # If the acquisition date is not available, use the required
            # date instead
            acquisition_date = date
        
        # Convert the bands data to a numpy array
        bands_name = self.get_bands_name(include_processed=preprocessed_indices)
        data_bands = self.download_numpy_data(ee_image, area, bands_name)

        # If there dynamic world data, download them
        if ee_image_dw is not None:
            data_dw = self.download_numpy_data(ee_image_dw, area, dynamic_world_bands)

        # Get the dimensions of the image
        nb_col = data_bands.shape[1]
        nb_row = data_bands.shape[0]

        # Create the CordobaImage
        image = CordobaImage(acquisition_date, area, self.resolution, nb_col, nb_row)

        # Split the numpy array per band
        for band_idx, band_name in enumerate(bands_name):
            image.bands[band_name] = data_bands[:, :, band_idx]

        # If the image is a satellite image
        if self.data_source != CordobaDataSource.DYNAMIC_WORLD:
            # # Set the mean ndvi of the image
            # if self.flag_verbose:
            #     print("compute mean ndvi...")
            #     sys.stdout.flush()
            # On large image, requesting the mean ndvi on server side is too
            # heavy.
            # Do it locally instead.
            # image.mean_ndvi = self.get_mean_ndvi(ee_image, area_bounding)
            # image.mean_ndvi = image.get_mean_ndvi()
            # if self.flag_verbose:
            #     print(f"mean ndvi: {image.mean_ndvi}")
            #     sys.stdout.flush()

            # # Apply dark object correction
            # if self.flag_verbose:
            #     print("dark object correction...")
            #     sys.stdout.flush()
            # image.dark_object_correction()

            # If we also have dynamic world data
            # If there dynamic world data, add them to the image
            if ee_image_dw is not None:
                for band_idx, band_name in enumerate(dynamic_world_bands):
                    image.bands[band_name] = data_dw[:, :, band_idx]

        return image
          
    def preprocess_ndvi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndvi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("NDVI...")
            sys.stdout.flush()

        # Calculate the NDVI values
        bands = {"nir": image.select("B8"), "red": image.select("B4")}
        ndvi = image.expression("(nir - red) / (nir + red)", bands).rename("ndvi")

        # Add the NDVI values to the image as a new band
        return image.addBands(ndvi)


    def preprocess_ndmi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndmi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("NDMI...")
            sys.stdout.flush()

        # Calculate the NDMI values
        bands = {"nir": image.select("B8"), "swir": image.select("B11")}
        ndmi = image.expression("(nir - swir) / (nir + swir)", bands).rename("ndmi")

        # Add the NDMI values to the image as a new band
        return image.addBands(ndmi)


    def preprocess_ndbi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndbi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("NDBI...")
            sys.stdout.flush()

        # Calculate the NDBI values
        bands = {"nir": image.select("B8"), "swir": image.select("B11")}
        ndbi = image.expression("(swir - nir) / (swir + nir)", bands).rename("ndbi")

        # Add the NDBI values to the image as a new band
        return image.addBands(ndbi)


    def preprocess_evi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'evi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("EVI...")
            sys.stdout.flush()

        # Calculate the EVI values
        bands = {"nir": image.select("B8"), "red": image.select("B4"), "blue": image.select("B2")}
        evi = image.expression(
            "2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0)",
            bands).rename("evi")

        # Add the EVI values to the image as a new band
        return image.addBands(evi)


    def preprocess_savi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'savi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("SAVI...")
            sys.stdout.flush()

        # Calculate the SAVI values
        bands = {"nir": image.select("B8"), "red": image.select("B4")}
        savi = image.expression(
            "1.5 * (nir - red) / (nir + red + 0.5)", bands).rename("savi")

        # Add the SAVI values to the image as a new band
        return image.addBands(savi)


    def preprocess_nbr(self, image: ee.Image) -> ee.Image:
        """
        Add a 'nbr' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("NBR...")
            sys.stdout.flush()

        # Calculate the NBR values
        bands = {"nir": image.select("B8"), "swir": image.select("B11")}
        nbr = image.expression("(nir - swir) / (nir + swir)", bands).rename("nbr")

        # Add the NBR values to the image as a new band
        return image.addBands(nbr)


    def preprocess_ndwi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndwi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        if self.flag_verbose:
            print("NDWI...")
            sys.stdout.flush()

        # Calculate the NDWI values
        bands = {"green": image.select("B3"), "nir": image.select("B8")}
        ndwi = image.expression("(green - nir) / (green + nir)", bands).rename("ndwi")

        # Add the NDWI values to the image as a new band
        return image.addBands(ndwi)
    
    def preprocess_gaussian_blur(self, image: ee.Image) -> ee.Image:
        """
        Add a gaussian blur to the ee.Image
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        # If there is no blurring apply, simply return the image
        if self.gaussian_blur["radius"] == 0:
            return image

        # Create burring gaussian kernel
        if self.flag_verbose:
            print(f"gaussian blur ({self.gaussian_blur['radius']}, {self.gaussian_blur['sigma']})...")
            sys.stdout.flush()
        kernel = ee.Kernel.gaussian(
          radius=self.gaussian_blur["radius"],
          sigma=self.gaussian_blur["sigma"], 
          units='pixels')

        # Apply the kernel to relevant bands and return the result
        relevant_bands = self.get_bands_name(False)
        return image.select(relevant_bands, relevant_bands).convolve(kernel)
    
    
    def get_best_acquisition_dates(self, date_from: str, date_to: str, 
                                   area: LongLatBBox, min_interval: int) -> List[str]:
        """
        Search for the best acquisition dates within a period.
        date_from, date_to: date as "YYYY-MM-DD" defining the range of search
        area: area of interest
        min_interval: minimum number of days separating two dates
        Return an array of suggested dates to acquire data, such as if it's
        used as argument of get_satellite_data it is guaranteed there will be
        at least one image available per date and there will be as many dates as
        possible (unless there are no image available at all in the requested
        range)
        """

        # To avoid infinite loop below if inputs are wrong
        if date_from > date_to or min_interval <= 0:
            return [date_from]

        # Create the list of candidates
        candidate_dates = []
        d = date_from
        while d <= date_to:
            candidate_dates += [d]
            d = \
                datetime.datetime.strptime(d, "%Y-%m-%d") + \
                datetime.timedelta(days=min_interval)
            d = d.strftime("%Y-%m-%d")

        # Variable to memorise the best dates
        best_dates = []

        # If in online mode
        if self.online is True:

            # Loop on the candidates
            for candidate_date in candidate_dates:

                # Check if there are data for this candidate date in any of
                # the data source
                sources = [CordobaDataSource.SENTINEL2, CordobaDataSource.LANDSAT8, CordobaDataSource.LANDSAT5]
                idx_source = 0
                dataset_range = None
                while dataset_range is None and idx_source < len(sources):
                    dataset_range = self.search_dataset_range(candidate_date, area, sources[idx_source])
                    idx_source += 1

                # If there was no data available for this range
                if dataset_range is None:
                    if self.flag_verbose:
                        print(f"{candidate_date} NG")
                        sys.stdout.flush()

                # Else this candidate is ok, add it to the result
                else:
                    if self.flag_verbose:
                        print(f"{candidate_date} OK")
                        sys.stdout.flush()
                    best_dates += [candidate_date]
        
        # Else, in offline mode we can't check so we return the
        # the candidates by default
        else:
            best_dates = candidate_dates

        # Return the dates
        return best_dates
