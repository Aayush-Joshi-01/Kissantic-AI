import json
import logging
from dataclasses import asdict
import asyncio

from common import get_aggregator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def get_soil_data(lat: float, lon: float):
    """Async wrapper for soil analysis"""
    aggregator = get_aggregator()
    return await aggregator.get_soil_analysis(lat=lat, lon=lon)

def lambda_handler(event, context):
    """
    Soil analysis with EDA
    """
    try:
        lat = float(event["queryStringParameters"]["lat"])
        lon = float(event["queryStringParameters"]["lon"])

        logger.info(f"Soil analysis request: lat={lat}, lon={lon}")

        data = asyncio.run(get_soil_data(lat, lon))

        data["soil"] = asdict(data["soil"])
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
        logger.error(f"Error fetching soil analysis: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps({"detail": str(e)})
        }