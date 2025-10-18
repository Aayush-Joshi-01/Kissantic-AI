# lambda_get_me.py
import json
import os
import traceback
from schemas import UserResponse, ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import get_user_by_email, get_iso_timestamp

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
        print(f"HEADERS: {json.dumps(headers)}")
        
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        print(f"AUTH_HEADER: {auth_header}")
        
        token = extract_token_from_header(auth_header)
        print(f"EXTRACTED_TOKEN: {token}")
        
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
        print(f"TOKEN_DATA: {token_data}")
        
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
        
        # Get user
        user = get_user_by_email(token_data['email'])
        if not user:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='NotFound',
                    message='User not found',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        response = UserResponse(
            user_id=user['UserId'],
            email=user['Email'],
            name=user.get('Name'),
            phone=user.get('Phone'),
            farm_size=user.get('FarmSize'),
            crop_type=user.get('CropType'),
            latitude=user.get('Latitude'),
            longitude=user.get('Longitude'),
            lat_direction=user.get('LatDirection'),
            long_direction=user.get('LongDirection'),
            address=user.get('Address'),
            created_at=user['CreatedAtISO'],
            updated_at=user['UpdatedAtISO']
        )
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps(response.dict())
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
