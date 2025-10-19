import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import statistics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_AIR_QUALITY_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    OPEN_METEO_HISTORICAL_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    REQUEST_TIMEOUT: int = 15
    HISTORICAL_YEARS: int = 2

CROP_SEASONS = {
    "kharif": {
        "months": [6, 7, 8, 9, 10], 
        "name": "Kharif (Monsoon)",
        "sowing_window": [5, 6, 7],
        "harvest_window": [9, 10, 11]
    },
    "rabi": {
        "months": [11, 12, 1, 2, 3], 
        "name": "Rabi (Winter)",
        "sowing_window": [10, 11, 12],
        "harvest_window": [3, 4, 5]
    },
    "zaid": {
        "months": [4, 5], 
        "name": "Zaid (Summer)",
        "sowing_window": [3, 4],
        "harvest_window": [5, 6]
    }
}

def get_relevant_season(date: datetime) -> Tuple[str, List[int], str]:
    """
    Determine which season is RELEVANT for farming decisions.
    
    Logic:
    - If in sowing window -> return that season (farmer is planting)
    - If in harvest window -> return NEXT season (farmer is preparing for next crop)
    - Otherwise -> return current season
    
    Returns:
        (season_name, season_months, context)
        context can be: "sowing", "upcoming", or "current"
    """
    month = date.month
    
    # Check if we're in any sowing window
    for season_name, season_info in CROP_SEASONS.items():
        if month in season_info["sowing_window"]:
            return season_name, season_info["months"], "sowing"
    
    # Check if we're in harvest window -> prepare for NEXT season
    season_order = ["kharif", "rabi", "zaid"]
    for i, season_name in enumerate(season_order):
        season_info = CROP_SEASONS[season_name]
        if month in season_info["harvest_window"]:
            # Return NEXT season
            next_season_name = season_order[(i + 1) % len(season_order)]
            next_season_info = CROP_SEASONS[next_season_name]
            return next_season_name, next_season_info["months"], "upcoming"
    
    # Otherwise, return current season
    for season_name, season_info in CROP_SEASONS.items():
        if month in season_info["months"]:
            return season_name, season_info["months"], "current"
    
    # Fallback
    return "rabi", CROP_SEASONS["rabi"]["months"], "current"

def get_seasonal_date_ranges(current_date: datetime, years_back: int = 2) -> List[Tuple[str, str]]:
    """Get full 2-year date range, then filter locally for season"""
    end_date = current_date - timedelta(days=10)
    start_date = end_date - timedelta(days=years_back * 365)
    return [(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))]

def filter_data_by_season(dates: List[str], values: List[Any], target_season_months: List[int]) -> List[Any]:
    """Filter data to only include values from specific months"""
    filtered = []
    for date_str, value in zip(dates, values):
        if value is None:
            continue
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if date_obj.month in target_season_months:
                filtered.append(value)
        except:
            continue
    return filtered

@dataclass
class CurrentConditions:
    temp_c: Optional[float]
    humidity_pct: Optional[float]
    precipitation_mm: Optional[float]
    wind_speed_kmh: Optional[float]
    wind_direction_deg: Optional[int]
    uv_index: Optional[float]

@dataclass
class SoilAnalysis:
    moisture_0_1: Optional[float]
    moisture_1_3: Optional[float]
    moisture_3_9: Optional[float]
    moisture_9_27: Optional[float]
    temp_0cm: Optional[float]
    temp_6cm: Optional[float]
    avg_moisture: Optional[float]
    moisture_variability: Optional[float]
    moisture_trend: Optional[str]
    dryness_index: Optional[float]

@dataclass
class SeasonalHistoricalStats:
    season_name: str
    years_analyzed: int
    temp_avg_historical: Optional[float]
    temp_max_historical: Optional[float]
    temp_min_historical: Optional[float]
    temp_stddev: Optional[float]
    total_precip_historical: Optional[float]
    avg_daily_precip: Optional[float]
    precip_stddev: Optional[float]
    max_dry_spell_days: Optional[int]
    avg_soil_moisture_historical: Optional[float]
    soil_moisture_stddev: Optional[float]
    avg_et0_historical: Optional[float]
    avg_gdd_per_day: Optional[float]
    total_gdd_historical: Optional[float]

