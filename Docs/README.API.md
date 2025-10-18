# Kisaantic API Documentation v1.0

## Base URL
```
https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod
```

## Table of Contents
1. [Authentication](#authentication)
2. [Auth Endpoints](#auth-endpoints)
3. [User Endpoints](#user-endpoints)
4. [Weather Endpoints](#weather-endpoints)
5. [Chat Session Endpoints](#chat-session-endpoints)
6. [Chat Endpoints](#chat-endpoints)
7. [Error Responses](#error-responses)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Token Lifecycle
- **Access Token**: Valid for 15 minutes
- **Refresh Token**: Valid for 30 days
- Tokens are JWT-based and contain user identification

---

## Auth Endpoints

### 1. Sign Up

Create a new user account.

**Endpoint:** `POST /api/auth/signup`

**Authentication:** None required

**Request Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "farmer@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| email | string | Yes | User email address | Valid email format |
| password | string | Yes | User password | Min 8 characters, max 100 |
| name | string | No | User's full name | Max 100 characters |

**Success Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT access token for API authentication |
| refresh_token | string | JWT refresh token for obtaining new access tokens |
| token_type | string | Token type (always "bearer") |
| expires_in | integer | Access token expiration time in seconds |

**Error Responses:**

**400 Bad Request** - Email already registered
```json
{
  "error": "BadRequest",
  "message": "Email already registered",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**400 Bad Request** - Validation error
```json
{
  "error": "ValidationError",
  "message": "Password must be at least 8 characters",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 2. Login

Authenticate user and receive tokens.

**Endpoint:** `POST /api/auth/login`

**Authentication:** None required

**Request Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "farmer@example.com",
  "password": "SecurePassword123!",
  "device_id": "mobile-device-12345"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| email | string | Yes | User email address | Valid email format |
| password | string | Yes | User password | - |
| device_id | string | No | Unique device identifier | Max 100 characters |

**Success Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**

**401 Unauthorized** - Invalid credentials
```json
{
  "error": "Unauthorized",
  "message": "Incorrect email or password",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 3. Refresh Token

Obtain a new access token using refresh token.

**Endpoint:** `POST /api/auth/refresh`

**Authentication:** None required (uses refresh token)

**Request Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh_token | string | Yes | Valid refresh token from login/signup |

**Success Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**

**401 Unauthorized** - Invalid refresh token
```json
{
  "error": "Unauthorized",
  "message": "Invalid refresh token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 4. Logout

Revoke all refresh tokens for the current user.

**Endpoint:** `POST /api/auth/logout`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:** None

**Success Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

**Error Responses:**

**401 Unauthorized** - Invalid or missing token
```json
{
  "error": "Unauthorized",
  "message": "Missing or invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

## User Endpoints

### 5. Get Current User

Retrieve current authenticated user's profile.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:** None

**Success Response:** `200 OK`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "farmer@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "farm_size": "50",
  "crop_type": "Wheat",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "lat_direction": "N",
  "long_direction": "W",
  "address": "123 Farm Road, Iowa City, IA",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-10-14T15:30:00Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | Unique user identifier (UUID) |
| email | string | User email address |
| name | string | User's full name |
| phone | string | Phone number |
| farm_size | string | Size of farm in acres |
| crop_type | string | Primary crop type |
| latitude | float | Farm location latitude (-90 to 90) |
| longitude | float | Farm location longitude (-180 to 180) |
| lat_direction | string | Latitude direction (N or S) |
| long_direction | string | Longitude direction (E or W) |
| address | string | Human-readable address |
| created_at | string | Account creation timestamp (ISO 8601) |
| updated_at | string | Last update timestamp (ISO 8601) |

**Error Responses:**

**401 Unauthorized** - Invalid token
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**404 Not Found** - User not found
```json
{
  "error": "NotFound",
  "message": "User not found",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 6. Update Current User

Update current user's profile information.

**Endpoint:** `PUT /api/auth/me`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:** (All fields are optional)
```json
{
  "name": "John Doe",
  "phone": "+1234567890",
  "farm_size": "75",
  "crop_type": "Corn",
  "latitude": 41.8781,
  "longitude": -87.6298,
  "lat_direction": "N",
  "long_direction": "W",
  "address": "456 New Farm Road, Chicago, IL"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| name | string | No | User's full name | Max 100 characters |
| phone | string | No | Phone number | Max 20 characters |
| farm_size | string | No | Size of farm | Max 50 characters |
| crop_type | string | No | Primary crop type | Max 100 characters |
| latitude | float | No | Farm location latitude | -90 to 90 |
| longitude | float | No | Farm location longitude | -180 to 180 |
| lat_direction | string | No | Latitude direction | "N" or "S" |
| long_direction | string | No | Longitude direction | "E" or "W" |
| address | string | No | Human-readable address | Max 500 characters |

**Success Response:** `200 OK`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "farmer@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "farm_size": "75",
  "crop_type": "Corn",
  "latitude": 41.8781,
  "longitude": -87.6298,
  "lat_direction": "N",
  "long_direction": "W",
  "address": "456 New Farm Road, Chicago, IL",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-10-14T15:35:00Z"
}
```

**Error Responses:**

**400 Bad Request** - Validation error
```json
{
  "error": "ValidationError",
  "message": "Latitude must be between -90 and 90",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**401 Unauthorized** - Invalid token
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

## Weather Endpoints

### 7. Get Current Weather

Retrieve current weather data for specified coordinates.

**Endpoint:** `GET /api/weather/current`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| lat | float | Yes | Latitude coordinate | -90 to 90 |
| lng | float | Yes | Longitude coordinate | -180 to 180 |

**Example Request:**
```http
GET /api/weather/current?lat=40.7128&lng=-74.0060
```

**Success Response:** `200 OK`
```json
{
  "location": {
    "name": "New York",
    "region": "New York",
    "country": "United States of America",
    "lat": 40.71,
    "lon": -74.01,
    "tz_id": "America/New_York",
    "localtime_epoch": 1697298600,
    "localtime": "2025-10-14 15:30"
  },
  "current": {
    "last_updated_epoch": 1697298000,
    "last_updated": "2025-10-14 15:20",
    "temp_c": 22.0,
    "temp_f": 71.6,
    "is_day": 1,
    "condition": {
      "text": "Partly cloudy",
      "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
      "code": 1003
    },
    "wind_mph": 9.4,
    "wind_kph": 15.1,
    "wind_degree": 210,
    "wind_dir": "SSW",
    "pressure_mb": 1013.0,
    "pressure_in": 29.91,
    "precip_mm": 0.0,
    "precip_in": 0.0,
    "humidity": 65,
    "cloud": 50,
    "feelslike_c": 21.5,
    "feelslike_f": 70.7,
    "vis_km": 16.0,
    "vis_miles": 9.0,
    "uv": 5.0,
    "gust_mph": 12.1,
    "gust_kph": 19.4
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| location | object | Location information |
| location.name | string | Location name |
| location.region | string | Region/state |
| location.country | string | Country name |
| location.lat | float | Latitude |
| location.lon | float | Longitude |
| location.tz_id | string | Timezone identifier |
| location.localtime | string | Local time |
| current | object | Current weather data |
| current.temp_c | float | Temperature in Celsius |
| current.temp_f | float | Temperature in Fahrenheit |
| current.condition.text | string | Weather condition description |
| current.condition.icon | string | Weather icon URL |
| current.wind_kph | float | Wind speed in km/h |
| current.humidity | integer | Humidity percentage |
| current.feelslike_c | float | Feels like temperature in Celsius |
| current.uv | float | UV index |

**Error Responses:**

**400 Bad Request** - Missing or invalid parameters
```json
{
  "error": "BadRequest",
  "message": "Missing required parameters: lat, lng",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**401 Unauthorized** - Invalid token
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**504 Gateway Timeout** - Weather API timeout
```json
{
  "error": "GatewayTimeout",
  "message": "Weather API request timed out",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 8. Get Weather Forecast

Retrieve weather forecast for specified coordinates.

**Endpoint:** `GET /api/weather/forecast`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| lat | float | Yes | Latitude coordinate | -90 to 90 |
| lng | float | Yes | Longitude coordinate | -180 to 180 |
| days | integer | No | Number of forecast days | 1 to 14 (default: 7) |

**Example Request:**
```http
GET /api/weather/forecast?lat=40.7128&lng=-74.0060&days=5
```

**Success Response:** `200 OK`
```json
{
  "location": {
    "name": "New York",
    "region": "New York",
    "country": "United States of America",
    "lat": 40.71,
    "lon": -74.01,
    "tz_id": "America/New_York",
    "localtime": "2025-10-14 15:30"
  },
  "current": {
    "temp_c": 22.0,
    "condition": {
      "text": "Partly cloudy"
    }
  },
  "forecast": {
    "forecastday": [
      {
        "date": "2025-10-14",
        "date_epoch": 1697241600,
        "day": {
          "maxtemp_c": 25.0,
          "maxtemp_f": 77.0,
          "mintemp_c": 18.0,
          "mintemp_f": 64.4,
          "avgtemp_c": 21.5,
          "avgtemp_f": 70.7,
          "maxwind_mph": 12.5,
          "maxwind_kph": 20.0,
          "totalprecip_mm": 0.5,
          "totalprecip_in": 0.02,
          "totalsnow_cm": 0.0,
          "avgvis_km": 10.0,
          "avgvis_miles": 6.0,
          "avghumidity": 70,
          "daily_will_it_rain": 0,
          "daily_chance_of_rain": 10,
          "daily_will_it_snow": 0,
          "daily_chance_of_snow": 0,
          "condition": {
            "text": "Partly cloudy",
            "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
            "code": 1003
          },
          "uv": 5.0
        },
        "astro": {
          "sunrise": "06:45 AM",
          "sunset": "06:30 PM",
          "moonrise": "08:15 PM",
          "moonset": "09:30 AM",
          "moon_phase": "Waxing Crescent",
          "moon_illumination": 25
        },
        "hour": [
          {
            "time_epoch": 1697245200,
            "time": "2025-10-14 00:00",
            "temp_c": 19.0,
            "temp_f": 66.2,
            "is_day": 0,
            "condition": {
              "text": "Clear",
              "icon": "//cdn.weatherapi.com/weather/64x64/night/113.png",
              "code": 1000
            },
            "wind_kph": 12.0,
            "humidity": 75,
            "feelslike_c": 18.5,
            "will_it_rain": 0,
            "chance_of_rain": 0
          }
          // ... more hourly data
        ]
      }
      // ... more days
    ]
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| forecast.forecastday | array | Array of forecast days |
| forecastday[].date | string | Forecast date (YYYY-MM-DD) |
| forecastday[].day | object | Day summary |
| day.maxtemp_c | float | Maximum temperature in Celsius |
| day.mintemp_c | float | Minimum temperature in Celsius |
| day.avgtemp_c | float | Average temperature in Celsius |
| day.maxwind_kph | float | Maximum wind speed in km/h |
| day.totalprecip_mm | float | Total precipitation in mm |
| day.avghumidity | integer | Average humidity percentage |
| day.daily_chance_of_rain | integer | Chance of rain (0-100%) |
| day.condition | object | Weather condition |
| day.uv | float | UV index |
| forecastday[].hour | array | Hourly forecast data |

**Error Responses:**

**400 Bad Request** - Invalid days parameter
```json
{
  "error": "BadRequest",
  "message": "Days must be between 1 and 14",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 9. Get Weather History

Retrieve historical weather data for a specific date.

**Endpoint:** `GET /api/weather/history`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| lat | float | Yes | Latitude coordinate | -90 to 90 |
| lng | float | Yes | Longitude coordinate | -180 to 180 |
| dt | string | Yes | Date for historical data | YYYY-MM-DD format |

**Example Request:**
```http
GET /api/weather/history?lat=40.7128&lng=-74.0060&dt=2025-10-01
```

**Success Response:** `200 OK`
```json
{
  "location": {
    "name": "New York",
    "region": "New York",
    "country": "United States of America",
    "lat": 40.71,
    "lon": -74.01
  },
  "forecast": {
    "forecastday": [
      {
        "date": "2025-10-01",
        "date_epoch": 1727740800,
        "day": {
          "maxtemp_c": 23.0,
          "maxtemp_f": 73.4,
          "mintemp_c": 16.0,
          "mintemp_f": 60.8,
          "avgtemp_c": 19.5,
          "avgtemp_f": 67.1,
          "maxwind_kph": 18.0,
          "totalprecip_mm": 2.5,
          "avghumidity": 72,
          "condition": {
            "text": "Light rain",
            "icon": "//cdn.weatherapi.com/weather/64x64/day/296.png",
            "code": 1183
          },
          "uv": 4.0
        },
        "astro": {
          "sunrise": "06:50 AM",
          "sunset": "06:45 PM"
        },
        "hour": [
          // Hourly historical data
        ]
      }
    ]
  }
}
```

**Error Responses:**

**400 Bad Request** - Invalid date format
```json
{
  "error": "BadRequest",
  "message": "Invalid parameters. Date must be in YYYY-MM-DD format",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

## Chat Session Endpoints

### 10. Create Chat Session

Create a new chat session.

**Endpoint:** `POST /api/sessions`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Corn Planting Advice"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| title | string | No | Session title | Max 200 characters (default: "New Chat") |

**Success Response:** `200 OK`
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Corn Planting Advice",
  "created_at": "2025-10-14T15:30:00Z",
  "updated_at": "2025-10-14T15:30:00Z",
  "message_count": 0,
  "messages": []
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | Unique session identifier (UUID) |
| user_id | string | User identifier |
| title | string | Session title |
| created_at | string | Creation timestamp (ISO 8601) |
| updated_at | string | Last update timestamp (ISO 8601) |
| message_count | integer | Number of messages in session |
| messages | array | Array of messages (empty for new sessions) |

**Error Responses:**

**401 Unauthorized**
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 11. Get All Chat Sessions

Retrieve all chat sessions for the current user (paginated).

**Endpoint:** `GET /api/sessions`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| limit | integer | No | Number of sessions to return | 1 to 100 (default: 20) |
| last_key | string | No | Pagination cursor | Base64 encoded key from previous response |

**Example Request:**
```http
GET /api/sessions?limit=10
```

**Success Response:** `200 OK`
```json
{
  "items": [
    {
      "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Pest Control Questions",
      "created_at": "2025-10-14T16:00:00Z",
      "updated_at": "2025-10-14T16:05:00Z",
      "message_count": 4,
      "messages": []
    },
    {
      "session_id": "3b241101-e2bb-4255-8caf-4136c566a962",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Corn Planting Advice",
      "created_at": "2025-10-14T15:30:00Z",
      "updated_at": "2025-10-14T15:35:00Z",
      "message_count": 2,
      "messages": []
    }
  ],
  "last_evaluated_key": "eyJQSyI6IlVTRVIjLCJTSyI6IlNFU1NJT04ifQ==",
  "count": 2
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| items | array | Array of chat sessions |
| last_evaluated_key | string | Pagination cursor for next page (null if no more results) |
| count | integer | Number of items in current response |

**Notes:**
- Sessions are ordered by `updated_at` in descending order (most recent first)
- Use `last_evaluated_key` from response as `last_key` query parameter for next page

**Error Responses:**

**400 Bad Request** - Invalid limit
```json
{
  "error": "BadRequest",
  "message": "Limit must be between 1 and 100",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 12. Get Single Chat Session

Retrieve a specific chat session with all messages.

**Endpoint:** `GET /api/sessions/{session_id}`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session identifier (UUID) |

**Example Request:**
```http
GET /api/sessions/7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Success Response:** `200 OK`
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Corn Planting Advice",
  "created_at": "2025-10-14T15:30:00Z",
  "updated_at": "2025-10-14T15:35:00Z",
  "message_count": 2,
  "messages": [
    {
      "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "text": "When is the best time to plant corn?",
      "sender": "user",
      "created_at": "2025-10-14T15:30:00Z",
      "metadata": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "weather_temp": 22.0
      }
    },
    {
      "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "text": "The best time to plant corn is when soil temperature reaches 50-55°F (10-13°C). In your region, this typically occurs in late April to early May. Given the current temperature of 22°C, conditions are favorable for planting.",
      "sender": "ai",
      "created_at": "2025-10-14T15:30:05Z",
      "metadata": null
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| messages[].message_id | string | Unique message identifier |
| messages[].session_id | string | Session identifier |
| messages[].text | string | Message content |
| messages[].sender | string | Message sender ("user" or "ai") |
| messages[].created_at | string | Message creation timestamp |
| messages[].metadata | object | Additional message metadata (optional) |

**Error Responses:**

**404 Not Found** - Session not found
```json
{
  "error": "NotFound",
  "message": "Session not found",
```json
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**401 Unauthorized** - Invalid token
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 13. Update Chat Session

Update chat session title.

**Endpoint:** `PUT /api/sessions/{session_id}`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session identifier (UUID) |

**Request Body:**
```json
{
  "title": "Updated Title - Corn Growing Tips"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| title | string | Yes | New session title | Max 200 characters |

**Example Request:**
```http
PUT /api/sessions/7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Success Response:** `200 OK`
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Title - Corn Growing Tips",
  "created_at": "2025-10-14T15:30:00Z",
  "updated_at": "2025-10-14T16:00:00Z",
  "message_count": 2,
  "messages": []
}
```

**Error Responses:**

**400 Bad Request** - Missing title
```json
{
  "error": "BadRequest",
  "message": "Title is required",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**404 Not Found** - Session not found
```json
{
  "error": "NotFound",
  "message": "Session not found",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

### 14. Delete Chat Session

Delete a chat session and all its messages.

**Endpoint:** `DELETE /api/sessions/{session_id}`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session identifier (UUID) |

**Example Request:**
```http
DELETE /api/sessions/7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Success Response:** `200 OK`
```json
{
  "message": "Session deleted successfully"
}
```

**Error Responses:**

**404 Not Found** - Session not found
```json
{
  "error": "NotFound",
  "message": "Session not found",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**401 Unauthorized** - Invalid token
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

## Chat Endpoints

### 15. Send Chat Message

Send a message to the AI assistant with optional location and weather context. The AI uses AWS Bedrock Agent for intelligent agricultural advice.

**Endpoint:** `POST /api/chat`

**Authentication:** Required (Bearer token)

**Request Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What fertilizer should I use for wheat in this weather?",
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "address": "New York, NY",
  "weather_temp": 22.5,
  "weather_condition": "Partly cloudy",
  "weather_humidity": 65,
  "context_data": {
    "soil_type": "loamy",
    "last_fertilization": "2025-09-01"
  }
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| message | string | Yes | User's question/message | Min 1, max 10000 characters |
| session_id | string | No | Existing session ID | UUID format. If not provided, creates new session |
| latitude | float | No | Current latitude | -90 to 90 |
| longitude | float | No | Current longitude | -180 to 180 |
| address | string | No | Human-readable address | Max 500 characters |
| weather_temp | float | No | Current temperature in Celsius | - |
| weather_condition | string | No | Weather condition description | Max 100 characters |
| weather_humidity | integer | No | Humidity percentage | 0 to 100 |
| context_data | object | No | Additional context data | Any valid JSON object |

**Success Response:** `200 OK`
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_message": {
    "message_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "text": "What fertilizer should I use for wheat in this weather?",
    "sender": "user",
    "created_at": "2025-10-14T16:00:00Z",
    "metadata": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "New York, NY",
      "weather_temp": 22.5,
      "weather_condition": "Partly cloudy",
      "weather_humidity": 65
    }
  },
  "ai_message": {
    "message_id": "d4e5f6a7-b8c9-0123-def0-123456789013",
    "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "text": "For wheat crops in your current conditions (22.5°C, partly cloudy, 65% humidity in New York, NY), I recommend the following fertilizer approach:\n\n**Nitrogen Application:**\n- Use a nitrogen-based fertilizer with a ratio of 20-10-10 or 15-15-15\n- Current temperature (22.5°C) is ideal for nitrogen uptake\n- Apply 40-60 lbs of nitrogen per acre during the tillering stage\n\n**Timing Considerations:**\n- With 65% humidity and partly cloudy conditions, soil moisture should be adequate\n- Apply fertilizer when rain is forecasted within 2-3 days for better absorption\n- Avoid application during extreme heat or drought\n\n**Additional Recommendations:**\n- Consider a soil test to determine exact nutrient deficiencies\n- Split nitrogen applications: 50% at planting, 50% at stem elongation\n- Monitor for phosphorus and potassium levels; supplement if needed\n\n**Safety Notes:**\n- Wear protective equipment when handling fertilizers\n- Follow label instructions for application rates\n- Keep fertilizer away from water sources to prevent runoff\n\nWould you like specific product recommendations or guidance on application methods?",
    "sender": "ai",
    "created_at": "2025-10-14T16:00:03Z",
    "metadata": null
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | Session identifier (new or existing) |
| user_message | object | Saved user message |
| user_message.message_id | string | User message ID |
| user_message.text | string | User message content |
| user_message.sender | string | Always "user" |
| user_message.created_at | string | Message timestamp |
| user_message.metadata | object | Context data from request |
| ai_message | object | AI response message |
| ai_message.message_id | string | AI message ID |
| ai_message.text | string | AI response content |
| ai_message.sender | string | Always "ai" |
| ai_message.created_at | string | Response timestamp |

**Behavior Notes:**
- If `session_id` is not provided, a new session is automatically created
- First message in a session auto-generates session title from message (first 50 chars)
- AI uses Bedrock Agent with access to agricultural knowledge bases
- Response considers user profile (farm size, crop type, location)
- Response considers current weather conditions for contextual advice
- Session `updated_at` timestamp is updated with each new message
- Message count is automatically incremented

**Error Responses:**

**400 Bad Request** - Validation error
```json
{
  "error": "ValidationError",
  "message": "Message must be between 1 and 10000 characters",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**401 Unauthorized** - Invalid token
```json
{
  "error": "Unauthorized",
  "message": "Invalid token",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**404 Not Found** - Session not found (when session_id provided)
```json
{
  "error": "NotFound",
  "message": "Session not found",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

**500 Internal Server Error** - AI service error
```json
{
  "error": "InternalServerError",
  "message": "An unexpected error occurred",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

---

## Error Responses

All error responses follow a consistent structure:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "timestamp": "2025-10-14T15:30:00Z",
  "request_id": "abc123"
}
```

### Error Types

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| BadRequest | 400 | Invalid request parameters or body |
| Unauthorized | 401 | Missing, invalid, or expired authentication token |
| NotFound | 404 | Requested resource does not exist |
| ValidationError | 400 | Request data failed validation rules |
| WeatherAPIError | 500/502 | External weather API failure |
| GatewayTimeout | 504 | External service timeout |
| InternalServerError | 500 | Unexpected server error |

### Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 OK | Request successful |
| 400 Bad Request | Invalid request parameters or validation error |
| 401 Unauthorized | Authentication failed or token invalid/expired |
| 404 Not Found | Resource not found |
| 500 Internal Server Error | Server-side error |
| 502 Bad Gateway | External service error |
| 504 Gateway Timeout | External service timeout |

---

## Rate Limiting

### Current Implementation
- No rate limiting is currently enforced at the API level
- Weather API calls are subject to external provider limits

### Recommended Implementation (Future)
```
Rate Limits (per user):
- Auth endpoints: 10 requests/minute
- Chat endpoint: 20 requests/minute
- Weather endpoints: 100 requests/hour
- Other endpoints: 60 requests/minute
```

### Rate Limit Headers (Future)
When rate limiting is implemented, responses will include:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1697298600
```

---

## Pagination

### Query Parameters
Endpoints that return lists support pagination:

| Parameter | Type | Description |
|-----------|------|----------|
| limit | integer | Number of items per page (1-100) |
| last_key | string | Cursor for next page |

### Response Format
```json
{
  "items": [...],
  "last_evaluated_key": "base64_encoded_key",
  "count": 20
}
```

### Usage Example
```http
# First request
GET /api/sessions?limit=20

# Next page (use last_evaluated_key from previous response)
GET /api/sessions?limit=20&last_key=eyJQSyI6IlVTRVIjLCJTSyI6IlNFU1NJT04ifQ==
```

---

## Best Practices

### Authentication
1. **Token Storage**: Store tokens securely (e.g., secure HTTP-only cookies, encrypted storage)
2. **Token Refresh**: Implement automatic token refresh before expiration
3. **Logout**: Always call logout endpoint to revoke refresh tokens
4. **Device ID**: Use consistent device_id for better session management

### API Usage
1. **Error Handling**: Always check error responses and handle appropriately
2. **Retries**: Implement exponential backoff for failed requests
3. **Timeouts**: Set appropriate timeouts for API calls (30s recommended)
4. **Validation**: Validate input data before sending to API

### Chat Functionality
1. **Session Management**: Reuse existing sessions for conversation continuity
2. **Context**: Always provide location and weather data when available
3. **Message Length**: Keep messages concise but descriptive
4. **Error Recovery**: Handle AI service errors gracefully with retry logic

### Weather Data
1. **Caching**: Cache weather data for 10-15 minutes to reduce API calls
2. **Coordinates**: Use precise coordinates for accurate weather data
3. **Forecast**: Request appropriate number of days (3-7 for most use cases)

---

## Examples

### Complete Authentication Flow

```javascript
// 1. Sign up
const signupResponse = await fetch('https://api.example.com/api/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'farmer@example.com',
    password: 'SecurePass123!',
    name: 'John Doe'
  })
});
const { access_token, refresh_token } = await signupResponse.json();

// 2. Store tokens securely
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// 3. Make authenticated request
const userResponse = await fetch('https://api.example.com/api/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const user = await userResponse.json();

// 4. Refresh token when expired
const refreshResponse = await fetch('https://api.example.com/api/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token })
});
const newTokens = await refreshResponse.json();

// 5. Logout
await fetch('https://api.example.com/api/auth/logout', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` }
});
localStorage.clear();
```

### Chat Conversation Flow

```javascript
// 1. Get current location and weather
const position = await getCurrentPosition();
const weatherData = await fetch(
  `https://api.example.com/api/weather/current?lat=${position.lat}&lng=${position.lng}`,
  { headers: { 'Authorization': `Bearer ${access_token}` }}
);
const weather = await weatherData.json();

// 2. Send first message (creates new session)
const chatResponse1 = await fetch('https://api.example.com/api/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What should I plant this season?',
    latitude: position.lat,
    longitude: position.lng,
    weather_temp: weather.current.temp_c,
    weather_condition: weather.current.condition.text,
    weather_humidity: weather.current.humidity
  })
});
const chat1 = await chatResponse1.json();
const sessionId = chat1.session_id;

// 3. Continue conversation in same session
const chatResponse2 = await fetch('https://api.example.com/api/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'How much fertilizer do I need?',
    session_id: sessionId,
    latitude: position.lat,
    longitude: position.lng,
    weather_temp: weather.current.temp_c,
    weather_condition: weather.current.condition.text
  })
});
const chat2 = await chatResponse2.json();

// 4. Get full conversation history
const sessionResponse = await fetch(
  `https://api.example.com/api/sessions/${sessionId}`,
  { headers: { 'Authorization': `Bearer ${access_token}` }}
);
const fullSession = await sessionResponse.json();
console.log(fullSession.messages); // All messages in conversation
```

### Pagination Example

```javascript
async function getAllSessions() {
  const allSessions = [];
  let lastKey = null;
  
  do {
    const url = lastKey 
      ? `https://api.example.com/api/sessions?limit=20&last_key=${lastKey}`
      : `https://api.example.com/api/sessions?limit=20`;
    
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${access_token}` }
    });
    
    const data = await response.json();
    allSessions.push(...data.items);
    lastKey = data.last_evaluated_key;
  } while (lastKey);
  
  return allSessions;
}
```

---

## Webhooks (Future Feature)

*Webhooks are not currently implemented but planned for future releases.*

Planned webhook events:
- `session.created` - New chat session created
- `message.received` - New user message received
- `message.completed` - AI response completed
- `user.updated` - User profile updated

---

## Versioning

**Current Version:** v1.0

The API uses URL path versioning. Future versions will be accessible via:
- v1: `/api/...` (current)
- v2: `/v2/api/...` (future)

Breaking changes will result in a new version. Non-breaking changes will be added to existing versions.

---

## Support

For API support, please contact:
- **Email**: support@kisaantic.com
- **Documentation**: https://docs.kisaantic.com
- **Status Page**: https://status.kisaantic.com

---

## Changelog

### Version 1.0.0 (2025-10-14)
- Initial release
- Authentication with JWT tokens
- Refresh token support
- User profile management
- Weather data integration
- Chat sessions with AI assistant (Bedrock Agent)
- DynamoDB single-table design
- Pagination support

---

**Last Updated:** October 14, 2025  
**API Version:** 1.0.0  
**Document Version:** 1.0.0