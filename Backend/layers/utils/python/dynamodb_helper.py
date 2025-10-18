# dynamodb_helper.py
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, List, Any

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('kissantic')

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def serialize_item(item: Dict) -> Dict:
    """Convert Python types to DynamoDB compatible types"""
    return json.loads(json.dumps(item, default=str), parse_float=Decimal)

def deserialize_item(item: Dict) -> Dict:
    """Convert DynamoDB types to Python types"""
    return json.loads(json.dumps(item, default=decimal_to_float))

def get_timestamp() -> int:
    """Get current Unix timestamp"""
    return int(datetime.utcnow().timestamp())

def get_iso_timestamp() -> str:
    """Get current ISO format timestamp"""
    return datetime.utcnow().isoformat() + 'Z'

# User Operations
def create_user(email: str, hashed_password: str, name: Optional[str] = None) -> Dict:
    user_id = str(uuid.uuid4())
    timestamp = get_timestamp()
    iso_timestamp = get_iso_timestamp()
    
    item = {
        'PK': f'USER#{email}',
        'SK': 'PROFILE',
        'GSI1PK': f'USER#{user_id}',
        'GSI1SK': 'PROFILE',
        'EntityType': 'User',
        'UserId': user_id,
        'Email': email,
        'HashedPassword': hashed_password,
        'Name': name,
        'Phone': None,
        'FarmSize': None,
        'CropType': None,
        'Latitude': None,
        'Longitude': None,
        'LatDirection': None,
        'LongDirection': None,
        'Address': None,
        'CreatedAt': timestamp,
        'UpdatedAt': timestamp,
        'CreatedAtISO': iso_timestamp,
        'UpdatedAtISO': iso_timestamp
    }
    
    table.put_item(Item=serialize_item(item))
    return deserialize_item(item)

def get_user_by_email(email: str) -> Optional[Dict]:
    response = table.get_item(
        Key={'PK': f'USER#{email}', 'SK': 'PROFILE'}
    )
    return deserialize_item(response['Item']) if 'Item' in response else None

def get_user_by_id(user_id: str) -> Optional[Dict]:
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq(f'USER#{user_id}') & Key('GSI1SK').eq('PROFILE')
    )
    items = response.get('Items', [])
    return deserialize_item(items[0]) if items else None

def update_user(email: str, updates: Dict) -> Dict:
    timestamp = get_timestamp()
    iso_timestamp = get_iso_timestamp()
    
    update_expression = "SET UpdatedAt = :updated_at, UpdatedAtISO = :updated_at_iso"
    expression_values = {
        ':updated_at': timestamp,
        ':updated_at_iso': iso_timestamp
    }
    expression_names = {}
    
    for key, value in updates.items():
        if value is not None:
            attr_name = f"#{key.lower()}"
            attr_value = f":{key.lower()}"
            update_expression += f", {attr_name} = {attr_value}"
            expression_values[attr_value] = value
            expression_names[attr_name] = key
    
    update_params = {
        'Key': {'PK': f'USER#{email}', 'SK': 'PROFILE'},
        'UpdateExpression': update_expression,
        'ExpressionAttributeValues': serialize_item(expression_values),
        'ReturnValues': 'ALL_NEW'
    }
    
    if expression_names:
        update_params['ExpressionAttributeNames'] = expression_names
    
    response = table.update_item(**update_params)
    
    return deserialize_item(response['Attributes'])

# Refresh Token Operations
def create_refresh_token(email: str, device_id: Optional[str] = None) -> str:
    token_id = str(uuid.uuid4())
    timestamp = get_timestamp()
    expiry = timestamp + (30 * 24 * 60 * 60)  # 30 days
    
    item = {
        'PK': f'USER#{email}',
        'SK': f'REFRESH_TOKEN#{token_id}',
        'EntityType': 'RefreshToken',
        'TokenId': token_id,
        'Email': email,
        'DeviceId': device_id,
        'CreatedAt': timestamp,
        'TTL': expiry
    }
    
    table.put_item(Item=serialize_item(item))
    return token_id

