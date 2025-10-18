# lambda_signup.py
import json
import os
import traceback
from datetime import timedelta
from schemas import UserCreate, Token, ErrorResponse
from auth import get_password_hash, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from dynamodb_helper import create_user, get_user_by_email, create_refresh_token as create_refresh_token_db, get_iso_timestamp

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
    
    request_id = 'unknown'
    try:
        request_id = context.aws_request_id if context else 'local'
    except (AttributeError, TypeError):
        pass
    
    try:
        # Handle different event formats
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        user_data = UserCreate(**body)
        
        # Check if user exists
        existing_user = get_user_by_email(user_data.email)
        if existing_user:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='BadRequest',
                    message='Email already registered',
                    timestamp=get_iso_timestamp(),
                    request_id=request_id
                ).dict())
            }
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            name=user_data.name
        )
        
        # Create tokens
        token_data = {"sub": user['Email'], "user_id": user['UserId']}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token
        refresh_token_id = create_refresh_token_db(user['Email'])
        
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
                timestamp=get_iso_timestamp(),
                request_id=request_id
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
                timestamp=get_iso_timestamp(),
                request_id=request_id
            ).dict())
        }
