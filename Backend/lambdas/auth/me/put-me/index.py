# lambda_update_me.py
import json
import os
import traceback
from schemas import UserUpdate, UserResponse, ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import get_user_by_email, update_user, get_iso_timestamp

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
        
        # Parse update data
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        update_data = UserUpdate(**body)
        
        # Update user
        updates = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            field_name = ''.join(word.capitalize() for word in field.split('_'))
            updates[field_name] = value
        
        updated_user = update_user(token_data['email'], updates)
        
        response = UserResponse(
            user_id=updated_user['UserId'],
            email=updated_user['Email'],
            name=updated_user.get('Name'),
            phone=updated_user.get('Phone'),
            farm_size=updated_user.get('FarmSize'),
            crop_type=updated_user.get('CropType'),
            latitude=updated_user.get('Latitude'),
            longitude=updated_user.get('Longitude'),
            lat_direction=updated_user.get('LatDirection'),
            long_direction=updated_user.get('LongDirection'),
            address=updated_user.get('Address'),
            created_at=updated_user['CreatedAtISO'],
            updated_at=updated_user['UpdatedAtISO']
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
