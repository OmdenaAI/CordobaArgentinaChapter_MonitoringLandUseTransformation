# Sandbox Directory - Brainstorm

## Overview
This directory contains working drafts of the `tasks` file and the main API gateway file. These drafts explore an alternative approach to integrating processing and prediction tasks within the queue system, leveraging the service layer in the FastAPI app (`api_gateway/app/services`).

## Purpose
The goal of these working drafts is to:
- Improve separation of concerns by keeping task execution logic in `tasks_working.py` and delegating processing/prediction logic to `services`.
- Ensure maintainability by centralizing data operations in the service layer instead of embedding them directly in Celery tasks.
- Prepare for future enhancements by making the processing pipeline more modular and adaptable.


### **API Gateway Structure**
- **Working Draft (`api_gateway_working.py`)**: The API gateway is structured to interact with service-layer functions that encapsulate business logic, ensuring a cleaner separation of concerns.

## How to Use These Files
1. **Testing & Validation**: These drafts should be tested against sample inputs to confirm proper integration with the existing system.
2. **Service Updates**: Before implementing these changes in the main API gateway and queue service, relevant service functions need to be updated to support this structure.

## Next Steps
- Validate Celery task execution and API responses in a testing environment.
- Update documentation and dependencies as needed before merging these changes into the main system.

