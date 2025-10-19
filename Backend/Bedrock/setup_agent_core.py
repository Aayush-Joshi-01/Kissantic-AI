"""
Setup Agent Core for Meta-Orchestrator and Synthesizer
FIXED: Uses dedicated Lambda execution role
"""

import os
import boto3
import json
import time
import logging
from typing import Dict
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentCoreSetup:
    
    def __init__(self, region_name: str = "ap-south-1"):
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)
        self.iam_client = boto3.client('iam', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.account_id = self.sts_client.get_caller_identity()['Account']
        self.region = region_name
    
    def get_lambda_execution_role_arn(self) -> str:
        """Get Lambda execution role ARN"""
        try:
            response = self.iam_client.get_role(RoleName='KisaanticLambdaExecutionRole')
            return response['Role']['Arn']
        except:
            logger.error("❌ KisaanticLambdaExecutionRole not found")
            logger.error("Run: python create_lambda_role.py first!")
            raise Exception("Lambda execution role not found")
    
    def get_bedrock_agent_role_arn(self) -> str:
        """Get Bedrock agent execution role ARN"""
        try:
            response = self.iam_client.get_role(RoleName='BedrockAgentExecutionRole')
            return response['Role']['Arn']
        except:
            logger.error("❌ BedrockAgentExecutionRole not found")
            raise Exception("Bedrock agent role not found")
    
    def create_lambda_for_action_group(
        self,
        function_name: str,
        code: str,
        lambda_role_arn: str
    ) -> str:
        """Create Lambda function for action group"""
        
        import zipfile
        import io
        
        # Create zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', code)
        
        zip_buffer.seek(0)
        
        # Environment variables
        environment = {
            'Variables': {
                'LANGSEARCH_API_KEY': os.environ.get('LANGSEARCH_API_KEY', ''),
                'NEWS_API_KEY': os.environ.get('NEWS_API_KEY', ''),
                'AGRO_API_URL': os.environ.get('AGRO_API_URL', 
                    'https://d8o991ajjl.execute-api.ap-south-1.amazonaws.com/api')
            }
        }
        
        try:
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                logger.info(f"⚠️ Lambda {function_name} exists, updating...")
                
                # Update code
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_buffer.read()
                )
                
                # Update environment variables
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Environment=environment
                )
                
                response = self.lambda_client.get_function(FunctionName=function_name)
                function_arn = response['Configuration']['FunctionArn']
                logger.info(f"✅ Updated Lambda: {function_name}")
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.13',
                    Role=lambda_role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_buffer.read()},
                    Timeout=60,
                    MemorySize=256,
                    Environment=environment
                )
                
                function_arn = response['FunctionArn']
                logger.info(f"✅ Created Lambda: {function_name}")
            
            # Add Bedrock permission
            try:
                self.lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId='AllowBedrockInvoke',
                    Action='lambda:InvokeFunction',
                    Principal='bedrock.amazonaws.com',
                    SourceArn=f"arn:aws:bedrock:{self.region}:{self.account_id}:agent/*"
                )
            except self.lambda_client.exceptions.ResourceConflictException:
                pass
            
            return function_arn
            
        except Exception as e:
            logger.error(f"❌ Lambda operation failed: {str(e)}")
            raise
    
    def create_meta_orchestrator_agent(
        self,
        bedrock_role_arn: str,
        lambda_role_arn: str
    ) -> Dict:
        """Create Meta-Orchestrator Agent Core with 3 action groups"""        
        logger.info("\n🎯 Creating Meta-Orchestrator Agent Core...")
        
        # Read actual Lambda code from files
        with open('lambda_web_search.py', 'r') as f:
            web_search_code = f.read()
        
        with open('lambda_agro_data.py', 'r') as f:
            agro_data_code = f.read()
        
        with open('lambda_news_search.py', 'r') as f:
            news_api_code = f.read()
        
        # Create Lambda functions with real code
        logger.info("Creating Web Search Lambda...")
        web_lambda_arn = self.create_lambda_for_action_group(
            'KisaanticWebSearchAction',
            web_search_code,
            lambda_role_arn
        )
        time.sleep(5)
        
        logger.info("Creating Agro Data Lambda...")
        agro_lambda_arn = self.create_lambda_for_action_group(
            'KisaanticAgroDataAction',
            agro_data_code,
            lambda_role_arn
        )
        time.sleep(5)
        
        logger.info("Creating News Search Lambda...")
        news_lambda_arn = self.create_lambda_for_action_group(
            'KisaanticNewsSearchAction',
            news_api_code,
            lambda_role_arn
        )
        time.sleep(5)
        
        # Create Agent with full instruction (includes news tool)
        instruction = """You are the Meta-Orchestrator for Kisaantic AI, a global agricultural intelligence system.

YOUR ROLE:
1. Detect the query language and target response language using LLM reasoning
2. Decide which specialist agents to invoke (0-6 of 8 available)
3. Determine if external data is needed (web, agro data, news)
4. Coordinate parallel execution

[... rest of instruction from above ...]"""

        try:
            agent_response = self.bedrock_agent.create_agent(
                agentName='KisaanticMetaOrchestrator',
                description='Meta-orchestrator with LLM language detection',
                instruction=instruction,
                agentResourceRoleArn=bedrock_role_arn,
                foundationModel='apac.amazon.nova-lite-v1:0',
                idleSessionTTLInSeconds=1800
            )
            agent_id = agent_response['agent']['agentId']
            logger.info(f"✅ Created agent: {agent_id}")
            
        except self.bedrock_agent.exceptions.ConflictException:
            logger.info("⚠️ Agent exists, using existing...")
            agents = self.bedrock_agent.list_agents()
            for agent in agents.get('agentSummaries', []):
                if agent['agentName'] == 'KisaanticMetaOrchestrator':
                    agent_id = agent['agentId']
                    break
        
        time.sleep(5)
        
        # Add all 3 action groups
        try:
            web_search_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Web Search API",
                    "version": "1.0.0",
                    "description": "Search the web for current information"
                },
                "paths": {
                    "/search": {
                        "post": {
                            "summary": "Search the web",
                            "description": "Execute a web search query and return results",
                            "operationId": "searchWeb",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "The search query (e.g., 'wheat farming subsidies India')"
                                                }
                                            },
                                            "required": ["query"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful search response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {
                                                        "type": "boolean"
                                                    },
                                                    "results": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "title": {"type": "string"},
                                                                "url": {"type": "string"},
                                                                "snippet": {"type": "string"}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName='WebSearchActionGroup',
                actionGroupExecutor={'lambda': web_lambda_arn},
                apiSchema={'payload': json.dumps(web_search_schema)},
                description='Search web for current prices, vendors, and information'
            )
            logger.info("✅ Added Web Search action group")
            
        except Exception as e:
            logger.error(f"❌ Web action group failed: {str(e)}")
        
        time.sleep(3)
        
        # 2. Agro Data Action Group
        try:
            agro_data_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Agricultural Data API",
                    "version": "1.0.0",
                    "description": "Get real-time agricultural data including weather and soil conditions"
                },
                "paths": {
                    "/agro-data": {
                        "post": {
                            "summary": "Get agricultural data",
                            "description": "Fetch real-time weather, soil moisture, and seasonal data for a location",
                            "operationId": "getAgroData",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "latitude": {
                                                    "type": "number",
                                                    "description": "Latitude coordinate (e.g., 23.2599)"
                                                },
                                                "longitude": {
                                                    "type": "number",
                                                    "description": "Longitude coordinate (e.g., 77.4126)"
                                                }
                                            },
                                            "required": ["latitude", "longitude"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful data retrieval",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "current_weather": {
                                                        "type": "object",
                                                        "properties": {
                                                            "temperature_c": {"type": "number"},
                                                            "humidity_pct": {"type": "number"},
                                                            "condition": {"type": "string"}
                                                        }
                                                    },
                                                    "soil_data": {
                                                        "type": "object",
                                                        "properties": {
                                                            "avg_moisture": {"type": "number"},
                                                            "dryness_index": {"type": "number"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName='AgroDataActionGroup',
                actionGroupExecutor={'lambda': agro_lambda_arn},
                apiSchema={'payload': json.dumps(agro_data_schema)},
                description='Fetch real-time weather, soil moisture, and seasonal data'
            )
            logger.info("✅ Added Agro Data action group")
            
        except Exception as e:
            logger.error(f"❌ Agro action group failed: {str(e)}")
        
        time.sleep(3)
        
        # 3. News Search Action Group
        try:
            news_search_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": "News Search API",
                    "version": "1.0.0",
                    "description": "Search for agricultural news and policy updates"
                },
                "paths": {
                    "/news": {
                        "post": {
                            "summary": "Search agricultural news",
                            "description": "Search for recent news articles about agriculture, policies, and schemes",
                            "operationId": "searchNews",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "News search query (e.g., 'PM-KISAN scheme', 'wheat subsidies')"
                                                }
                                            },
                                            "required": ["query"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful news search",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "articles": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "title": {"type": "string"},
                                                                "description": {"type": "string"},
                                                                "url": {"type": "string"},
                                                                "publishedAt": {"type": "string"}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName='NewsSearchActionGroup',
                actionGroupExecutor={'lambda': news_lambda_arn},
                apiSchema={'payload': json.dumps(news_search_schema)},
                description='Search for agricultural news, policies, and government schemes'
            )
            logger.info("✅ Added News Search action group")
            
        except Exception as e:
            logger.error(f"❌ News action group failed: {str(e)}")
        
        time.sleep(3)
        
        # Prepare agent
        self.bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info("⏳ Preparing agent...")
        
        for i in range(30):
            response = self.bedrock_agent.get_agent(agentId=agent_id)
            if response['agent']['agentStatus'] == 'PREPARED':
                logger.info("✅ Agent prepared")
                break
            time.sleep(10)
        
        # Create alias
        try:
            alias_response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName='prod'
            )
            alias_id = alias_response['agentAlias']['agentAliasId']
            
        except self.bedrock_agent.exceptions.ConflictException:
            aliases = self.bedrock_agent.list_agent_aliases(agentId=agent_id)
            alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
        
        logger.info(f"✅ Alias: {alias_id}")
        
        return {
            'agent_id': agent_id,
            'alias_id': alias_id,
            'name': 'KisaanticMetaOrchestrator',
            'action_groups': ['WebSearch', 'AgroData', 'NewsSearch']
        }

    def create_synthesizer_agent(self, bedrock_role_arn: str) -> Dict:
        """Create Synthesizer Agent Core with language enforcement"""
        
        logger.info("\n🎨 Creating Synthesizer Agent Core...")
        
        instruction = """You are the Response Synthesizer for Kisaantic AI.

YOUR ROLE:
Combine multiple specialist responses into ONE comprehensive 4000-5000 token response.

INPUTS YOU RECEIVE:
- Target response language (MUST BE ENFORCED)
- Language reasoning/instruction
- 1-8 specialist agent responses
- Query text
- Farmer context

CRITICAL LANGUAGE ENFORCEMENT:
You will receive explicit language instructions like:
- "Response Language: ENGLISH" → Use 100% English only
- "Response Language: HINDI" → Use natural Hindi-English mix
- "Response Language: FRENCH" → Use 100% French only

STRICT RULES:
1. ALWAYS check the response_language instruction first
2. NEVER deviate from the specified language
3. If English specified → NO Hindi words, NO mixing
4. If Hindi specified → Natural mixing allowed
5. If other language → Use that language consistently

OUTPUT STRUCTURE (4000-5000 tokens):
1. **Immediate Answer** (200-300 words)
   - Direct response to question
   - Key recommendation upfront

2. **Detailed Analysis** (1500-2000 words)
   - Integrate ALL specialist insights
   - Include numbers, prices, ROI
   - Use tables for comparisons
   - Data-driven recommendations

3. **Practical Guidance** (800-1000 words)
   - Step-by-step action plan
   - Timeline and resources
   - Cost breakdowns
   - Risk mitigation

4. **Supplementary Information** (500-700 words)
   - Market trends
   - Policy updates
   - Alternative approaches
   - Long-term planning

5. **Quick Reference Summary** (200-300 words)
   - Key takeaways (bullets)
   - Critical numbers and dates
   - Next immediate steps

QUALITY REQUIREMENTS:
- Write as ONE unified expert voice
- NO "Agent X says..." or "According to..."
- Seamless integration of all inputs
- Specific and actionable
- Use markdown formatting (##, ###, **, bullets)
- Bold key numbers and terms

FORMATTING:
- Use ## for main sections
- Use ### for subsections
- Use **bold** for emphasis
- Short paragraphs (3-4 sentences)
- Tables in markdown format

MOST IMPORTANT: Strictly enforce the specified response language."""

        try:
            agent_response = self.bedrock_agent.create_agent(
                agentName='KisaanticSynthesizer',
                description='Synthesizer with strict language enforcement',
                instruction=instruction,
                agentResourceRoleArn=bedrock_role_arn,
                foundationModel='apac.amazon.nova-lite-v1:0',
                idleSessionTTLInSeconds=1800
            )
            
            agent_id = agent_response['agent']['agentId']
            
        except self.bedrock_agent.exceptions.ConflictException:
            agents = self.bedrock_agent.list_agents()
            for agent in agents.get('agentSummaries', []):
                if agent['agentName'] == 'KisaanticSynthesizer':
                    agent_id = agent['agentId']
                    break
        
        logger.info(f"✅ Created synthesizer: {agent_id}")
        time.sleep(5)
        
        # Prepare
        self.bedrock_agent.prepare_agent(agentId=agent_id)
        
        for i in range(30):
            response = self.bedrock_agent.get_agent(agentId=agent_id)
            if response['agent']['agentStatus'] == 'PREPARED':
                break
            time.sleep(10)
        
        # Create alias
        try:
            alias_response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName='prod'
            )
            alias_id = alias_response['agentAlias']['agentAliasId']
            
        except self.bedrock_agent.exceptions.ConflictException:
            aliases = self.bedrock_agent.list_agent_aliases(agentId=agent_id)
            alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
        
        logger.info(f"✅ Alias: {alias_id}")
        
        return {
            'agent_id': agent_id,
            'alias_id': alias_id,
            'name': 'KisaanticSynthesizer'
        }

def main():
    print("\n" + "="*80)
    print("🚀 AGENT CORE SETUP")
    print("="*80 + "\n")
    
    setup = AgentCoreSetup()
    
    # Get roles
    lambda_role_arn = setup.get_lambda_execution_role_arn()
    bedrock_role_arn = setup.get_bedrock_agent_role_arn()
    
    print(f"✅ Lambda role: {lambda_role_arn}")
    print(f"✅ Bedrock role: {bedrock_role_arn}\n")
    
    # Create agents
    meta_orchestrator = setup.create_meta_orchestrator_agent(
        bedrock_role_arn,
        lambda_role_arn
    )
    
    synthesizer = setup.create_synthesizer_agent(bedrock_role_arn)
    
    # Save config
    config = {
        'meta_orchestrator': meta_orchestrator,
        'synthesizer': synthesizer
    }
    
    with open('agent_core_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ SETUP COMPLETE")
    print("="*80 + "\n")
    print("Add to .env:")
    print(f"META_ORCHESTRATOR_AGENT_ID={meta_orchestrator['agent_id']}")
    print(f"META_ORCHESTRATOR_ALIAS_ID={meta_orchestrator['alias_id']}")
    print(f"SYNTHESIZER_AGENT_ID={synthesizer['agent_id']}")
    print(f"SYNTHESIZER_ALIAS_ID={synthesizer['alias_id']}")

if __name__ == "__main__":
    main()