@dataclass
class SeasonalComparison:
    current_temp_vs_historical: Optional[float]
    current_precip_vs_historical: Optional[float]
    current_soil_moisture_vs_historical: Optional[float]
    temp_percentile: Optional[float]
    precip_percentile: Optional[float]
    anomaly_flags: List[str]

@dataclass
class HistoricalDataset:
    location: Dict[str, float]
    relevant_season: str
    season_context: str
    analysis_period: str
    historical_stats: SeasonalHistoricalStats
    seasonal_comparison: SeasonalComparison
    timestamp: str
    data_quality: Dict[str, Any]

class SeasonalDataAnalyzer:
    
    @staticmethod
    def analyze_seasonal_temperature(daily_temps: List[float]) -> Dict[str, Optional[float]]:
        if not daily_temps or len(daily_temps) < 7:
            return {"avg": None, "max": None, "min": None, "stddev": None}
        
        valid_temps = [t for t in daily_temps if t is not None]
        if not valid_temps:
            return {"avg": None, "max": None, "min": None, "stddev": None}
        
        return {
            "avg": round(statistics.mean(valid_temps), 2),
            "max": round(max(valid_temps), 2),
            "min": round(min(valid_temps), 2),
            "stddev": round(statistics.stdev(valid_temps), 2) if len(valid_temps) > 1 else 0
        }
    
    @staticmethod
    def analyze_seasonal_precipitation(daily_precip: List[float]) -> Dict[str, Optional[float]]:
        if not daily_precip:
            return {"total": None, "avg_daily": None, "stddev": None, "max_dry_spell": None}
        
        valid_precip = [p for p in daily_precip if p is not None]
        if not valid_precip:
            return {"total": None, "avg_daily": None, "stddev": None, "max_dry_spell": None}
        
        max_dry_spell = 0
        current_dry_spell = 0
        for p in valid_precip:
            if p < 1.0:
                current_dry_spell += 1
                max_dry_spell = max(max_dry_spell, current_dry_spell)
            else:
                current_dry_spell = 0
        
        return {
            "total": round(sum(valid_precip), 2),
            "avg_daily": round(statistics.mean(valid_precip), 2),
            "stddev": round(statistics.stdev(valid_precip), 2) if len(valid_precip) > 1 else 0,
            "max_dry_spell": max_dry_spell
        }
    
    @staticmethod
    def calculate_percentile(value: float, historical_values: List[float]) -> Optional[float]:
        if not historical_values or value is None:
            return None
        
        valid_values = [v for v in historical_values if v is not None]
        if not valid_values:
            return None
        
        sorted_values = sorted(valid_values)
        position = sum(1 for v in sorted_values if v <= value)
        percentile = (position / len(sorted_values)) * 100
        
        return round(percentile, 1)
    
    @staticmethod
    def detect_anomalies(
        current_temp: Optional[float],
        current_precip: Optional[float],
        current_soil: Optional[float],
        hist_temp_avg: Optional[float],
        hist_temp_std: Optional[float],
        hist_precip_avg: Optional[float],
        hist_soil_avg: Optional[float]
    ) -> List[str]:
        anomalies = []
        
        if current_temp and hist_temp_avg and hist_temp_std and hist_temp_std > 0:
            deviation = (current_temp - hist_temp_avg) / hist_temp_std
            if deviation > 1.5:
                anomalies.append("significantly_warmer_than_historical")
            elif deviation < -1.5:
                anomalies.append("significantly_cooler_than_historical")
        
        if current_precip is not None and hist_precip_avg and hist_precip_avg > 0:
            pct_diff = ((current_precip - hist_precip_avg) / hist_precip_avg) * 100
            if pct_diff < -50:
                anomalies.append("much_drier_than_historical")
            elif pct_diff > 50:
                anomalies.append("much_wetter_than_historical")
        
        if current_soil and hist_soil_avg:
            diff = current_soil - hist_soil_avg
            if diff < -0.1:
                anomalies.append("soil_drier_than_historical")
            elif diff > 0.1:
                anomalies.append("soil_wetter_than_historical")
        
        return anomalies