def verify_refresh_token(token_id: str, email: str) -> bool:
    response = table.get_item(
        Key={'PK': f'USER#{email}', 'SK': f'REFRESH_TOKEN#{token_id}'}
    )
    return 'Item' in response

def revoke_refresh_token(token_id: str, email: str):
    table.delete_item(
        Key={'PK': f'USER#{email}', 'SK': f'REFRESH_TOKEN#{token_id}'}
    )

def revoke_all_refresh_tokens(email: str):
    response = table.query(
        KeyConditionExpression=Key('PK').eq(f'USER#{email}') & Key('SK').begins_with('REFRESH_TOKEN#')
    )
    
    with table.batch_writer() as batch:
        for item in response.get('Items', []):
            batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})

# Chat Session Operations
def create_chat_session(user_id: str, title: str = "New Chat") -> Dict:
    session_id = str(uuid.uuid4())
    timestamp = get_timestamp()
    iso_timestamp = get_iso_timestamp()
    
    item = {
        'PK': f'USER#{user_id}',
        'SK': f'SESSION#{session_id}',
        'GSI1PK': f'SESSION#{session_id}',
        'GSI1SK': 'METADATA',
        'GSI2PK': f'USER#{user_id}',
        'GSI2SK': str(timestamp),
        'EntityType': 'ChatSession',
        'SessionId': session_id,
        'UserId': user_id,
        'Title': title,
        'MessageCount': 0,
        'CreatedAt': timestamp,
        'UpdatedAt': timestamp,
        'CreatedAtISO': iso_timestamp,
        'UpdatedAtISO': iso_timestamp
    }
    
    table.put_item(Item=serialize_item(item))
    return deserialize_item(item)

def get_chat_session(session_id: str, user_id: str) -> Optional[Dict]:
    response = table.get_item(
        Key={'PK': f'USER#{user_id}', 'SK': f'SESSION#{session_id}'}
    )
    return deserialize_item(response['Item']) if 'Item' in response else None

def list_chat_sessions(user_id: str, limit: int = 20, last_key: Optional[str] = None) -> Dict:
    query_kwargs = {
        'IndexName': 'GSI2',
        'KeyConditionExpression': Key('GSI2PK').eq(f'USER#{user_id}'),
        'ScanIndexForward': False,  # Descending order
        'Limit': limit
    }
    
    if last_key:
        query_kwargs['ExclusiveStartKey'] = json.loads(last_key)
    
    response = table.query(**query_kwargs)
    
    return {
        'items': [deserialize_item(item) for item in response.get('Items', [])],
        'last_evaluated_key': json.dumps(response['LastEvaluatedKey']) if 'LastEvaluatedKey' in response else None,
        'count': len(response.get('Items', []))
    }

def update_chat_session(session_id: str, user_id: str, title: str) -> Dict:
    timestamp = get_timestamp()
    iso_timestamp = get_iso_timestamp()
    
    response = table.update_item(
        Key={'PK': f'USER#{user_id}', 'SK': f'SESSION#{session_id}'},
        UpdateExpression='SET Title = :title, UpdatedAt = :updated_at, UpdatedAtISO = :updated_at_iso, GSI2SK = :gsi2sk',
        ExpressionAttributeValues=serialize_item({
            ':title': title,
            ':updated_at': timestamp,
            ':updated_at_iso': iso_timestamp,
            ':gsi2sk': str(timestamp)
        }),
        ReturnValues='ALL_NEW'
    )
    
    return deserialize_item(response['Attributes'])

def delete_chat_session(session_id: str, user_id: str):
    # Delete session
    table.delete_item(
        Key={'PK': f'USER#{user_id}', 'SK': f'SESSION#{session_id}'}
    )
    
    # Delete all messages
    response = table.query(
        KeyConditionExpression=Key('PK').eq(f'SESSION#{session_id}')
    )
    
    with table.batch_writer() as batch:
        for item in response.get('Items', []):
            batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})

