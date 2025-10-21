"""
Lambda: Get User Bookings and Orders
GET /bookings-orders?status=pending
"""
import json
import logging
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from auth import verify_token, extract_token_from_header
from dynamodb_helper import deserialize_item

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('kissantic')

dynamodb = boto3.resource('dynamodb')

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}

def lambda_handler(event, context):
    """Get user's bookings and orders"""
    
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
        
        # Get query params
        query_params = event.get('queryStringParameters') or {}
        status = query_params.get('status')  # pending, approved, rejected, cancelled
        booking_type = query_params.get('type')  # 'booking' or 'order'
        
        logger.info(f"Fetching bookings/orders for user: {user_id}, status: {status}, type: {booking_type}")
        
        # Query DynamoDB
        if status:
            # Query by status using GSI2
            response = table.query(
                IndexName='GSI2',
                KeyConditionExpression=Key('GSI2PK').eq(f'USER#{user_id}#STATUS#{status}'),
                ScanIndexForward=False,  # Newest first
                Limit=100
            )
            items = response.get('Items', [])
        else:
            # Query all bookings/orders for user
            response = table.query(
                KeyConditionExpression=Key('PK').eq(f'USER#{user_id}'),
                ScanIndexForward=False,
                Limit=100
            )
            # Filter only booking/order items
            items = [
                item for item in response.get('Items', [])
                if item.get('SK', '').startswith('BOOKING#') or item.get('SK', '').startswith('ORDER#')
            ]
        
        # Deserialize items
        items = [deserialize_item(item) for item in items]
        
        # Filter by type if specified
        if booking_type:
            items = [item for item in items if item.get('Type') == booking_type]
        
        # Separate bookings and orders
        bookings = [item for item in items if item.get('Type') == 'booking']
        orders = [item for item in items if item.get('Type') == 'order']
        
        logger.info(f"Found {len(bookings)} bookings, {len(orders)} orders")
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'bookings': bookings,
                'orders': orders,
                'total_count': len(items),
                'bookings_count': len(bookings),
                'orders_count': len(orders)
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