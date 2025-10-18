import json
import logging
from dataclasses import asdict
import asyncio

from common import get_aggregator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def get_historical_data(lat: float, lon: float):
    """Async wrapper for historical analysis"""
    aggregator = get_aggregator()
    return await aggregator.get_historical_analysis(lat=lat, lon=lon)

def lambda_handler(event, context):
    """
    Historical seasonal analysis
    """
    try:
        lat = float(event["queryStringParameters"]["lat"])
        lon = float(event["queryStringParameters"]["lon"])

        logger.info(f"Historical analysis request: lat={lat}, lon={lon}")

        dataset = asyncio.run(get_historical_data(lat, lon))

        response = asdict(dataset)
        response["api_version"] = "2.0.0"
        response["lambda_optimized"] = True

        logger.info(f"Historical analysis completed for lat={lat}, lon={lon}")
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
        logger.error(f"Error in historical analysis: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
            "body": json.dumps({"detail": str(e)})
        }