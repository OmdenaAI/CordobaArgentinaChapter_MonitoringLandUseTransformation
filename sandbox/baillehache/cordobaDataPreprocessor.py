from typing import List
from enum import Enum
import numpy
# Install the Earth Engine Python API with
# pip install earthengine-api
import ee

class CordobaDataSource(Enum):
    """
    Enumeration to identify the available image sources
    """
    # https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
    SENTINEL2 = 1
    # https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
    LANDSAT8 = 2
    # https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LT05_C02_T1_L2
    LANDSAT5 = 3


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

    def toEERectangle(self) -> ee.Geometry.Rectangle:
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

        # Contains image data per band, dictionay key is the band name
        self.bands = {}

    def __str__(self):
        """
        String representation
        """
        return f"acquisition date: {self.date}, area: {self.area}, resolution: {self.resolution}m/px, width: {self.width}px, height: {self.height}px"

    def toRGB(self, gamma=1.0) -> numpy.array:
        """
        Convert a CordobaImage into a RGB array
        Return the composite of red, green, blue bands as a numpy array.
        Pixel values in [0,255]. Red, gree, blue bands normalised.
        """
        
        # Get the max value over red, green, blue bands for normalisation
        max_val = max(self.bands["red"].max(), max(self.bands["green"].max(), self.bands["blue"].max()))

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

    def toNDVI(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDVI array
        Return the NDVI as a numpy array.
        Pixel values in [0,255]. NDVI band normalised.
        """
        
        # Get the max value over ndvi bands for normalisation
        max_val = self.bands["ndvi"].max()

        # Create the result image
        image = numpy.zeros([self.height, self.width, 3], numpy.uint8)
        
        # Variable to memorise eventual exceptions
        raised_exc = None

        # Loop over the pixels
        for y in range(self.height):
            for x in range(self.width):
 
                # Convert the band value to a pixel value
                try:
                    pixel_value = int(self.bands["ndvi"][y][x] / max_val * 255.0)
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

    def darkObjectCorrection(self):
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


class CordobaDataPreprocessor:
    """
    Class implementing tasks of the team 'data preprocessing and analysis'
    """

    def __init__(self):
        """
        Constructor for an instance of CordobaDataPreprocessor
        """
        # Authentication to Google Earth Engine API
        # This video was instructive regarding how to get the service
        # account and API key
        # https://www.youtube.com/watch?v=wHBUNDTvgtk
        # TODO: change to the credentials to those of the app
        service_account = "cordoba@ee-baillehachepascal.iam.gserviceaccount.com"
        credentials_path = "../../../earthengine_api_key.json"
        credentials = ee.ServiceAccountCredentials(
          service_account, credentials_path)
        ee.Initialize(credentials)

        # Set the data source to Sentinel-2 by default
        self.data_source = CordobaDataSource.SENTINEL2

        # Set the threshold for the cloud coverage to 25% by default
        # (percentage of image pixels; in [0.0, 100.0])
        self.max_cloud_coverage = 25.0

        # Resolution of the returned image (in meter per pixel)
        self.resolution = 30.0

        # Verbose mode
        self.flag_verbose = True

    def select_source(self, source: CordobaDataSource):
        """
        Select a data source for the images.
        source: the data source
        Update the source and related parameters (resolution)
        """
        self.data_source = source
        if source == CordobaDataSource.SENTINEL2:
            # TODO:
            # would like to use
            # self.resolution = 10.0
            # but it raises in cvtEEImageToCordobaImage
            # ee.ee_exception.EEException: Computed value is too large.
            self.resolution = 30.0
        elif source == CordobaDataSource.LANDSAT8:
            self.resolution = 30.0
        elif source == CordobaDataSource.LANDSAT5:
            self.resolution = 30.0

    def get_image(self, date: str, area: LongLatBBox) -> List[CordobaImage]:
        """
        Get the satellite image for a given date and area.
        date: the date (eg. "2024-12-01")
        area: the area of interest
        Return the available image fully covering the area of interest
        and nearest to the required date
        """

        # Get the relevant image collection according to the data source
        if self.data_source == CordobaDataSource.SENTINEL2:
          dataset = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        elif self.data_source == CordobaDataSource.LANDSAT8:
          dataset = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        elif self.data_source == CordobaDataSource.LANDSAT5:
          dataset = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
        else:
          return []

        # Filter the image collection over the area of interest
        area_bounding = area.toEERectangle()
        dataset = dataset.filterBounds(area_bounding)

        # Filter the image collection to reject images with too many clouds
        filter_cloud = \
            ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.max_cloud_coverage)
        dataset = dataset.filter(filter_cloud)

        # Loop to search a date range around the required date which includes
        # at least one image
        if self.flag_verbose:
            print("image acquisition...")
        shift_day = 1
        date_from = ee.Date(date).advance(-shift_day, "day");
        date_to = ee.Date(date).advance(shift_day, "day");
        dataset_range = dataset.filterDate(date_from, date_to)
        while dataset_range.size().getInfo() == 0:
            if self.flag_verbose:
                print(f"no image in {date_from.format('yyyy-MM-dd', 'UTC').getInfo()} - {date_to.format('yyyy-MM-dd', 'UTC').getInfo()}")
            shift_day += 5
            date_from = ee.Date(date).advance(-shift_day, "day");
            date_to = ee.Date(date).advance(shift_day, "day");
            dataset_range = dataset.filterDate(date_from, date_to)
        ee_image = dataset_range.first()

        # Add the remotely preprocessed bands
        if self.flag_verbose:
            print("remote preprocessing...")
        # Example placeholder (ndvi is calculated directly in GEE)
        ee_image = self.preprocessNdvi(ee_image)

        # Convert the first available image into a CordobaImage
        if self.flag_verbose:
            print("converting to CordobaImage...")
        image = self.cvtEEImageToCordobaImage(ee_image, area, area_bounding)
        
        # Add the locally preprocessed bands
        if self.flag_verbose:
            print("local preprocessing...")
        image.darkObjectCorrection()

        # Return the image
        return image

    def cvtEEImageToCordobaImage(self,
        ee_image: ee.Image, area: LongLatBBox,
        area_bounding: ee.Geometry.Rectangle) -> CordobaImage:
        """
        Convert an ee.Image to a CordobaImage
        eeImage: the image to convert
        area: the requested area as a LongLatBBox
        area_bounding: the requested area as a ee.Geometry.Rectangle
        Return a CordobaImage
        """
        
        # Get the acquisition date of the image
        date = ee_image.date().format("yyyy-MM-dd HH:mm", "UTC").getInfo()

        # The image returned from filterBounds() contains entire swaths,
        # clip it to get only the area of interest
        clipped_ee_image = ee_image.clip(area_bounding)

        # Create an ee.Image with all bands from the original image and two
        # new bands containing longitude and latitude information
        raw_data = ee.Image.pixelLonLat().addBands(clipped_ee_image)

        # Reduce the raw data at the required resolution
        raw_data = raw_data.reduceRegion(
          reducer = ee.Reducer.toList(),
          geometry = area_bounding,
          maxPixels = 1e8,
          scale = self.resolution)

        # List of relevant bands ([lbl_CordobaImage, lbl_EE_Image])
        if self.data_source == CordobaDataSource.SENTINEL2:
            relevant_bands = [
              ["latitude", "latitude"],
              ["longitude", "longitude"],
              ["red", "B4"],
              ["green", "B3"],
              ["blue", "B2"],
              ["nir", "B8"],
              ["ndvi", "ndvi"]
            ]
        elif self.data_source == CordobaDataSource.LANDSAT8:
            relevant_bands = [
              ["latitude", "latitude"],
              ["longitude", "longitude"],
              ["red", "SR_B4"],
              ["green", "SR_B3"],
              ["blue", "SR_B2"],
              ["nir", "SR_B5"],
              ["ndvi", "ndvi"]
            ]
        elif self.data_source == CordobaDataSource.LANDSAT5:
            relevant_bands = [
              ["latitude", "latitude"],
              ["longitude", "longitude"],
              ["red", "SR_B3"],
              ["green", "SR_B2"],
              ["blue", "SR_B1"],
              ["nir", "SR_B4"],
              ["ndvi", "ndvi"]
            ]
        else:
          return None

        # Extract each relevant band as a numpy array
        data_bands = {}
        for band_lbl in relevant_bands:
            data_bands[band_lbl[0]] = \
              numpy.array((ee.Array(raw_data.get(band_lbl[1])).getInfo()))

        # Get the list of unique latitude and longitude coordinates available
        unique_lats = numpy.unique(data_bands["latitude"])
        unique_lons = numpy.unique(data_bands["longitude"])

        # Get the range of latitude and longitude
        lat_min = unique_lats.min()
        lat_max = unique_lats.max()
        lon_min = unique_lons.min()
        lon_max = unique_lons.max()

        # Get the dimensions of the image
        nb_col = len(unique_lons)    
        nb_row = len(unique_lats)

        # Create the CordobaImage
        image = CordobaImage(date, area, self.resolution, nb_col, nb_row)

        # Initialise the result numpy array for each relevant band
        for band_lbl in relevant_bands:
            image.bands[band_lbl[0]] = \
                numpy.zeros([nb_row, nb_col], numpy.float32)
        
        # Loop on the data (all bands have same amount of data, use 'latitude'
        # to get the number of data point)
        for idx in range(len(data_bands["latitude"])):

            # Convert the (longitude, latitude) of the data to a (x,y) pixel
            # coordinate in the image
            x = nb_col - 1 - round(
              (lon_max - data_bands["longitude"][idx]) / (lon_max - lon_min) *
              (nb_col - 1))
            y = round(
              (lat_max - data_bands["latitude"][idx]) / (lat_max - lat_min) *
              (nb_row - 1))

            # Update the pixel value for each relevant band in the
            # numpy arrays
            for band_lbl in relevant_bands:
                # TODO
                # Different bands have different size array. Why ??
                if idx < data_bands[band_lbl[0]].shape[0]:
                    image.bands[band_lbl[0]][y][x] = data_bands[band_lbl[0]][idx]

        # Return the result image
        return image
        
    def preprocessNdvi(self, image: ee.Image):
        """
        Add a 'ndvi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        The image is updated.
        """
        # Get the dictionary of needed bands according to the source
        if self.data_source == CordobaDataSource.SENTINEL2:
            bands = {"NIR" : image.select("B8"), "RED" : image.select("B4")}
        elif self.data_source == CordobaDataSource.LANDSAT8:
            bands = {"NIR" : image.select("SR_B5"), "RED" : image.select("SR_B4")}
        elif self.data_source == CordobaDataSource.LANDSAT5:
            bands = {"NIR" : image.select("SR_B4"), "RED" : image.select("B3")}
        else:
          return image

        # Calculate the NDVI values
        ndvi = \
            image.expression("(NIR - RED) / (NIR + RED)", bands).rename("ndvi")

        # Add the NDVI values to the image as a new band
        return image.addBands(ndvi)

    def preprocessNdviLocal(self, image: CordobaImage):
        """
        Add a 'ndvi' band to the Cordoba image and calculate its value based
        on other bands
        image: the image to be preprocessed
        The image is updated.
        """

        # Add the new band
        image.bands["ndvi"] = \
            numpy.zeros([image.height, image.width], numpy.float32)

        # Variable to memorise eventual exceptions
        raised_exc = None

        # Loop on the pixels
        for y in range(image.height):
            for x in range(image.width):

                # Calculate the NDVI value
                try:
                    ndvi_value = \
                        (image.bands["nir"][y][x] - image.bands["red"][y][x]) / \
                        (image.bands["nir"][y][x] + image.bands["red"][y][x])
                except Exception as exc:
                    raised_exc = exc
                    ndvi_value = 0.0

                # Update the NDVI value
                image.bands["ndvi"][y][x] = ndvi_value

        # Inform the user if there has been exception
        if raised_exc:
            print(f"Exception raised during conversion:\n{raised_exc}")
