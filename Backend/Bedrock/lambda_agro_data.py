"""
Agricultural Data Lambda Function for Bedrock Agent Action Group
Fetches real-time weather, soil, and seasonal data from Agro API
"""

import json
import os
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create HTTP client
http = urllib3.PoolManager()

def fetch_agro_data(latitude: float, longitude: float) -> dict:
    """
    Fetch comprehensive agricultural data from Agro API
    """
    api_url = os.environ.get('AGRO_API_URL', 
                             'https://d8o991ajjl.execute-api.ap-south-1.amazonaws.com/api')
    
    try:
        logger.info(f"Fetching agro data for: ({latitude}, {longitude})")
        
        # Call complete dataset endpoint
        url = f"{api_url}/complete?lat={latitude}&lon={longitude}"
        
        response = http.request(
            'GET',
            url,
            timeout=30.0
        )
        
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            
            logger.info("Successfully fetched agro data")
            
            # Extract key information
            result = {
                "success": True,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "current_weather": {},
                "soil_data": {},
                "seasonal_context": {},
                "raw_data": data  # Include full data
            }
            
            # Extract current weather
            if 'current' in data:
                current = data['current']
                result['current_weather'] = {
                    "temperature_c": current.get('temp_c'),
                    "feels_like_c": current.get('feels_like_c'),
                    "humidity_pct": current.get('humidity_pct'),
                    "precipitation_mm": current.get('precipitation_mm'),
                    "wind_speed_kmh": current.get('wind_speed_kmh'),
                    "condition": current.get('condition'),
                    "uv_index": current.get('uv_index')
                }
            
            # Extract soil data
            if 'soil' in data:
                soil = data['soil']
                result['soil_data'] = {
                    "moisture_0_1cm": soil.get('moisture_0_1'),
                    "moisture_1_3cm": soil.get('moisture_1_3'),
                    "avg_moisture": soil.get('avg_moisture'),
                    "dryness_index": soil.get('dryness_index'),
                    "temp_0cm": soil.get('temp_0cm'),
                    "temp_6cm": soil.get('temp_6cm'),
                    "moisture_trend": soil.get('moisture_trend')
                }
            
            # Extract seasonal context
            if 'historical' in data:
                historical = data['historical']
                result['seasonal_context'] = {
                    "current_season": historical.get('relevant_season'),
                    "season_stage": historical.get('season_context'),
                    "comparison": historical.get('seasonal_comparison', {})
                }
                
                # Add anomaly flags if present
                comparison = historical.get('seasonal_comparison', {})
                anomalies = comparison.get('anomaly_flags', [])
                if anomalies:
                    result['seasonal_context']['anomalies'] = anomalies
            
            return result
            
        else:
            error_msg = f"Agro API returned status {response.status}"
            logger.error(error_msg)
            
            # Try to get error details
            try:
                error_data = json.loads(response.data.decode('utf-8'))
                error_msg = f"{error_msg}: {error_data.get('message', 'Unknown error')}"
            except:
                pass
            
            return {
                "success": False,
                "error": error_msg,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
            
    except Exception as e:
        error_msg = f"Agro data fetch error: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

def lambda_handler(event, context):
    """
    Lambda handler for Bedrock Agent Action Group
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract parameters from Bedrock Agent event
    action = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    request_body = event.get('requestBody', {})
    
    # Get latitude and longitude from requestBody
    latitude = None
    longitude = None
    
    if request_body:
        content = request_body.get('content', {})
        application_json = content.get('application/json', {})
        properties = application_json.get('properties', [])
        
        for prop in properties:
            prop_name = prop.get('name', '')
            prop_value = prop.get('value', '')
            
            if prop_name == 'latitude':
                try:
                    latitude = float(prop_value)
                except (ValueError, TypeError):
                    logger.error(f"Invalid latitude: {prop_value}")
            elif prop_name == 'longitude':
                try:
                    longitude = float(prop_value)
                except (ValueError, TypeError):
                    logger.error(f"Invalid longitude: {prop_value}")
    
    # Fallback: check old parameters format
    if latitude is None or longitude is None:
        parameters = event.get('parameters', [])
        for param in parameters:
            param_name = param.get('name', '')
            param_value = param.get('value', '')
            
            if param_name == 'latitude':
                try:
                    latitude = float(param_value)
                except (ValueError, TypeError):
                    pass
            elif param_name == 'longitude':
                try:
                    longitude = float(param_value)
                except (ValueError, TypeError):
                    pass
    
    # Validate coordinates
    if latitude is None or longitude is None:
        result = {
            "success": False,
            "error": "Invalid or missing coordinates. Latitude and longitude required."
        }
    else:
        # Fetch agro data
        result = fetch_agro_data(latitude, longitude)
    
    # Return in Bedrock Agent format
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': response_body
        }
    }