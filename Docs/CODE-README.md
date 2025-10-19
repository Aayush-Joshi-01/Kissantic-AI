# Kisaantic AI - Technical Documentation

**An Intelligent Multi-Agentic AI Agricultural Assistant**

Kisaantic AI implements an advanced LLM-powered orchestration system that coordinates 8 specialized Bedrock agents with real-time external data sources to deliver comprehensive agricultural guidance.

---

## Table of Contents

1. [Overview](#overview)
2. [Intelligent Orchestration Architecture](#intelligent-orchestration-architecture)
3. [Chat Lambda Implementation](#chat-lambda-implementation)
4. [Multi-Agent Orchestrator](#multi-agent-orchestrator)
5. [Technology Stack](#technology-stack)
6. [External API Integration](#external-api-integration)
7. [Database Design](#database-design)
8. [Frontend Application](#frontend-application)
9. [Deployment](#deployment)
10. [Performance & Optimization](#performance--optimization)

---

## Overview

### Mission
Empower every farmer with intelligent multi-agent AI decision-making free from middlemen and political dependencies so they keep the full value of their work.

### Core Innovation: LLM-Powered Orchestration with API Tools

Unlike traditional rule-based routing systems, Kisaantic AI uses **Amazon Nova Lite as an intelligent routing LLM** that:
- Analyzes query complexity and intent
- Dynamically selects 0-6 agents based on requirements
- Determines when to invoke specific API tools (Web Search, News Search)
- Coordinates parallel execution across agents and API tools
- Uses **Amazon Nova Pro** for sophisticated response synthesis

**4 Integrated API Tools**:
1. **Agricultural Data Tool** - Real-time weather, soil, historical data
2. **Web Search Tool** - Market intelligence via LangSearch
3. **News Search Tool** - Latest agricultural news via NewsAPI
4. **Market Data Tool** - Planned for Phase 2

---

## Intelligent Orchestration Architecture

### Complete Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Sends Query                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS API Gateway (REST API)                     │
│                 JWT Authorization                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Chat Lambda Handler (lambda_handler.py)             │
│                                                             │
│  STEP 1: Authentication (verify_token)                      │
│  STEP 2: Parse & validate request (ChatRequest schema)      │
│  STEP 3: Fetch user profile (DynamoDB)                      │
│  STEP 4: Get/create session (DynamoDB)                      │
│  STEP 5: Save user message (DynamoDB)                       │
│  STEP 6: Build context (user + location + history)          │
│  STEP 7: ORCHESTRATION (MultiAgentOrchestrator)             │
│  STEP 8: Save AI response + metadata (DynamoDB)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│      Multi-Agent Orchestrator (orchestrator.py)             │
│      Primary Model: Amazon Nova Lite (routing)              │
│      Synthesis Model: Amazon Nova Pro                       │
│      API Tools: 4 integrated tools                          │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PHASE 1: Agricultural Data API Tool Invocation         │ │
│  │ → Invoke fetch_agricultural_data tool                  │ │
│  │ → Returns: weather + soil (5 depths) + historical      │ │
│  │ → Includes anomaly detection, GDD, seasonal context    │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                │
│                            ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PHASE 2: LLM-Based Query Analysis                      │ │
│  │ → Invoke Nova Lite with comprehensive prompt           │ │
│  │ → Input: query + user context + agro data + history    │ │
│  │ → Output: JSON analysis with:                          │ │
│  │   • query_type (simple/complex/multi_aspect)           │ │
│  │   • required_agents (0-6 agent names)                  │ │
│  │   • requires_web_search (boolean + queries)            │ │
│  │   • requires_news (boolean + query)                    │ │
│  │   • response_complexity (simple/detailed/comp)         │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                │
│                            ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PHASE 3: Parallel Execution (asyncio.gather)           │ │
│  │                                                        │ │
│  │  ┌──────────────────┐  ┌──────────────────┐            │ │
│  │  │ Bedrock Agents   │  │ API Tools        │            │ │
│  │  ├──────────────────┤  ├──────────────────┤            │ │
│  │  │ • Weather Advisor│  │ • Web Search     │            │ │
│  │  │ • Crop Specialist│  │   Tool           │            │ │
│  │  │ • Pest Manager   │  │ • News Search    │            │ │
│  │  │ • Soil Analyst   │  │   Tool           │            │ │
│  │  │ • Irrigation     │  └──────────────────┘            │ │
│  │  │ • Crop Planner   │                                  │ │
│  │  │ • Equipment      │  Each agent receives:            │ │
│  │  │ • Market Linkage │  • Enhanced prompt with          │ │
│  │  └──────────────────┘    agro data                     │ │
│  │                          • Role-specific instructions  │ │
│  │                          • Real-time context           │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                │
│                            ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PHASE 4: Response Synthesis (Nova Pro)                 │ │
│  │                                                        │ │
│  │ Input to synthesizer:                                  │ │
│  │ • Original query                                       │ │
│  │ • Query analysis                                       │ │
│  │ • Agro data (weather, soil, historical)                │ │
│  │ • Agent responses (0-6 responses)                      │ │
│  │ • Web search results (0-3 searches)                    │ │
│  │ • News articles (0-5 articles)                         │ │
│  │                                                        │ │
│  │ Synthesis process:                                     │ │
│  │ • 5000 token comprehensive prompt                      │ │
│  │ • Structured format instructions                       │ │
│  │ • Real-time data integration rules                     │ │
│  │ • Markdown formatting with tables/emojis               │ │
│  │ • Temperature: 0.9 (creative synthesis)                │ │
│  │ • MaxTokens: 5000 (long-form response)                 │ │
│  │                                                        │ │
│  │ Output: 3000-5000 word unified response                │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Chat Lambda: Save Response + Metadata to DynamoDB          │
│                                                             │
│  Metadata tracked:                                          │
│  • orchestrator_used: true                                  │
│  • query_type: from analysis                                │
│  • agents_consulted: [list of agent names]                  │
│  • agent_count: number                                      │
│  • web_search_used: boolean                                 │
│  • news_used: boolean                                       │
│  • has_agro_data: boolean                                   │
│  • response_tokens: estimated count                         │
│  • processing_time_seconds: float                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Return ChatResponse to Frontend                    │
│  • session_id                                               │
│  • user_message (MessageResponse object)                    │
│  • ai_message (MessageResponse object with metadata)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Chat Lambda Implementation

### File: `Backend/lambdas/chat/lambda_handler.py`

#### Key Components

```python
# Core imports
from orchestrator import MultiAgentOrchestrator
from agriculture_context import AgriculturalContextFetcher
from schemas import ChatRequest, ChatResponse, MessageResponse
from auth import verify_token
from dynamodb_helper import (
    get_chat_session, create_chat_session, create_message,
    update_chat_session, get_user_by_id, get_chat_history_for_agent
)

# Configuration
USE_ORCHESTRATOR = os.getenv('USE_ORCHESTRATOR', 'true').lower() == 'true'
OUTPUT_TOKEN_LIMIT = int(os.getenv('OUTPUT_TOKEN_LIMIT', '5000'))
CHAT_HISTORY_LIMIT = int(os.getenv('CHAT_HISTORY_LIMIT', '10'))
AGRO_API_URL = os.getenv('AGRO_API_URL', 'base_url')

# Initialization
orchestrator = MultiAgentOrchestrator()
agro_fetcher = AgriculturalContextFetcher(AGRO_API_URL)
```

#### 8-Step Processing Flow

**STEP 1: Authentication**
```python
token = extract_token_from_header(auth_header)
token_data = verify_token(token)
user_id = token_data['user_id']
```

**STEP 2: Parse Request**
```python
body = json.loads(event['body'])
chat_request = ChatRequest(**body)  # Pydantic validation
# Fields: message, session_id, latitude, longitude, address, 
#         weather_temp, weather_condition, weather_humidity
```

**STEP 3: Get User Data**
```python
user = get_user_by_id(user_id)
# Returns: UserId, Email, Name, FarmSize, CropType, 
#          Latitude, Longitude, Address
```

**STEP 4: Handle Session**
```python
if chat_request.session_id:
    session = get_chat_session(chat_request.session_id, user_id)
else:
    session = create_chat_session(user_id, "New Chat")
```

**STEP 5: Save User Message**
```python
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

# Auto-generate session title from first message
if session.get('MessageCount', 0) == 0:
    title = chat_request.message[:50] + ("..." if len(...) > 50 else "")
    update_chat_session(session_id, user_id, title)
```

**STEP 6: Build Context**
```python
user_context = {
    'UserId': user.get('UserId'),
    'Name': user.get('Name'),
    'FarmSize': user.get('FarmSize'),
    'CropType': user.get('CropType'),
    'Address': chat_request.address or user.get('Address'),
    'Latitude': chat_request.latitude or user.get('Latitude'),
    'Longitude': chat_request.longitude or user.get('Longitude')
}

# Get chat history (last 10 messages)
chat_history = get_chat_history_for_agent(
    session_id=session_id,
    limit=CHAT_HISTORY_LIMIT
)

# Optionally fetch agricultural data via AgriculturalContextFetcher
# (Note: Orchestrator also fetches this internally)
agro_data = await agro_fetcher.get_complete_dataset(lat, lon)

context = {
    'user_profile': user_context,
    'location': {'latitude': lat, 'longitude': lon, 'address': address},
    'weather_data': {...},
    'agricultural_data': agro_data,
    'chat_history': chat_history,
    'query': chat_request.message,
    'timestamp': datetime.now().isoformat()
}
```

**STEP 7: Orchestration (Core Intelligence)**
```python
loop = asyncio.get_event_loop()
orchestration_result = loop.run_until_complete(
    orchestrator.process_query(
        query=chat_request.message,
        context=context,
        session_id=str(session_id)
    )
)

# Returns:
# {
#   'phase': 'query_type',
#   'agents_consulted': ['agent1', 'agent2', ...],
#   'responses': [agent response objects],
#   'web_search_data': [...],
#   'news_data': {...},
#   'agro_data': {...},
#   'final_response': 'synthesized response text',
#   'analysis': {...}
# }

ai_text = orchestration_result.get('final_response')
analysis = orchestration_result.get('analysis', {})
agents_used = orchestration_result.get('agents_consulted', [])
```

**STEP 8: Save AI Response**
```python
ai_message = create_message(
    session_id=session_id,
    text=ai_text,
    sender='ai',
    metadata=ai_metadata  # Includes orchestration insights
)
```

#### Error Handling

```python
try:
    # ... orchestration ...
except Exception as e:
    logger.error(f"Orchestration failed: {str(e)}")
    
    # Fallback response
    ai_text = """I apologize, but I encountered an issue processing your request.

However, I'm here to help with:
- 🌾 Crop planning and profitability analysis
- 🚜 Equipment recommendations and vendor connections
- 💰 Market prices and selling strategies
...
"""
```

---

## Multi-Agent Orchestrator

### File: `orchestrator.py`

#### Class: `MultiAgentOrchestrator`

##### Initialization

```python
def __init__(self, region_name: str = "ap-south-1"):
    self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name)
    self.bedrock = boto3.client('bedrock-runtime', region_name)
    
    # Models
    self.routing_model = "apac.amazon.nova-lite-v1:0"  # Fast routing LLM
    self.synthesis_model = "apac.amazon.nova-pro-v1:0"  # Quality synthesis
    
    # API Keys from environment
    self.langsearch_key = os.getenv('LANGSEARCH_API_KEY', '')
    self.news_api_key = os.getenv('NEWS_API_KEY', '')
    
    # Agro API URL with /agro-api prefix handling
    base_url = os.getenv('AGRO_API_URL', 'default_url')
    if '/agro-api' not in base_url:
        self.agro_api_url = f"{base_url.rstrip('/')}/agro-api"
    else:
        self.agro_api_url = base_url.rstrip('/')
    
    # Load agent configurations from agent_config.json
    self.agents = self._load_agent_config()
```

##### Method: `process_query()` - Main Orchestration

```python
async def process_query(
    self,
    query: str,
    context: Dict,
    session_id: str
) -> Dict:
    """
    Main orchestration flow:
    1. Invoke Agricultural Data API Tool
    2. Analyze query with LLM
    3. Parallel execution (agents + API tools)
    4. Synthesize comprehensive response
    """
    
    user_context = context.get('user_profile', {})
    location = context.get('location', {})
    
    # PHASE 1: Invoke Agricultural Data API Tool FIRST
    agro_data = await self.fetch_agricultural_data(
        latitude=location.get('latitude'),
        longitude=location.get('longitude')
    )
    
    # PHASE 2: LLM-based query analysis
    analysis = await self.analyze_query_with_llm(
        query, user_context, chat_history, agro_data
    )
    # Returns: query_type, required_agents, requires_web_search, etc.
    
    # PHASE 3: Parallel execution - agents and API tools
    tasks = []
    
    # Add agent invocation tasks
    if analysis.get('requires_agents'):
        for agent_name in analysis['required_agents'][:6]:  # Max 6 agents
            tasks.append(
                self.invoke_agent(
                    AgentType(agent_name),
                    query, user_context, agro_data,
                    session_id, analysis
                )
            )
    
    # Add Web Search API Tool invocation
    if analysis.get('requires_web_search'):
        tasks.append(
            self.execute_web_searches(  # Web Search API Tool
                analysis['web_search_queries'],
                location
            )
        )
    
    # Add News Search API Tool invocation
    if analysis.get('requires_news'):
        tasks.append(
            self.fetch_news(  # News Search API Tool
                analysis['news_search_query'],
                location
            )
        )
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Separate results by type
    agent_responses = [r for r in results if isinstance(r, dict) and 'agent' in r]
    web_search_results = [r for r in results if isinstance(r, list)]
    news_results = [r for r in results if isinstance(r, dict) and 'articles' in r]
    
    # PHASE 4: Synthesize comprehensive response
    synthesized_response = await self.synthesize_comprehensive_response(
        query=query,
        analysis=analysis,
        agent_responses=agent_responses,
        web_search_results=web_search_results,
        news_results=news_results,
        agro_data=agro_data,
        user_context=user_context
    )
    
    return {
        'phase': analysis.get('query_type'),
        'agents_consulted': [r['agent'] for r in agent_responses],
        'responses': agent_responses,
        'web_search_data': web_search_results,
        'news_data': news_results,
        'agro_data': agro_data,
        'final_response': synthesized_response,
        'analysis': analysis
    }
```

##### Method: `fetch_agricultural_data()` - Agricultural Data API Tool

```python
async def fetch_agricultural_data(
    self,
    latitude: float,
    longitude: float
) -> Optional[Dict]:
    """
    API Tool: fetch_agricultural_data
    Invokes internal Agro API for comprehensive agricultural data
    
    Returns:
    {
      'current': {
        'temp_c': 28.5,
        'feels_like_c': 30.2,
        'humidity_pct': 65,
        'precipitation_mm': 0.0,
        'wind_speed_kmh': 15,
        'uv_index': 7,
        'condition': 'Partly cloudy'
      },
      'soil': {
        'moisture_0_1': 0.25,  # m³/m³
        'moisture_1_3': 0.28,
        'moisture_3_9': 0.30,
        'moisture_9_27': 0.32,
        'moisture_27_81': 0.35,
        'avg_moisture': 0.30,
        'dryness_index': 65,  # 0-100, higher = drier
        'moisture_trend': 'decreasing',
        'temp_0cm': 32.0,
        'temp_6cm': 28.5
      },
      'historical': {
        'relevant_season': 'Kharif',
        'season_context': 'Mid-season',
        'historical_stats': {
          'temp_avg_historical': 27.3,
          'total_precip_historical': 450.2,
          'total_gdd_historical': 1250
        },
        'seasonal_comparison': {
          'current_temp_vs_historical': 1.2,  # °C above
          'temp_percentile': 75,  # Warmer than 75% of historical
          'current_precip_vs_historical': -45.5,  # mm below
          'precip_percentile': 30,  # Drier than 70% of historical
          'anomaly_flags': ['warmer_than_normal', 'drier_than_normal']
        }
      }
    }
    """
    
    full_url = f"{self.agro_api_url}/complete?lat={latitude}&lon={longitude}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            full_url,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Agro data fetched")
                return data
            else:
                logger.error(f"❌ Agro API error {response.status}")
                return None
```

##### Method: `analyze_query_with_llm()` - Intelligent Routing

```python
async def analyze_query_with_llm(
    self,
    query: str,
    user_context: Dict,
    chat_history: List[Dict],
    agro_data: Optional[Dict]
) -> Dict:
    """
    Uses Nova Lite LLM to analyze query and determine routing strategy
    
    Builds comprehensive prompt with:
    - Farmer profile
    - Recent chat history (last 3 messages)
    - Real-time agricultural data
    - Available agents list
    - Routing logic guidance
    
    Returns JSON analysis:
    {
      "query_type": "simple_greeting | simple_question | complex_farming | multi_aspect",
      "requires_agents": true/false,
      "required_agents": ["agent_name1", "agent_name2", ...],  # 0-6 agents
      "agent_priority": {"agent_name": "why needed"},
      "requires_web_search": true/false,
      "web_search_queries": ["query1", "query2"],
      "requires_news": true/false,
      "news_search_query": "news query",
      "requires_agro_data": true/false,
      "agro_data_available": true/false,
      "response_complexity": "simple | detailed | comprehensive",
      "key_data_points": ["data1", "data2"],
      "location_specific": true/false
    }
    """
    
    # Build comprehensive analysis prompt
    analysis_prompt = f"""You are an expert agricultural AI system analyzer...
    
FARMER PROFILE:
- Location: {user_context.get('Address')}
- Farm Size: {user_context.get('FarmSize')} acres
- Primary Crop: {user_context.get('CropType')}

RECENT CONVERSATION:
{format_chat_history(chat_history[-3:])}

CURRENT AGRICULTURAL CONDITIONS:
{format_agro_data(agro_data)}

AVAILABLE AGENTS:
1. weather_advisor - Weather forecasts, climate impact
2. crop_specialist - Crop management, varieties
3. pest_manager - Pest/disease identification
4. soil_analyst - Soil health, fertility
5. irrigation_expert - Water management
6. crop_planner - ROI analysis, profitability
7. equipment_vendor - Equipment, vendors
8. market_linkage - Market prices, strategies

FARMER'S QUERY: "{query}"

Analyze and respond in JSON format:
{{
  "query_type": "...",
  "requires_agents": true/false,
  "required_agents": [...],
  ...
}}
"""
    
    # Invoke Nova Lite for routing decision
    response = self.bedrock.invoke_model(
        modelId=self.routing_model,  # Nova Lite
        body=json.dumps({
            "messages": [{"role": "user", "content": [{"text": analysis_prompt}]}],
            "inferenceConfig": {
                "temperature": 0.1,  # Low temp for consistent routing
                "maxTokens": 1500
            }
        })
    )
    
    # Parse JSON response
    response_body = json.loads(response['body'].read())
    analysis = extract_and_parse_json(response_body)
    
    return analysis
```



##### Method: `execute_web_searches()` - Web Search API Tool

```python
async def execute_web_searches(
    self,
    queries: List[str],
    location: Dict
) -> List[Dict]:
    """
    API Tool: execute_web_searches (Web Search Tool)
    Invokes LangSearch API with up to 3 parallel search queries
    """
    
    async def single_search(query: str) -> Dict:
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
                    return {'query': query, 'results': results, 'success': True}
                return {'query': query, 'results': [], 'success': False}
    
    # Execute up to 3 searches in parallel
    searches = [single_search(q) for q in queries[:3]]
    results = await asyncio.gather(*searches)
    
    return results
```

##### Method: `fetch_news()` - News Search API Tool

```python
async def fetch_news(
    self,
    query: str,
    location: Dict
) -> Dict:
    """
    API Tool: fetch_news (News Search Tool)
    Invokes NewsAPI.org for latest agricultural news
    """
    
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
                return {
                    'query': query,
                    'articles': articles,
                    'success': True
                }
            return {'query': query, 'articles': [], 'success': False}
```

##### Method: `invoke_agent()` - Bedrock Agent Invocation

```python
async def invoke_agent(
    self,
    agent_type: AgentType,
    query: str,
    user_context: Dict,
    agro_data: Optional[Dict],
    session_id: str,
    analysis: Dict
) -> Dict:
    """
    Invokes single Bedrock agent with enhanced context
    """
    
    agent_config = self.agents.get(agent_type.value, {})
    
    # Build comprehensive prompt with real-time data
    prompt = self._build_enhanced_prompt(
        query, user_context, agro_data, agent_type, analysis
    )
    
    # Invoke Bedrock agent
    response = self.bedrock_runtime.invoke_agent(
        agentId=agent_config['agent_id'],
        agentAliasId=agent_config['alias_id'],
        sessionId=f"{session_id}-{agent_type.value}",
        inputText=prompt,
        enableTrace=False
    )
    
    # Collect streaming response
    agent_response = ""
    for event in response.get('completion', []):
        if 'chunk' in event and 'bytes' in event['chunk']:
            agent_response += event['chunk']['bytes'].decode('utf-8')
    
    return {
        'agent': agent_type.value,
        'response': agent_response,
        'success': bool(agent_response)
    }
```

##### Method: `_build_enhanced_prompt()` - Context-Rich Prompts

```python
def _build_enhanced_prompt(
    self,
    query: str,
    user_context: Dict,
    agro_data: Optional[Dict],
    agent_type: AgentType,
    analysis: Dict
) -> str:
    """
    Builds comprehensive prompt for agent with:
    - User profile and location
    - Real-time agricultural data (weather, soil, historical)
    - Query analysis context
    - Agent-specific instructions
    """
    
    prompt = f"""You are Kisaantic AI's {agent_type.value.replace('_', ' ').title()}.

FARMER PROFILE:
- Location: {user_context.get('Address')}
- Farm Size: {user_context.get('FarmSize')} acres
- Crop: {user_context.get('CropType')}

YOUR ROLE IN THIS QUERY:
{analysis.get('agent_priority', {}).get(agent_type.value)}

"""
    
    # Add real-time agricultural data
    if agro_data:
        prompt += f"""
REAL-TIME AGRICULTURAL DATA:

CURRENT WEATHER:
- Temperature: {agro_data['current']['temp_c']}°C
- Humidity: {agro_data['current']['humidity_pct']}%
- Precipitation: {agro_data['current']['precipitation_mm']} mm
- Condition: {agro_data['current']['condition']}

SOIL CONDITIONS:
- Surface Moisture (0-1cm): {agro_data['soil']['moisture_0_1']} m³/m³
- Average Moisture: {agro_data['soil']['avg_moisture']} m³/m³
- Dryness Index: {agro_data['soil']['dryness_index']}/100
- Trend: {agro_data['soil']['moisture_trend']}

SEASONAL CONTEXT:
- Season: {agro_data['historical']['relevant_season']}
- Stage: {agro_data['historical']['season_context']}
- Anomalies: {', '.join(agro_data['historical']['seasonal_comparison']['anomaly_flags'])}

"""
    
    # Agent-specific instructions
    agent_instructions = {
        AgentType.IRRIGATION_EXPERT: """
YOUR EXPERTISE: Water management, irrigation optimization

RESPONSE GUIDELINES:
- **USE REAL-TIME SOIL MOISTURE DATA extensively**
- Dryness index >70 = immediate irrigation needed
- Calculate water requirements based on current moisture
- **Provide specific irrigation schedule based on data**
""",
        AgentType.CROP_PLANNER: """
YOUR EXPERTISE: ROI analysis, crop profitability

RESPONSE GUIDELINES:
- Calculate detailed costs with specific numbers
- Provide ROI percentages and profit projections
- Use regional data when available (MP in knowledge base)
- **USE REAL-TIME WEATHER/SOIL DATA to adjust timing and costs**
""",
        # ... other agent instructions
    }
    
    prompt += agent_instructions.get(agent_type, "")
    
    prompt += f"""

FARMER'S QUESTION: "{query}"

Provide expert advice with real-time data integration (300-600 words):
"""
    
    return prompt
```

##### Method: `synthesize_comprehensive_response()` - Nova Pro Synthesis

```python
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
    Synthesizes all sources into comprehensive 3000-5000 word response
    
    Uses Nova Pro with:
    - Temperature: 0.9 (creative synthesis)
    - MaxTokens: 5000 (long-form content)
    
    Format enforced:
    1. Immediate Answer 🌾 (150-250 words)
    2. Detailed Analysis 🌱 (multiple subsections, 200-400 words each)
    3. Action Plan 📋 (markdown table format)
    4. Additional Insights (100-200 words per subsection)
    5. Quick Summary (5-8 bullet points)
    """
    
    # Build massive synthesis prompt (5000+ tokens)
    synthesis_prompt = f"""You are synthesizing a COMPREHENSIVE agricultural response.

FARMER'S QUESTION: "{query}"

FARMER CONTEXT:
- Location: {user_context.get('Address')}
- Farm Size: {user_context.get('FarmSize')} acres

{'='*60}
REAL-TIME AGRICULTURAL DATA:
{'='*60}

{format_agro_data_for_synthesis(agro_data)}

{'='*60}
SPECIALIST AGENT INSIGHTS ({len(agent_responses)} agents):
{'='*60}

{format_agent_responses(agent_responses)}

{'='*60}
WEB SEARCH DATA:
{'='*60}

{format_web_results(web_search_results)}

{'='*60}
RECENT NEWS:
{'='*60}

{format_news(news_results)}

{'='*60}
SYNTHESIS TASK - KISAANTIC AI FORMAT
{'='*60}

Create ONE UNIFIED response following this structure:

1. **Immediate Answer 🌾** (descriptive heading, not "Immediate Answer")
   - Direct answer with real-time data integration
   - 150-250 words

2. **Detailed Analysis 🌱** (multiple specific subsections)
   - Examples: "Equipment Insights", "Cost-Benefit Analysis", "Seasonal Recommendations"
   - Each subsection: 200-400 words
   - **Seamlessly weave real-time data** (e.g., "With current soil moisture at 0.25 m³/m³...")
   - Use **bold** for key terms

3. **Action Plan 📋** (ALWAYS table format)
   | Timeline / Stage | Action | Details / Resources |
   |-----------------|--------|---------------------|
   | Immediate | First step | Specific details, costs, vendors |
   | Week 1-2 | Second step | Quantities, prices |

4. **Additional Insights** (if relevant)
   - Market trends, news updates, alternatives, risks
   - 100-200 words per subsection

5. **Quick Summary**
   - 5-8 bullet points
   - Key numbers and dates
   - Current conditions snapshot

CRITICAL RULES:
✅ DO: Weave real-time data naturally, use tables for action plans, short paragraphs
❌ DON'T: Mention "tokens", say "According to X agent", use generic headings

TARGET LENGTH: 3000-5000 words (NEVER mention this to user)

Begin synthesis now:
"""
    
    # Invoke Nova Pro for synthesis
    response = self.bedrock.invoke_model(
        modelId=self.synthesis_model,  # Nova Pro
        body=json.dumps({
            "messages": [{
                "role": "user",
                "content": [{"text": synthesis_prompt}]
            }],
            "inferenceConfig": {
                "temperature": 0.9,  # High for creative synthesis
                "maxTokens": 5000
            }
        })
    )
    
    response_body = json.loads(response['body'].read())
    synthesized = extract_text(response_body)
    
    return synthesized
```



---

## Technology Stack

### Backend Core

```python
# Lambda Runtime
Python 3.13

# AWS SDK
boto3==1.34.144  # Bedrock, DynamoDB, S3

# Async HTTP
aiohttp==3.9.5   # For parallel API calls

# Data Validation
pydantic==2.7.4  # Request/response schemas

# Authentication
PyJWT==2.8.0     # JWT tokens
bcrypt==4.0.1    # Password hashing

# Utilities
python-dotenv==1.0.1  # Environment variables
```

### AI Models

```yaml
Routing LLM: apac.amazon.nova-lite-v1:0
  - Purpose: Query analysis, agent selection
  - Temperature: 0.1 (consistent routing)
  - MaxTokens: 1500
  - Cost: ~$0.00006/request

Domain Agents: apac.amazon.nova-lite-v1:0 (8 agents)
  - Purpose: Specialized domain expertise
  - Context: RAG with knowledge bases
  - Streaming: Yes
  - Cost: ~$0.0003/agent invocation

Synthesizer: apac.amazon.nova-pro-v1:0
  - Purpose: Comprehensive response synthesis
  - Temperature: 0.9 (creative synthesis)
  - MaxTokens: 5000
  - Cost: ~$0.0012/synthesis
```

### Frontend

```json
{
  "next": "15.2.4",
  "react": "19.0.0",
  "react-dom": "19.0.0",
  "typescript": "5.x",
  "tailwindcss": "4.1.9",
  "@radix-ui/*": "latest",
  "react-hook-form": "7.60.0",
  "zod": "3.23.8",
  "react-leaflet": "5.0.0",
  "react-markdown": "9.0.1",
  "install_note": "Use --legacy-peer-deps for React 19"
}
```

---

## API Tools Integration

The orchestrator has 4 API tools at its disposal, invoked based on query analysis:

### 1. Agricultural Data API Tool (Internal)

**Tool Name**: `fetch_agricultural_data`

**Invocation Method**: GET

**Endpoint**: `{AGRO_API_URL}/agro-api/complete`

**Parameters**: `lat`, `lon`

**Backend Providers**: 
- Open Meteo (primary weather + soil)
- OpenWeather API (additional weather data)

**Invocation Timing**: Automatically invoked FIRST before query analysis

**Response Structure**:
```json
{
  "current": {
    "temp_c": 28.5,
    "feels_like_c": 30.2,
    "humidity_pct": 65,
    "precipitation_mm": 0.0,
    "wind_speed_kmh": 15,
    "uv_index": 7,
    "condition": "Partly cloudy"
  },
  "soil": {
    "moisture_0_1": 0.25,
    "moisture_1_3": 0.28,
    "moisture_3_9": 0.30,
    "moisture_9_27": 0.32,
    "moisture_27_81": 0.35,
    "avg_moisture": 0.30,
    "dryness_index": 65,
    "moisture_trend": "decreasing",
    "temp_0cm": 32.0,
    "temp_6cm": 28.5
  },
  "historical": {
    "relevant_season": "Kharif",
    "season_context": "Mid-season",
    "historical_stats": {
      "temp_avg_historical": 27.3,
      "total_precip_historical": 450.2,
      "total_gdd_historical": 1250
    },
    "seasonal_comparison": {
      "current_temp_vs_historical": 1.2,
      "temp_percentile": 75,
      "current_precip_vs_historical": -45.5,
      "precip_percentile": 30,
      "anomaly_flags": ["warmer_than_normal", "drier_than_normal"]
    }
  }
}
```

**Data Sources**:
- Open Meteo (primary weather + soil)
- OpenWeather API (additional weather data)

**Invocation Trigger**: Automatic - always invoked first

---

### 2. Web Search API Tool (External)

**Tool Name**: `execute_web_searches`

**Invocation Method**: POST

**Backend Provider**: LangSearch API

**Endpoint**: `https://api.langsearch.com/v1/web-search`

**Headers**:
```json
{
  "Authorization": "Bearer {LANGSEARCH_API_KEY}",
  "Content-Type": "application/json"
}
```

**Request Body**:
```json
{
  "query": "wheat market prices India",
  "freshness": "oneWeek",
  "summary": true,
  "count": 5
}
```

**Invocation Triggers**:
- Market prices, mandi rates
- Equipment availability, vendor contacts
- Current trends, recent developments

**Parallel Invocation**: Up to 3 search queries executed simultaneously

---

### 3. News Search API Tool (External)

**Tool Name**: `fetch_news`

**Invocation Method**: GET

**Backend Provider**: NewsAPI.org

**Endpoint**: `https://newsapi.org/v2/everything`

**Parameters**:
```python
{
    'q': 'government schemes agriculture',
    'apiKey': NEWS_API_KEY,
    'language': 'en',
    'sortBy': 'publishedAt',
    'pageSize': 5
}
```

**Invocation Triggers**:
- Government schemes, policy changes
- Market news, price trends
- Crop-specific developments
- Subsidy announcements

**Response**: Up to 5 recent articles with title, description, publishedAt

---

### 4. Market Data API Tool (Planned - Phase 2)

**Tool Name**: `fetch_market_prices`

**Purpose**: Real-time mandi prices, MSP data

**Status**: Development planned

**Backend Provider**: Government mandi APIs, AgriMarket

---

## Database Design

### DynamoDB Single-Table Design

**Table**: `kisaantic-prod`

**Access Patterns**:
```
1. Get user by email → PK=USER#{email}, SK=PROFILE
2. Get user by ID → GSI1: GSI1PK=USERID#{user_id}
3. Get refresh tokens → PK=USER#{email}, SK begins_with REFRESH_TOKEN#
4. Get user sessions → PK=USER#{user_id}, SK begins_with SESSION#
5. Get session messages → PK=SESSION#{session_id}, SK begins_with MESSAGE#
6. List recent sessions → Query + sort by UpdatedAt (GSI1SK)
```

### Entity Examples

**User Profile**:
```python
{
    "PK": "USER#farmer@example.com",
    "SK": "PROFILE",
    "UserId": "uuid-1234-5678",
    "Email": "farmer@example.com",
    "HashedPassword": "bcrypt_hash",
    "Name": "Ram Singh",
    "Phone": "+919876543210",
    "FarmSize": "50",
    "CropType": "Wheat",
    "Latitude": 23.2599,
    "Longitude": 77.4126,
    "Address": "Bhopal, Madhya Pradesh",
    "CreatedAt": "2025-10-19T00:00:00Z",
    "UpdatedAt": "2025-10-19T00:00:00Z",
    "GSI1PK": "USERID#uuid-1234-5678"
}
```

**AI Message**:
```python
{
    "PK": "SESSION#session-uuid",
    "SK": "MESSAGE#2025-10-19T10:05:00Z#msg-uuid",
    "MessageId": "msg-uuid",
    "SessionId": "session-uuid",
    "Text": "[3000-5000 word comprehensive response]",
    "Sender": "ai",
    "CreatedAt": 1729331100,
    "CreatedAtISO": "2025-10-19T10:05:00Z",
    "Metadata": {
        "orchestrator_used": true,
        "agents_consulted": ["crop_planner", "equipment_vendor", "market_linkage"]
    }
}
```

---

## Frontend Application

### Key Files

**API Client**: `App/lib/api.ts`
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function chatWithAI(data: ChatRequestData) {
  const token = getAccessToken();
  
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  
  if (response.status === 401) {
    // Auto-refresh token
    await refreshTokens();
    return chatWithAI(data);  // Retry
  }
  
  return response.json();
}
```

**Chat Interface**: `App/components/chat/chat-ui.tsx`
```typescript
// Displays comprehensive responses with markdown
// Handles streaming (though backend doesn't stream yet)
// Shows loading states during orchestration
// Formats tables, emojis, code blocks
```

---

## Deployment

### Lambda Configuration

**Chat Lambda**:
```yaml
Runtime: python3.13
Architecture: x86_64
Memory: 1024 MB
Timeout: 300 seconds (5 minutes)
Layers:
  - utils-layer (dynamodb, auth, schemas)
  - bedrock-integration-layer (orchestrator, context)
Environment:
  USE_ORCHESTRATOR: "true"
  OUTPUT_TOKEN_LIMIT: "5000"
  CHAT_HISTORY_LIMIT: "10"
  AGRO_API_URL: "https://{api-id}.execute-api.ap-south-1.amazonaws.com/api"
  LANGSEARCH_API_KEY: "{encrypted}"
  NEWS_API_KEY: "{encrypted}"
IAM Permissions:
  - bedrock:InvokeAgent
  - bedrock:InvokeModel
  - bedrock-agent-runtime:InvokeAgent
  - dynamodb:GetItem
  - dynamodb:PutItem
  - dynamodb:Query
```

**Other Lambdas**:
```yaml
Auth Lambdas: 512 MB, 30s timeout
Weather/Agro Lambdas: 512 MB, 30s timeout
Session Lambdas: 256 MB, 10s timeout
```

---

## Performance & Optimization

### Parallel Execution Benefits

```python
# Sequential (slow):
agro_data = await fetch_agro()              # 2-3s
analysis = await analyze_query()            # 1-2s
agent1 = await invoke_agent1()              # 5-10s
agent2 = await invoke_agent2()              # 5-10s
web = await web_search()                    # 2-3s
Total: 15-28 seconds

# Parallel (fast):
analysis = await analyze_query()            # 1-2s
results = await asyncio.gather(
    invoke_agent1(),
    invoke_agent2(),
    web_search()
)                                            # 5-10s (max of parallel)
Total: 6-12 seconds (50-60% faster)
```

### Response Time Breakdown

```
Typical complex query with 3 agents + web search + news:

1. Authentication & context: 0.5s
2. Agro data fetch: 2-3s
3. LLM analysis: 1-2s
4. Parallel execution:
   - 3 agents (parallel): 8-12s
   - Web search (3 queries): 3-5s
   - News fetch: 2-3s
   Max parallel time: 12s
5. Synthesis (Nova Pro): 8-12s
6. Save to DynamoDB: 0.5s

Total: 24-30 seconds
```

### Caching Strategy

```python
# Agricultural data caching (future)
CACHE_TTL = {
    "weather": 600,       # 10 minutes
    "soil": 1800,         # 30 minutes
    "historical": 86400,  # 24 hours
}

# Knowledge base caching (Bedrock handles this)
```

### Cost Optimization

```
Per Query Costs (estimated):

Routing LLM (Nova Lite):        $0.00006
Domain Agents (3 avg @ Lite):   $0.00090
Synthesizer (Nova Pro):         $0.00120
External APIs:                  $0.00030
Total AI cost per query:        $0.00246

DynamoDB:                       $0.00005
Lambda execution:               $0.00010
Total infrastructure:           $0.00015

Total cost per query:           $0.00261

At 1000 queries/day:            $2.61/day = $78.30/month
At 10,000 queries/day:          $26.10/day = $783/month
```

---

## License

MIT License

---

**Built with ❤️ for farmers, by engineers who care.**

*Last Updated: October 19, 2025*
*Version: 2.0.0 (LLM-Powered Multi-Agentic Architecture)*