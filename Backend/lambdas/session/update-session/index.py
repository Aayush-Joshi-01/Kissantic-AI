# lambda_update_session.py
import json
import os
import traceback
from schemas import ChatSessionUpdate, ChatSessionResponse, ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import get_chat_session, update_chat_session, get_iso_timestamp

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
        
        # Get session ID
        path_params = event.get('pathParameters') or {}
        session_id = path_params.get('session_id')
        if not session_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='BadRequest',
                    message='Missing session_id in path',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Check if session exists
        session = get_chat_session(session_id, token_data['user_id'])
        if not session:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='NotFound',
                    message='Session not found',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Parse update data
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        update_data = ChatSessionUpdate(**body)
        
        if not update_data.title:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='BadRequest',
                    message='Title is required',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Update session
        updated_session = update_chat_session(session_id, token_data['user_id'], update_data.title)
        
        response = ChatSessionResponse(
            session_id=updated_session['SessionId'],
            user_id=updated_session['UserId'],
            title=updated_session['Title'],
            created_at=updated_session['CreatedAtISO'],
            updated_at=updated_session['UpdatedAtISO'],
            message_count=updated_session.get('MessageCount', 0),
            messages=[]
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
