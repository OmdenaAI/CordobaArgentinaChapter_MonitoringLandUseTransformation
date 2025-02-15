# Land Use Change Detection API

REST API for the land use change detection system in Córdoba, Argentina.

## Table of Contents

- [Setup](#setup)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Image Processing](#image-processing)
  - [Authentication](#authentication-endpoints)
  - [Places](#places-endpoints)
- [Data Models](#data-models)
- [Usage Examples](#usage-examples)

## Setup

### Environment Variables

Create a `.env` file with the following variables:

```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=omdena_argentina_land_use_db
POSTGRES_PORT=5432

JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Authentication

The API uses JWT authentication. To access protected endpoints, include the token in the header:

```
Authorization: Bearer <token>
```

## Endpoints

### Health Check

#### GET /health

Check the API status.

```bash
curl -X 'GET' 'http://localhost:8000/health'
```

### Image Processing

#### POST /process

Start a change detection process.

```bash
curl -X 'POST' 'http://localhost:8000/process' \
  -H 'Content-Type: application/json' \
  -d '{
    "polygon": [[-64.18, -31.42], [-64.17, -31.42], [-64.17, -31.41], [-64.18, -31.41], [-64.18, -31.42]],
    "start_date": "2021-01-01",
    "end_date": "2021-12-31",
    "period": "monthly"
  }'
```

#### GET /status/{task_id}

Get the status of a process.

```bash
curl -X 'GET' 'http://localhost:8000/status/12345'
```

### Authentication Endpoints

#### POST /api/v1/auth/signup

Register a new user.

```bash
curl -X 'POST' 'http://localhost:8000/api/v1/auth/signup' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "strongpassword",
    "full_name": "John Doe"
  }'
```

#### POST /api/v1/auth/login

Login and get a JWT token.

```bash
curl -X 'POST' 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=user@example.com&password=strongpassword'
```

#### GET /api/v1/auth/me

Get current user information.

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/auth/me' \
  -H 'Authorization: Bearer <token>'
```

### Places Endpoints

#### POST /api/v1/places/

Create a new place.

```bash
curl -X 'POST' 'http://localhost:8000/api/v1/places/' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Place",
    "description": "A test place",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[-64.18, -31.42], [-64.17, -31.42], [-64.17, -31.41], [-64.18, -31.41], [-64.18, -31.42]]]
    }
  }'
```

#### GET /api/v1/places/

List all places for the current user.

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/places/' \
  -H 'Authorization: Bearer <token>'
```

#### GET /api/v1/places/{place_id}

Get a specific place.

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/places/1' \
  -H 'Authorization: Bearer <token>'
```

#### PUT /api/v1/places/{place_id}

Update a place.

```bash
curl -X 'PUT' 'http://localhost:8000/api/v1/places/1' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Updated Place",
    "description": "This place was updated",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[-64.18, -31.42], [-64.17, -31.42], [-64.17, -31.41], [-64.18, -31.41], [-64.18, -31.42]]]
    }
  }'
```

#### DELETE /api/v1/places/{place_id}

Delete a place.

```bash
curl -X 'DELETE' 'http://localhost:8000/api/v1/places/1' \
  -H 'Authorization: Bearer <token>'
```

#### GET /api/v1/places/bbox/

Find places within a bounding box.

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/places/bbox/?min_lon=-64.19&min_lat=-31.43&max_lon=-64.16&max_lat=-31.40' \
  -H 'Authorization: Bearer <token>'
```

#### GET /api/v1/places/nearby/

Find places near a point.

```bash
curl -X 'GET' 'http://localhost:8000/api/v1/places/nearby/?lat=-31.415&lon=-64.175&distance=1000' \
  -H 'Authorization: Bearer <token>'
```

## Data Models

### User

```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "id": 1,
  "is_active": true,
  "created_at": "2024-02-15T10:00:00",
  "updated_at": null
}
```

### Place

```json
{
  "name": "Test Place",
  "description": "A test place",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[-64.18, -31.42], [-64.17, -31.42], [-64.17, -31.41], [-64.18, -31.41], [-64.18, -31.42]]]
  },
  "id": 1,
  "user_id": 1,
  "created_at": "2024-02-15T10:00:00",
  "updated_at": null
}
```

### Token

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Usage Examples

### Typical Usage Flow

1. Register a user:
```bash
curl -X 'POST' 'http://localhost:8000/api/v1/auth/signup' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "strongpassword",
    "full_name": "John Doe"
  }'
```

2. Login and get token:
```bash
curl -X 'POST' 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=user@example.com&password=strongpassword'
```

3. Create a place:
```bash
curl -X 'POST' 'http://localhost:8000/api/v1/places/' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "My Field",
    "description": "Agricultural field in Córdoba",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[-64.18, -31.42], [-64.17, -31.42], [-64.17, -31.41], [-64.18, -31.41], [-64.18, -31.42]]]
    }
  }'
```

4. Start change detection process:
```bash
curl -X 'POST' 'http://localhost:8000/process' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "polygon": [[-64.18, -31.42], [-64.17, -31.42], [-64.17, -31.41], [-64.18, -31.41], [-64.18, -31.42]],
    "start_date": "2021-01-01",
    "end_date": "2021-12-31",
    "period": "monthly"
  }'
```

5. Check process status:
```bash
curl -X 'GET' 'http://localhost:8000/status/<task_id>' \
  -H 'Authorization: Bearer <token>'
```

For more details, check the interactive documentation at Swagger UI: http://localhost:8000/docs 