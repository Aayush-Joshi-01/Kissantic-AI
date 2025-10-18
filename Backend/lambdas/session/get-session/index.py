# lambda_get_session.py
import json
import os
import traceback
from schemas import ChatSessionResponse, MessageResponse, ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import get_chat_session, list_messages, get_iso_timestamp

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
        
        # Get session
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
        
        # Get messages
        messages_result = list_messages(session_id)
        # Sort messages by created_at in ascending order (oldest first)
        sorted_items = sorted(messages_result['items'], key=lambda x: x['CreatedAtISO'])
        messages = [
            MessageResponse(
                message_id=m['MessageId'],
                session_id=m['SessionId'],
                text=m['Text'],
                sender=m['Sender'],
                created_at=m['CreatedAtISO'],
                metadata=m.get('Metadata')
            ) for m in sorted_items
        ]
        
        response = ChatSessionResponse(
            session_id=session['SessionId'],
            user_id=session['UserId'],
            title=session['Title'],
            created_at=session['CreatedAtISO'],
            updated_at=session['UpdatedAtISO'],
            message_count=session.get('MessageCount', 0),
            messages=messages
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
