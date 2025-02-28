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

                # If we could get a CordobaImage, add it to the list of result
                # images
                if image is not None:
                    image.source = actual_source
                    images.append(image)

        # Return the images
        return images
