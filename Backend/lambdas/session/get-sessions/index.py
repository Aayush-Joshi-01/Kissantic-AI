# lambda_get_sessions.py
import json
import os
import traceback
from schemas import ChatSessionResponse, PaginatedResponse, ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import list_chat_sessions, get_iso_timestamp

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
        
        # Get pagination parameters
        params = event.get('queryStringParameters') or {}
        limit = int(params.get('limit', 20))
        last_key = params.get('last_key')
        
        # Validate limit
        if not (1 <= limit <= 100):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='BadRequest',
                    message='Limit must be between 1 and 100',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Get sessions
        result = list_chat_sessions(token_data['user_id'], limit, last_key)
        
        sessions = [
            ChatSessionResponse(
                session_id=s['SessionId'],
                user_id=s['UserId'],
                title=s['Title'],
                created_at=s['CreatedAtISO'],
                updated_at=s['UpdatedAtISO'],
                message_count=s.get('MessageCount', 0),
                messages=[]
            ).dict() for s in result['items']
        ]
        
        response = PaginatedResponse(
            items=sessions,
            last_evaluated_key=result['last_evaluated_key'],
            count=result['count']
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
