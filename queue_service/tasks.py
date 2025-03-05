from celery import Celery
from typing import Dict, Any
import requests  # **New Import**: To send HTTP requests to the Flask pre-processing app

# Initialize Celery app
celery_app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")


# Process image using the model
# We will use 'polygon' as input but for simplicity refer to it as 'image'
@celery_app.task(name="process_image")
def process_image(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a change detection request using the provided data.
    Args:
        data: Dictionary containing:
            - polygon: List[List[float]]: List of coordinates defining the area of interest
            - start_date: str: Start date for change detection
            - end_date: str: End date for change detection
            - period: str: Time period for analysis (e.g., 'monthly', 'yearly')
    """
    try:
        # Extract data for Flask app call
        days = [data['start_date'], data['end_date']]
        area = {
            "long_from": data['polygon'][0][1],  # Longitude from first coordinate
            "long_to": data['polygon'][1][1],  # Longitude from second coordinate
            "lat_from": data['polygon'][0][0],  # Latitude from first coordinate
            "lat_to": data['polygon'][2][0]  # Latitude from third coordinate
        }

        # Construct the data to be sent to the Flask app
        prediction_data = {
            "inpT1": days[0],
            "inpT2": days[1],
            "inpLongFrom": area["long_from"],
            "inpLongTo": area["long_to"],
            "inpLatFrom": area["lat_from"],
            "inpLatTo": area["lat_to"]
        }

        # Send a POST request to the Flask app's /run_prediction endpoint
        flask_url = "http://localhost:5000/run_prediction"  # Flask app running on localhost
        response = requests.post(flask_url, data=prediction_data)

        if response.status_code == 200:
            # Return the result received from Flask
            result_data = response.json()

            return {
                "status": "processed",
                "message": "Change detection analysis completed successfully",
                "request_data": {
                    "area": data["polygon"],
                    "start_date": data["start_date"],
                    "end_date": data["end_date"],
                    "period": data["period"]
                },
                "results": result_data  # Using result_data received from Flask
            }
        else:
            return {"status": "error", "message": f"Failed to process prediction: {response.text}"}

    except Exception as e:
        return {"status": "error", "message": str(e), "request_data": data}

    # (This portion is not necessary since we are calling the Flask app for the actual work)
    # Load the model
    # model = load_model(model_name)

    # Load the image
    # image = load_image(image_path)

    # Perform inference
    # prediction = model.predict(image)

    # return {"status": "processed", "message": "Image processed successfully", "input_data": image_data}


