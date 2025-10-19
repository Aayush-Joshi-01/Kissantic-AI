"""
Web Search Lambda Function for Bedrock Agent Action Group
Uses LangSearch API for real-time web search
"""

import json
import os
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create HTTP client
http = urllib3.PoolManager()

def search_web(query: str) -> dict:
    """
    Execute web search using LangSearch API
    """
    api_key = os.environ.get('LANGSEARCH_API_KEY', '')
    
    if not api_key:
        logger.error("LANGSEARCH_API_KEY not set")
        return {
            "success": False,
            "error": "API key not configured",
            "results": []
        }
    
    try:
        logger.info(f"Searching web for: {query}")
        
        # LangSearch API request
        url = 'https://api.langsearch.com/v1/web-search'
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        body = {
            'query': query,
            'freshness': 'oneWeek',
            'summary': True,
            'count': 5
        }
        
        response = http.request(
            'POST',
            url,
            headers=headers,
            body=json.dumps(body),
            timeout=10.0
        )
        
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            
            # Extract results
            web_pages = data.get('webPages', {})
            results = web_pages.get('value', [])
            
            # Format results
            formatted_results = []
            for result in results[:5]:  # Top 5 results
                formatted_results.append({
                    'title': result.get('name', 'No title'),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', ''),
                    'datePublished': result.get('datePublished', '')
                })
            
            logger.info(f"Found {len(formatted_results)} results")
            
            return {
                "success": True,
                "results": formatted_results,
                "query": query
            }
        else:
            error_msg = f"LangSearch API returned status {response.status}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "results": []
            }
            
    except Exception as e:
        error_msg = f"Web search error: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "results": []
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
            "results": []
        }
    else:
        # Execute web search
        result = search_web(query)
    
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