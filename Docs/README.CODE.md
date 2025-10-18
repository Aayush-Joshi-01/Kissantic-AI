# Kisaantic AI - Complete Technical Documentation

**An AI-Powered Agricultural Assistant for Farmers**

Kisaantic AI is a comprehensive agricultural platform that empowers farmers with data-driven, intelligent decision-making through AI agents, real-time weather data, and contextual agricultural insights. Built for the AWS Hackathon, this platform removes dependencies on middlemen and provides farmers with direct access to actionable agricultural advice.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Frontend Application](#frontend-application)
5. [Backend Infrastructure](#backend-infrastructure)
6. [AWS Bedrock Integration](#aws-bedrock-integration)
7. [Database Design](#database-design)
8. [API Documentation](#api-documentation)
9. [Deployment](#deployment)
10. [Environment Configuration](#environment-configuration)
11. [Development Setup](#development-setup)
12. [Project Structure](#project-structure)

---

## Overview

### Mission
Empower every farmer with data-driven, agentic decision-making free from middlemen and political dependencies so they keep the full value of their work.

### Key Features

#### For Farmers
- **AI-Powered Chat Assistant**: Intelligent conversational interface powered by AWS Bedrock Agents
- **Real-Time Weather Data**: Current conditions, forecasts, and historical weather patterns
- **Agricultural Context**: Soil analysis, seasonal data, and historical baselines
- **Multi-Agent System**: Specialized agents for different farming domains
- **User Profiles**: Store farm details, location, crop types, and preferences
- **Session Management**: Maintain conversation history and context

#### Technical Capabilities
- **5 Specialized AI Agents**: Weather, Crop, Pest, Soil, and Irrigation experts
- **Real-Time Data Integration**: Weather API, Soil API, and Historical Climate Data
- **Serverless Architecture**: Fully serverless on AWS Lambda
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **DynamoDB Single-Table Design**: Efficient NoSQL database architecture
- **Progressive Web App (PWA)**: Mobile-first responsive design

---

## Architecture

### High-Level Architecture Diagram

```
+---------------------------------------------------------------+
|                       Frontend Layer                          |
|  Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn  |
+---------------------------+-----------------------------------+
                            |
                    HTTPS/REST API
                            |
+---------------------------v-----------------------------------+
|                   API Gateway (REST API)                      |
|                   CORS + Authorization                        |
+---------------------------+-----------------------------------+
                            |
           +----------------+----------------+
           |                |                |
+----------v----------+ +---v---------+ +---v--------------+
|   Auth Lambdas      | |  Chat       | |   Weather        |
|                     | |  Lambda     | |   Lambdas        |
| - Login             | |             | |                  |
| - Signup            | | - Bedrock   | | - Current        |
| - Refresh           | |   Agents    | | - Forecast       |
| - Logout            | | - Context   | | - History        |
| - Get/Update        | |   Builder   | |                  |
+----------+----------+ +---+---------+ +---+--------------+
           |                |              |
           |     +----------v----------+   |
           |     |  Bedrock Agents     |   |
           |     | 5 Specialized AI    |   |
           |     +---------------------+   |
           |                               |
+----------v-------------------------------v-----------------+
|              DynamoDB (kisaantic-prod)                     |
|          Single-Table Design with GSIs                     |
|  - Users & Profiles                                        |
|  - Chat Sessions & Messages                                |
|  - Refresh Tokens                                          |
+------------------------------------------------------------+

+------------------------------------------------------------+
|            Lambda Layers (Shared Code)                     |
|  - Utils Layer (auth, dynamodb, schemas)                   |
|  - Bedrock Integration Layer                               |
|  - Agriculture Context Layer                               |
+------------------------------------------------------------+

+------------------------------------------------------------+
|             External APIs (Integrated)                     |
|  - Weather API (WeatherAPI.com)                            |
|  - Agricultural Data API (OpenMeteo/Soil API)              |
+------------------------------------------------------------+
```

### Request Flow

1. **User Authentication**:
   - User signs up/logs in through the frontend
   - Auth Lambda validates credentials and generates JWT tokens
   - Access token (15 min) + Refresh token (30 days) returned
   - Tokens stored in browser localStorage

2. **Chat Interaction**:
   - User sends a message from the chat UI
   - Request includes: message, location, weather context, session_id
   - Chat Lambda authenticates the user via JWT
   - Fetches user profile and chat history from DynamoDB
   - Determines appropriate Bedrock Agent based on query keywords
   - Fetches real-time agricultural data (weather, soil, historical)
   - Builds context-rich prompt with all available data
   - Invokes appropriate Bedrock Agent
   - Saves user message and AI response to DynamoDB
   - Returns structured response to frontend

3. **Weather & Agricultural Data**:
   - Weather Lambdas fetch data from external APIs
   - Soil Lambdas provide soil moisture and analysis
   - Historical Lambdas provide seasonal baselines and anomaly detection
   - Data cached and formatted for Bedrock Agents

---

## Technology Stack

### Frontend
- **Framework**: Next.js 15.2.4 (App Router)
- **UI Library**: React 19
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4.1.9
- **Component Library**: shadcn/ui (Radix UI primitives)
- **Form Handling**: React Hook Form 7.60 + Zod validation
- **Maps**: React Leaflet 5.0 + Pigeon Maps
- **Markdown**: React Markdown with remark-gfm
- **Animation**: Framer Motion
- **Analytics**: Vercel Analytics
- **Theme**: next-themes (dark/light mode support)

### Backend (AWS Services)
- **Compute**: AWS Lambda (Python 3.12)
- **API**: AWS API Gateway (REST API)
- **Database**: AWS DynamoDB (Single-table design with GSIs)
- **AI**: AWS Bedrock (Claude 3 Sonnet with Agents)
- **Storage**: S3 (for knowledge bases)
- **Authentication**: JWT tokens (PyJWT library)
- **Region**: ap-south-1 (Mumbai) and us-east-1

### Backend Libraries
- **boto3**: AWS SDK for Python
- **pydantic**: Data validation and schemas
- **aiohttp**: Async HTTP client for API calls
- **bcrypt**: Password hashing
- **PyJWT**: JWT token generation and validation

### External APIs
- **Weather API**: WeatherAPI.com (current, forecast, historical)
- **Agricultural API**: OpenMeteo Soil API + Historical Climate Data
- **Geolocation**: Integrated location services

---

## Frontend Application

### Directory Structure

```
App/
 app/                    # Next.js App Router pages
    chat/              # Chat interface page
    login/             # Login page
    signup/            # Signup page
    profile/           # User profile page
    layout.tsx         # Root layout
    page.tsx           # Home page
 components/            # React components
    auth/              # Authentication forms
       login-form.tsx
       signup-form.tsx
    chat/              # Chat UI components
       chat-ui.tsx
    map/               # Map components
       location-map.tsx
    profile/           # Profile components
       profile-form.tsx
       location-map.tsx
    ui/                # shadcn/ui components
    site-header.tsx    # Navigation header
    theme-provider.tsx # Theme context
    pwa-provider.tsx   # PWA support
 contexts/              # React contexts
    auth-context.tsx   # Authentication state
 lib/                   # Utility libraries
    api.ts            # API client with auth
    auth.ts           # Auth utilities
    utils.ts          # Helper functions
 package.json
```

### Key Frontend Features

#### 1. Authentication System
**Files**: contexts/auth-context.tsx, lib/auth.ts

Features:
- JWT-based authentication with access and refresh tokens
- Automatic token refresh before expiration
- Secure token storage in localStorage
- Auth state management via React Context
- Protected routes with auth checks
- Cross-tab synchronization via Storage events

#### 2. Chat Interface
**Files**: components/chat/chat-ui.tsx, app/chat/page.tsx

Features:
- Real-time message streaming
- Markdown rendering with syntax highlighting
- Context-aware messaging (location, weather)
- Session management (create, resume, delete)
- Message history persistence
- Loading states and error handling
- Responsive mobile-first design

#### 3. User Profile Management
**Files**: components/profile/profile-form.tsx, app/profile/page.tsx

Features:
- Interactive map for location selection
- Farm details (size, crop type, contact)
- Geolocation integration
- Form validation with Zod schemas
- Real-time updates

#### 4. API Client
**File**: lib/api.ts

Features:
- Automatic authentication header injection
- Token refresh on 401 errors
- Request timeout handling (30s)
- CORS configuration
- Error handling and retries
- TypeScript type safety

---

## Backend Infrastructure

### Lambda Functions Overview

The backend consists of 20+ Lambda functions organized by domain:

1. **Authentication** (6 functions)
2. **Chat** (1 function with Bedrock integration)
3. **Weather** (3 functions)
4. **Agricultural Data** (4 functions)
5. **Session Management** (5 functions)

### Lambda Layers

Lambda Layers provide shared code across multiple Lambda functions:

#### 1. Utils Layer
**Location**: Backend/lambda-layers/utils/python/

**Contains**:
- dynamodb_helper.py: DynamoDB operations
- auth.py: JWT generation and validation
- schemas.py: Pydantic data models

#### 2. Bedrock Integration Layer
**Location**: Backend/lambda-layers/bedrock-integration/python/

**Contains**:
- bedrock_chat_integration.py: Main Bedrock integration
- agriculture_context.py: Agricultural data fetcher and prompt builder

---

## AWS Bedrock Integration

### 5 Specialized AI Agents

Each agent is powered by Claude 3 Sonnet with domain-specific knowledge:

#### 1. Weather Advisor Agent
- Agent ID: AEKTMWVOGU
- Focus: Weather impact on farming, timing recommendations
- Example: "Should I plant wheat today?"

#### 2. Crop Specialist Agent
- Agent ID: 9N4E3JWBGR
- Focus: Crop selection, planting schedules, yield optimization
- Example: "Which crop variety is best for my region?"

#### 3. Pest Manager Agent
- Agent ID: QHNDS61CIO
- Focus: Pest identification, IPM strategies, treatment timing
- Example: "My wheat has yellow spots. What should I do?"

#### 4. Soil Analyst Agent
- Agent ID: 9LYFXBVJOL
- Focus: Soil health, nutrient management, fertilizer timing
- Example: "When should I apply fertilizer?"

#### 5. Irrigation Expert Agent
- Agent ID: Q2HUSNVOSK
- Focus: Water management, irrigation scheduling
- Example: "How much water does my crop need?"

### Agent Selection Logic

The system automatically routes queries to the appropriate agent based on keywords:

```python
def detect_agent_type(query: str) -> str:
    query_lower = query.lower()

    if any(kw in query_lower for kw in ['weather', 'rain', 'temperature']):
        return "weather"
    if any(kw in query_lower for kw in ['pest', 'disease', 'insect']):
        return "pest"
    if any(kw in query_lower for kw in ['soil', 'fertilizer', 'nutrient']):
        return "soil"
    if any(kw in query_lower for kw in ['water', 'irrigation']):
        return "irrigation"

    return "crop"  # Default agent
```

### Context Enrichment

Each agent receives comprehensive context including:
- Farmer profile (name, farm size, crop type, location)
- Current weather conditions
- 7-day weather forecast
- Soil moisture data (5 depth levels)
- Historical climate baselines (2-year averages)
- Seasonal context (Rabi/Kharif/Zaid seasons)
- Anomaly detection (warmer/cooler, wetter/drier than normal)
- Growing degree days (GDD)
- Recent chat history (5-10 messages)

---

## Database Design

### DynamoDB Single-Table Design

**Table Name**: kisaantic-prod

**Primary Key**:
- PK (Partition Key)
- SK (Sort Key)

**Global Secondary Indexes**:
- GSI1 (GSI1PK, GSI1SK)
- GSI2 (GSI2PK, GSI2SK)

### Entity Types

#### 1. User Entity
```
PK: USER#{email}
SK: PROFILE
Attributes: UserId, Email, HashedPassword, Name, Phone,
           FarmSize, CropType, Latitude, Longitude, Address
```

#### 2. Refresh Token Entity
```
PK: USER#{email}
SK: REFRESH_TOKEN#{token_id}
Attributes: TokenId, DeviceId, CreatedAt, TTL (30 days)
```

#### 3. Chat Session Entity
```
PK: USER#{user_id}
SK: SESSION#{session_id}
Attributes: SessionId, Title, MessageCount,
           CreatedAt, UpdatedAt
```

#### 4. Message Entity
```
PK: SESSION#{session_id}
SK: MESSAGE#{timestamp}#{message_id}
Attributes: MessageId, Text, Sender (user/ai),
           Metadata (location, weather, agent info)
```

---

## API Documentation

Complete API documentation is available in README.md.

### Authentication Endpoints
- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout
- GET /api/auth/me
- PUT /api/auth/me

### Weather Endpoints
- GET /api/weather/current
- GET /api/weather/forecast
- GET /api/weather/history

### Chat Endpoint
- POST /api/chat

### Session Endpoints
- POST /api/sessions
- GET /api/sessions
- GET /api/sessions/{session_id}
- PUT /api/sessions/{session_id}
- DELETE /api/sessions/{session_id}

---

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.12
- AWS CLI configured
- Git

### Frontend Setup

```bash
cd App
npm install
npm run dev
```

Access at: http://localhost:3000

### Backend Setup

```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install boto3 pydantic bcrypt pyjwt aiohttp
```

---

## Project Structure

```
Kisaantic-AI/
 App/                          # Frontend (Next.js)
    app/                      # Pages (App Router)
    components/               # React components
    contexts/                 # React contexts
    lib/                      # Utilities
    public/                   # Static assets

 Backend/                      # Backend (AWS Lambda)
    lambdas/                  # Lambda functions
       auth/                 # Authentication
       chat/                 # Chat Lambda
       weather/              # Weather Lambdas
       agro/                 # Agricultural Lambdas
       session/              # Session management
   
    lambda-layers/            # Lambda Layers
       utils/                # Shared utilities
       bedrock-integration/  # Bedrock integration
   
    Bedrock/                  # Bedrock Agent code
        agents/

 README.md                     # API Documentation
 Code-Readme.md               # This file
```

---

## Inspiration

While my father served in the Indian administration, he witnessed dozens of farmers driven to suicide by a broken system that failed them. He eventually quit, but the trauma stayed with him and with us as teenagers. The only thing a farmer knows in India is farming. The agony of a farmer who ends up his life to feed the nation has carved an impact deep in our family.

We are building an Agentic AI solution to remove dependence on politics and middlemen and give farmers the resources, markets, and resilience they deserve.

---

## License

This project is licensed under the terms specified in LICENSE.

---

**Built with love for farmers, by engineers who care.**

*Last Updated: October 19, 2025*
