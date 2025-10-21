"""
Kisaantic AI - Production Lambda Handler
Multi-Agent Agricultural Assistant with Comprehensive Orchestration
"""

import json
import os
import traceback
import asyncio
import logging
from datetime import datetime
import uuid


from schemas import ChatRequest, ChatResponse, MessageResponse, ErrorResponse
from auth import verify_token, extract_token_from_header
from dynamodb_helper import (
    get_chat_session, create_chat_session, create_message, 
    update_chat_session, get_user_by_id, get_iso_timestamp,
    get_chat_history_for_agent, get_timestamp, serialize_item, table
)

# Import orchestrator
try:
    from orchestrator import MultiAgentOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    print("❌ Orchestrator not available")
    ORCHESTRATOR_AVAILABLE = False

# Import agricultural context
try:
    from agriculture_context import AgriculturalContextFetcher
    AGRO_CONTEXT_AVAILABLE = True
except ImportError:
    print("⚠️ Agricultural context fetcher not available")
    AGRO_CONTEXT_AVAILABLE = False

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,Accept,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
}

# Configuration
USE_ORCHESTRATOR = os.getenv('USE_ORCHESTRATOR', 'true').lower() == 'true'
OUTPUT_TOKEN_LIMIT = int(os.getenv('OUTPUT_TOKEN_LIMIT', '5000'))
CHAT_HISTORY_LIMIT = int(os.getenv('CHAT_HISTORY_LIMIT', '10'))
AGRO_API_URL = os.getenv('AGRO_API_URL', 'https://d8o991ajjl.execute-api.ap-south-1.amazonaws.com/api')

# Initialize components
orchestrator = None
agro_fetcher = None

if USE_ORCHESTRATOR and ORCHESTRATOR_AVAILABLE:
    try:
        orchestrator = MultiAgentOrchestrator()
        logger.info("✅ Orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Orchestrator initialization failed: {str(e)}")
        orchestrator = None

if AGRO_CONTEXT_AVAILABLE:
    try:
        agro_fetcher = AgriculturalContextFetcher(AGRO_API_URL)
        logger.info("✅ Agricultural context fetcher initialized")
    except Exception as e:
        logger.error(f"⚠️ Agro fetcher initialization failed: {str(e)}")
        agro_fetcher = None

