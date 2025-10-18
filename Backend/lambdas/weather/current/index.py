# lambda_weather_current.py
import json
import httpx
import os
import traceback
from schemas import ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import get_iso_timestamp

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_TIMEOUT = int(os.getenv("WEATHER_API_TIMEOUT", 10))

# CORS headers - add to ALL responses
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,Accept,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
}

def lambda_handler(event, context):
    # Handle OPTIONS preflight request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Extract and verify token - check both casing
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        
        token = extract_token_from_header(auth_header)
        if not token:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='Unauthorized',
                    message='Missing or invalid token',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        token_data = verify_token(token)
        if not token_data:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='Unauthorized',
                    message='Invalid token',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Get parameters
        params = event.get('queryStringParameters') or {}
        if 'lat' not in params or 'lng' not in params:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='BadRequest',
                    message='Missing required parameters: lat, lng',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        lat = params.get('lat')
        lng = params.get('lng')
        
        # Validate coordinates
        try:
            lat_float = float(lat)
            lng_float = float(lng)
            if not (-90 <= lat_float <= 90) or not (-180 <= lng_float <= 180):
                raise ValueError("Invalid coordinates")
        except ValueError:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='BadRequest',
                    message='Invalid latitude or longitude values',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Call weather API
        with httpx.Client(timeout=WEATHER_API_TIMEOUT) as client:
            response = client.get(
                "https://api.weatherapi.com/v1/current.json",
                params={"key": WEATHER_API_KEY, "q": f"{lat},{lng}", "aqi": "no"}
            )
            
            if response.status_code != 200:
                return {
                    'statusCode': response.status_code,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(ErrorResponse(
                        error='WeatherAPIError',
                        message='Failed to fetch weather data',
                        timestamp=get_iso_timestamp()
                    ).dict())
                }
            
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': response.text
            }
        
    except httpx.TimeoutException:
        return {
            'statusCode': 504,
            'headers': CORS_HEADERS,
            'body': json.dumps(ErrorResponse(
                error='GatewayTimeout',
                message='Weather API request timed out',
                timestamp=get_iso_timestamp()
            ).dict())
        }
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps(ErrorResponse(
                error='ValidationError',
                message=str(e),
                timestamp=get_iso_timestamp()
            ).dict())
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(ErrorResponse(
                error='InternalServerError',
                message=str(e),
                timestamp=get_iso_timestamp()
            ).dict())
        }
