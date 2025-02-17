from flask import *

# PIL to convert numpy arrays to images
from PIL import Image

# Import the CordobaDataPreprocessor module
from cordobaDataPreprocessor import *

# Import the CordobaPredictor module
from cordobaPredictor import *

# Create the app
app = Flask(__name__)

# Render the main page
@app.route("/")
def main_page():
    return render_template("main.html")

# Process the prediction request
@app.route('/run_prediction', methods=["POST"])
def run_prediction():

    # Get the data from GEE
    preprocessor = CordobaDataPreprocessor()
    days = [request.form["inpT1"], request.form["inpT2"]]
    area = LongLatBBox(
        float(request.form["inpLongFrom"]),
        float(request.form["inpLongTo"]),
        float(request.form["inpLatFrom"]),
        float(request.form["inpLatTo"]))
    images = preprocessor.get_satellite_data(days, area)
    
    # Run the prediction model on the data
    predictor = CordobaPredictor()
    prediction_image = \
        predictor.predictPcaKMeanClustering([images[0], images[1]])

    # Save the result as images to be displayed in the UI
    rgb_paths = [
      url_for('static',filename='rgb00.png'),
      url_for('static',filename='rgb01.png')]
    for i_img in range(2):
        rgb = images[i_img].to_rgb(gamma=0.66)
        Image.fromarray(rgb).save("." + rgb_paths[i_img])

    prediction_path = url_for('static',filename='prediction.png')
    Image.fromarray(prediction_image).save("." + prediction_path)

    # Return the result
    return {"rgb_paths": rgb_paths, "prediction_path": prediction_path}
