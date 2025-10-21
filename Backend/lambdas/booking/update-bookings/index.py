"""
Lambda: Update Booking/Order Status
PUT /bookings-orders/update
Body: {"booking_order_id": "...", "status": "approved|rejected|cancelled"}
"""

import json
import logging
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from auth import verify_token, extract_token_from_header
from dynamodb_helper import deserialize_item
from decimal import Decimal
from datetime import datetime
from schemas import ErrorResponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('kissantic')

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'PUT,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def deserialize_item(item):
    """Convert DynamoDB types to Python types"""
    return json.loads(json.dumps(item, default=decimal_to_float))

def serialize_item(item):
    """Convert Python types to DynamoDB compatible types"""
    return json.loads(json.dumps(item, default=str), parse_float=Decimal)

def get_iso_timestamp():
    """Get ISO timestamp"""
    return datetime.utcnow().isoformat() + 'Z'

def get_timestamp():
    """Get Unix timestamp"""
    return int(datetime.utcnow().timestamp())

def lambda_handler(event, context):
    """Update booking/order status"""
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}
    
    try:
        # Auth
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        token = extract_token_from_header(auth_header)
        
        if not token:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Unauthorized', 'message': 'Missing token'})
            }
        
        token_data = verify_token(token)
        if not token_data:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Unauthorized', 'message': 'Invalid token'})
            }
        
        user_id = token_data['user_id']
        
        # Parse body
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        booking_order_id = body.get('booking_order_id')
        booking_order_type = body.get('type')  # 'booking' or 'order'
        new_status = body.get('status')
        
        if not all([booking_order_id, booking_order_type, new_status]):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'ValidationError',
                    'message': 'booking_order_id, type, and status are required'
                })
            }
        
        if new_status not in ['approved', 'rejected', 'cancelled']:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'ValidationError',
                    'message': 'status must be: approved, rejected, or cancelled'
                })
            }
        
        logger.info(f"Updating {booking_order_type} {booking_order_id} to {new_status} for user {user_id}")
        
        # Get current item using GSI1 to find the SK
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'{booking_order_type.upper()}#{booking_order_id}') & Key('GSI1SK').eq('METADATA')
        )
        
        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'NotFound', 'message': 'Booking/order not found'})
            }
        
        current_item = response['Items'][0]
        
        # Verify ownership
        if current_item.get('UserId') != user_id:
            return {
                'statusCode': 403,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Forbidden', 'message': 'Unauthorized access'})
            }
        
        # Update status
        timestamp = get_timestamp()
        iso_timestamp = get_iso_timestamp()
        
        update_response = table.update_item(
            Key={'PK': f'USER#{user_id}', 'SK': current_item['SK']},
            UpdateExpression='SET #status = :new_status, GSI2PK = :new_gsi2pk, UpdatedAt = :updated_at, UpdatedAtISO = :updated_at_iso',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues=serialize_item({
                ':new_status': new_status,
                ':new_gsi2pk': f'USER#{user_id}#STATUS#{new_status}',
                ':updated_at': timestamp,
                ':updated_at_iso': iso_timestamp
            }),
            ReturnValues='ALL_NEW'
        )
        
        updated_item = deserialize_item(update_response['Attributes'])
        
        logger.info(f"✅ Status updated successfully")
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'message': f'Status updated to {new_status}',
                'booking_order': updated_item
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'InternalServerError', 'message': str(e)})
        }