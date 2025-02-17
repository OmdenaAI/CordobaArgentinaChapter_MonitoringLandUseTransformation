from typing import List
from enum import Enum
import numpy
# Install the Earth Engine Python API with
# pip install earthengine-api
import ee
import requests
import io
import sys
import math
import datetime

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

    def __str__(self):
        """
        String representation
        """
        return str(self.name)

class LongLatBBox:
    """
    Longitude-latitude boudning box
    """
    def __init__(self,
        long_from: float, long_to: float,
        lat_from: float, lat_to: float):
        """
        Constructor for an instance of LongLatBox.
        long_from, long_to, lat_from, lat_to: the bounding longitudes and
        latitudes
        """
        self.long_from = long_from
        self.long_to = long_to
        self.lat_from = lat_from
        self.lat_to = lat_to

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
        return f"lo[{self.long_from},{self.long_to}],la[{self.lat_from},{self.lat_to}]"

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

        # Mean NDVI
        # NDVI is in [-1,1], the higher the more vegetation, 0 is considered as
        # no vegetation, <0 suggests water.
        # Can be used to filter out images without vegetation:
        # if self.mean_ndvi < 0.2: no vegetation
        self.mean_ndvi = 0.0

    def __str__(self):
        """
        String representation
        """
        return f"acquisition date: {self.date}, area: {self.area}, resolution: {self.resolution}m/px, width: {self.width}px, height: {self.height}px"

    def to_rgb(self, gamma=1.0) -> numpy.array:
        """
        Convert a CordobaImage into a RGB array
        Return the composite of red, green, blue bands as a numpy array.
        Pixel values in [0,255]. Red, gree, blue bands normalised.
        """
        
        # Get the max value over red, green, blue bands for normalisation
        max_val = max(self.bands["red"].max(), max(self.bands["green"].max(), self.bands["blue"].max()))
        if max_val == 0.0:
            max_val = 1.0

        # Create the result image
        image = numpy.zeros([self.height, self.width, 3], numpy.uint8)
        
        # Loop over the pixels
        for y in range(self.height):
            for x in range(self.width):

                # Composite the normalised bands
                image[y][x][0] = \
                  ((self.bands["red"][y][x] / max_val) ** gamma) * 255.0
                image[y][x][1] = \
                  ((self.bands["green"][y][x] / max_val) ** gamma) * 255.0
                image[y][x][2] = \
                  ((self.bands["blue"][y][x] / max_val) ** gamma) * 255.0

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

        # Create the result image
        image = numpy.zeros([self.height, self.width, 3], numpy.uint8)
        
        # Variable to memorise eventual exceptions
        raised_exc = None

        # Loop over the pixels
        for y in range(self.height):
            for x in range(self.width):
 
                # Convert the band value to a pixel value
                try:
                    pixel_value = int(self.bands[band][y][x] / max_val * 255.0)
                except Exception as exc:
                    raised_exc = exc
                    pixel_value = 0

                # Composite the normalised bands
                image[y][x][0] = pixel_value
                image[y][x][1] = image[y][x][0]
                image[y][x][2] = image[y][x][0]

        # Inform the user if there has been exception
        if raised_exc:
            print(f"Exception raised during conversion:\n{raised_exc}")

        # Return the result image
        return image

    def get_mean_ndvi(self) -> float:
        return numpy.mean(self.bands["ndvi"])

    def to_ndvi(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDVI array
        Return the NDVI as a numpy array.
        Pixel values in [0,255], 3 channels. NDVI band normalised.
        """
        return self.to_grey_scale("ndvi")

    def to_ndbi(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDBI array
        Return the NDVI as a numpy array.
        Pixel values in [0,255], 3 channels. NDBI band normalised.
        """
        return self.to_grey_scale("ndbi")

    def to_evi(self) -> numpy.array:
        """
        Convert a CordobaImage into a EVI array
        Return the EVI as a numpy array.
        Pixel values in [0,255], 3 channels. EVI band normalised.
        """
        return self.to_grey_scale("evi")

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

    def add_ndvi(self):
        """
        Add a 'ndvi' band to the Cordoba image and calculate its value based
        on other bands
        The image is updated.
        """

        # Add the new band
        self.bands["ndvi"] = \
            numpy.zeros([self.height, self.width], numpy.float32)

        # Variable to memorise eventual exceptions
        raised_exc = None

        # Loop on the pixels
        for y in range(self.height):
            for x in range(self.width):

                # Calculate the NDVI value
                try:
                    ndvi_value = \
                        (self.bands["nir"][y][x] - self.bands["red"][y][x]) / \
                        (self.bands["nir"][y][x] + self.bands["red"][y][x])
                except Exception as exc:
                    raised_exc = exc
                    ndvi_value = 0.0

                # Update the NDVI value
                self.bands["ndvi"][y][x] = ndvi_value

        # Inform the user if there has been exception
        if raised_exc:
            print(f"Exception raised during conversion:\n{raised_exc}")


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
            ee.Initialize(credentials)

        # Set the data source to automatic by default
        self.data_source = CordobaDataSource.AUTO

        # Set the threshold for the cloud coverage to 50% by default
        # (percentage of image pixels; in [0.0, 100.0])
        self.max_cloud_coverage = 50.0

        # Resolution of the returned image (in meter per pixel)
        self.resolution = 30.0

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
        else:
          return None

        # Filter the image collection over the area of interest
        dataset = dataset.filterBounds(area_bounding)

        # Filter the image collection to reject images with too many clouds
        if source == CordobaDataSource.SENTINEL2:
            filter_cloud = \
                ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.max_cloud_coverage)
        elif source == CordobaDataSource.LANDSAT8:
            filter_cloud = \
                ee.Filter.lt('CLOUD_COVER', self.max_cloud_coverage)
        elif source == CordobaDataSource.LANDSAT5:
            filter_cloud = \
                ee.Filter.lt('CLOUD_COVER', self.max_cloud_coverage)
        else:
          return None
        dataset = dataset.filter(filter_cloud)

        # Loop to search a date range around the required date which includes
        # at least one image
        shift_day = self.step_search_image
        date_from = ee.Date(date).advance(-shift_day, "day");
        date_to = ee.Date(date).advance(shift_day, "day");
        dataset_range = dataset.filterDate(date_from, date_to)
        nb_try = 0
        while dataset_range.size().getInfo() == 0 and nb_try < self.nb_max_step_search:
            if self.flag_verbose:
                print(f"no image in {date_from.format('yyyy-MM-dd', 'UTC').getInfo()} - {date_to.format('yyyy-MM-dd', 'UTC').getInfo()} for {source}")
                sys.stdout.flush()
            shift_day += self.step_search_image
            date_from = ee.Date(date).advance(-shift_day, "day");
            date_to = ee.Date(date).advance(shift_day, "day");
            dataset_range = dataset.filterDate(date_from, date_to)
            nb_try += 1

        # Return the ImageCollection for the result date range
        if nb_try >= self.nb_max_step_search:
            return None
        else:
            return dataset_range

    def get_ee_image(self, date: str, area: LongLatBBox, source: CordobaDataSource) -> ee.Image:
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
        dataset_range = self.search_dataset_range(date, area, source)
        
        # If no image is available, stop here
        if dataset_range is None:
            return None

        # Composite all images into a single one using the median of all values
        # (don't know why but the .clip() is necessary, else we get a
        # "Unable to compute bounds for geometry" in getDownloadUrl())
        # To improve results use a mask to exclude clouds when calculating
        # the median
        if dataset_range.size().getInfo() > 1:
            if self.flag_verbose:
                print(f"median composite of {dataset_range.size().getInfo()} images...")
                sys.stdout.flush()
            if self.flag_cloud_filtering:
                if source == CordobaDataSource.SENTINEL2:
                    ee_image = dataset_range.map(mask_clouds_sentinel).median().clip(area_bounding)
                elif source == CordobaDataSource.LANDSAT8:
                    ee_image = dataset_range.map(mask_clouds_landsat).median().clip(area_bounding)
                elif source == CordobaDataSource.LANDSAT5:
                    ee_image = dataset_range.map(mask_clouds_landsat).median().clip(area_bounding)
            else:
                ee_image = dataset_range.median().clip(area_bounding)
        else:
            ee_image = dataset_range.first().clip(area_bounding)
        
        # Image properties get lost through the composition, put them back
        # by using those of the first image in the collection
        # (not necessary, left for reference)
        ee_image.copyProperties(
            dataset_range.first(), dataset_range.first().propertyNames())

        # Rename the bands to have common names independently of the source
        ee_image = ee_image.select(
            self.get_ee_bands_name(source, False), self.get_bands_name(False))

        # Return the ee.Image
        return ee_image

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
        bands_name = self.get_ee_bands_name()[:4]
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
                ee_image = self.get_ee_image(date, area, sources[idx_source])
                if ee_image is not None:
                      actual_source = sources[idx_source]
                      print(f"data source: {sources[idx_source]}")
                idx_source += 1
        else:
            print(f"data source: {self.data_source}")
            ee_image = self.get_ee_image(date, area, self.data_source)

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
            #if self.flag_verbose:
            #    print("radiometric registration...")
            #    sys.stdout.flush()
            #ee_image = \
            #    self.radiometric_registration(ee_image_ref, ee_image, area)

        # Return the image
        return ee_image, actual_source

    def get_dummy_image(self, date: str, area: LongLatBBox) -> CordobaImage:
        """
        Create a dummy CordobaImage for a given area
        date: acquisition date (eg. "2024-11-01")
        area: the area of interest
        Return a CordobaImage with all values for all bands set to zero.
        Dimensions of the image approximately match those of the one that
        would have been retrieved from GEE
        """
        # One degree = 111111.1 meters (approx.)
        width = \
            int(111111.1 / self.resolution * \
            math.fabs(area.long_from - area.long_to))
        height = \
            int(111111.1 / self.resolution * \
            math.fabs(area.lat_from - area.lat_to))
        image = CordobaImage(date, area, self.resolution, width, height)
        band_names = self.get_bands_name(True)
        image.source = self.data_source
        for band_name in band_names:
            image.bands[band_name] = numpy.zeros((height, width))
        return image

    def get_satellite_data(self, dates: List[str], area: LongLatBBox) -> List[CordobaImage]:
        """
        Get the satellite images for an area and a list of dates
        dates: list of dates (eg. ["2024-11-01", "2024-12-01"])
        area: the area of interest
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
            for i_date, date in enumerate(dates):

                # Get the ee image for the date
                ee_image, actual_source = \
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
                    ee_image = self.preprocess_gaussian_blur(ee_image)
                    ee_image = self.preprocess_ndvi(ee_image)
                    ee_image = self.preprocess_ndbi(ee_image)
                    ee_image = self.preprocess_evi(ee_image)

                    # Convert the ee.image into a CordobaImage
                    if self.flag_verbose:
                        print("converting to CordobaImage...")
                        sys.stdout.flush()
                    image = \
                        self.cvt_ee_image_to_cordoba_image(date, ee_image, area)

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

    def get_ee_bands_name(self, source: CordobaDataSource, include_processed: bool) -> List[str]:
        """
        Return the list of relevant bands name in the ee.Image according to the
        current data source.
        source: the data source
        include_processed: if true, include the processed bands
        """
        bands = []
        if source == CordobaDataSource.SENTINEL2:
            bands = ["B4", "B3", "B2", "B8", "B11", "ndvi", "ndbi", "evi"]
        elif source == CordobaDataSource.LANDSAT8:
            bands = ["SR_B4", "SR_B3", "SR_B2", "SR_B5", "SR_B6", "ndvi", "ndbi", "evi"]
        elif source == CordobaDataSource.LANDSAT5:
            # No swir band, used the nir band instead
            bands = ["SR_B3", "SR_B2", "SR_B1", "SR_B4", "SR_B4", "ndvi", "ndbi", "evi"]
        if include_processed:
            return bands
        else:
            return bands[:5]

    def get_bands_name(self, include_processed: bool) -> List[str]:
        """
        Return the list of bands name.
        include_processed: if true, include the processed bands
        """
        bands = ["red", "green", "blue", "nir", "swir", "ndvi", "ndbi", "evi"]
        if include_processed:
            return bands
        else:
            return bands[:5]

    def download_numpy_data(self, ee_image: ee.Image, area: LongLatBBox) -> numpy.array:
        """
        Download the image data as numpy array. Recursively split the area
        if necessary to be able to download the data.
        eeImage: the image to convert
        area: the requested area as a LongLatBBox
        Return the image data as numpy array for the requested area
        """
        long_span = area.long_to - area.long_from
        lat_span = area.lat_to - area.lat_from
        threshold_angle = self.max_area_angle / 30.0 * self.resolution
        if long_span > threshold_angle:
            area_left = LongLatBBox(
                area.long_from, area.long_from + long_span / 2,
                area.lat_from, area.lat_to)
            area_right = LongLatBBox(
                area.long_from + long_span / 2, area.long_to,
                area.lat_from, area.lat_to)
            chunk_left = self.download_numpy_data(ee_image, area_left)
            chunk_right = self.download_numpy_data(ee_image, area_right)
            return numpy.hstack((chunk_left, chunk_right))
        elif lat_span > threshold_angle:
            area_up = LongLatBBox(
                area.long_from, area.long_to,
                area.lat_from + lat_span / 2, area.lat_to)
            area_down = LongLatBBox(
                area.long_from, area.long_to,
                area.lat_from, area.lat_from + lat_span / 2)
            chunk_up = self.download_numpy_data(ee_image, area_up)
            chunk_down = self.download_numpy_data(ee_image, area_down)
            return numpy.vstack((chunk_up, chunk_down))
        else:
            area_bounding = area.to_ee_rectangle()
            if self.flag_verbose:
                print(f"download...({area})")
                sys.stdout.flush()
            bands_name = self.get_bands_name(True)
            try:
                url = ee_image.getDownloadUrl({
                    'bands': bands_name,
                    'region': area_bounding,
                    'format': 'NPY',
                    'crs': ee.Projection("EPSG:3395"),
                    'scale': self.resolution
                })
                response = requests.get(url)
                data_bands = numpy.load(io.BytesIO(response.content))
            except Exception as exc:
                if self.flag_verbose:
                    print(f"Image data download failed...\n{exc}")
                    sys.stdout.flush()
                return None
            return data_bands

    def cvt_ee_image_to_cordoba_image(self,
        date: str, ee_image: ee.Image, area: LongLatBBox) -> CordobaImage:
        """
        Convert an ee.Image to a CordobaImage
        date: date of the image (eg. "2024-11-01")
        eeImage: the image to convert
        area: the requested area as a LongLatBBox
        Return a CordobaImage
        """

        # Convert the area of interest to a ee.GeometryRectangle
        area_bounding = area.to_ee_rectangle()

        # Try to get the acquisition date
        try:
            acquisition_date = \
                ee_image.date().format("yyyy-MM-dd-HH-mm", "UTC").getInfo()
        except:
            # If the acquisition date is not available, use the required
            # date instead
            acquisition_date = date
        
        # Convert the bands data to a numpy array
        # (it's possible to also get GeoTIFF format here)
        # Apply a mercator projection to convert the data to a 2D array
        data_bands = self.download_numpy_data(ee_image, area)

        # Get the dimensions of the image
        nb_col = data_bands.shape[1]
        nb_row = data_bands.shape[0]

        # Create the CordobaImage
        image = CordobaImage(acquisition_date, area, self.resolution, nb_col, nb_row)

        # Split the numpy array per band
        bands_name = self.get_bands_name(True)
        for band_idx in range(len(bands_name)):
            image.bands[bands_name[band_idx]] = \
                data_bands[:, :][bands_name[band_idx]]

        # Set the mean ndvi of the image
        if self.flag_verbose:
            print("compute mean ndvi...")
            sys.stdout.flush()
        # On large image, requesting the mean ndvi on server side is too heavy.
        # Do it locally instead.
        #image.mean_ndvi = self.get_mean_ndvi(ee_image, area_bounding)
        image.mean_ndvi = image.get_mean_ndvi()
        if self.flag_verbose:
            print(f"mean ndvi: {image.mean_ndvi}")
            sys.stdout.flush()

        # Apply dark object correction
        if self.flag_verbose:
            print("dark object correction...")
            sys.stdout.flush()
        image.dark_object_correction()

        # Return the result image
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
        bands = {"nir" : image.select("nir"), "red" : image.select("red")}
        ndvi = \
            image.expression("(nir - red) / (nir + red)", bands).rename("ndvi")

        # Add the NDVI values to the image as a new band
        return image.addBands(ndvi)

    def get_mean_ndvi(self, image: ee.Image, area_bounding: ee.Geometry.Rectangle) -> float:
        """
        Calculate the mean value of the 'ndvi' band of an ee.Image
        image: the image to be preprocessed
        area_bounding: the bounding area
        Return the value.
        """
        mean_ndvi = image.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=area_bounding).get('ndvi').getInfo()
        # Sometime returns None, don't know why, in doubt return 1.0
        if mean_ndvi is None:
            mean_ndvi = 1.0
        return mean_ndvi

    def preprocess_ndbi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndbi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """

        # Calculate the NDBI values
        bands = {"nir" : image.select("nir"), "swir" : image.select("swir")}
        ndbi = \
            image.expression("(swir - nir) / (swir + nir)", bands).rename("ndbi")

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
        bands = {"nir" : image.select("nir"), "red" : image.select("red"), "blue" : image.select("blue")}
        evi = \
            image.expression(
            "2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0)",
            bands).rename("evi")

        # Add the EVI values to the image as a new band
        return image.addBands(evi)

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

    def get_best_acquisition_dates(self, date_from: str, date_to: str, area: LongLatBBox, min_interval: int) -> List[str]:
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