def lambda_handler(event, context):
    """Main Lambda handler"""
    
    start_time = datetime.now()
    
    logger.info(f"{'='*70}")
    logger.info(f"{'='*70}")
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        logger.info("OPTIONS request - returning CORS headers")
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}
    
    try:
        # ========== AUTHENTICATION ==========
        logger.info("STEP 1: Authentication...")
        
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        
        token = extract_token_from_header(auth_header)
        if not token:
            logger.error("❌ AUTH FAILED: Missing token")
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='Unauthorized',
                    message='Missing or invalid token',
                    timestamp=get_iso_timestamp(),
                ).dict())
            }
        
        token_data = verify_token(token)
        if not token_data:
            logger.error("❌ AUTH FAILED: Invalid token")
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='Unauthorized',
                    message='Invalid token',
                    timestamp=get_iso_timestamp(),
                ).dict())
            }
        
        user_id = token_data['user_id']
        logger.info(f"✅ Authenticated: User {user_id}")
        
        # ========== PARSE REQUEST ==========
        logger.info("STEP 2: Parsing request...")
        
        body = json.loads(event['body']) if 'body' in event and isinstance(event['body'], str) else event.get('body', event)
        chat_request = ChatRequest(**body)
        
        logger.info(f"✅ Request validated: {len(chat_request.message)} chars")
        
        # ========== GET USER DATA ==========
        logger.info("STEP 3: Fetching user data...")
        
        user = get_user_by_id(user_id)
        if not user:
            logger.error(f"❌ USER NOT FOUND: {user_id}")
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='NotFound',
                    message='User not found',
                    timestamp=get_iso_timestamp(),
                ).dict())
            }
        
        logger.info(f"✅ User found: {user.get('Email')}")
        
        # ========== HANDLE SESSION ==========
        logger.info("STEP 4: Managing session...")
        
        if chat_request.session_id:
            session = get_chat_session(chat_request.session_id, user_id)
            if not session:
                logger.error(f"❌ SESSION NOT FOUND: {chat_request.session_id}")
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(ErrorResponse(
                        error='NotFound',
                        message='Session not found',
                        timestamp=get_iso_timestamp(),
                    ).dict())
                }
        else:
            session = create_chat_session(user_id, "New Chat")
        
        session_id = session['SessionId']
        logger.info(f"✅ Session: {session_id}")
        
        # ========== SAVE USER MESSAGE ==========
        logger.info("STEP 5: Saving user message...")
        
        user_message = create_message(
            session_id=session_id,
            text=chat_request.message,
            sender='user',
            metadata={
                'latitude': chat_request.latitude,
                'longitude': chat_request.longitude,
                'address': chat_request.address,
                'weather_temp': chat_request.weather_temp,
                'weather_condition': chat_request.weather_condition,
                'weather_humidity': chat_request.weather_humidity
            }
        )
        
        logger.info(f"✅ User message saved: {user_message['MessageId']}")
        
        # Update session title if first message
        if session.get('MessageCount', 0) == 0:
            title = chat_request.message[:50] + ("..." if len(chat_request.message) > 50 else "")
            update_chat_session(session_id, user_id, title)
        
        # ========== BUILD CONTEXT ==========
        logger.info("STEP 6: Building context...")
        
        user_context = {
            'UserId': user.get('UserId'),
            'Name': user.get('Name'),
            'FarmSize': user.get('FarmSize'),
            'CropType': user.get('CropType'),
            'Address': chat_request.address or user.get('Address'),
            'Latitude': chat_request.latitude or user.get('Latitude'),
            'Longitude': chat_request.longitude or user.get('Longitude')
        }
        
        # Get chat history
        chat_history = []
        try:
            chat_history = get_chat_history_for_agent(
                session_id=session_id,
                limit=CHAT_HISTORY_LIMIT
            )
            logger.info(f"✅ Retrieved {len(chat_history)} history messages")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch history: {str(e)}")
        
        # Fetch agricultural data
        agro_data = None
        lat = user_context.get('Latitude')
        lon = user_context.get('Longitude')
        
        if lat and lon and agro_fetcher:
            logger.info(f"🌾 Fetching agricultural data for ({lat}, {lon})...")
            try:
                loop = asyncio.get_event_loop()
                agro_data = loop.run_until_complete(
                    agro_fetcher.get_complete_dataset(lat, lon)
                )
                if agro_data:
                    logger.info(f"✅ Agricultural data retrieved")
                else:
                    logger.info(f"⚠️ No agricultural data available")
            except Exception as e:
                logger.warning(f"⚠️ Agricultural data fetch failed: {str(e)}")
        
        # Build comprehensive context
        context = {
            'user_profile': user_context,
            'location': {
                'latitude': lat,
                'longitude': lon,
                'address': user_context.get('Address')
            },
            'weather_data': {
                'temp_c': chat_request.weather_temp,
                'condition': chat_request.weather_condition,
                'humidity': chat_request.weather_humidity
            },
            'agricultural_data': agro_data,
            'chat_history': chat_history,
            'query': chat_request.message,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Context built: {len(chat_history)} history, agro_data={'Yes' if agro_data else 'No'}")
        
        # ========== ORCHESTRATION ==========
        logger.info("STEP 7: Multi-agent orchestration...")
        
        if not orchestrator:
            logger.error("❌ CRITICAL: Orchestrator not initialized")
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps(ErrorResponse(
                    error='InternalServerError',
                    message='Orchestrator not available',
                    timestamp=get_iso_timestamp(),
                ).dict())
            }
        
        try:
            loop = asyncio.get_event_loop()
            orchestration_result = loop.run_until_complete(
                orchestrator.process_query(
                    query=chat_request.message,
                    context=context,
                    session_id=str(session_id)
                )
            )
            
            ai_text = orchestration_result.get('final_response')
            analysis = orchestration_result.get('analysis', {})
            agents_used = orchestration_result.get('agents_consulted', [])
            
            logger.info(f"✅ Orchestration complete:")
            logger.info(f"   Query type: {analysis.get('query_type')}")
            logger.info(f"   Agents: {len(agents_used)}")
            logger.info(f"   Response length: {len(ai_text)} chars")
            logger.info(f"   Estimated tokens: ~{int(len(ai_text.split()) * 1.3)}")
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Fallback response
            ai_text = f"""I apologize, but I encountered an issue processing your request. 

However, I'm here to help with:
- 🌾 Crop planning and profitability analysis
- 🚜 Equipment recommendations and vendor connections
- 💰 Market prices and selling strategies
- 🌤️ Weather-based farming advice
- 🌱 Crop management and pest control

Could you please rephrase your question or provide more details? I'll do my best to assist you."""

            analysis = {}
            agents_used = []
        
        # ========== SAVE AI RESPONSE ==========
        logger.info("STEP 8: Processing booking/order suggestions...")

        # Process booking/order suggestions FIRST
        booking_saved = None
        order_saved = None

        if orchestration_result.get('booking_suggestion'):
            try:
                booking_data = orchestration_result['booking_suggestion']
                
                booking_id = str(uuid.uuid4())
                timestamp_booking = int(datetime.now().timestamp())
                iso_timestamp_booking = get_iso_timestamp()
                
                booking_item = {
                    'PK': f'USER#{user_id}',
                    'SK': f'BOOKING#{timestamp_booking}#{booking_id}',
                    'GSI1PK': f'BOOKING#{booking_id}',
                    'GSI1SK': 'METADATA',
                    'GSI2PK': f'USER#{user_id}#STATUS#pending',
                    'GSI2SK': str(timestamp_booking),
                    'EntityType': 'BookingOrder',
                    'BookingOrderId': booking_id,
                    'UserId': user_id,
                    'SessionId': session_id,
                    'MessageId': 'PENDING',  # Will be updated after message creation
                    'Type': 'booking',
                    'VendorName': booking_data['vendor_name'],
                    'ServiceProduct': booking_data['service_product'],
                    'EstimatedCost': booking_data.get('estimated_cost'),
                    'Message': booking_data['message'],
                    'Status': 'pending',
                    'AdditionalInfo': booking_data.get('additional_info', {}),
                    'CreatedAt': timestamp_booking,
                    'UpdatedAt': timestamp_booking,
                    'CreatedAtISO': iso_timestamp_booking,
                    'UpdatedAtISO': iso_timestamp_booking
                }
                
                from dynamodb_helper import serialize_item, table
                table.put_item(Item=serialize_item(booking_item))
                
                booking_saved = booking_item
                logger.info(f"✅ Booking suggestion saved: {booking_id}")
            except Exception as e:
                logger.error(f"❌ Failed to save booking: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

        if orchestration_result.get('order_suggestion'):
            try:
                order_data = orchestration_result['order_suggestion']
                
                order_id = str(uuid.uuid4())
                timestamp_order = int(datetime.now().timestamp())
                iso_timestamp_order = get_iso_timestamp()
                
                order_item = {
                    'PK': f'USER#{user_id}',
                    'SK': f'ORDER#{timestamp_order}#{order_id}',
                    'GSI1PK': f'ORDER#{order_id}',
                    'GSI1SK': 'METADATA',
                    'GSI2PK': f'USER#{user_id}#STATUS#pending',
                    'GSI2SK': str(timestamp_order),
                    'EntityType': 'BookingOrder',
                    'BookingOrderId': order_id,
                    'UserId': user_id,
                    'SessionId': session_id,
                    'MessageId': 'PENDING',  # Will be updated after message creation
                    'Type': 'order',
                    'VendorName': order_data['vendor_name'],
                    'ServiceProduct': order_data['service_product'],
                    'SuggestedQuantity': order_data.get('suggested_quantity'),
                    'EstimatedCost': order_data.get('estimated_cost'),
                    'Message': order_data['message'],
                    'Status': 'pending',
                    'AdditionalInfo': order_data.get('additional_info', {}),
                    'CreatedAt': timestamp_order,
                    'UpdatedAt': timestamp_order,
                    'CreatedAtISO': iso_timestamp_order,
                    'UpdatedAtISO': iso_timestamp_order
                }
                
                from dynamodb_helper import serialize_item, table
                table.put_item(Item=serialize_item(order_item))
                
                order_saved = order_item
                logger.info(f"✅ Order suggestion saved: {order_id}")
            except Exception as e:
                logger.error(f"❌ Failed to save order: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

        # Build ai_metadata with booking/order suggestions
        ai_metadata = {
            'orchestrator_used': True,
            'query_type': analysis.get('query_type'),
            'agents_consulted': agents_used,
            'agent_count': len(agents_used),
            'web_search_used': analysis.get('requires_web_search', False),
            'news_used': analysis.get('requires_news', False),
            'has_agro_data': bool(agro_data),
            'chat_history_length': len(chat_history),
            'response_tokens': int(len(ai_text.split()) * 1.3),
            'processing_time_seconds': (datetime.now() - start_time).total_seconds()
        }

        # Add booking/order suggestions to metadata
        if booking_saved:
            ai_metadata['booking_suggestion'] = {
                'booking_id': booking_saved['BookingOrderId'],
                'vendor': booking_saved['VendorName'],
                'service': booking_saved['ServiceProduct'],
                'message': booking_saved['Message'],
                'estimated_cost': booking_saved.get('EstimatedCost')
            }
        if order_saved:
            ai_metadata['order_suggestion'] = {
                'order_id': order_saved['BookingOrderId'],
                'vendor': order_saved['VendorName'],
                'product': order_saved['ServiceProduct'],
                'message': order_saved['Message'],
                'suggested_quantity': order_saved.get('SuggestedQuantity'),
                'estimated_cost': order_saved.get('EstimatedCost')
            }

        logger.info("STEP 9: Saving AI message with suggestions...")

        ai_message = create_message(
            session_id=session_id,
            text=ai_text,
            sender='ai',
            metadata=ai_metadata
        )

        logger.info(f"✅ AI message saved: {ai_message['MessageId']}")
        
        # ========== BUILD RESPONSE ==========
        response = ChatResponse(
            session_id=session_id,
            user_message=MessageResponse(
                message_id=user_message['MessageId'],
                session_id=user_message['SessionId'],
                text=user_message['Text'],
                sender=user_message['Sender'],
                created_at=user_message['CreatedAtISO'],
                metadata=user_message.get('Metadata')
            ),
            ai_message=MessageResponse(
                message_id=ai_message['MessageId'],
                session_id=ai_message['SessionId'],
                text=ai_message['Text'],
                sender=ai_message['Sender'],
                created_at=ai_message['CreatedAtISO'],
                metadata=ai_message.get('Metadata')
            )
        )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"{'='*70}")
        logger.info(f"✅ REQUEST COMPLETED")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"{'='*70}")
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps(response.dict())
        }
        
    except ValueError as e:
        logger.error(f"❌ VALIDATION ERROR: {str(e)}")
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps(ErrorResponse(
                error='ValidationError',
                message=str(e),
                timestamp=get_iso_timestamp(),
            ).dict())
        }
    except Exception as e:
        logger.error("❌ INTERNAL SERVER ERROR")
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps(ErrorResponse(
                error='InternalServerError',
                message=f"{type(e).__name__}: {str(e)}",
                timestamp=get_iso_timestamp(),
            ).dict())
        }