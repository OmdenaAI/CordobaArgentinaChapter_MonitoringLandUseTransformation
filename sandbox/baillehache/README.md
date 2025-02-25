# Detecting and Monitoring Land Use Transformation in Córdoba, Argentina Using Satellite Imagery

## Data preprocessing and analysis module

### Input

* Rectangular bounding box of longitude/latitude coordinates of the area of interest (AOI), as a LongLatBBox instance (cf below)
* Desired dates of data acquisition, as an array of string in "YYY-MM-DD" format

### Output

*  bands data of the AOI at each date (when available), as an array of CordobaImage instances (cf below)

### LongLatBBox

Class to manipulate rectangular bounding boxes of longitude/latitude coordinates.

Example of how to create a bounding box around Cordoba city:
```
area_cordoba_city = LongLatBBox(-64.3, -64.2, -31.4, -31.3)
```

### CordobaImage

Class to manipulate bands data of an AOI at a given date.

Available bands are: "red", "green", "blue", "nir", "swir", "ndvi", "ndbi", "evi", "ndmi"

Properties:
* `date`: approximate acquisition date (image data may be a composite of data acquired at several date), as a string in "YYYY-MM-DD" format
* `area`: bounding box of longitude/latitude coordinates, as a LongLatBBox
* `resolution`: resolution, in meter per pixel
* `width`, `height`: dimensions of the image
* `bands`: bands data as a dictionary of numpy 2D arrays, for example `image.bands['ndvi']` is a numpy 2D array containing the NDVI band raw data

Bands raw data need to be converted to be used by predicition models or as images. This can be done with one of the following methods:
```
image.to_rgb()
image.to_ndvi()
image.to_ndmi()
image.to_evi()
image.to_ndbi()
```
`image.to_rgb()` accepts and optional argument `gamma` for gamma correction. Each method returns numpy arrays of normalised value in [0,255] as `numy.uint8` and shape (height, width, 3).

Example of conversion to an image for display or saving to image file as follow:
```
rgb = images[i_image].to_rgb()
path = "path/to/img/file"
Image.fromarray(rgb).save(path)
```

Example of usage with the FCCDN model:
```
pre = images[0].to_rgb()
pre = cv2.resize(pre, (1024, 1024)) 
post = images[1].to_rgb()
post = cv2.resize(post, (1024, 1024)) 
pre = normalize(torch.Tensor(pre.transpose(2, 0, 1) / 255))[None].cpu()
post = normalize(torch.Tensor(post.transpose(2, 0, 1) / 255))[None].cpu()
pred = model([pre, post])
```

### CordobaDataPreprocessor

Class implementing the data preprocessing.

Create an instance as follow:
```
preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path)
```

`gee_account` and `gee_credential_path` are the connection information to the Google Earth Engine API. One can refer to this video regarding how to get the service account and API key: https://www.youtube.com/watch?v=wHBUNDTvgtk

The instance can be created in 'offline' mode, in which case there is no interaction with GEE and empty images are returned instead. This is useful when testing, to avoid the slow interaction with GEE.
```
preprocessor = CordobaDataPreprocessor(gee_account, gee_credentials_path, online=False)
```
`gee_account` and `gee_credential_path` are actually ignored in 'offline' mode.

Several parameters control how the data are retrieved.
* `preprocessor.data_source`: one of `CordobaDataSource.SENTINEL2`, `CordobaDataSource.LANDSAT8`, `CordobaDataSource.LANDSAT5`, `CordobaDataSource.AUTO`. Select the data source for data retrieval. If `AUTO`, try `SENTINEL2`, then if no data available, try `LANDSAT8` then if no data available try `LANDSAT5`. Default is `AUTO`.
* `preprocessor.max_cloud_coverage`: percentage in [0,100], maximum cloud coverage allowed in an image, if higher cloud coverage the image is discarded. Default, 50%.
* `preprocessor.resolution`: resolution in meter per pixel. Default, 30m/px.
* `preprocessor.flag_verbose`: verbose mode, if True display information on the standard output during data preprocessing. Default, True.
* `preprocessor.gaussian_blur`: parameters to apply gaussian blur to the image to reduce noise. Default, `{"radius": 3, "sigma": 0.5}`. If `radius` is 0 no blur is applied.
* `preprocessor.flag_cloud_filtering`: flag to apply cloud mask when compositing several images. Help reducing the clouds interference, but can create confusing artefacts. Default, False.

Other parameters.
* `preprocessor.step_search_image`: step in days when searching for images around the requested date. Default, 5.
* `preprocessor.nb_max_step_search`: max number of steps when searching images around a date. Default, 2.
* `preprocessor.max_area_angle`: threshold in degrees used to split large AOI into smaller chunks to avoid exceeding GEE quota. Default, 0.1.

One can retrieve data using the instance as follow, for example Cordoba city on 2025, January 1st:
```
dates = ["2025-01-01"]
area_of_interest = LongLatBBox(-64.3, -64.2, -31.4, -31.3)
images = preprocessor.get_satellite_data(dates, area_of_interest)
```
As satellite data are not available on every day, there may be no data for the requested date(s). The preprocessor then increases progressively the range of acceptable dates to look for available data, in the range `date+-preprocessor.step_search_image*k` for `k` in `[0,preprocessor.nb_max_step_search[`. If several images are found within the interval they are composed into one using the median of values. If no data at all were found for a requested date, a dummy image (all band data set to 0) is returned instead.

The result image(s) can be used as explained in the CordobaImage section.

It is possible to automatically search for dates for which there is data available (subject to the cloud cover threshold and other search parameters) with the `get_best_acquisition_dates()` method. For example, to search available dates in the 6 first months of 2024 with a one week interval:
```
min_interval = 7
area_of_interest = ...
available_dates = preprocessor.get_best_acquisition_dates("2024-01-01", "2024-05-31", area_of_interest, min_interval)
```
