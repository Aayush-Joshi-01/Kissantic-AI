
"""
News Search Lambda Function for Bedrock Agent Action Group
Uses NewsAPI.org for agricultural news and policy updates
"""

import json
import os
import urllib3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create HTTP client
http = urllib3.PoolManager()

def search_news(query: str) -> dict:
    """
    Search for agricultural news using NewsAPI.org
    """
    api_key = os.environ.get('NEWS_API_KEY', '')
    
    if not api_key:
        logger.error("NEWS_API_KEY not set")
        return {
            "success": False,
            "error": "API key not configured",
            "articles": []
        }
    
    try:
        logger.info(f"Searching news for: {query}")
        
        # NewsAPI endpoint
        url = 'https://newsapi.org/v2/everything'
        
        # Calculate date range (last 30 days)
        today = datetime.now()
        from_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Build query parameters
        params = {
            'q': query,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'from': from_date,
            'pageSize': 10
        }
        
        # Build URL with parameters
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"
        
        response = http.request(
            'GET',
            full_url,
            timeout=10.0
        )
        
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            
            # Check status
            if data.get('status') != 'ok':
                error_msg = f"NewsAPI error: {data.get('message', 'Unknown error')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "articles": []
                }
            
            # Extract articles
            articles = data.get('articles', [])
            
            # Format articles
            formatted_articles = []
            for article in articles[:10]:  # Top 10 articles
                formatted_articles.append({
                    'title': article.get('title', 'No title'),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'publishedAt': article.get('publishedAt', ''),
                    'author': article.get('author', 'Unknown')
                })
            
            logger.info(f"Found {len(formatted_articles)} articles")
            
            return {
                "success": True,
                "articles": formatted_articles,
                "totalResults": data.get('totalResults', 0),
                "query": query
            }
            
        elif response.status == 426:
            # Rate limit or upgrade required
            error_msg = "NewsAPI rate limit exceeded or upgrade required"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "articles": []
            }
            
        elif response.status == 401:
            # Invalid API key
            error_msg = "Invalid NewsAPI key"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "articles": []
            }
            
        else:
            error_msg = f"NewsAPI returned status {response.status}"
            logger.error(error_msg)
            
            # Try to get error details
            try:
                error_data = json.loads(response.data.decode('utf-8'))
                error_msg = f"{error_msg}: {error_data.get('message', 'Unknown error')}"
            except:
                pass
            
            return {
                "success": False,
                "error": error_msg,
                "articles": []
            }
            
    except Exception as e:
        error_msg = f"News search error: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "articles": []
        }

def lambda_handler(event, context):
    """
    Lambda handler for Bedrock Agent Action Group
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract parameters from Bedrock Agent event
    action = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    request_body = event.get('requestBody', {})
    
    # Get query from requestBody
    query = ''
    
    if request_body:
        content = request_body.get('content', {})
        application_json = content.get('application/json', {})
        properties = application_json.get('properties', [])
        
        for prop in properties:
            if prop.get('name') == 'query':
                query = prop.get('value', '')
                break
    
    # Fallback: check old parameters format
    if not query:
        parameters = event.get('parameters', [])
        for param in parameters:
            if param.get('name') == 'query':
                query = param.get('value', '')
                break
    
    if not query:
        result = {
            "success": False,
            "error": "No query provided",
            "articles": []
        }
    else:
        # Execute news search
        result = search_news(query)
    
    # Return in Bedrock Agent format
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': response_body
        }
    }