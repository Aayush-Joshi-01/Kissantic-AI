# lambda_refresh_token.py
import json
import os
import traceback
from schemas import RefreshTokenRequest, Token, ErrorResponse
from auth import verify_token, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from dynamodb_helper import get_user_by_email, create_refresh_token as create_refresh_token_db, get_iso_timestamp

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
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        request_data = RefreshTokenRequest(**body)
        
        # Verify refresh token JWT
        token_data = verify_token(request_data.refresh_token, token_type='refresh')
        if not token_data:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='Unauthorized',
                    message='Invalid refresh token',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        email = token_data['email']
        
        # Get user
        user = get_user_by_email(email)
        if not user:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='Unauthorized',
                    message='User not found',
                    timestamp=get_iso_timestamp()
                ).dict())
            }
        
        # Create new tokens
        new_token_data = {"sub": user['Email'], "user_id": user['UserId']}
        access_token = create_access_token(new_token_data)
        refresh_token = create_refresh_token(new_token_data)
        
        # Store new refresh token
        new_refresh_token_id = create_refresh_token_db(user['Email'])
        
        response = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
