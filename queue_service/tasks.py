from celery import Celery
from celery_app import app
import sys
import os
import runpy
import json
import logging

# Configure logging for task execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.append(os.path.abspath("CordobaArgentinaChapter_MonitoringLandUseTransformation/demo_processing_prediction"))

@app.task
def run_preprocessing_and_prediction(roi, days):
    """
    Run the entire pre-processing and prediction with dynamic arguments.
    :param roi: List of coordinates [[lat, lon], ..]
    :param days: List of two dates ["start_date", "end_date"]
    """
    try:
        logging.info(f"Running process_predict.py with ROI: {roi} and Days: {days}")

        # Pass arguments directly to the script
        sys.argv = ["process_predict.py"] # Just set the script name to prevent errors

        # Pass the 'roi' and 'days' directly to the script by setting them as global variables
        # to make them accessible within the 'process_predict.py' execution context.
        globals()['roi'] = roi
        globals()['days'] = days

        # Run the process_predict script
        result = runpy.run_path("process_predict.py")

        # Ensure 'deforest_rois' exists in the result
        if "deforest_rois" not in result:
            logging.error("Error: 'deforest_rois' was not found in the script's result.")
            return json.dumps({"error": "deforest_rois not found"})

        deforest_rois = result["deforest_rois"]

        if not deforest_rois:
            logging.warning("No deforestation regions detected.")

        # Convert deforest_rois to JSON-serializable format
        deforest_rois_json = json.dumps(deforest_rois)
        logging.info("Deforestation regions processed successfully.")

        return deforest_rois_json

    except Exception as e:
        logging.error(f"Error running preprocessing and prediction: {str(e)}")
        return json.dumps({"error": str(e)})