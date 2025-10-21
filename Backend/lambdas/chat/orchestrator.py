"""
Multi-Agent Orchestrator for Kisaantic Agricultural AI
Uses LLM-based intelligent routing with web search, news, and agro API integration
"""

import boto3
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import os
from boto3.dynamodb.conditions import Key


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    WEATHER_ADVISOR = "weather_advisor"
    CROP_SPECIALIST = "crop_specialist"
    PEST_MANAGER = "pest_manager"
    SOIL_ANALYST = "soil_analyst"
    IRRIGATION_EXPERT = "irrigation_expert"
    CROP_PLANNER = "crop_planner"
    EQUIPMENT_VENDOR = "equipment_vendor"
    MARKET_LINKAGE = "market_linkage"

class MultiAgentOrchestrator:
    """
    Intelligent orchestrator using LLM for routing decisions
    Integrates web search, news APIs, and agricultural data APIs
    """
    
    def __init__(self, region_name: str = "ap-south-1"):
        self.bedrock_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=region_name
        )
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=region_name
        )
        
        # Use Nova Lite for routing - fast and cost-effective
        self.routing_model = "apac.amazon.nova-lite-v1:0"
        self.synthesis_model = "apac.amazon.nova-pro-v1:0"
        
        # API keys and URLs
        self.langsearch_key = os.getenv('LANGSEARCH_API_KEY', '')
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        
        # FIX: Construct full Agro API URL with /agro-api prefix
        base_url = os.getenv('AGRO_API_URL', 'https://d8o991ajjl.execute-api.ap-south-1.amazonaws.com/api')
        
        # Ensure URL doesn't have duplicate /agro-api
        if '/agro-api' not in base_url:
            self.agro_api_url = f"{base_url.rstrip('/')}/agro-api"
        else:
            self.agro_api_url = base_url.rstrip('/')
        
        # Load agent configurations
        self.agents = self._load_agent_config()
        
        logger.info("✅ Multi-Agent Orchestrator initialized")
        logger.info(f"   Loaded {len(self.agents)} agents")
        logger.info(f"   Web Search: {'Enabled' if self.langsearch_key else 'Disabled'}")
        logger.info(f"   News API: {'Enabled' if self.news_api_key else 'Disabled'}")
        logger.info(f"   Agro API: {self.agro_api_url}")
    
    def _load_agent_config(self) -> Dict:
        """Load agent configurations"""
        try:
            with open('agent_config.json', 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.error("❌ agent_config.json not found")
            return {}
    
    async def fetch_agricultural_data(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict]:
        """
        Fetch comprehensive agricultural data from Agro API
        Returns current weather, soil data, and historical context
        """
        
        if not latitude or not longitude:
            logger.warning("⚠️ No coordinates provided for agro data")
            return None
        
        try:
            logger.info(f"🌾 Fetching agricultural data for ({latitude}, {longitude})")
            logger.info(f"   URL: {self.agro_api_url}/complete")
            api_start = asyncio.get_event_loop().time()
            
            # Construct full URL for debugging
            full_url = f"{self.agro_api_url}/complete?lat={latitude}&lon={longitude}"
            logger.info(f"   Full URL: {full_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.agro_api_url}/complete",
                    params={"lat": latitude, "lon": longitude},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    api_time = asyncio.get_event_loop().time() - api_start
                    
                    logger.info(f"   Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Log key data points
                        if 'current' in data:
                            temp = data['current'].get('temp_c', 'N/A')
                            humidity = data['current'].get('humidity_pct', 'N/A')
                            logger.info(f"   Current: {temp}°C, {humidity}% humidity")
                        
                        if 'soil' in data:
                            moisture = data['soil'].get('avg_moisture', 'N/A')
                            dryness = data['soil'].get('dryness_index', 'N/A')
                            logger.info(f"   Soil: {moisture} m³/m³, dryness {dryness}/100")
                        
                        if 'historical' in data:
                            season = data['historical'].get('relevant_season', 'N/A')
                            context = data['historical'].get('season_context', 'N/A')
                            logger.info(f"   Season: {season} ({context})")
                            
                            # Log anomalies
                            anomalies = data['historical'].get('seasonal_comparison', {}).get('anomaly_flags', [])
                            if anomalies:
                                logger.info(f"   ⚠️ Anomalies: {', '.join(anomalies)}")
                        
                        logger.info(f"✅ Agro data fetched in {api_time:.2f}s")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Agro API error {response.status}: {error_text[:500]}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ Agro API timeout after 30s")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"❌ Agro API network error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Agro API unexpected error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def analyze_query_with_llm(
        self,
        query: str,
        user_context: Dict,
        chat_history: Optional[List[Dict]] = None,
        agro_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze query and determine routing strategy
        Now includes agricultural data context
        """
        
        # Build chat history context
        history_context = ""
        if chat_history:
            recent = chat_history[-3:]
            history_context = "\nRECENT CONVERSATION:\n"
            for msg in recent:
                sender = "Farmer" if msg.get('Sender') == 'user' else "AI"
                history_context += f"{sender}: {msg.get('Text', '')[:150]}\n"
        
        # Build agricultural data context
        agro_context = ""
        if agro_data:
            agro_context = "\n\nCURRENT AGRICULTURAL CONDITIONS:\n"
            
            if 'current' in agro_data:
                current = agro_data['current']
                agro_context += f"- Temperature: {current.get('temp_c', 'N/A')}°C\n"
                agro_context += f"- Humidity: {current.get('humidity_pct', 'N/A')}%\n"
                agro_context += f"- Precipitation: {current.get('precipitation_mm', 'N/A')} mm\n"
            
            if 'soil' in agro_data:
                soil = agro_data['soil']
                agro_context += f"- Soil Moisture: {soil.get('avg_moisture', 'N/A')} m³/m³\n"
                agro_context += f"- Dryness Index: {soil.get('dryness_index', 'N/A')}/100\n"
            
            if 'historical' in agro_data:
                hist = agro_data['historical']
                agro_context += f"- Current Season: {hist.get('relevant_season', 'N/A')}\n"
                agro_context += f"- Season Stage: {hist.get('season_context', 'N/A')}\n"
        
        analysis_prompt = f"""You are an expert agricultural AI system analyzer. Analyze the farmer's query and provide structured routing decisions.

FARMER PROFILE:
- Location: {user_context.get('Address', 'Not specified')}
- Farm Size: {user_context.get('FarmSize', 'Not specified')} acres
- Primary Crop: {user_context.get('CropType', 'Not specified')}
- Coordinates: {user_context.get('Latitude')}, {user_context.get('Longitude')}

CURRENT DATE: {datetime.now().strftime('%B %d, %Y')}

{history_context}

{agro_context}

AVAILABLE SPECIALIST AGENTS:
1. weather_advisor - Weather forecasts, climate impact, timing
2. crop_specialist - Crop management, varieties, practices
3. pest_manager - Pest/disease identification, treatment
4. soil_analyst - Soil health, fertility, nutrients
5. irrigation_expert - Water management, irrigation
6. crop_planner - ROI analysis, crop selection, profitability
7. equipment_vendor - Equipment recommendations, vendors
8. market_linkage - Market prices, mandis, selling strategies

FARMER'S QUERY: "{query}"

Analyze and respond in JSON format:

{{
  "query_type": "simple_greeting / simple_question / complex_farming / multi_aspect",
  "requires_agents": true or false,
  "required_agents": ["list of 0-6 agent names"],
  "agent_priority": {{"agent_name": "why needed"}},
  "requires_web_search": true or false,
  "web_search_queries": ["search query 1", "search query 2"],
  "requires_news": true or false,
  "news_search_query": "news query",
  "requires_agro_data": true or false,
  "agro_data_available": {True if agro_context else False},
  "response_complexity": "simple / detailed / comprehensive",
  "key_data_points": ["list of data needed"],
  "location_specific": true or false
}}

ROUTING LOGIC:
- Simple greetings/chitchat: requires_agents=false, no searches
- Simple factual questions: 0-1 agents, maybe web search
- Standard farming queries: 2-4 agents, web search if prices/markets/news
- Complex multi-part queries: 3-6 agents, web + news search

WEB SEARCH TRIGGERS:
- Market prices, mandi rates, current rates
- Equipment availability, vendor contacts
- News about crops, policies, subsidies
- Weather forecasts beyond 7 days
- Current trends, recent developments

NEWS SEARCH TRIGGERS:
- Government schemes, policy changes
- Market news, price trends
- Agricultural developments
- Crop-specific news
- Subsidy announcements

AGRO DATA USAGE:
- Weather-based advice needs current temperature, precipitation
- Irrigation queries need soil moisture data
- Timing recommendations need seasonal context
- Pest/disease correlation with humidity, temperature
- If agro_data_available=true, prioritize weather_advisor, irrigation_expert, soil_analyst

Respond ONLY with valid JSON.
"""

        try:
            response = self.bedrock.invoke_model(
                modelId=self.routing_model,
                body=json.dumps({
                    "messages": [{
                        "role": "user",
                        "content": [{"text": analysis_prompt}]
                    }],
                    "inferenceConfig": {
                        "temperature": 0.1,
                        "maxTokens": 1500
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract content
            if 'output' in response_body:
                content = response_body['output'].get('message', {}).get('content', [])
                if content:
                    analysis_text = content[0].get('text', '{}')
                else:
                    analysis_text = '{}'
            else:
                analysis_text = response_body.get('completion', '{}')
            
            # Clean JSON
            analysis_text = analysis_text.strip()
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif analysis_text.startswith('```'):
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(analysis_text)
            
            logger.info(f"🧠 Query Analysis:")
            logger.info(f"   Type: {analysis.get('query_type')}")
            logger.info(f"   Agents: {len(analysis.get('required_agents', []))}")
            logger.info(f"   Web Search: {analysis.get('requires_web_search')}")
            logger.info(f"   News: {analysis.get('requires_news')}")
            logger.info(f"   Agro Data: {analysis.get('agro_data_available')}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ LLM analysis error: {str(e)}")
            return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> Dict:
        """Fallback if LLM analysis fails"""
        return {
            "query_type": "complex_farming",
            "requires_agents": True,
            "required_agents": ["crop_specialist"],
            "agent_priority": {"crop_specialist": "Default agent"},
            "requires_web_search": False,
            "web_search_queries": [],
            "requires_news": False,
            "news_search_query": "",
            "requires_agro_data": True,
            "agro_data_available": False,
            "response_complexity": "detailed",
            "key_data_points": ["General farming advice"],
            "location_specific": False
        }
    
    async def execute_web_searches(
        self,
        queries: List[str],
        location: Dict
    ) -> List[Dict]:
        """Execute multiple web searches in parallel"""
        
        if not self.langsearch_key or not queries:
            return []
        
        logger.info(f"🔍 Executing {len(queries)} web searches...")
        
        async def single_search(query: str) -> Dict:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'https://api.langsearch.com/v1/web-search',
                        headers={
                            'Authorization': f'Bearer {self.langsearch_key}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'query': query,
                            'freshness': 'oneWeek',
                            'summary': True,
                            'count': 5
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get('webPages', {}).get('value', [])
                            logger.info(f"   ✅ '{query}': {len(results)} results")
                            return {
                                'query': query,
                                'results': results,
                                'success': True
                            }
                        else:
                            logger.warning(f"   ⚠️ '{query}': Status {response.status}")
                            return {'query': query, 'results': [], 'success': False}
            except Exception as e:
                logger.error(f"   ❌ '{query}': {str(e)}")
                return {'query': query, 'results': [], 'success': False}
        
        searches = [single_search(q) for q in queries[:3]]  # Max 3 searches
        results = await asyncio.gather(*searches)
        
        successful = sum(1 for r in results if r.get('success'))
        logger.info(f"✅ Web searches complete: {successful}/{len(queries)} successful")
        
        return results
    
    async def fetch_news(
        self,
        query: str,
        location: Dict
    ) -> Dict:
        """Fetch agricultural news"""
        
        if not self.news_api_key or not query:
            return {'articles': [], 'success': False}
        
        logger.info(f"📰 Fetching news for: {query}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://newsapi.org/v2/everything',
                    params={
                        'q': query,
                        'apiKey': self.news_api_key,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': 5
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('articles', [])
                        logger.info(f"   ✅ Found {len(articles)} news articles")
                        return {
                            'query': query,
                            'articles': articles,
                            'success': True
                        }
                    else:
                        logger.warning(f"   ⚠️ News API status {response.status}")
                        return {'query': query, 'articles': [], 'success': False}
        except Exception as e:
            logger.error(f"   ❌ News fetch error: {str(e)}")
            return {'query': query, 'articles': [], 'success': False}
    
    def _build_enhanced_prompt(
        self,
        query: str,
        user_context: Dict,
        agro_data: Optional[Dict],
        agent_type: AgentType,
        analysis: Dict
    ) -> str:
        """Build comprehensive prompt for agent"""
        
        lat = user_context.get('Latitude')
        lon = user_context.get('Longitude')
        address = user_context.get('Address', 'Not provided')
        
        base_prompt = f"""You are Kisaantic AI's {agent_type.value.replace('_', ' ').title()}.

GLOBAL AGRICULTURAL ASSISTANT:
- You serve farmers WORLDWIDE, not just India/Madhya Pradesh
- When specific regional data unavailable, provide general best practices
- Adapt recommendations to farmer's location and climate

QUERY CONTEXT:
- Farmer Location: {address}
- GPS: {lat}°N, {lon}°E
- Farm Size: {user_context.get('FarmSize', 'Not specified')} acres
- Primary Crop: {user_context.get('CropType', 'Not specified')}
- Query Complexity: {analysis.get('response_complexity', 'detailed')}

YOUR ROLE IN THIS QUERY:
{analysis.get('agent_priority', {}).get(agent_type.value, 'Provide expert guidance')}

KEY DATA TO ADDRESS:
{', '.join(analysis.get('key_data_points', []))}

"""
        
        # Add agricultural data if available
        if agro_data:
            base_prompt += f"""
REAL-TIME AGRICULTURAL DATA (From farmer's location):

"""
            current = agro_data.get('current', {})
            soil = agro_data.get('soil', {})
            historical = agro_data.get('historical', {})
            
            if current:
                base_prompt += f"""CURRENT WEATHER CONDITIONS:
- Temperature: {current.get('temp_c', 'N/A')}°C
- Feels Like: {current.get('feels_like_c', 'N/A')}°C
- Humidity: {current.get('humidity_pct', 'N/A')}%
- Precipitation: {current.get('precipitation_mm', 'N/A')} mm
- Wind Speed: {current.get('wind_speed_kmh', 'N/A')} km/h
- UV Index: {current.get('uv_index', 'N/A')}
- Condition: {current.get('condition', 'N/A')}

"""
            
            if soil:
                base_prompt += f"""SOIL CONDITIONS (Real-time):
- Surface Moisture (0-1cm): {soil.get('moisture_0_1', 'N/A')} m³/m³
- Root Zone Moisture (1-3cm): {soil.get('moisture_1_3', 'N/A')} m³/m³
- Average Moisture: {soil.get('avg_moisture', 'N/A')} m³/m³
- Dryness Index: {soil.get('dryness_index', 'N/A')}/100 (higher = drier)
- Soil Temperature (0cm): {soil.get('temp_0cm', 'N/A')}°C
- Soil Temperature (6cm): {soil.get('temp_6cm', 'N/A')}°C
- Moisture Trend: {soil.get('moisture_trend', 'N/A')}

"""
            
            if historical:
                season = historical.get('relevant_season', 'N/A')
                base_prompt += f"""SEASONAL CONTEXT (Historical Comparison):
- Current Season: {season}
- Season Stage: {historical.get('season_context', 'N/A')}

"""
                
                hist_stats = historical.get('historical_stats', {})
                if hist_stats:
                    base_prompt += f"""Historical Season Averages:
- Average Temperature: {hist_stats.get('temp_avg_historical', 'N/A')}°C
- Total Seasonal Rainfall: {hist_stats.get('total_precip_historical', 'N/A')} mm
- Growing Degree Days: {hist_stats.get('total_gdd_historical', 'N/A')}

"""
                
                comparison = historical.get('seasonal_comparison', {})
                if comparison:
                    base_prompt += f"""CURRENT VS HISTORICAL:
- Temperature Deviation: {comparison.get('current_temp_vs_historical', 'N/A')}°C
- Temperature Percentile: {comparison.get('temp_percentile', 'N/A')}th
- Precipitation Deviation: {comparison.get('current_precip_vs_historical', 'N/A')} mm
- Precipitation Percentile: {comparison.get('precip_percentile', 'N/A')}th

"""
                    
                    anomalies = comparison.get('anomaly_flags', [])
                    if anomalies:
                        base_prompt += f"""⚠️ ANOMALIES DETECTED:
"""
                        for anomaly in anomalies:
                            readable = anomaly.replace('_', ' ').title()
                            base_prompt += f"  • {readable}\n"
                        base_prompt += "\n"
        
        # Agent-specific instructions
        agent_instructions = {
            AgentType.CROP_PLANNER: """
YOUR EXPERTISE: ROI analysis, crop profitability, economic planning

RESPONSE GUIDELINES:
- Calculate detailed costs: seeds, fertilizers, labor, equipment, transport
- Provide ROI percentages and profit projections
- Use regional data when available (MP data in knowledge base)
- For other regions, provide typical cost ranges and profitability ratios
- Compare 2-3 crop options with data tables
- Include MSP information for India, market price guidance for elsewhere
- Break down revenue calculations clearly
- **USE REAL-TIME WEATHER/SOIL DATA to adjust timing and costs**
""",
            AgentType.EQUIPMENT_VENDOR: """
YOUR EXPERTISE: Agricultural equipment, vendors, purchase/rental economics

RESPONSE GUIDELINES:
- Recommend equipment based on farm size and crop
- For India (esp. MP): Use specific vendor data from knowledge base
- For other regions: Provide equipment types, typical prices, rental vs purchase analysis
- Include subsidy information (India: Krishiyantra Anudan; Others: general subsidy guidance)
- Provide equipment specifications and capacity matching
- Calculate breakeven for purchase vs rental
""",
            AgentType.MARKET_LINKAGE: """
YOUR EXPERTISE: Market prices, selling strategies, market access

RESPONSE GUIDELINES:
- For India (esp. MP): Use specific mandi prices and MSP from knowledge base
- For other regions: Provide guidance on finding local markets, cooperatives, FPOs
- Calculate net realization after transport and commission costs
- Recommend selling timing based on seasonal patterns
- Compare multiple market options when possible
- Include storage vs immediate sale analysis
""",
            AgentType.CROP_SPECIALIST: """
YOUR EXPERTISE: Crop management, varieties, agricultural practices

RESPONSE GUIDELINES:
- Tailor advice to farmer's climate and soil (from real-time data above)
- Provide growth stage guidance
- Include timing recommendations based on CURRENT WEATHER
- Use local crop data when available, general practices otherwise
- **REFERENCE soil moisture, temperature in irrigation/fertilizer advice**
""",
            AgentType.WEATHER_ADVISOR: """
YOUR EXPERTISE: Weather analysis, agricultural meteorology

RESPONSE GUIDELINES:
- **USE REAL-TIME WEATHER DATA provided above extensively**
- Provide farming operation timing based on current conditions
- Explain weather impacts on specific crops
- Use temperature, humidity, precipitation data to give specific advice
- Reference anomaly flags if present
- Give timing for sowing/spraying/harvesting based on conditions
""",
            AgentType.PEST_MANAGER: """
YOUR EXPERTISE: Pest/disease identification, IPM, treatment

RESPONSE GUIDELINES:
- Systematic diagnosis approach
- IPM strategies prioritized
- **Consider current weather for pest pressure (humidity, temp from agro data)**
- High humidity + warm temp = increased fungal disease risk
- Safe, economical treatments
""",
            AgentType.SOIL_ANALYST: """
YOUR EXPERTISE: Soil health, fertility management

RESPONSE GUIDELINES:
- **USE REAL-TIME SOIL DATA above (moisture, temperature)**
- Recommend soil testing when appropriate
- Nutrient management for specific crops
- Adjust fertilizer timing based on soil moisture
- Organic and sustainable approaches
- **Reference dryness index for irrigation needs**
""",
            AgentType.IRRIGATION_EXPERT: """
YOUR EXPERTISE: Water management, irrigation optimization

RESPONSE GUIDELINES:
- **USE REAL-TIME SOIL MOISTURE DATA extensively**
- Dryness index >70 = immediate irrigation needed
- Calculate water requirements
- System recommendations based on farm size
- Water conservation techniques
- **Provide specific irrigation schedule based on current moisture levels**
"""
        }
        
        base_prompt += agent_instructions.get(agent_type, "")
        
        base_prompt += f"""

        RESPONSE REQUIREMENTS:
        - Be SPECIFIC and ACTIONABLE with numbers, names, prices
        - Use knowledge base data when farmer location matches
        - **INTEGRATE real-time weather/soil data throughout your response**
        - Provide general best practices for other regions
        - Explain reasoning behind recommendations
        - Use clear, farmer-friendly language
        - Include 300-600 words of detailed guidance

        FARMER'S QUESTION: "{query}"

        Provide expert advice addressing their specific situation with real-time data integration:
        """
        
        return base_prompt
    
    async def invoke_agent(
        self,
        agent_type: AgentType,
        query: str,
        user_context: Dict,
        agro_data: Optional[Dict],
        session_id: str,
        analysis: Dict
    ) -> Dict:
        """Invoke single Bedrock agent"""
        
        try:
            agent_config = self.agents.get(agent_type.value, {})
            
            if not agent_config.get('agent_id'):
                logger.warning(f"⚠️ Agent {agent_type.value} not configured")
                return {'response': None, 'success': False}
            
            prompt = self._build_enhanced_prompt(
                query, user_context, agro_data, agent_type, analysis
            )
            
            logger.info(f"→ Invoking {agent_type.value}...")
            
            response = self.bedrock_runtime.invoke_agent(
                agentId=agent_config['agent_id'],
                agentAliasId=agent_config['alias_id'],
                sessionId=f"{session_id}-{agent_type.value}",
                inputText=prompt,
                enableTrace=False
            )
            
            agent_response = ""
            for event in response.get('completion', []):
                if 'chunk' in event and 'bytes' in event['chunk']:
                    agent_response += event['chunk']['bytes'].decode('utf-8')
            
            if agent_response:
                logger.info(f"   ✅ {agent_type.value} responded ({len(agent_response)} chars)")
                return {
                    'agent': agent_type.value,
                    'response': agent_response,
                    'success': True
                }
            else:
                logger.warning(f"   ⚠️ {agent_type.value} empty response")
                return {'agent': agent_type.value, 'response': None, 'success': False}
                    
        except Exception as e:
            logger.error(f"❌ {agent_type.value} error: {str(e)}")
            return {'agent': agent_type.value, 'response': None, 'success': False, 'error': str(e)}
    
    async def synthesize_comprehensive_response(
        self,
        query: str,
        analysis: Dict,
        agent_responses: List[Dict],
        web_search_results: List[Dict],
        news_results: Dict,
        agro_data: Optional[Dict],
        user_context: Dict
    ) -> str:
        """
        Synthesize all sources into comprehensive response
        Matches Kisaantic AI response format
        """
        
        logger.info("🎯 Synthesizing comprehensive response...")
        
        # Build synthesis prompt
        synthesis_prompt = f"""You are synthesizing a COMPREHENSIVE agricultural response from multiple expert sources.

    FARMER'S ORIGINAL QUESTION: "{query}"

    CURRENT DATE: {datetime.now().strftime('%B %d, %Y')}

    FARMER CONTEXT:
    - Location: {user_context.get('Address')}
    - Farm Size: {user_context.get('FarmSize')} acres
    - Crop: {user_context.get('CropType')}

    QUERY ANALYSIS:
    - Type: {analysis.get('query_type')}
    - Complexity: {analysis.get('response_complexity')}
    - Location-specific: {analysis.get('location_specific')}

    """
        
        # Add real-time agricultural data summary
        if agro_data:
            synthesis_prompt += f"\n{'='*60}\nREAL-TIME AGRICULTURAL DATA:\n{'='*60}\n\n"
            
            current = agro_data.get('current', {})
            if current:
                synthesis_prompt += f"""Current Conditions:
    - Temperature: {current.get('temp_c')}°C
    - Humidity: {current.get('humidity_pct')}%
    - Precipitation: {current.get('precipitation_mm')} mm
    - Condition: {current.get('condition')}

    """
            
            soil = agro_data.get('soil', {})
            if soil:
                synthesis_prompt += f"""Soil Status:
    - Average Moisture: {soil.get('avg_moisture')} m³/m³
    - Dryness Index: {soil.get('dryness_index')}/100
    - Trend: {soil.get('moisture_trend')}

    """
            
            historical = agro_data.get('historical', {})
            if historical:
                synthesis_prompt += f"""Historical Seasonal Context:
    - Season: {historical.get('relevant_season')}
    - Stage: {historical.get('season_context')}

    """
        
        # Add agent responses
        if agent_responses:
            synthesis_prompt += f"\n{'='*60}\nSPECIALIST AGENT INSIGHTS ({len(agent_responses)} agents):\n{'='*60}\n\n"
            
            for i, resp in enumerate(agent_responses, 1):
                agent_name = resp['agent'].replace('_', ' ').title()
                synthesis_prompt += f"### {i}. {agent_name}\n\n{resp['response']}\n\n"
        
        # Add web search results
        if web_search_results:
            synthesis_prompt += f"\n{'='*60}\nWEB SEARCH DATA ({len(web_search_results)} searches):\n{'='*60}\n\n"
            
            for search in web_search_results:
                if search.get('success') and search.get('results'):
                    synthesis_prompt += f"**Search: {search['query']}**\n\n"
                    for result in search['results'][:3]:
                        synthesis_prompt += f"- {result.get('name', 'Result')}\n"
                        synthesis_prompt += f"  {result.get('snippet', '')[:200]}\n\n"
        
        # Add news results
        if news_results.get('success') and news_results.get('articles'):
            synthesis_prompt += f"\n{'='*60}\nRECENT NEWS ({len(news_results['articles'])} articles):\n{'='*60}\n\n"
            
            for article in news_results['articles'][:3]:
                synthesis_prompt += f"- {article.get('title', 'News')}\n"
                synthesis_prompt += f"  {article.get('description', '')[:200]}\n"
                synthesis_prompt += f"  Date: {article.get('publishedAt', 'Recent')}\n\n"
        
        synthesis_prompt += f"""
    {'='*60}
    YOUR SYNTHESIS TASK - KISAANTIC AI RESPONSE FORMAT
    {'='*60}

    Create ONE UNIFIED, COMPREHENSIVE response following this EXACT structure:

    **RESPONSE STRUCTURE(Follow this structure but do not mention them If any data is not there dont mention it use general intelligence):**

    1. **Immediate Answer 🌾** (Opening section with emoji)
    - Start with a clear heading related to the query (e.g., "Crop Max Vendor Overview", "Wheat Cultivation Guide")
    - First paragraph: Direct answer addressing the farmer's location, farm size, and current conditions
    - **Weave in real-time data naturally** (e.g., "Given the current conditions with temperatures around 28°C...")
    - Include a concrete recommendation or key insight
    - Length: 150-250 words

    2. **Detailed Analysis 🌱** (Major section with emoji)
    - Multiple subsections with clear, topic-specific headings (NO generic labels like "Detailed Analysis")
    - Examples: "Equipment Insights", "Cost-Benefit Analysis", "Seasonal Recommendations", "Market Intelligence"
    - Each subsection: 200-400 words
    - Include specific numbers: costs, yields, prices, ROI percentages
    - **Integrate real-time agricultural data seamlessly** (e.g., "Current soil moisture at 0.25 m³/m³ indicates...")
    - Use data naturally in recommendations
    - Reference web search data and news when relevant
    - Use **bold** for key terms and numbers

    3. **Action Plan 📋** (ALWAYS in table format)
    - Create a markdown table with clear action steps
    - Columns: "Timeline / Stage" | "Action" | "Details / Resources"
    - Include 5-10 actionable steps
    - Be specific with timing based on current conditions
    - Include costs, quantities, and vendor names where applicable
    
    Example format:
    | Timeline / Stage | Action | Details / Resources |
    |-----------------|--------|---------------------|
    | Immediate (1-3 days) | Soil testing | Contact AgriMax Labs, ₹500 per sample |
    | Week 1 | Purchase seeds | Recommended: XYZ variety, 25kg needed |

    4. **Additional Insights** (If relevant)
    - Subsections for: Market trends, News updates, Alternative options, Risk factors
    - Each: 100-200 words
    - Include recent news/policies from news data
    - **Weather-based considerations using current data**

    5. **Quick Summary** (Closing section)
    - Brief bullet points (5-8 points)
    - Key numbers and critical dates
    - **Current conditions snapshot** (temp, moisture, season)
    - Next immediate action

    **CRITICAL FORMATTING RULES:**

    ✅ DO:
    - Use ## for main sections with relevant emojis (e.g., "## Immediate Answer 🌾")
    - Use ### for subsections with descriptive names (e.g., "### Equipment Cost Analysis")
    - Use **bold** for emphasis on key terms, numbers, and vendor names
    - Use tables for action plans, cost breakdowns, and comparisons
    - Keep paragraphs short (3-4 sentences)
    - Write as ONE unified expert voice
    - **Seamlessly integrate real-time data**: "Current soil moisture of 0.25 m³/m³ suggests..." not "The soil moisture is 0.25"

    ❌ DON'T:
    - Never use headings like "Detailed Analysis" or "Immediate Answer" as shown to user
    - Never mention "tokens", "word count", or "length requirements"
    - Never say "According to X agent" or "The weather advisor says"
    - Never use generic subsection names
    - Never list data without context
    - Never use bullet points for action plans (use tables instead)

    **REAL-TIME DATA INTEGRATION EXAMPLES:**

    ✅ GOOD: "With current temperatures at 28°C and soil moisture at 0.25 m³/m³ (dryness index 65/100), your wheat crop requires irrigation within 2-3 days to prevent stress during the grain-filling stage."

    ✅ GOOD: "Given the current humidity of 75% and temperature of 26°C, fungal disease pressure is elevated. Apply preventive fungicide within 48 hours."

    ❌ BAD: "Current temperature: 28°C. Current soil moisture: 0.25 m³/m³. Here is advice on irrigation..."

    **TABLE FORMAT FOR ACTION PLANS:**

    Always use markdown tables:
    ```
    | Timeline / Stage | Action | Details / Resources |
    |-----------------|--------|---------------------|
    | Immediate | First step | Specific details |
    | Week 1-2 | Second step | Costs, vendors, quantities |
    ```

    **QUALITY CHECKLIST:**
    - [ ] Opening has descriptive heading with emoji, not "Immediate Answer"
    - [ ] Real-time data woven naturally throughout
    - [ ] Multiple specific subsections under main sections
    - [ ] Action plan is in table format
    - [ ] No mention of word/token counts
    - [ ] All numbers, costs, vendor names included
    - [ ] Written as unified voice, not separate agents
    - [ ] Appropriate emojis for scannability
    - [ ] Short paragraphs throughout
    - [ ] Same language as query

    **TARGET LENGTH:** Write comprehensively to fully address the query (typically 3000-4000 words), but NEVER mention the length in your response.

    Begin synthesis now:
    """

        try:
            # Use Bedrock for synthesis with high token limit
            response = self.bedrock.invoke_model(
                modelId=self.synthesis_model,
                body=json.dumps({
                    "messages": [{
                        "role": "user",
                        "content": [{"text": synthesis_prompt}]
                    }],
                    "inferenceConfig": {
                        "temperature": 0.9,
                        "maxTokens": 5000
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract synthesized response
            if 'output' in response_body:
                content = response_body['output'].get('message', {}).get('content', [])
                if content:
                    synthesized = content[0].get('text', '')
                else:
                    synthesized = ''
            else:
                synthesized = response_body.get('completion', '')
            
            if synthesized:
                token_estimate = len(synthesized.split()) * 1.3
                logger.info(f"✅ Synthesized response: ~{int(token_estimate)} tokens, {len(synthesized)} chars")
                return synthesized
            else:
                logger.warning("⚠️ Empty synthesis, using fallback")
                return self._fallback_synthesis(agent_responses, web_search_results, news_results, agro_data)
                    
        except Exception as e:
            logger.error(f"❌ Synthesis error: {str(e)}")
            return self._fallback_synthesis(agent_responses, web_search_results, news_results, agro_data)

    async def analyze_for_booking_order(
        self,
        query: str,
        final_response: str,
        chat_history: List[Dict],
        user_id: str
    ) -> dict:
        """Analyze response for booking/order suggestions using Nova Lite"""
        
        logger.info(f"🔍 Analyzing response for bookings/orders (user: {user_id})")
        logger.info(f"   Response length: {len(final_response)} chars")
        
        last_messages = ""
        if chat_history:
            recent = chat_history[-2:]
            for msg in recent:
                sender = "Farmer" if msg.get('Sender') == 'user' else "AI"
                last_messages += f"{sender}: {msg.get('Text', '')[:200]}\n"
        
        analysis_prompt = f"""Analyze if this agricultural AI response suggests vendor bookings or product orders.

    CONTEXT (Last 2 messages):
    {last_messages}

    CURRENT QUERY: "{query}"

    AI RESPONSE:
    {final_response[:3000]}

    TASK: Determine if response contains vendor recommendations requiring:
    1. BOOKING: Equipment rental, service booking (tractors, harvesters, soil testing)
    2. ORDER: Product purchase (seeds, fertilizers, pesticides)

    RULES:
    - Only suggest if vendor name explicitly mentioned
    - Check if farmer is asking for vendors OR response recommends specific vendors
    - Max 1 booking + 1 order suggestion per response
    - Extract: vendor name, product/service, quantity (if mentioned), estimated cost (if mentioned)

    OUTPUT JSON:
    {{
    "has_booking": true/false,
    "has_order": true/false,
    "booking": {{
        "vendor_name": "exact vendor name from response",
        "service": "service being booked",
        "message": "human-readable confirmation message",
        "estimated_cost": "cost if mentioned, else null",
        "additional_info": {{"any": "relevant details"}}
    }} or null,
    "order": {{
        "vendor_name": "exact vendor name from response",
        "product": "product being ordered",
        "quantity": "quantity if mentioned, else null",
        "message": "human-readable confirmation message",
        "estimated_cost": "cost if mentioned, else null",
        "additional_info": {{"any": "relevant details"}}
    }} or null
    }}

    If no bookings/orders needed, return {{"has_booking": false, "has_order": false, "booking": null, "order": null}}
    """

        try:
            logger.info("   Calling Nova Lite for analysis...")
            response = self.bedrock.invoke_model(
                modelId=self.routing_model,
                body=json.dumps({
                    "messages": [{
                        "role": "user",
                        "content": [{"text": analysis_prompt}]
                    }],
                    "inferenceConfig": {
                        "temperature": 0.1,
                        "maxTokens": 800
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'output' in response_body:
                content = response_body['output'].get('message', {}).get('content', [])
                analysis_text = content[0].get('text', '{}') if content else '{}'
            else:
                analysis_text = response_body.get('completion', '{}')
            
            logger.info(f"   Raw LLM response: {analysis_text[:200]}...")
            
            analysis_text = analysis_text.strip()
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(analysis_text)
            logger.info(f"   Parsed analysis: has_booking={analysis.get('has_booking')}, has_order={analysis.get('has_order')}")
            
            result = {'booking': None, 'order': None}
            
            # Create booking suggestion if detected
            if analysis.get('has_booking') and analysis.get('booking'):
                booking_data = analysis['booking']
                result['booking'] = {
                    'type': 'booking',
                    'vendor_name': booking_data.get('vendor_name'),
                    'service_product': booking_data.get('service'),
                    'estimated_cost': booking_data.get('estimated_cost'),
                    'message': booking_data.get('message'),
                    'approved': False,
                    'additional_info': booking_data.get('additional_info', {})
                }
                logger.info(f"📋 Booking suggestion: {booking_data.get('vendor_name')}")
            
            # Create order suggestion if detected
            if analysis.get('has_order') and analysis.get('order'):
                order_data = analysis['order']
                result['order'] = {
                    'type': 'order',
                    'vendor_name': order_data.get('vendor_name'),
                    'service_product': order_data.get('product'),
                    'suggested_quantity': order_data.get('quantity'),
                    'estimated_cost': order_data.get('estimated_cost'),
                    'message': order_data.get('message'),
                    'approved': False,
                    'additional_info': order_data.get('additional_info', {})
                }
                logger.info(f"🛒 Order suggestion: {order_data.get('vendor_name')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Booking/order analysis failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'booking': None, 'order': None}

    def _fallback_synthesis(
        self,
        agent_responses: List[Dict],
        web_search_results: List[Dict],
        news_results: Dict,
        agro_data: Optional[Dict]
    ) -> str:
        """Fallback synthesis if LLM synthesis fails"""
        
        result = "# Comprehensive Agricultural Guidance\n\n"
        
        # Add real-time data summary
        if agro_data:
            result += "## 📊 Current Conditions\n\n"
            
            current = agro_data.get('current', {})
            if current:
                result += f"**Weather:** {current.get('temp_c', 'N/A')}°C, "
                result += f"{current.get('humidity_pct', 'N/A')}% humidity, "
                result += f"{current.get('condition', 'N/A')}\n\n"
            
            soil = agro_data.get('soil', {})
            if soil:
                result += f"**Soil:** Moisture {soil.get('avg_moisture', 'N/A')} m³/m³, "
                result += f"Dryness Index {soil.get('dryness_index', 'N/A')}/100\n\n"
            
            result += "---\n\n"
        
        # Add agent responses
        agent_names = {
            'crop_planner': '🌾 Crop Planning & Profitability',
            'equipment_vendor': '🚜 Equipment & Resources',
            'market_linkage': '💰 Market Intelligence',
            'crop_specialist': '🌱 Crop Management',
            'weather_advisor': '🌤️ Weather Advisory',
            'pest_manager': '🐛 Pest & Disease',
            'soil_analyst': '🌍 Soil Health',
            'irrigation_expert': '💧 Water Management'
        }
        
        for resp in agent_responses:
            if resp.get('success'):
                name = agent_names.get(resp['agent'], resp['agent'])
                result += f"\n## {name}\n\n{resp['response']}\n\n"
        
        # Add web search insights
        if web_search_results:
            result += "\n## 🔍 Current Market Intelligence\n\n"
            for search in web_search_results:
                if search.get('success'):
                    result += f"**{search['query']}:**\n"
                    for r in search.get('results', [])[:2]:
                        result += f"- {r.get('snippet', '')[:150]}\n"
                    result += "\n"
        
        # Add news
        if news_results.get('success'):
            result += "\n## 📰 Recent Agricultural News\n\n"
            for article in news_results.get('articles', [])[:3]:
                result += f"- **{article.get('title', 'News')}**\n"
                result += f"  {article.get('description', '')[:150]}\n\n"
        
        return result
    
    async def process_query(
        self,
        query: str,
        context: Dict,
        session_id: str
    ) -> Dict:
        """Main orchestration method with integrated agro data fetching"""
        
        logger.info(f"{'='*70}")
        logger.info(f"🎯 ORCHESTRATION START")
        logger.info(f"{'='*70}")
        logger.info(f"Query: {query[:100]}...")
        
        try:
            user_context = context.get('user_profile', {})
            chat_history = context.get('chat_history', [])
            location = context.get('location', {})
            
            # Extract coordinates
            lat = location.get('latitude')
            lon = location.get('longitude')
            
            # Step 1: Fetch agricultural data FIRST (needed for analysis)
            agro_data = None
            if lat and lon:
                logger.info(f"🌾 Fetching real-time agricultural data...")
                agro_data = await self.fetch_agricultural_data(lat, lon)
                
                if agro_data:
                    logger.info(f"✅ Agricultural data available for routing decision")
                else:
                    logger.warning(f"⚠️ No agricultural data available")
            else:
                logger.warning(f"⚠️ No coordinates provided (lat: {lat}, lon: {lon})")
            
            # Step 2: Analyze query with LLM (now includes agro data context)
            analysis = await self.analyze_query_with_llm(
                query, user_context, chat_history, agro_data
            )
            
            # Step 3: Execute parallel tasks
            tasks = []
            
            # Agent invocations
            if analysis.get('requires_agents') and analysis.get('required_agents'):
                agent_types = [
                    AgentType(name) for name in analysis['required_agents']
                    if name in [a.value for a in AgentType]
                ][:6]  # Max 6 agents
                
                for agent_type in agent_types:
                    tasks.append(
                        self.invoke_agent(
                            agent_type, query, user_context, agro_data, 
                            session_id, analysis
                        )
                    )
            
            # Web searches
            if analysis.get('requires_web_search') and analysis.get('web_search_queries'):
                tasks.append(
                    self.execute_web_searches(
                        analysis['web_search_queries'],
                        location
                    )
                )
            
            # News search
            if analysis.get('requires_news') and analysis.get('news_search_query'):
                tasks.append(
                    self.fetch_news(
                        analysis['news_search_query'],
                        location
                    )
                )
            
            # Execute all tasks in parallel
            logger.info(f"🚀 Launching {len(tasks)} parallel tasks...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate results
            agent_responses = []
            web_search_results = []
            news_results = {}
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed: {str(result)}")
                    continue
                
                if isinstance(result, list):  # Web search results
                    web_search_results = result
                elif isinstance(result, dict):
                    if 'agent' in result:  # Agent response
                        if result.get('success'):
                            agent_responses.append(result)
                    elif 'articles' in result:  # News results
                        news_results = result
            
            logger.info(f"✅ Parallel execution complete:")
            logger.info(f"   Agents: {len(agent_responses)}")
            logger.info(f"   Web searches: {len(web_search_results)}")
            logger.info(f"   News: {'Yes' if news_results.get('success') else 'No'}")
            logger.info(f"   Agro data: {'Yes' if agro_data else 'No'}")
            
            # Step 4: Synthesize comprehensive response
            if not agent_responses and not web_search_results and not news_results.get('success') and not agro_data:
                # Simple response if no sources
                synthesized_response = f"""Thank you for your question about {query}.

I'm here to help with comprehensive agricultural guidance. However, I need a bit more context to provide the most accurate advice.

**What I can help with:**
- 🌾 Crop planning and profitability analysis
- 🚜 Equipment recommendations and vendor connections
- 💰 Market prices and selling strategies
- 🌤️ Weather-based farming advice
- 🌱 Crop management and pest control
- 💧 Irrigation and water management

**To provide better guidance, please share:**
- What crop are you growing or planning to grow?
- What specific challenge or decision are you facing?
- What stage of farming are you in (planning, growing, harvesting)?

I'll then provide detailed, location-specific recommendations with specific numbers, costs, and action steps.

Feel free to ask anything about farming - I have access to market data, weather information, and agricultural expertise!
"""
            else:
                synthesized_response = await self.synthesize_comprehensive_response(
                    query=query,
                    analysis=analysis,
                    agent_responses=agent_responses,
                    web_search_results=web_search_results,
                    news_results=news_results,
                    agro_data=agro_data,
                    user_context=user_context
                )
            
            logger.info(f"{'='*70}")
            logger.info(f"✅ ORCHESTRATION COMPLETE")
            logger.info(f"{'='*70}")

            # Step 5: Analyze for booking/order suggestions
            logger.info("🔍 Starting booking/order analysis...")
            booking_order_suggestions = await self.analyze_for_booking_order(
                query=query,
                final_response=synthesized_response,
                chat_history=chat_history,
                user_id=user_context.get('UserId')
            )
            logger.info(f"📊 Booking/order analysis result: {booking_order_suggestions}")

            # Then modify the return dict to include these two new keys:
            return {
                'phase': analysis.get('query_type', 'general'),
                'agents_consulted': [r['agent'] for r in agent_responses],
                'responses': agent_responses,
                'web_search_data': web_search_results,
                'news_data': news_results,
                'agro_data': agro_data,
                'context': context,
                'query': query,
                'final_response': synthesized_response,
                'analysis': analysis,
                'booking_suggestion': booking_order_suggestions.get('booking'),
                'order_suggestion': booking_order_suggestions.get('order')
            }
            
        except Exception as e:
            logger.error(f"❌ ORCHESTRATION FAILED: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise e