# Kisaantic AI - Architecture Documentation

**Complete AWS Infrastructure & Deployment Architecture**

This document provides a comprehensive overview of Kisaantic AI's cloud architecture, deployment processes, and infrastructure configuration.

---

## 📖 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [AWS Services Summary](#aws-services-summary)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture](#backend-architecture)
4. [Database Architecture](#database-architecture)
5. [AI & ML Architecture](#ai--ml-architecture)
6. [API Architecture](#api-architecture)
7. [Deployment Process](#deployment-process)
8. [Service Configuration](#service-configuration)
9. [Security & Authentication](#security--authentication)
10. [Monitoring & Logging](#monitoring--logging)
11. [Scalability & Performance](#scalability--performance)
12. [Cost Optimization](#cost-optimization)

---

## Architecture Overview

Kisaantic AI is built on a **fully serverless AWS architecture** leveraging **10 AWS services** to deliver an intelligent, scalable, and cost-effective agricultural AI platform. All infrastructure is manually configured via AWS Console for maximum control and customization.

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         END USERS                               │
│              (Farmers accessing via browsers/mobile)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                     HTTPS (TLS 1.2+)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    AWS AMPLIFY (Frontend)                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Hosting & CDN                                             │  │
│  │ • Next.js 15 Static & Server-Side Rendering               │  │
│  │ • React 19 Application                                    │  │
│  │ • Global CDN Distribution                                 │  │
│  │ • Automatic SSL/TLS                                       │  │
│  │ • GitHub CI/CD Integration                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Source: GitHub Repository (monorepo)                           │
│  Build: Amplify Build System (automated)                        │
│  Deploy: Automatic on git push                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    REST API Calls
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              AWS API GATEWAY (REST API)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Configuration:                                            │  │
│  │ • REST API (not HTTP API)                                 │  │
│  │ • CORS Enabled (All origins: *)                           │  │
│  │ • Lambda Proxy Integration: ENABLED                       │  │
│  │ • Request Timeout: 90 seconds (1.5 minutes)               │  │
│  │ • Integration Request: Direct Lambda mapping              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Endpoints:                                                     │
│  • /api/auth/* (6 endpoints)                                    │
│  • /api/chat (1 endpoint)                                       │
│  • /api/weather/* (3 endpoints)                                 │
│  • /api/agro-api/* (4 endpoints)                                │
│  • /api/sessions/* (5 endpoints)                                │
│  • /api/bookings-orders/* (2 endpoints)                         │
│                                                                 │
│  Created: Manually via AWS Console                              │
│  Deployment: Manual stage deployment                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│ Auth Lambdas     │ │ Chat Lambda  │ │ Data Lambdas │
│ (6 functions)    │ │ (1 function) │ │ (14 funcs)   │
│                  │ │              │ │              │
│ Python 3.13      │ │ Python 3.13  │ │ Python 3.13  │
│ 512 MB RAM       │ │ 512 MB RAM   │ │ 512 MB RAM   │
│ 30s timeout      │ │ 300s timeout │ │ 30s timeout  │
│                  │ │              │ │              │
│ Created: Manual  │ │ Created:     │ │ Created:     │
│ via Console      │ │ Manual       │ │ Manual       │
└──────────────────┘ └──────┬───────┘ └──────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌───────────────┐ ┌──────────┐ ┌──────────┐
    │   DynamoDB    │ │ Bedrock  │ │ External │
    │               │ │ Agents   │ │ APIs     │
    │ Single Table  │ │ 8 Agents │ │ • LangS  │
    │ On-Demand     │ │ + LLMs   │ │ • NewsAPI│
    │               │ │          │ │ • Weather│
    └───────────────┘ └──────────┘ └──────────┘
```

### Architecture Layers

| Layer | Technology | Purpose | Deployment Method |
|-------|-----------|---------|-------------------|
| **Presentation** | Next.js 15 + React 19 | User Interface | AWS Amplify (GitHub CI/CD) |
| **API Gateway** | AWS API Gateway REST | Request routing, CORS, auth | Manual via AWS Console |
| **Compute** | AWS Lambda (Python 3.13) | Business logic, orchestration | Manual via AWS Console |
| **Database** | DynamoDB | Data persistence | Manual via AWS Console |
| **AI/ML** | AWS Bedrock (Nova Lite/Pro) | Multi-agent intelligence | Bedrock Console Configuration / Code |
| **Storage** | S3 | Knowledge bases, static assets | Manual via AWS Console |
| **CDN** | CloudFront (via Amplify) | Global content delivery | Automatic via Amplify |
| **Monitoring** | CloudWatch | Logs, metrics, alarms | Automatic |

---

## AWS Services Summary

### Total AWS Services Used: 10

Kisaantic AI leverages a comprehensive suite of AWS services to deliver a scalable, serverless, and intelligent agricultural platform.

#### Service Breakdown by Category

**1. Compute & Application Services (2)**

| Service | Usage | Quantity | Deployment Method |
|---------|-------|----------|-------------------|
| **AWS Lambda** | Serverless compute for business logic | 19 functions | Manual via Console |
| **AWS Amplify** | Frontend hosting, CI/CD, global CDN | 1 application | GitHub integration |

**2. Networking & Content Delivery (2)**

| Service | Usage | Quantity | Deployment Method |
|---------|-------|----------|-------------------|
| **Amazon CloudFront** | Global CDN for frontend assets | 1 distribution | Automatic via Amplify |
| **AWS API Gateway** | REST API management and routing | 1 REST API (19 endpoints) | Manual via Console |

**3. Database & Storage (2)**

| Service | Usage | Quantity | Deployment Method |
|---------|-------|----------|-------------------|
| **Amazon DynamoDB** | NoSQL database for all application data | 1 table + 2 GSIs | Manual via Console |
| **Amazon S3** | Knowledge base document storage | 6 buckets | Manual via Console |

**4. AI & Machine Learning (1)**

| Service | Usage | Quantity | Deployment Method |
|---------|-------|----------|-------------------|
| **AWS Bedrock** | Foundation models, agents, knowledge bases | 2 models, 8 agents, 6 KBs | Bedrock Console |

**5. Security & Identity (1)**

| Service | Usage | Quantity | Deployment Method |
|---------|-------|----------|-------------------|
| **AWS IAM** | Identity and access management | Multiple roles & policies | Manual via Console |

**6. Management & Monitoring (2)**

| Service | Usage | Quantity | Deployment Method |
|---------|-------|----------|-------------------|
| **Amazon CloudWatch** | Logging, metrics, monitoring | Logs + Metrics | Automatic |
| **AWS Shield Standard** | DDoS protection | 1 (automatic with CloudFront) | Automatic |

### Detailed Service Utilization

#### 1. AWS Amplify
- **Purpose**: Frontend hosting and continuous deployment
- **Configuration**: 
  - Monorepo support enabled
  - GitHub integration (main branch)
  - Automatic builds on git push
  - Environment variable management
- **Resources**: 1 hosted application
- **Region**: Global (CloudFront distribution)
- **Cost Model**: Per build minute + bandwidth

#### 2. AWS Lambda
- **Purpose**: Serverless compute for all backend logic
- **Configuration**:
  - Runtime: Python 3.13
  - Architecture: x86_64
  - 19 total functions across 5 categories
- **Function Categories**:
  - Authentication: 6 functions (512 MB, 30s timeout)
  - Chat Orchestration: 1 function (1024 MB, 300s timeout)
  - Weather APIs: 3 functions (512 MB, 30s timeout)
  - Agricultural Data: 4 functions (512 MB, 30s timeout)
  - Session Management: 5 functions (256-512 MB, 10-30s timeout)
- **Layers**: 2 custom layers (utils, bedrock-integration)
- **Region**: ap-south-1 (Mumbai)
- **Cost Model**: Per request + compute time

#### 3. Amazon API Gateway (REST API)
- **Purpose**: API management, routing, CORS, authentication
- **Configuration**:
  - Type: REST API (not HTTP API)
  - Lambda Proxy Integration: Enabled
  - CORS: Enabled on all endpoints
  - Timeout: 90 seconds (increased via service quota)
- **Endpoints**: 19 total across 5 resource groups
- **Stage**: prod (production)
- **Region**: ap-south-1 (Mumbai)
- **Cost Model**: Per million API calls

#### 4. Amazon CloudFront
- **Purpose**: Global CDN for frontend assets
- **Configuration**:
  - Automatically provisioned via Amplify
  - SSL/TLS certificates (automatic)
  - Global edge locations
  - Cache policies optimized for Next.js
- **Distributions**: 1
- **Cost Model**: Per GB data transfer + requests

#### 5. Amazon DynamoDB
- **Purpose**: Primary database for all application data
- **Configuration**:
  - Table: kisaantic-prod
  - Capacity mode: On-demand
  - Encryption: AWS managed keys
  - Point-in-time recovery: Enabled
  - TTL: Enabled for token cleanup
- **Indexes**: 
  - Primary: PK (partition), SK (sort)
  - GSI1: GSI1PK, GSI1SK
  - GSI2: GSI2PK, GSI2SK
- **Region**: ap-south-1 (Mumbai)
- **Cost Model**: Per read/write request unit

#### 6. Amazon S3
- **Purpose**: Storage for Bedrock knowledge base documents
- **Configuration**:
  - 6 buckets (one per knowledge base)
  - Versioning: Enabled
  - Encryption: AES-256
  - Access: Private (IAM only)
- **Storage**: ~500 MB total (PDF/text documents)
- **Region**: ap-south-1 (Mumbai)
- **Cost Model**: Per GB storage + requests

#### 7. AWS Bedrock
- **Purpose**: AI/ML foundation models and agent orchestration
- **Configuration**:
  - **Foundation Models**: 2
    - Amazon Nova Lite (apac.amazon.nova-lite-v1:0)
    - Amazon Nova Pro (apac.amazon.nova-pro-v1:0)
  - **Agents**: 8 specialized domain experts
  - **Knowledge Bases**: 6 vector databases
  - **Embeddings**: Amazon Titan Embeddings
- **Usage**:
  - Nova Lite: Query routing + 8 domain agents
  - Nova Pro: Response synthesis (multilingual)
  - RAG: Knowledge base integration via vector search
- **Region**: ap-south-1 (Mumbai)
- **Cost Model**: Per 1000 input/output tokens

#### 8. AWS IAM
- **Purpose**: Access control and permissions management
- **Resources**:
  - Lambda execution roles: 19 roles (one per function)
  - Service-linked roles: 3 (Amplify, Bedrock, DynamoDB)
  - Custom policies: 5+ (DynamoDB, Bedrock, S3 access)
- **Configuration**: Least privilege principle
- **Region**: Global
- **Cost**: Free

#### 9. Amazon CloudWatch
- **Purpose**: Application monitoring, logging, and observability
- **Configuration**:
  - **Logs**: 
    - Lambda log groups: 19 (one per function)
    - API Gateway logs: Execution + Access logs
    - Retention: 7 days
  - **Metrics**: 
    - Lambda metrics (invocations, duration, errors)
    - API Gateway metrics (requests, latency, errors)
    - DynamoDB metrics (capacity, throttles)
  - **Alarms**: Planned (not yet configured)
- **Region**: ap-south-1 (Mumbai)
- **Cost Model**: Per GB ingested + storage

#### 10. AWS Shield Standard
- **Purpose**: DDoS protection for CloudFront and API Gateway
- **Configuration**: 
  - Automatically enabled (no configuration needed)
  - Protects against common DDoS attacks
  - Layer 3/4 attack mitigation
- **Coverage**: CloudFront distribution + API Gateway
- **Cost**: Free (included with CloudFront)

### Service Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│ User Request                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ AWS Shield Standard (DDoS Protection)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ CloudFront (CDN) ◄──► Amplify (Frontend Hosting)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ API Gateway (REST API) ◄──► IAM (Authentication)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Lambda (19 Functions) ◄──► CloudWatch (Logging)             │
└────────┬─────────────┴─────────────┬────────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ DynamoDB         │        │ Bedrock          │
│ (Database)       │        │ ◄──► S3 (KBs)    │
└──────────────────┘        └──────────────────┘
```

### Service Dependencies

**Critical Path Services** (Must be operational):
1. API Gateway → All requests route through here
2. Lambda → Core business logic
3. DynamoDB → Data persistence
4. Bedrock → AI intelligence

**Supporting Services**:
- CloudWatch → Monitoring (non-blocking)
- IAM → Security (configured once)
- S3 → Knowledge bases (loaded at agent invocation)

**Frontend Services**:
- Amplify → Hosting + deployment
- CloudFront → Content delivery
- Shield → DDoS protection

### Regional Distribution

| Region | Services | Purpose |
|--------|----------|---------|
| **ap-south-1 (Mumbai)** | Lambda, API Gateway, DynamoDB, Bedrock, S3, CloudWatch | Primary application region |
| **Global** | CloudFront, Amplify, IAM, Shield | Global availability and security |

**Why ap-south-1?**
- Proximity to primary user base (India)
- Bedrock Nova models availability
- Lower latency for Indian farmers
- Compliance with data residency preferences

### Service Limits & Quotas

| Service | Default Limit | Current Usage | Quota Increase |
|---------|---------------|---------------|----------------|
| Lambda concurrent executions | 1000 | <100 | Not needed |
| API Gateway timeout | 29 seconds | N/A | ✅ Increased to 90s |
| API Gateway requests/second | 10,000 | <10 | Not needed |
| DynamoDB on-demand capacity | Unlimited | Auto-scaled | Not needed |
| Bedrock tokens/minute | Varies by model | <1000 | Not needed |

### Cost Summary by Service (Monthly - 10K requests)

| Service | Estimated Cost | Percentage |
|---------|----------------|------------|
| AWS Bedrock | $26.00 | 65% |
| AWS Lambda | $5.00 | 12% |
| Amazon DynamoDB | $2.50 | 6% |
| Amazon CloudWatch | $2.00 | 5% |
| AWS Amplify | $0-5.00 | 0-12% |
| Amazon S3 | $0.50 | 1% |
| API Gateway | $0.04 | 0.1% |
| **Total** | **$36-41** | **100%** |

**Notes**:
- CloudFront, IAM, Shield Standard are free tier or included
- Bedrock is the largest cost due to AI model usage
- Costs scale linearly with request volume

### Service Selection Rationale

**Why These Services?**

1. **Serverless First**: No server management, automatic scaling
2. **Pay-per-use**: Cost only when used, no idle costs
3. **Managed Services**: AWS handles patching, updates, availability
4. **Regional Availability**: All services available in ap-south-1
5. **Integration**: Native AWS service integration
6. **Scalability**: Can handle 10x growth without changes
7. **Security**: Enterprise-grade security built-in

### Alternative Services Considered (Not Used)

| Service | Why Not Used | Alternative Chosen |
|---------|--------------|-------------------|
| Amazon ECS/EKS | Overkill for current scale | Lambda (serverless) |
| Amazon RDS | NoSQL better for our access patterns | DynamoDB |
| API Gateway HTTP API | Need advanced features | REST API |
| AWS Cognito | Custom JWT logic preferred | Manual JWT implementation |
| Amazon SQS/SNS | No async processing needed yet | Direct invocation |
| AWS Step Functions | Orchestration handled in code / Agents | Lambda + Bedrock(Agent Core) |

---

## Frontend Architecture

### AWS Amplify Deployment

**Service**: AWS Amplify Hosting  
**Region**: Automatically distributed (Global CDN)  
**Repository**: GitHub (private/public)  
**Branch**: `main` (production)

#### Deployment Configuration

**1. Repository Setup**
```yaml
Repository Structure: Monorepo
Frontend Location: /App
Build Path: App/
Framework Detection: Next.js 15
```

**2. Build Configuration**

Created via Amplify Console with the following settings:

```yaml
# amplify.yml (auto-generated by Amplify)
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd App
        - npm ci --legacy-peer-deps
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: App/.next
    files:
      - '**/*'
  cache:
    paths:
      - App/node_modules/**/*
      - App/.next/cache/**/*
```

**3. Environment Variables (Amplify Console)**

Set via Amplify Console → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://[api-id].execute-api.ap-south-1.amazonaws.com/prod
NODE_ENV=production
```

**4. Build Settings**

| Setting | Value |
|---------|-------|
| App Root Directory | `App` |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Node.js Version | 18.x |
| Package Manager | npm |
| Install Command | `npm ci --legacy-peer-deps` |

#### CI/CD Pipeline

**Automatic Deployment Trigger**:
```
GitHub Push to main branch
        ↓
Amplify detects commit
        ↓
Pulls latest code
        ↓
Runs build commands in App/ directory
        ↓
Detects Next.js framework
        ↓
Builds production bundle
        ↓
Deploys to global CDN
        ↓
Invalidates CloudFront cache
        ↓
Live in ~3-5 minutes
```

**Build Process**:
1. **Source**: Clone from GitHub repository
2. **Install**: `npm ci --legacy-peer-deps` (handles React 19 peer dependency conflicts)
3. **Build**: `npm run build` (creates optimized Next.js production build)
4. **Deploy**: Automatic deployment to CloudFront CDN
5. **SSL**: Automatic SSL certificate provisioning

**Amplify Features Used**:
- ✅ Continuous deployment from GitHub
- ✅ Automatic SSL/TLS certificates
- ✅ Global CDN distribution
- ✅ Monorepo support
- ✅ Environment variable management
- ✅ Build caching
- ✅ Rollback capability
- ✅ Preview deployments (optional)

#### Frontend Stack Details

```javascript
{
  "framework": "Next.js 15.2.4",
  "ui_library": "React 19.0.0",
  "language": "TypeScript 5.x",
  "styling": "Tailwind CSS 4.1.9",
  "components": "shadcn/ui (Radix UI)",
  "state_management": "React Context",
  "routing": "App Router (Next.js)",
  "deployment": "AWS Amplify",
  "cdn": "CloudFront (automatic)"
}
```

**Progressive Web App (PWA)**:
- Service worker for offline support
- Installable on mobile devices
- App-like experience
- Cache-first strategy for static assets

---

## Backend Architecture

### AWS Lambda Functions (21 Total)

**Deployment Method**: Manual creation via AWS Console

#### Lambda Configuration Process

**For Each Lambda**:

1. **Navigate**: AWS Console → Lambda → Create function
2. **Configuration**:
   - **Author from scratch**: Selected
   - **Function name**: `kisaantic-lambda-[name]`
   - **Runtime**: Python 3.13
   - **Architecture**: x86_64
   - **Permissions**: Create new role with basic Lambda permissions

3. **Function Code**:
   - Upload .zip file with function code
   - Or paste code directly in console editor
   - Include dependencies in deployment package

4. **Environment Variables** (Set in Configuration tab):
   ```
   USE_ORCHESTRATOR=true
   OUTPUT_TOKEN_LIMIT=5000
   CHAT_HISTORY_LIMIT=10
   AGRO_API_URL=https://[api-id].execute-api.ap-south-1.amazonaws.com/api
   LANGSEARCH_API_KEY=[encrypted]
   NEWS_API_KEY=[encrypted]
   JWT_SECRET=[encrypted]
   ```

5. **Resource Configuration**:
   - Memory, timeout, ephemeral storage
   - VPC settings (if needed)
   - Layers attachment

6. **Permissions**:
   - IAM role with required permissions
   - Resource-based policies (for API Gateway)

#### Lambda Categories & Configuration

**1. Authentication Lambdas (6 functions)**

| Function Name | Memory | Timeout | Layers | Purpose |
|--------------|--------|---------|--------|---------|
| `kisaantic-lambda-signup` | 512 MB | 30s | utils | User registration |
| `kisaantic-lambda-login` | 512 MB | 30s | utils | User login |
| `kisaantic-lambda-refresh-token` | 512 MB | 30s | utils | Token refresh |
| `kisaantic-lambda-logout` | 512 MB | 30s | utils | User logout |
| `kisaantic-lambda-get-me` | 512 MB | 30s | utils | Get user profile |
| `kisaantic-lambda-update-me` | 512 MB | 30s | utils | Update profile |

**IAM Permissions**:
- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:UpdateItem`
- `dynamodb:Query`
- `dynamodb:DeleteItem`

**2. Chat Lambda (1 function)**

| Function Name | Memory | Timeout | Layers | Purpose |
|--------------|--------|---------|--------|---------|
| `kisaantic-lambda-chat` | 1024 MB | 120s | utils, bedrock-integration | Multi-agent orchestration |

**IAM Permissions**:
- All DynamoDB operations
- `bedrock:InvokeModel`
- `bedrock:InvokeAgent`
- `bedrock-agent-runtime:InvokeAgent`

**Critical Settings**:
- **Timeout**: 300 seconds (5 minutes) - Required for complex agent orchestration
- **Memory**: 1024 MB - Handles multiple parallel API calls
- **Environment**: Multiple API keys and configuration

**3. Weather Lambdas (3 functions)**

| Function Name | Memory | Timeout | Purpose |
|--------------|--------|---------|---------|
| `kisaantic-lambda-weather-current` | 512 MB | 30s | Current weather |
| `kisaantic-lambda-weather-forecast` | 512 MB | 30s | Weather forecast |
| `kisaantic-lambda-weather-history` | 512 MB | 30s | Historical weather |

**4. Agricultural Data Lambdas (4 functions)**

| Function Name | Memory | Timeout | Purpose |
|--------------|--------|---------|---------|
| `kisaantic-lambda-agrodata-soil` | 512 MB | 30s | Soil moisture data |
| `kisaantic-lambda-agrodata-news` | 512 MB | 30s | Agricultural news |
| `kisaantic-lambda-agrodata-market` | 512 MB | 30s | Market prices |
| `kisaantic-lambda-agrodata-complete` | 512 MB | 30s | Complete agro dataset |

**5. Session Management Lambdas (5 functions)**

| Function Name | Memory | Timeout | Purpose |
|--------------|--------|---------|---------|
| `kisaantic-lambda-create-session` | 256 MB | 10s | Create chat session |
| `kisaantic-lambda-get-sessions` | 256 MB | 10s | List sessions |
| `kisaantic-lambda-get-session` | 512 MB | 30s | Get session + messages |
| `kisaantic-lambda-update-session` | 256 MB | 10s | Update session |
| `kisaantic-lambda-delete-session` | 256 MB | 10s | Delete session |

### Lambda Layers (Shared Code)

**Manual Creation Process**:

1. **Create Layer**:
   - AWS Console → Lambda → Layers → Create layer
   - Upload .zip with dependencies in `python/` folder structure

2. **Layer Structure**:
   ```
   layer.zip
   └── python/
       ├── module1.py
       ├── module2.py
       └── requirements.txt dependencies
   ```

**Layer 1: Utils Layer**
```
layer-utils.zip
└── python/
    ├── dynamodb_helper.py
    ├── auth.py
    ├── schemas.py
    └── [dependencies]
```

**Layer 2: Dependencies Layer**
```
layer-bedrock-integration.zip
└── python/
    └── [dependencies: boto3, aiohttp]
```

**Attaching Layers**:
- Lambda → Configuration → Layers → Add layer
- Select custom layer
- Choose version
- Save

---

## API Architecture

### AWS API Gateway (REST API)

**Creation Method**: Manual via AWS Console  
**API Type**: REST API (not HTTP API)  
**Region**: ap-south-1 (Mumbai)

#### Step-by-Step API Gateway Setup

**1. Create REST API**

AWS Console → API Gateway → Create API → REST API → Build

```
API Name: kisaantic-api
Description: Agricultural AI Assistant API
Endpoint Type: Regional
```

**2. Configure Resources**

Created manually for each endpoint group:

```
/api
├── /auth
│   ├── /signup (POST)
│   ├── /login (POST)
│   ├── /refresh (POST)
│   ├── /logout (POST)
│   └── /me (GET, PUT)
├── /chat (POST)
├── /weather
│   ├── /current (GET)
│   ├── /forecast (GET)
│   └── /history (GET)
├── /agro-api
│   ├── /soil (GET)
│   ├── /news (GET)
│   ├── /market (GET)
│   └── /complete (GET)
└── /sessions
    ├── / (GET, POST)
    └── /{session_id} (GET, PUT, DELETE)
```

**3. Method Configuration (Per Endpoint)**

**Example: POST /api/chat**

**A. Create Method**:
- Resource: `/api/chat`
- Method: POST
- Integration type: Lambda Function
- Lambda proxy integration: **ENABLED** ✅
- Lambda function: `kisaantic-lambda-chat`
- Region: ap-south-1

**B. Enable CORS**:
- Actions → Enable CORS
- Access-Control-Allow-Origin: `*`
- Access-Control-Allow-Headers: `Content-Type,Authorization,Accept,X-Amz-Date,X-Api-Key,X-Amz-Security-Token`
- Access-Control-Allow-Methods: `GET,POST,PUT,DELETE,OPTIONS`

**C. Configure Integration Request**:
- Integration type: Lambda Proxy (automatically configured)
- Content Handling: Passthrough
- Request Templates: None needed (proxy mode)

**D. Configure Method Response**:
- Status Code: 200, 400, 401, 404, 500
- Response Headers:
  - Access-Control-Allow-Origin
  - Access-Control-Allow-Headers
  - Access-Control-Allow-Methods

**4. Lambda Proxy Integration**

**Why Enabled**:
- Lambda receives entire HTTP request as event
- Lambda returns structured response with statusCode, headers, body
- Simplifies request/response handling
- Automatic JSON parsing

**Event Structure Received by Lambda**:
```json
{
  "httpMethod": "POST",
  "headers": {
    "Authorization": "Bearer token...",
    "Content-Type": "application/json"
  },
  "body": "{...JSON payload...}",
  "queryStringParameters": {...},
  "pathParameters": {...}
}
```

**Expected Lambda Response**:
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{...JSON response...}"
}
```

**5. Service Quota Increase**

**Issue**: Default API Gateway timeout = 29 seconds (too short for complex agent orchestration)

**Solution**: Service quota increase request

**Process**:
1. AWS Console → Service Quotas
2. Search: "API Gateway"
3. Find: "Integration timeout"
4. Request increase: 29s → 90s (1.5 minutes)
5. Justification: "Multi-agent AI system requires extended processing time for complex agricultural queries involving 8 agents, real-time data fetching, and response synthesis"
6. Status: **APPROVED** ✅
7. New timeout: **90 seconds**

**Configuration After Approval**:
- API Gateway → Settings → Maximum integration timeout: 90000 ms
- Applies to all endpoints

**6. Deploy API**

- Actions → Deploy API
- Deployment stage: `prod`
- Stage description: Production environment
- Deploy

**Resulting URL**:
```
https://[api-id].execute-api.ap-south-1.amazonaws.com/prod
```

#### CORS Configuration Details

**Manual CORS Setup** (per resource):

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
Access-Control-Allow-Headers: Content-Type,Authorization,Accept,X-Amz-Date,X-Api-Key,X-Amz-Security-Token
```

**OPTIONS Method** (Preflight):
- Automatically created when enabling CORS
- Mock integration (no Lambda invocation)
- Returns CORS headers immediately

**Why CORS Needed**:
- Frontend hosted on Amplify domain
- API on different domain (API Gateway)
- Browser requires CORS headers for cross-origin requests

#### API Gateway Features Used

| Feature | Configuration | Purpose |
|---------|--------------|---------|
| **REST API** | Enabled | Full REST API functionality |
| **Lambda Proxy** | Enabled | Simplified integration |
| **CORS** | Enabled (all origins) | Cross-origin requests |
| **Request Timeout** | 90 seconds | Extended processing |
| **Throttling** | Default (10000 req/s) | Rate limiting |
| **Caching** | Disabled | Real-time data |
| **API Keys** | Not used | JWT authentication instead |
| **Usage Plans** | Not configured | Future feature |
| **Logging** | CloudWatch enabled | Request/response logs |

---

## Database Architecture

### DynamoDB Configuration

**Creation Method**: Manual via AWS Console  
**Table Name**: `kisaantic-prod`  
**Region**: ap-south-1 (Mumbai)

#### Table Configuration

**1. Create Table** (AWS Console → DynamoDB → Create table)

```
Table name: kisaantic-prod
Partition key: PK (String)
Sort key: SK (String)
Table settings: Customize settings
Table class: Standard
Capacity mode: On-demand
```

**2. Secondary Indexes**

**GSI1** (Global Secondary Index 1):
```
Index name: GSI1
Partition key: GSI1PK (String)
Sort key: GSI1SK (String)
Projected attributes: All
```

**GSI2** (Global Secondary Index 2):
```
Index name: GSI2
Partition key: GSI2PK (String)
Sort key: GSI2SK (String)
Projected attributes: All
```

**3. Settings**

| Setting | Value | Reason |
|---------|-------|--------|
| Capacity Mode | On-demand | Variable workload |
| Read/Write Units | Auto-scaled | Cost optimization |
| Encryption | AWS managed | Data security |
| Point-in-time recovery | Enabled | Data protection |
| TTL | Enabled on TTL field | Automatic token cleanup |
| Streams | Disabled | Not needed currently |

#### Single-Table Design

**Entity Types & Keys**:

```
User Profile:
  PK: USER#{email}
  SK: PROFILE
  GSI1PK: USERID#{user_id}

Refresh Token:
  PK: USER#{email}
  SK: REFRESH_TOKEN#{token_id}
  TTL: [30 days from creation]

Chat Session:
  PK: USER#{user_id}
  SK: SESSION#{session_id}
  GSI1PK: USER#{user_id}
  GSI1SK: [updated_at timestamp]

Message:
  PK: SESSION#{session_id}
  SK: MESSAGE#{timestamp}#{message_id}
```

**Access Patterns**:
1. Get user by email → Query PK
2. Get user by ID → Query GSI1
3. Get sessions → Query PK + SK prefix
4. Get recent sessions → Query GSI1 sorted by GSI1SK
5. Get messages → Query PK + SK prefix

---

## AI & ML Architecture

### AWS Bedrock Configuration

**Region**: ap-south-1 (Mumbai)  
**Setup Method**: Bedrock Console + agent_config.json

#### Bedrock Components

**1. Foundation Models**

| Model | Model ID | Purpose | Usage |
|-------|----------|---------|-------|
| Nova Lite | `apac.amazon.nova-lite-v1:0` | Query routing, domain agents | Fast, cost-effective |
| Nova Pro | `apac.amazon.nova-pro-v1:0` | Response synthesis | High quality, multilingual |

**2. Bedrock Agents (8 Domain Experts)**

Created via Bedrock Console → Agents:

| Agent Name | Agent ID | Knowledge Base | Purpose |
|------------|----------|----------------|---------|
| KisaanticWeatherAdvisor | [ID] | WeatherAdvisor KB | Weather guidance |
| KisaanticCropSpecialist | [ID] | CropSpecialist KB | Crop management |
| KisaanticPestManager | [ID] | PestManager KB | Pest control |
| KisaanticSoilAnalyst | [ID] | SoilAnalyst KB | Soil health |
| KisaanticIrrigationExpert | [ID] | IrrigationExpert KB | Water management |
| KisaanticCropPlanner | [ID] | CropSpecialist KB | ROI analysis |
| KisaanticEquipmentVendor | [ID] | MP Vendor KB | Equipment info |
| KisaanticMarketLinkage | [ID] | CropSpecialist KB | Market prices |

**Agent Configuration** (per agent):
- Foundation model: Nova Lite
- Instructions: Agent-specific prompt
- Knowledge base: Attached relevant KB
- Action groups: None (all via orchestrator)

**3. Knowledge Bases (6 Total)**

Created via Bedrock Console → Knowledge bases:

| KB Name | Vector Store | Documents | Purpose |
|---------|--------------|-----------|---------|
| WeatherAdvisor KB | S3 + Vector DB | Weather patterns, seasonal guidance | Weather expertise |
| CropSpecialist KB | S3 + Vector DB | Crop varieties, practices | Crop management |
| PestManager KB | S3 + Vector DB | Pest identification, IPM | Pest control |
| SoilAnalyst KB | S3 + Vector DB | Soil health, fertility | Soil management |
| IrrigationExpert KB | S3 + Vector DB | Water management | Irrigation |
| MP Vendor KB | S3 + Vector DB | Madhya Pradesh vendors | Regional vendors |

**Knowledge Base Setup** (per KB):
1. Create S3 bucket for documents
2. Upload PDF/text documents
3. Bedrock → Knowledge bases → Create
4. Connect S3 bucket
5. Configure chunking strategy
6. Sync documents → Vector embeddings created

**4. Agent Aliases**

Each agent has an alias for production:
- Alias: `[agent-alias]`
- Version: Latest
- Used in orchestrator configuration

#### Orchestrator Logic

**Not a Bedrock Agent** - Custom Python code in Lambda

**How It Works**:
1. Uses Nova Lite LLM for query analysis
2. Determines which agents to invoke
3. Calls `bedrock-agent-runtime:InvokeAgent` for each selected agent
4. Uses Nova Pro LLM for synthesis

**Configuration File**: `agent_config.json`
```json
{
  "weather_advisor": {
    "agent_id": "**********",
    "alias_id": "[alias_id]",
    "name": "KisaanticWeatherAdvisor"
  },
  ...
}
```

---

## Deployment Process

### End-to-End Deployment Flow

#### 1. Frontend Deployment (Automatic)

```
Developer pushes code to GitHub main branch
        ↓
AWS Amplify webhook triggered
        ↓
Amplify pulls latest code from GitHub
        ↓
Detects monorepo structure, navigates to App/
        ↓
Runs: npm ci --legacy-peer-deps
        ↓
Runs: npm run build
        ↓
Generates optimized production bundle
        ↓
Deploys to CloudFront CDN
        ↓
Invalidates cache
        ↓
Live in 3-5 minutes
        ↓
Build logs available in Amplify Console
```

**Rollback Process**:
- Amplify Console → Deployments
- Select previous successful deployment
- Click "Redeploy this version"

#### 2. Backend Deployment (Manual)

**Lambda Function Update**:

```
Developer updates function code locally
        ↓
Package code + dependencies into .zip
        ↓
AWS Console → Lambda → Select function
        ↓
Code tab → Upload from → .zip file
        ↓
Upload deployment package
        ↓
Save
        ↓
Test with test event
        ↓
Deploy
        ↓
Live immediately
```

**For Multiple Functions**:
- Repeat for each Lambda
- Or use AWS CLI/SDK for batch updates (future)

**Lambda Layer Update**:

```
Create layer.zip with python/ folder
        ↓
AWS Console → Lambda → Layers
        ↓
Create layer version
        ↓
Upload .zip
        ↓
Select compatible runtimes (Python 3.13)
        ↓
Create
        ↓
Update Lambdas to use new layer version
```

#### 3. API Gateway Deployment

**After Lambda Changes**:

```
AWS Console → API Gateway → kisaantic-api
        ↓
Select modified resources/methods
        ↓
Actions → Deploy API
        ↓
Select deployment stage: prod
        ↓
Deploy
        ↓
Changes live immediately
        ↓
No downtime (blue-green deployment)
```

**Important**: Must deploy after:
- Adding/modifying resources
- Changing method configurations
- Updating integrations

#### 4. DynamoDB Updates

**Schema Changes**: Not applicable (NoSQL, schemaless)

**Index Changes**:
```
DynamoDB Console → kisaantic-prod
        ↓
Indexes tab → Create index
        ↓
Configure GSI
        ↓
Create index (takes a few minutes)
        ↓
Update application code to use new index
```

#### 5. Bedrock Updates

**Agent Updates**:
```
Bedrock Console → Agents → Select agent
        ↓
Edit agent (instructions, KB, model)
        ↓
Save and create new version
        ↓
Update alias to point to new version
        ↓
No Lambda code changes needed (uses alias)
```

**Knowledge Base Updates**:
```
Upload new documents to S3 bucket
        ↓
Bedrock Console → Knowledge bases
        ↓
Select KB → Sync
        ↓
Bedrock re-indexes documents
        ↓
New knowledge available to agents
```

---

## Service Configuration

### Detailed Service Settings

#### AWS Amplify

| Setting | Value |
|---------|-------|
| App Name | kisaantic-ai |
| Region | Auto (Global CDN) |
| Repository | GitHub |
| Branch | main |
| Framework | Next.js 15 |
| Build Settings | Custom build spec |
| Environment | Production |
| Domain | main.d1jex6uisa3pv2.amplifyapp.com |
| SSL/TLS | Automatic (AWS managed) |
| Rewrites/Redirects | Next.js default |

#### AWS Lambda

**Chat Lambda** (Critical Settings):
```yaml
Function name: kisaantic-lambda-chat
Runtime: Python 3.13
Architecture: x86_64
Memory: 512 MB
Timeout: 300 seconds
Ephemeral storage: 512 MB
Layers:
  - kissantic-layer-utils:latest
  - kissantic-layer-dependencies:latest
Environment variables:
  USE_ORCHESTRATOR: "true"
  OUTPUT_TOKEN_LIMIT: "5000"
  CHAT_HISTORY_LIMIT: "10"
  AGRO_API_URL: "[api-gateway-url]"
  LANGSEARCH_API_KEY: "[encrypted]"
  NEWS_API_KEY: "[encrypted]"
```

**Auth Lambdas**:
```yaml
Runtime: Python 3.13
Memory: 512 MB
Timeout: 30 seconds
Layers:
  - utils-layer:latest
Environment variables:
  JWT_SECRET: "[encrypted]"
  JWT_REFRESH_SECRET: "[encrypted]"
  ACCESS_TOKEN_EXPIRE_MINUTES: "15"
  REFRESH_TOKEN_EXPIRE_DAYS: "30"
```

#### API Gateway

```yaml
API name: kisaantic-api
Type: REST API
Region: ap-south-1
Endpoint: Regional
Stage: prod
Throttling: 10000 requests/sec (default)
Burst: 5000 requests (default)
Minimum integration timeout: 50 ms
Maximum integration timeout: 90000 ms (increased via quota)
Binary media types: */*
CORS: Enabled (all origins)
CloudWatch logs: Enabled
X-Ray tracing: Disabled
```

#### DynamoDB

```yaml
Table: kisaantic-prod
Capacity: On-demand
Read units: Auto-scaled
Write units: Auto-scaled
Encryption: AWS managed
Backup: Point-in-time recovery (enabled)
TTL: Enabled on TTL attribute
Deletion protection: Enabled
```

#### AWS Bedrock

```yaml
Region: ap-south-1
Models:
  - apac.amazon.nova-lite-v1:0
  - apac.amazon.nova-pro-v1:0
Agents: 8 domain experts
Knowledge bases: 6 vector databases
Model invocation: On-demand
No provisioned throughput
```

---

## Security & Authentication

### Security Layers

**1. Frontend Security**
- HTTPS only (TLS 1.2+)
- CloudFront with AWS Shield Standard
- Content Security Policy headers
- XSS protection

**2. API Gateway Security**
- CORS configuration
- Request validation
- Throttling and rate limiting
- CloudWatch monitoring

**3. Lambda Security**
- IAM roles with least privilege
- Environment variable encryption
- VPC isolation (if needed)
- Secrets Manager integration (future)

**4. Database Security**
- Encryption at rest (AWS managed)
- Encryption in transit (TLS)
- IAM-based access control
- VPC endpoints (optional)

**5. Authentication Flow**

```
User credentials → API Gateway → Auth Lambda
        ↓
Verify against DynamoDB (bcrypt)
        ↓
Generate JWT tokens (access + refresh)
        ↓
Return tokens to client
        ↓
Client stores in localStorage
        ↓
Subsequent requests include Bearer token
        ↓
API Gateway → Lambda → Verify JWT
        ↓
Extract user_id from token
        ↓
Process request
```

### IAM Roles & Policies

**Lambda Execution Role** (per function):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-south-1:*:table/kisaantic-prod"
    }
  ]
}
```

**Chat Lambda Additional Permissions**:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock-agent-runtime:InvokeAgent"
  ],
  "Resource": "*"
}
```

---

## Monitoring & Logging

### CloudWatch Configuration

**Lambda Metrics** (Automatic):
- Invocations
- Duration
- Errors
- Throttles
- Concurrent executions

**Lambda Logs**:
- Log group: `/aws/lambda/[function-name]`
- Retention: 7 days (configurable)
- Log level: INFO (console.log in code)

**API Gateway Metrics**:
- Request count
- Latency
- 4XX/5XX errors
- Integration latency

**API Gateway Logs**:
- Execution logs (request/response)
- Access logs
- Format: JSON

**Custom Metrics** (Future):
- Agent invocation count
- Response synthesis time
- Query complexity distribution
- Language usage statistics

### Alarms (Future)

Planned CloudWatch alarms:
- Lambda error rate > 1%
- API Gateway 5XX errors > 10/min
- Lambda concurrent executions > 900
- DynamoDB throttled requests > 0

---

## Scalability & Performance

### Horizontal Scalability

**Lambda**:
- Auto-scales based on request volume
- Concurrent execution limit: 1000 (default)
- Can request increase via service quotas

**API Gateway**:
- Handles 10,000 requests/second by default
- Automatic scaling
- Regional deployment (can add more regions)

**DynamoDB**:
- On-demand capacity mode
- Auto-scales read/write throughput
- No manual provisioning needed

**Amplify/CloudFront**:
- Global CDN
- Automatic edge caching
- Handles millions of requests

### Performance Optimizations

**1. Lambda Cold Starts**
- Layers reduce deployment package size
- 1024 MB for chat Lambda (faster cold starts)
- Keep functions warm (optional via CloudWatch Events)

**2. API Gateway**
- Lambda proxy integration (minimal overhead)
- No request transformation
- CORS preflight caching

**3. DynamoDB**
- Single-table design (fewer queries)
- Efficient access patterns
- GSI for common queries

**4. Bedrock**
- Parallel agent invocation (asyncio)
- Streaming responses (future)
- Model selection (Lite for speed, Pro for quality)

### Load Testing Results (Future)

Target metrics:
- 100 concurrent users
- < 35 second response time (P95)
- < 1% error rate
- 1000 requests/hour sustainable

---

## Cost Optimization

### Current Cost Structure (Estimated)

**Monthly Costs** (10,000 requests):

| Service | Usage | Cost |
|---------|-------|------|
| **AWS Lambda** | 10K invocations, 1024MB, avg 25s | ~$5 |
| **API Gateway** | 10K requests | ~$0.04 |
| **DynamoDB** | On-demand, 20K reads, 10K writes | ~$2.50 |
| **Bedrock** | Nova Lite (8 agents) + Nova Pro (synthesis) | ~$26 |
| **S3** | Knowledge bases, minimal storage | ~$0.50 |
| **CloudWatch** | Logs, metrics | ~$2 |
| **Amplify** | Hosting + build minutes | ~$0-5 |
| **Total** | | **~$36-41/month** |

**At 100,000 requests/month**: ~$350-400

### Cost Optimization Strategies

1. **Bedrock Optimization**
   - Use Nova Lite where possible (routing, agents)
   - Reserve Nova Pro for synthesis only
   - Optimize prompts to reduce token usage

2. **Lambda Optimization**
   - Right-size memory allocation
   - Reduce cold starts with layers
   - Minimize dependencies

3. **DynamoDB Optimization**
   - On-demand for variable workload
   - TTL for automatic cleanup
   - Efficient queries with GSI

4. **API Gateway Optimization**
   - No caching (data is real-time)
   - Use REST API (cheaper than HTTP API for our use case)

5. **Amplify Optimization**
   - Cache build artifacts
   - Optimize build time

---

## Future Enhancements

### Infrastructure Roadmap

**Phase 2 (Q1 2026)**:
- AWS Secrets Manager for API keys
- CloudWatch Dashboards
- Custom CloudWatch Alarms
- VPC for Lambda functions
- AWS WAF for API Gateway

**Phase 3 (Q2-Q3 2026)**:
- Multi-region deployment
- DynamoDB Global Tables
- Route 53 for custom domain
- CloudFront custom domain
- ElastiCache for response caching

**Phase 4 (Long-term)**:
- Kubernetes for microservices (if needed)
- SageMaker for custom ML models
- Step Functions for workflow orchestration
- EventBridge for event-driven architecture

---

## Deployment Checklist

### Pre-Deployment

- [✔] Code tested locally
- [✔] Environment variables configured
- [✔] Lambda layers updated
- [✔] API Gateway resources configured
- [✔] CORS enabled on all endpoints
- [✔] Lambda proxy integration enabled
- [✔] IAM roles and permissions verified

### Frontend Deployment

- [✔] Push code to GitHub main branch
- [✔] Amplify build triggered automatically
- [✔] Monitor build logs in Amplify Console
- [✔] Verify deployment success
- [✔] Test live site

### Backend Deployment

- [✔] Package Lambda code into .zip
- [✔] Upload to Lambda via Console
- [✔] Verify environment variables
- [✔] Test with Lambda test events
- [✔] Deploy API Gateway changes
- [✔] Verify endpoint responses

### Post-Deployment

- [✔] End-to-end testing
- [✔] Monitor CloudWatch logs
- [✔] Check error rates
- [✔] Verify all features working
- [✔] Update documentation if needed

---

## Troubleshooting Guide

### Common Issues

**1. Lambda Timeout**
- Check timeout setting (300s for chat Lambda)
- Monitor execution time in CloudWatch
- Optimize code if needed

**2. API Gateway 502/504**
- Verify Lambda proxy integration enabled
- Check Lambda response format
- Ensure Lambda doesn't timeout

**3. CORS Errors**
- Verify CORS enabled on API Gateway
- Check headers in Lambda response
- Ensure OPTIONS method configured

**4. Authentication Failures**
- Verify JWT secret in environment
- Check token expiration
- Validate token format

**5. Bedrock Errors**
- Verify IAM permissions
- Check agent IDs in configuration
- Ensure models available in region

---

## Contact & Support

### Infrastructure Team

- **AWS Architect**: [Your Name]
- **Backend Lead**: [Name]
- **Frontend Lead**: [Name]

### AWS Resources

- Lambda Console: AWS Console → Lambda
- API Gateway Console: AWS Console → API Gateway
- DynamoDB Console: AWS Console → DynamoDB
- Amplify Console: AWS Console → Amplify
- Bedrock Console: AWS Console → Bedrock

---

## Summary

### Infrastructure at a Glance

**Total AWS Services**: 10  
**Total Lambda Functions**: 19  
**Total API Endpoints**: 19  
**Total Bedrock Agents**: 8  
**Total Knowledge Bases**: 6  
**Deployment Method**: Manual via AWS Console (Infrastructure as Configuration)  
**Primary Region**: ap-south-1 (Mumbai)  
**Global Services**: CloudFront, Amplify, IAM, Shield  

### Service Categories Breakdown

| Category | Services | Count |
|----------|----------|-------|
| **Compute & Application** | Amplify, Lambda | 2 |
| **Networking & CDN** | CloudFront, API Gateway | 2 |
| **Database & Storage** | DynamoDB, S3 | 2 |
| **AI & Machine Learning** | Bedrock | 1 |
| **Security & Identity** | IAM | 1 |
| **Management & Monitoring** | CloudWatch, Shield | 2 |
| **Total** | | **10** |

### Key Achievements

✅ **Serverless Architecture** - Zero server management, auto-scaling  
✅ **Manual Console Deployment** - Full control over each service configuration  
✅ **Extended API Timeout** - Service quota approved for 90-second timeout  
✅ **Lambda Proxy Integration** - Simplified request/response handling  
✅ **GitHub CI/CD** - Automatic frontend deployment via Amplify  
✅ **Multi-Agent AI** - 8 specialized Bedrock agents coordinated intelligently  
✅ **Global CDN** - CloudFront distribution for low-latency access  
✅ **Cost Optimized** - Pay-per-use model, ~$36-41/month for 10K requests  
✅ **Production Ready** - Live application serving real users  
✅ **Comprehensive Monitoring** - CloudWatch logs and metrics across all services  

### Technology Stack Summary

```
Frontend:    Next.js 15 + React 19 → AWS Amplify → CloudFront
API Layer:   REST API Gateway (90s timeout) → Lambda Proxy Integration
Compute:     19 Lambda Functions (Python 3.13) + 2 Layers
Database:    DynamoDB (On-demand) + S3 (Knowledge Bases)
AI/ML:       Bedrock (Nova Lite/Pro) + 8 Agents + 6 KBs
Security:    IAM + JWT + Shield Standard
Monitoring:  CloudWatch Logs + Metrics
```

### Critical Dependencies

**Must Be Running**:
1. API Gateway (entry point)
2. Lambda Functions (business logic)
3. DynamoDB (data persistence)
4. Bedrock (AI intelligence)

**Supporting Infrastructure**:
- Amplify/CloudFront (frontend delivery)
- S3 (knowledge base storage)
- CloudWatch (observability)
- IAM (access control)

### Next Steps for Infrastructure

**Short-term (Phase 2)**:
- [ ] AWS Secrets Manager for API keys
- [ ] Custom CloudWatch Dashboards
- [ ] Automated CloudWatch Alarms
- [ ] VPC for enhanced security
- [ ] AWS WAF for API Gateway protection

**Long-term (Phase 3-4)**:
- [ ] Multi-region deployment
- [ ] DynamoDB Global Tables
- [ ] Route 53 for custom domain
- [ ] ElastiCache for caching
- [ ] Infrastructure as Code (Terraform/CloudFormation)

---

**Architecture Version**: 2.0.0  
**Last Updated**: October 19, 2025  
**Status**: Production Deployed  
**Total AWS Services**: 10

---

*This architecture is designed for scalability, reliability, and cost-efficiency while maintaining the flexibility for future enhancements.*