# Message Operations
def create_message(session_id: str, text: str, sender: str, metadata: Optional[Dict] = None) -> Dict:
    message_id = str(uuid.uuid4())
    timestamp = get_timestamp()
    iso_timestamp = get_iso_timestamp()
    
    item = {
        'PK': f'SESSION#{session_id}',
        'SK': f'MESSAGE#{timestamp}#{message_id}',
        'GSI1PK': f'SESSION#{session_id}',
        'GSI1SK': f'MESSAGE#{timestamp}',
        'EntityType': 'Message',
        'MessageId': message_id,
        'SessionId': session_id,
        'Text': text,
        'Sender': sender,
        'Metadata': metadata,
        'CreatedAt': timestamp,
        'CreatedAtISO': iso_timestamp
    }
    
    table.put_item(Item=serialize_item(item))
    
    # Increment message count
    table.update_item(
        Key={'PK': f'USER#{session_id.split("#")[0]}', 'SK': f'SESSION#{session_id}'},
        UpdateExpression='ADD MessageCount :inc SET UpdatedAt = :updated_at, UpdatedAtISO = :updated_at_iso',
        ExpressionAttributeValues=serialize_item({
            ':inc': 1,
            ':updated_at': timestamp,
            ':updated_at_iso': iso_timestamp
        })
    )
    
    return deserialize_item(item)

def list_messages(session_id: str, limit: int = 50, last_key: Optional[str] = None) -> Dict:
    query_kwargs = {
        'KeyConditionExpression': Key('PK').eq(f'SESSION#{session_id}'),
        'ScanIndexForward': True,  # Ascending order
        'Limit': limit
    }
    
    if last_key:
        query_kwargs['ExclusiveStartKey'] = json.loads(last_key)
    
    response = table.query(**query_kwargs)
    
    return {
        'items': [deserialize_item(item) for item in response.get('Items', [])],
        'last_evaluated_key': json.dumps(response['LastEvaluatedKey']) if 'LastEvaluatedKey' in response else None,
        'count': len(response.get('Items', []))
    }

def get_chat_history_for_agent(
    session_id: str,
    limit: int = 10,
    include_metadata: bool = False
) -> List[Dict]:
    """
    Get formatted chat history for Bedrock Agent context
    Returns recent messages in chronological order (oldest first)
    
    Args:
        session_id: The chat session ID
        limit: Maximum number of messages to retrieve (default: 10)
        include_metadata: Whether to include message metadata (default: False)
        
    Returns:
        List of message dictionaries formatted for agent context
        Example: [
            {'Sender': 'user', 'Text': 'Hello', 'CreatedAt': '2025-01-15T10:30:00Z'},
            {'Sender': 'ai', 'Text': 'Hi there!', 'CreatedAt': '2025-01-15T10:30:05Z'}
        ]
    """
    try:
        # Query messages for this session using GSI1
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'SESSION#{session_id}') & Key('GSI1SK').begins_with('MESSAGE#'),
            ScanIndexForward=False,  # Get most recent first
            Limit=limit
        )
        
        messages = [deserialize_item(item) for item in response.get('Items', [])]
        
        # Sort by CreatedAtISO in ascending order (oldest first) - consistent with get_session
        messages = sorted(messages, key=lambda x: x['CreatedAtISO'])
        
        # Format for agent context
        formatted_history = []
        for msg in messages:
            history_item = {
                'Sender': msg.get('Sender'),
                'Text': msg.get('Text'),
                'CreatedAt': msg.get('CreatedAtISO')
            }
            
            # Optionally include metadata
            if include_metadata and msg.get('Metadata'):
                history_item['Metadata'] = msg['Metadata']
            
            formatted_history.append(history_item)
        
        return formatted_history
        
    except Exception as e:
        print(f"Error getting chat history for agent: {e}")
        
        return []