# lambda_logout.py
import json
import os
import traceback
from schemas import ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import revoke_all_refresh_tokens, get_iso_timestamp

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
        # Debug: Log the event to see header structure
        print(f"EVENT: {json.dumps(event)}")
        
        # Extract and verify token - check both casing
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        
        print(f"AUTH_HEADER: {auth_header}")
        
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
        
        # Revoke all refresh tokens
        revoke_all_refresh_tokens(token_data['email'])
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': 'Logged out successfully'})
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
