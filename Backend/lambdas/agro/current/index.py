import json
import logging
from dataclasses import asdict
import asyncio

from common import get_aggregator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def get_current_data(lat: float, lon: float):
    """Async wrapper for current conditions"""
    aggregator = get_aggregator()
    return await aggregator.get_current_minimal(lat=lat, lon=lon)

def lambda_handler(event, context):
    """
    Current weather conditions - fastest endpoint
    """
    try:
        lat = float(event["queryStringParameters"]["lat"])
        lon = float(event["queryStringParameters"]["lon"])

        logger.info(f"Current conditions request: lat={lat}, lon={lon}")

        data = asyncio.run(get_current_data(lat, lon))

        data["current"] = asdict(data["current"])
        data["api_version"] = "2.0.0"

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps(data)
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
        logger.error(f"Error fetching current conditions: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps({"detail": str(e)})
        }