class AgriculturalDataAggregator:
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def _fetch_current_conditions(self, lat: float, lon: float) -> Dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m",
            "daily": "uv_index_max",
            "timezone": "auto",
            "forecast_days": 1
        }
        
        try:
            async with self._session.get(
                self.config.OPEN_METEO_BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            ) as response:
                if response.status != 200:
                    logger.error(f"Current conditions API returned {response.status}")
                    return {}
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching current conditions: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error("Timeout fetching current conditions")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching current conditions: {e}")
            return {}
    
    async def _fetch_current_soil(self, lat: float, lon: float) -> Dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "soil_temperature_0cm,soil_temperature_6cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm",
            "timezone": "auto",
            "forecast_days": 1
        }
        
        try:
            async with self._session.get(
                self.config.OPEN_METEO_BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            ) as response:
                if response.status != 200:
                    logger.error(f"Soil API returned {response.status}")
                    return {}
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching soil data: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error("Timeout fetching soil data")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching soil data: {e}")
            return {}
    
    async def _fetch_historical_seasonal(
        self, lat: float, lon: float, start_date: str, end_date: str
    ) -> Dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration",
            "timezone": "auto"
        }
        
        try:
            async with self._session.get(
                self.config.OPEN_METEO_HISTORICAL_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Historical API returned {response.status} for {start_date} to {end_date}: {error_text}")
                    return {}
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching historical data: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching historical data for {start_date} to {end_date}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching historical data: {e}")
            return {}
    
    async def get_current_minimal(self, lat: float, lon: float) -> Dict:
        weather_data = await self._fetch_current_conditions(lat, lon)
        
        if not weather_data or 'current' not in weather_data:
            raise ValueError("Failed to fetch current weather data")
        
        current = weather_data.get('current', {})
        daily = weather_data.get('daily', {})
        
        return {
            "location": {"lat": lat, "lon": lon},
            "current": CurrentConditions(
                temp_c=current.get('temperature_2m'),
                humidity_pct=current.get('relative_humidity_2m'),
                precipitation_mm=current.get('precipitation'),
                wind_speed_kmh=current.get('wind_speed_10m'),
                wind_direction_deg=current.get('wind_direction_10m'),
                uv_index=daily.get('uv_index_max', [None])[0] if daily.get('uv_index_max') else None
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_soil_analysis(self, lat: float, lon: float) -> Dict:
        soil_data = await self._fetch_current_soil(lat, lon)
        
        if not soil_data or 'hourly' not in soil_data:
            raise ValueError("Failed to fetch soil data")
        
        hourly = soil_data.get('hourly', {})
        
        def get_first(key):
            values = hourly.get(key, [])
            return values[0] if values and len(values) > 0 else None
        
        m_0_1 = get_first('soil_moisture_0_to_1cm')
        m_1_3 = get_first('soil_moisture_1_to_3cm')
        m_3_9 = get_first('soil_moisture_3_to_9cm')
        m_9_27 = get_first('soil_moisture_9_to_27cm')
        
        readings = [r for r in [m_0_1, m_1_3, m_3_9, m_9_27] if r is not None]
        
        if not readings:
            soil_analysis = SoilAnalysis(
                moisture_0_1=None, moisture_1_3=None, moisture_3_9=None, moisture_9_27=None,
                temp_0cm=None, temp_6cm=None,
                avg_moisture=None, moisture_variability=None,
                moisture_trend=None, dryness_index=None
            )
        else:
            avg = statistics.mean(readings)
            variability = (statistics.stdev(readings) / avg * 100) if len(readings) > 1 and avg > 0 else 0
            
            trend = "unknown"
            if m_0_1 is not None and m_9_27 is not None:
                if m_0_1 > m_9_27 + 0.05:
                    trend = "wetter_at_surface"
                elif m_9_27 > m_0_1 + 0.05:
                    trend = "drier_at_surface"
                else:
                    trend = "uniform"
            
            dryness = max(0, min(100, (0.35 - avg) / 0.35 * 100)) if avg > 0 else 100
            
            soil_analysis = SoilAnalysis(
                moisture_0_1=m_0_1, moisture_1_3=m_1_3,
                moisture_3_9=m_3_9, moisture_9_27=m_9_27,
                temp_0cm=get_first('soil_temperature_0cm'),
                temp_6cm=get_first('soil_temperature_6cm'),
                avg_moisture=round(avg, 3),
                moisture_variability=round(variability, 1),
                moisture_trend=trend,
                dryness_index=round(dryness, 1)
            )
        
        return {
            "location": {"lat": lat, "lon": lon},
            "soil": soil_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_historical_analysis(self, lat: float, lon: float) -> HistoricalDataset:
        current_date = datetime.now()
        season_name, season_months, context = get_relevant_season(current_date)
        
        date_ranges = get_seasonal_date_ranges(current_date, self.config.HISTORICAL_YEARS)
        
        context_msg = {
            "sowing": f"Currently in sowing window for {season_name}",
            "upcoming": f"Harvest period - preparing for upcoming {season_name} season",
            "current": f"Currently in {season_name} season"
        }
        
        logger.info(f"{context_msg.get(context, '')}. Fetching {self.config.HISTORICAL_YEARS} years of data, filtering for months: {season_months}")
        
        historical_tasks = [
            self._fetch_historical_seasonal(lat, lon, start, end)
            for start, end in date_ranges
        ]
        
        current_task = self._fetch_current_conditions(lat, lon)
        soil_task = self._fetch_current_soil(lat, lon)
        
        results = await asyncio.gather(
            *historical_tasks, current_task, soil_task, return_exceptions=True
        )
        
        historical_data = results[:-2]
        current_data = results[-2]
        soil_data = results[-1]
        
        quality = {
            "historical_fetches": sum(1 for r in historical_data if not isinstance(r, Exception) and r),
            "total_attempts": len(historical_data),
            "current_data": not isinstance(current_data, Exception) and bool(current_data),
            "soil_data": not isinstance(soil_data, Exception) and bool(soil_data)
        }
        
        all_temps = []
        all_precip = []
        all_et0 = []
        all_temp_daily = []
        
        for hist_result in historical_data:
            if isinstance(hist_result, Exception) or not hist_result:
                continue
            
            daily = hist_result.get('daily', {})
            dates = daily.get('time', [])
            
            temps_mean = daily.get('temperature_2m_mean', [])
            temps_max = daily.get('temperature_2m_max', [])
            temps_min = daily.get('temperature_2m_min', [])
            precip = daily.get('precipitation_sum', [])
            et0 = daily.get('et0_fao_evapotranspiration', [])
            
            filtered_temps = filter_data_by_season(dates, temps_mean, season_months)
            filtered_precip = filter_data_by_season(dates, precip, season_months)
            filtered_et0 = filter_data_by_season(dates, et0, season_months)
            
            all_temps.extend(filtered_temps)
            all_precip.extend(filtered_precip)
            all_et0.extend(filtered_et0)
            
            for date_str, tmax, tmin in zip(dates, temps_max, temps_min):
                if tmax is None or tmin is None:
                    continue
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    if date_obj.month in season_months:
                        all_temp_daily.append((tmax, tmin))
                except:
                    continue
        
        logger.info(f"Filtered to {len(all_temps)} temperature readings and {len(all_precip)} precipitation readings for {season_name} season")
        
        temp_stats = SeasonalDataAnalyzer.analyze_seasonal_temperature(all_temps)
        precip_stats = SeasonalDataAnalyzer.analyze_seasonal_precipitation(all_precip)
        
        total_gdd = sum(
            max(0, (tmax + tmin) / 2 - 10)
            for tmax, tmin in all_temp_daily
        ) if all_temp_daily else None
        
        avg_gdd_per_day = total_gdd / len(all_temp_daily) if all_temp_daily else None
        
        historical_stats = SeasonalHistoricalStats(
            season_name=CROP_SEASONS[season_name]["name"],
            years_analyzed=quality["historical_fetches"],
            temp_avg_historical=temp_stats["avg"],
            temp_max_historical=temp_stats["max"],
            temp_min_historical=temp_stats["min"],
            temp_stddev=temp_stats["stddev"],
            total_precip_historical=precip_stats["total"],
            avg_daily_precip=precip_stats["avg_daily"],
            precip_stddev=precip_stats["stddev"],
            max_dry_spell_days=precip_stats["max_dry_spell"],
            avg_soil_moisture_historical=None,
            soil_moisture_stddev=None,
            avg_et0_historical=round(statistics.mean(all_et0), 2) if all_et0 else None,
            avg_gdd_per_day=round(avg_gdd_per_day, 2) if avg_gdd_per_day else None,
            total_gdd_historical=round(total_gdd, 2) if total_gdd else None
        )
        
        current_temp = None
        current_precip = None
        current_soil = None
        
        if isinstance(current_data, dict) and current_data:
            current_temp = current_data.get('current', {}).get('temperature_2m')
            current_precip = current_data.get('current', {}).get('precipitation')
        
        if isinstance(soil_data, dict) and soil_data:
            soil_hourly = soil_data.get('hourly', {})
            soil_values = soil_hourly.get('soil_moisture_0_to_1cm', [])
            current_soil = soil_values[0] if soil_values else None
        
        temp_diff = (current_temp - temp_stats["avg"]) if current_temp and temp_stats["avg"] else None
        precip_diff = (current_precip - precip_stats["avg_daily"]) if current_precip is not None and precip_stats["avg_daily"] else None
        
        temp_percentile = SeasonalDataAnalyzer.calculate_percentile(current_temp, all_temps) if current_temp else None
        precip_percentile = SeasonalDataAnalyzer.calculate_percentile(current_precip, all_precip) if current_precip is not None else None
        
        anomalies = SeasonalDataAnalyzer.detect_anomalies(
            current_temp, current_precip, current_soil,
            temp_stats["avg"], temp_stats["stddev"],
            precip_stats["avg_daily"],
            None
        )
        
        seasonal_comparison = SeasonalComparison(
            current_temp_vs_historical=round(temp_diff, 2) if temp_diff else None,
            current_precip_vs_historical=round(precip_diff, 2) if precip_diff else None,
            current_soil_moisture_vs_historical=None,
            temp_percentile=temp_percentile,
            precip_percentile=precip_percentile,
            anomaly_flags=anomalies
        )
        
        analysis_period = f"Last {self.config.HISTORICAL_YEARS} years, filtered for {CROP_SEASONS[season_name]['name']}"
        
        return HistoricalDataset(
            location={"lat": lat, "lon": lon},
            relevant_season=season_name,
            season_context=context,
            analysis_period=analysis_period,
            historical_stats=historical_stats,
            seasonal_comparison=seasonal_comparison,
            timestamp=datetime.now().isoformat(),
            data_quality=quality
        )


async def main():
    lat, lon = 28.6139, 77.2090
    
    async with AgriculturalDataAggregator() as aggregator:
        historical = await aggregator.get_historical_analysis(lat, lon)
        print("=== HISTORICAL SEASONAL ANALYSIS ===")
        print(json.dumps(asdict(historical), indent=2))
        
        print("\n=== CURRENT CONDITIONS ===")
        current = await aggregator.get_current_minimal(lat, lon)
        print(json.dumps({**current, "current": asdict(current["current"])}, indent=2))
        
        print("\n=== SOIL ANALYSIS ===")
        soil = await aggregator.get_soil_analysis(lat, lon)
        print(json.dumps({**soil, "soil": asdict(soil["soil"])}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())