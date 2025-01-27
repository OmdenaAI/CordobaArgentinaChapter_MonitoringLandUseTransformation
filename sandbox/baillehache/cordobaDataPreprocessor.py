from typing import List
from enum import Enum
import numpy
# Install the Earth Engine Python API with
# pip install earthengine-api
import ee
import requests
import io
import sys

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

    def toGreyScale(self, band) -> numpy.array:
        """
        Convert a CordobaImage into a numpy array
        band: the band to use
        Return the numpy array.
        Pixel values in [0,255]. Values normalised.
        """
        
        # Get the max value for normalisation
        max_val = self.bands[band].max()

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

    def toNDVI(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDVI array
        Return the NDVI as a numpy array.
        Pixel values in [0,255], 3 channels. NDVI band normalised.
        """
        return self.toGreyScale("ndvi")

    def toNDBI(self) -> numpy.array:
        """
        Convert a CordobaImage into a NDBI array
        Return the NDVI as a numpy array.
        Pixel values in [0,255], 3 channels. NDBI band normalised.
        """
        return self.toGreyScale("ndbi")

    def toEVI(self) -> numpy.array:
        """
        Convert a CordobaImage into a EVI array
        Return the EVI as a numpy array.
        Pixel values in [0,255], 3 channels. EVI band normalised.
        """
        return self.toGreyScale("evi")

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

    def addNdvi(self):
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
def mask_clouds(image: ee.Image) -> ee.Image:
    qa = image.select('QA60')
    cloud_bit_mask = 1 << 10  # Bit 10 represents clouds
    cirrus_bit_mask = 1 << 11  # Bit 11 represents cirrus clouds
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    return image.updateMask(mask)


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

        # Gaussian blur parameters (if radius==0, no blur)
        self.gaussian_blur = {"radius": 3, "sigma": 0.5}

        # Step (in days) when searching an image around a given date
        self.step_search_image = 5

        # Minimum number of images to be used for the median composite (used to
        # reduce artefacts in image by compositing several ones around the
        # requested date)
        self.nb_median_composite = 5

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

    def get_ee_image(self, date: str, area_bounding: ee.Geometry.Rectangle) -> ee.Image:
        """
        Get the satellite image for a given date and area.
        date: the date (eg. "2024-12-01")
        area_bnding: the area of interest
        Return the available ee.Image fully covering the area of interest
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
          return None

        # Filter the image collection over the area of interest
        dataset = dataset.filterBounds(area_bounding)

        # Filter the image collection to reject images with too many clouds
        if self.data_source == CordobaDataSource.SENTINEL2:
            filter_cloud = \
                ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.max_cloud_coverage)
        elif self.data_source == CordobaDataSource.LANDSAT8:
            filter_cloud = \
                ee.Filter.lt('CLOUD_COVER', self.max_cloud_coverage)
        elif self.data_source == CordobaDataSource.LANDSAT5:
            filter_cloud = \
                ee.Filter.lt('CLOUD_COVER', self.max_cloud_coverage)
        else:
          return None
        dataset = dataset.filter(filter_cloud)

        # Loop to search a date range around the required date which includes
        # at least one image
        if self.flag_verbose:
            print("image acquisition...")
            sys.stdout.flush()

        shift_day = 1
        date_from = ee.Date(date).advance(-shift_day, "day");
        date_to = ee.Date(date).advance(shift_day, "day");
        dataset_range = dataset.filterDate(date_from, date_to)
        nb_try = 0
        nb_max_try = 5
        while dataset_range.size().getInfo() < self.nb_median_composite and nb_try < nb_max_try:
            if self.flag_verbose:
                print(f"no image in {date_from.format('yyyy-MM-dd', 'UTC').getInfo()} - {date_to.format('yyyy-MM-dd', 'UTC').getInfo()}")
                sys.stdout.flush()

            shift_day += self.step_search_image
            date_from = ee.Date(date).advance(-shift_day, "day");
            date_to = ee.Date(date).advance(shift_day, "day");
            dataset_range = dataset.filterDate(date_from, date_to)
            nb_try += 1
        if nb_try >= nb_max_try:
            return None

        # Composite all images into a single one using the median of all values
        # (don't know why but the .clip() is necessary, else we get a
        # "Unable to compute bounds for geometry" in getDownloadUrl())
        # To improve results use a mask to exclude clouds when calculating
        # the median
        if self.flag_verbose:
            print(f"median composite of {dataset_range.size().getInfo()} images...")
            sys.stdout.flush()
        ee_image = dataset_range.map(mask_clouds).median().clip(area_bounding)
        
        # Image properties get lost through the composition, put them back
        # by using those of the first image in the collection
        # (not necessary, left for reference)
        ee_image.copyProperties(
            dataset_range.first(), dataset_range.first().propertyNames())

        # Apply the remote preprocessing
        if self.flag_verbose:
            print("remote preprocessing...")
            sys.stdout.flush()
        ee_image = self.preprocessGaussianBlur(ee_image)
        ee_image = self.preprocessNdvi(ee_image)
        ee_image = self.preprocessNdbi(ee_image)
        ee_image = self.preprocessEvi(ee_image)

        # Return the ee.Image
        return ee_image

    def get_image(self, date: str, area: LongLatBBox) -> CordobaImage:
        """
        Get the satellite image for a given date and area.
        date: the date (eg. "2024-12-01")
        area: the area of interest
        Return the available image fully covering the area of interest
        and nearest to the required date
        """

        # Get the ee.Image
        area_bounding = area.toEERectangle()
        ee_image = self.get_ee_image(date, area_bounding)
        if ee_image is None:
            if self.flag_verbose:
                print("couldn't get the ee.Image...")
                sys.stdout.flush()
            return None

        # Convert the first available image into a CordobaImage
        if self.flag_verbose:
            print("converting to CordobaImage...")
            sys.stdout.flush()
        image = self.cvtEEImageToCordobaImage(ee_image, area, area_bounding)
        
        # Add the locally preprocessed bands
        if self.flag_verbose:
            print("local preprocessing...")
            sys.stdout.flush()
        image.darkObjectCorrection()

        # Return the image
        return image

    def get_registered_images(self, dates: List[str], area: LongLatBBox) -> List[CordobaImage]:
        """
        Get the satellite image for a given date and area.
        dates: list of dates (eg. ["2024-11-01", "2024-12-01"])
        area: the area of interest
        Return the available images fully covering the area of interest
        and nearest to the required date, the second image is registered against
        the first one
        """

        # Array of result CordobaImage
        images = []

        # Convert the area of interest to a ee.GeometryRectangle
        area_bounding = area.toEERectangle()

        # Reference image for registration
        ee_image_ref = None

        # Loop on the requested date
        for i_date, date in enumerate(dates):
            ee_image = self.get_ee_image(date, area_bounding)
            image = None
            # If we could get the image
            if ee_image is not None:
                # If there is a reference image
                if ee_image_ref is not None:
                    if self.flag_verbose:
                        print("registering images...")
                        sys.stdout.flush()
                    # TODO parameter maxoffset
                    ee_image = ee_image.register(
                        referenceImage=ee_image_ref,
                        maxOffset=50.0,
                        patchWidth=100.0)
                # Else, we have no reference image yet
                else:
                    # Set the current image as the reference one
                    ee_image_ref = ee_image

                # Try to get the acquisition date
                try:
                    acquisition_date = \
                        ee_image.date().format("yyyy-MM-dd HH:mm", "UTC").getInfo()
                except:
                    # If the acquisition date is not available, use the required
                    # date instead
                    acquisition_date = date

                # Convert the ee.image into a CordobaImage
                if self.flag_verbose:
                    print("converting to CordobaImage...")
                    sys.stdout.flush()
                image = \
                    self.cvtEEImageToCordobaImage(
                        acquisition_date, ee_image, area, area_bounding)

            # If we could get a CordobaImage
            if image is not None:
                # Add the locally preprocessed bands
                if self.flag_verbose:
                    print("local preprocessing...")
                    sys.stdout.flush()
                image.darkObjectCorrection()

                # Add the image to the list of result images
                images.append(image)

        # Return the images
        return images

    def cvtEEImageToCordobaImage(self,
        date: str, ee_image: ee.Image, area: LongLatBBox,
        area_bounding: ee.Geometry.Rectangle) -> CordobaImage:
        """
        Convert an ee.Image to a CordobaImage
        date: date of the image (eg. "2024-11-01")
        eeImage: the image to convert
        area: the requested area as a LongLatBBox
        area_bounding: the requested area as a ee.Geometry.Rectangle
        Return a CordobaImage
        """
        
        # List of relevant bands ([[lbl_CordobaImage], [lbl_EE_Image]])
        if self.data_source == CordobaDataSource.SENTINEL2:
            relevant_bands = [
                ["red", "green", "blue", "nir", "ndvi", "ndbi", "evi"],
                ["B4", "B3", "B2", "B8", "ndvi", "ndbi", "evi"]
            ]
        elif self.data_source == CordobaDataSource.LANDSAT8:
            relevant_bands = [
                ["red", "green", "blue", "nir", "ndvi", "ndbi", "evi"],
                ["SR_B4", "SR_B3", "SR_B2", "SR_B5", "ndvi", "ndbi", "evi"]
            ]
        elif self.data_source == CordobaDataSource.LANDSAT5:
            relevant_bands = [
                ["red", "green", "blue", "nir", "ndvi", "ndbi", "evi"],
                ["SR_B3", "SR_B2", "SR_B1", "SR_B4", "ndvi", "ndbi", "evi"]
            ]
        else:
            return None

        # Select only the relevant bands and rename them
        select_ee_image = \
            ee_image.select(relevant_bands[1], relevant_bands[0])

        # Convert the bands data to a numpy array
        # (it's possible to also get GeoTIFF format here)
        # Apply a mercator projection to convert the data to a 2D array
        if self.flag_verbose:
            print("download...")
            sys.stdout.flush()
        try:
            url = select_ee_image.getDownloadUrl({
                'bands': relevant_bands[0],
                'region': area_bounding,
                'format': 'NPY',
                'crs': ee.Projection("EPSG:3395"),
                'scale': self.resolution
            })
            response = requests.get(url)
            data_bands = numpy.load(io.BytesIO(response.content))
        except:
            if self.flag_verbose:
                print("Image data download failed...")
                sys.stdout.flush()
            return None

        # Get the dimensions of the image
        nb_col = data_bands.shape[1]
        nb_row = data_bands.shape[0]

        # Create the CordobaImage
        image = CordobaImage(date, area, self.resolution, nb_col, nb_row)

        # Split the numpy array per band
        for band_idx in range(len(relevant_bands[0])):
            image.bands[relevant_bands[0][band_idx]] = \
                data_bands[:, :][relevant_bands[0][band_idx]]

        # Set the mean ndvi of the image
        image.mean_ndvi = self.get_mean_ndvi(ee_image, area_bounding)
        if self.flag_verbose:
            print(f"mean ndvi: {image.mean_ndvi}")
            sys.stdout.flush()

        # Return the result image
        return image
        
    def preprocessNdvi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndvi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        # Get the dictionary of needed bands according to the source
        if self.flag_verbose:
            print("NDVI...")
            sys.stdout.flush()
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

    def get_mean_ndvi(self, image: ee.Image, area_bounding: ee.Geometry.Rectangle) -> float:
        """
        Calculate the mean value of the 'ndvi' band of an ee.Image
        image: the image to be preprocessed
        area_bounding: the bounding area
        Return the value.
        """
        mean_ndvi = image.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=area_bounding).get('ndvi').getInfo()
        return mean_ndvi

    def preprocessNdbi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'ndbi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        # Get the dictionary of needed bands according to the source
        if self.flag_verbose:
            print("NDBI...")
            sys.stdout.flush()
        if self.data_source == CordobaDataSource.SENTINEL2:
            bands = {"NIR" : image.select("B8"), "SWIR" : image.select("B11")}
        elif self.data_source == CordobaDataSource.LANDSAT8:
            bands = {"NIR" : image.select("SR_B5"), "SWIR" : image.select("SR_B6")}
        elif self.data_source == CordobaDataSource.LANDSAT5:
            # No swir band
            return image
        else:
          return image

        # Calculate the NDBI values
        ndbi = \
            image.expression("(SWIR - NIR) / (SWIR + NIR)", bands).rename("ndbi")

        # Add the NDBI values to the image as a new band
        return image.addBands(ndbi)

    def preprocessEvi(self, image: ee.Image) -> ee.Image:
        """
        Add a 'evi' band to the ee.Image and calculate its value based
        on other bands
        image: the image to be preprocessed
        Return the preprocessed image.
        """
        # Get the dictionary of needed bands according to the source
        if self.flag_verbose:
            print("EVI...")
            sys.stdout.flush()
        if self.data_source == CordobaDataSource.SENTINEL2:
            bands = {
                "NIR" : image.select("B8"),
                "RED" : image.select("B4"),
                "BLUE" : image.select("B2")}
        elif self.data_source == CordobaDataSource.LANDSAT8:
            bands = {
                "NIR" : image.select("SR_B5"),
                "RED" : image.select("SR_B4"),
                "BLUE" : image.select("SR_B2")}
        elif self.data_source == CordobaDataSource.LANDSAT5:
            bands = {
                "NIR" : image.select("SR_B4"),
                "RED" : image.select("SR_B3"),
                "BLUE" : image.select("SR_B1")}
        else:
          return image

        # Calculate the EVI values
        evi = \
            image.expression(
            "2.5 * (NIR - RED) / (NIR + 6.0 * RED - 7.5 * BLUE + 1.0)",
            bands).rename("evi")

        # Add the EVI values to the image as a new band
        return image.addBands(evi)

    def preprocessGaussianBlur(self, image: ee.Image) -> ee.Image:
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
        if self.data_source == CordobaDataSource.SENTINEL2:
            relevant_bands = ["B4", "B3", "B2", "B8", "B11"]
        elif self.data_source == CordobaDataSource.LANDSAT8:
            relevant_bands = ["SR_B4", "SR_B3", "SR_B2", "SR_B5", "SR_B6"]
        elif self.data_source == CordobaDataSource.LANDSAT5:
            relevant_bands = ["SR_B3", "SR_B2", "SR_B1", "SR_B4"]
        else:
          return None
        return image.select(relevant_bands, relevant_bands).convolve(kernel)
