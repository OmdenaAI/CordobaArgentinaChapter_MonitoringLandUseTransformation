# Land Use Change Detection API

This project provides an API for Land Use Change Detection using machine learning models. It is designed to identify and predict land use changes by analyzing geo-spatial data.

## Environment Setup

### Prerequisites
Before running the project, ensure you have the following installed:

- Python 3.7 or higher
- pip (Python package manager)


### Execution Steps

1. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` file with contents shown in `.env.example`
3. Run the celery 
   ```bash
   celery -A app.main:celery_app worker --loglevel=info
   ```
4. Run the server
   ```bash
   python manage.py
   ```
5. Check API Documentation: http://0.0.0.0:8080/docs

Example API Payload for submitting change detection task:
{
  "inp_t1": "2019-01-24",
  "inp_t2": "2019-12-24",
  "inp_long_from": -62.28,
  "inp_long_to": -62.15,
  "inp_lat_from": -21.8,
  "inp_lat_to": -21.7
}