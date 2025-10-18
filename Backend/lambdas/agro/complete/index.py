import json
import logging
from dataclasses import asdict
import asyncio
from datetime import datetime

from common import get_aggregator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def get_all_data(lat: float, lon: float):
    """Async wrapper for fetching all data"""
    aggregator = get_aggregator()
    
    historical = await aggregator.get_historical_analysis(lat=lat, lon=lon)
    current = await aggregator.get_current_minimal(lat=lat, lon=lon)
    soil = await aggregator.get_soil_analysis(lat=lat, lon=lon)
    
    return historical, current, soil

def lambda_handler(event, context):
    """
    Complete dataset - all data in one request
    """
    try:
        lat = float(event["queryStringParameters"]["lat"])
        lon = float(event["queryStringParameters"]["lon"])

        logger.info(f"Complete dataset request: lat={lat}, lon={lon}")

        historical, current, soil = asyncio.run(get_all_data(lat, lon))

        response = {
            "location": {"lat": lat, "lon": lon},
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0",
            "historical": asdict(historical),
            "current": asdict(current["current"]),
            "soil": asdict(soil["soil"])
        }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps(response)
        }

    except (ValueError, KeyError) as e:
        logger.error(f"Validation error: {e}")
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps({"detail": str(e)})
        }
    except Exception as e:
        logger.error(f"Error fetching complete dataset: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps({"detail": str(e)})
        }