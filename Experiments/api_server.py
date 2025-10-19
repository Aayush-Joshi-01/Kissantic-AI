from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os
from dataclasses import asdict

from agro_weather import (
    AgriculturalDataAggregator,
    APIConfig,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI(
    title="Agricultural Data API - Lambda",
    description="Seasonal historical analysis optimized for AWS Lambda",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_aggregator = None

def get_aggregator():
    """Get or create aggregator instance for connection reuse"""
    global _aggregator
    if _aggregator is None:
        config = APIConfig(
            REQUEST_TIMEOUT=int(os.environ.get("REQUEST_TIMEOUT", "12")),
            HISTORICAL_YEARS=int(os.environ.get("HISTORICAL_YEARS", "2"))
        )
        _aggregator = AgriculturalDataAggregator(config)
    return _aggregator

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agricultural Data API v2.0 - AWS Lambda",
        "version": "2.0.0",
        "environment": "AWS Lambda",
        "endpoints": {
            "historical": "/historical?lat={lat}&lon={lon}",
            "current": "/current?lat={lat}&lon={lon}",
            "soil": "/soil?lat={lat}&lon={lon}",
            "complete": "/complete?lat={lat}&lon={lon}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "AWS Lambda"
    }

@app.get("/historical")
async def historical_analysis(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """
    Historical seasonal analysis
    
    Returns statistics for the SAME CROP SEASON in previous years.
    Optimized for Lambda with connection reuse and timeout handling.
    """
    try:
        logger.info(f"Historical analysis request: lat={lat}, lon={lon}")
        
        aggregator = get_aggregator()
        dataset = await aggregator.get_historical_analysis(lat=lat, lon=lon)
        
        response = asdict(dataset)
        response["api_version"] = "2.0.0"
        response["lambda_optimized"] = True
        
        logger.info(f"Historical analysis completed for lat={lat}, lon={lon}")
        return JSONResponse(content=response)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in historical analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/current")
async def current_conditions(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """Current weather conditions - fastest endpoint"""
    try:
        logger.info(f"Current conditions request: lat={lat}, lon={lon}")
        
        aggregator = get_aggregator()
        data = await aggregator.get_current_minimal(lat=lat, lon=lon)
        
        data["current"] = asdict(data["current"])
        data["api_version"] = "2.0.0"
        
        return JSONResponse(content=data)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching current conditions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/soil")
async def soil_analysis(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """Soil analysis with EDA"""
    try:
        logger.info(f"Soil analysis request: lat={lat}, lon={lon}")
        
        aggregator = get_aggregator()
        data = await aggregator.get_soil_analysis(lat=lat, lon=lon)
        
        data["soil"] = asdict(data["soil"])
        data["api_version"] = "2.0.0"
        
        return JSONResponse(content=data)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching soil analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/complete")
async def complete_dataset(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """Complete dataset - all data in one request"""
    try:
        logger.info(f"Complete dataset request: lat={lat}, lon={lon}")
        
        aggregator = get_aggregator()
        
        # Fetch all data
        historical = await aggregator.get_historical_analysis(lat=lat, lon=lon)
        current = await aggregator.get_current_minimal(lat=lat, lon=lon)
        soil = await aggregator.get_soil_analysis(lat=lat, lon=lon)
        
        response = {
            "location": {"lat": lat, "lon": lon},
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0",
            "historical": asdict(historical),
            "current": asdict(current["current"]),
            "soil": asdict(soil["soil"])
        }
        
        return JSONResponse(content=response)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching complete dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)