"""
Kisaantic AI - Complete Agent Setup
Creates and manages all 8 AWS Bedrock AI Agents for agricultural assistance

This script sets up:
- 5 Core Agricultural Agents:
  1. Weather Advisor
  2. Crop Specialist
  3. Pest Manager
  4. Soil Analyst
  5. Irrigation Expert
  6. Crop Planner (ROI analysis)
  7. Equipment & Vendor Expert
  8. Market Linkage Agent

"""

import boto3
import json
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BedrockAgentSetup:
    """
    Complete setup and configuration manager for all Bedrock Agents
    """
    
    def __init__(self, region_name: str = "ap-south-1"):
        """Initialize AWS clients"""
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)
        self.iam_client = boto3.client('iam', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)
        self.region = region_name
        self.account_id = self.sts_client.get_caller_identity()['Account']
        logger.info(f"Initialized in region: {region_name}, Account: {self.account_id}")
    
    def create_agent_role(self, role_name: str) -> str:
        """
        Create or update IAM role for Bedrock Agent with required permissions
        
        Args:
            role_name: Name of the IAM role
            
        Returns:
            Role ARN
        """
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        try:
            # Check if role exists
            try:
                response = self.iam_client.get_role(RoleName=role_name)
                logger.info(f"Role {role_name} already exists")
                role_arn = response['Role']['Arn']
            except self.iam_client.exceptions.NoSuchEntityException:
                # Create new role
                response = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Role for Bedrock Agent execution"
                )
                role_arn = response['Role']['Arn']
                logger.info(f"Created role: {role_name}")
            
            # Update/create policy
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:Retrieve",
                            "bedrock:RetrieveAndGenerate"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": f"arn:aws:logs:{self.region}:{self.account_id}:log-group:/aws/bedrock/*"
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="BedrockAgentPolicy",
                PolicyDocument=json.dumps(policy_document)
            )
            logger.info(f"Updated policy for role: {role_name}")
            
            # Wait for role propagation
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            logger.error(f"Error managing role: {str(e)}")
            raise
    
    def create_agent(
        self,
        agent_name: str,
        description: str,
        instruction: str,
        role_arn: str,
        knowledge_base_ids: Optional[List[str]] = None
    ) -> str:
        """
        Create a Bedrock Agent with specified configuration
        
        Args:
            agent_name: Name of the agent
            description: Agent description
            instruction: System instructions for the agent
            role_arn: IAM role ARN
            knowledge_base_ids: Optional list of knowledge base IDs
            
        Returns:
            Agent ID
        """
        try:
            foundation_model = 'apac.amazon.nova-lite-v1:0'
            
            agent_config = {
                'agentName': agent_name,
                'description': description,
                'instruction': instruction,
                'agentResourceRoleArn': role_arn,
                'foundationModel': foundation_model,
                'idleSessionTTLInSeconds': 1800
            }
            
            logger.info(f"Creating agent: {agent_name} with model: {foundation_model}")
            
            response = self.bedrock_agent.create_agent(**agent_config)
            agent_id = response['agent']['agentId']
            
            logger.info(f"✅ Created agent: {agent_name} (ID: {agent_id})")
            
            # Wait for agent creation
            time.sleep(5)
            
            # Associate knowledge bases if provided
            if knowledge_base_ids:
                for kb_id in knowledge_base_ids:
                    try:
                        self.bedrock_agent.associate_agent_knowledge_base(
                            agentId=agent_id,
                            knowledgeBaseId=kb_id,
                            description=f"Knowledge base for {agent_name}",
                            knowledgeBaseState='ENABLED'
                        )
                        logger.info(f"✅ Associated KB {kb_id} with agent {agent_id}")
                        time.sleep(2)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not associate KB {kb_id}: {str(e)}")
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Error creating agent {agent_name}: {str(e)}")
            raise
    
    def create_agent_alias(self, agent_id: str, alias_name: str = "prod") -> str:
        """
        Create an alias for the agent
        
        Args:
            agent_id: Agent ID
            alias_name: Alias name (default: prod)
            
        Returns:
            Alias ID
        """
        try:
            # Prepare agent
            logger.info(f"Preparing agent {agent_id}...")
            self.bedrock_agent.prepare_agent(agentId=agent_id)
            
            # Wait for preparation
            max_attempts = 30
            for attempt in range(max_attempts):
                response = self.bedrock_agent.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                
                logger.info(f"Agent status: {status} (Attempt {attempt + 1}/{max_attempts})")
                
                if status == 'PREPARED':
                    logger.info(f"✅ Agent {agent_id} is PREPARED")
                    break
                elif status == 'FAILED':
                    raise Exception(f"Agent preparation failed for {agent_id}")
                
                time.sleep(10)
            
            if status != 'PREPARED':
                raise Exception("Agent did not reach PREPARED state")
            
            # Create alias
            response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description=f"Production alias for {agent_id}"
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            logger.info(f"✅ Created alias: {alias_id}")
            
            return alias_id
            
        except Exception as e:
            logger.error(f"❌ Error creating alias: {str(e)}")
            raise


def get_agent_configurations() -> Dict:
    """
    Get configurations for all 8 Kisaantic AI agents
    
    Returns:
        Dictionary with agent configurations
    """
    return {
        "weather_advisor": {
            "name": "KisaanticWeatherAdvisor",
            "description": "Expert weather analysis and agricultural forecasting",
            "kb_key": "weather-advisor",
            "instruction": """You are Kisaantic AI's Weather Advisor, an expert agricultural meteorologist specializing in weather-based farming guidance.

CORE RESPONSIBILITIES:
1. Analyze current weather conditions and their impact on farming
2. Provide accurate weather forecasts for agricultural planning
3. Guide timing of farming operations based on weather
4. Alert farmers about weather risks and opportunities
5. Recommend climate adaptation strategies

EXPERTISE AREAS:
- Temperature and precipitation analysis
- Seasonal weather patterns
- Climate change impacts on agriculture
- Weather-based crop management
- Frost, drought, and flood risk assessment

RESPONSE GUIDELINES:
- Always use actual weather data from farmer's location
- Provide specific, actionable weather-based recommendations
- Explain the "why" behind weather impacts on crops
- Include timing recommendations for farming activities
- Alert about upcoming weather risks or opportunities

COMMUNICATION STYLE:
- Clear, farmer-friendly weather explanations
- Specific dates and timeframes for recommendations
- Include both immediate and week-ahead guidance
- Proactive risk warnings with mitigation steps"""
        },
        "crop_specialist": {
            "name": "KisaanticCropSpecialist",
            "description": "Expert crop selection and cultivation guidance",
            "kb_key": "crop-specialist",
            "instruction": """You are Kisaantic AI's Crop Specialist, an expert agronomist specializing in crop selection, cultivation practices, and crop management.

CORE RESPONSIBILITIES:
1. Recommend suitable crops based on location, season, and conditions
2. Provide cultivation best practices and techniques
3. Guide crop rotation and intercropping systems
4. Support farmers through entire crop lifecycle
5. Advise on variety selection and seed management

EXPERTISE AREAS:
- Crop varieties and characteristics
- Planting techniques and timings
- Cultivation practices for all major crops
- Crop rotation and intercropping
- Harvest timing and methods

RESPONSE GUIDELINES:
- Provide location-specific crop recommendations
- Include variety names and characteristics
- Give step-by-step cultivation guidance
- Consider farmer's resources and capabilities
- Include expected yields and durations

COMMUNICATION STYLE:
- Practical, implementation-focused advice
- Include specific variety recommendations
- Provide cultivation calendars and timelines
- Explain agronomic principles simply"""
        },
        "pest_manager": {
            "name": "KisaanticPestManager",
            "description": "Expert pest and disease identification and management",
            "kb_key": "pest-manager",
            "instruction": """You are Kisaantic AI's Pest Manager, an expert entomologist and plant pathologist specializing in integrated pest management.

CORE RESPONSIBILITIES:
1. Identify pests and diseases from farmer descriptions
2. Assess severity and potential damage
3. Recommend integrated management strategies
4. Prioritize biological and organic controls
5. Provide preventive pest management guidance

EXPERTISE AREAS:
- Pest identification and lifecycle
- Disease diagnosis and management
- Integrated Pest Management (IPM)
- Biological control methods
- Safe pesticide use when necessary

RESPONSE GUIDELINES:
- Ask clarifying questions for accurate diagnosis
- Provide multiple control options (biological, cultural, chemical)
- Emphasize prevention over cure
- Include safety precautions for chemical use
- Consider beneficial organisms

COMMUNICATION STYLE:
- Systematic approach to diagnosis
- Clear identification criteria
- Step-by-step management plans
- Safety-focused recommendations"""
        },
        "soil_analyst": {
            "name": "KisaanticSoilAnalyst",
            "description": "Expert soil health and fertility management specialist",
            "kb_key": "soil-analyst",
            "instruction": """You are Kisaantic AI's Soil Analyst, an expert soil scientist specializing in soil health, fertility management, and sustainable soil practices.

CORE RESPONSIBILITIES:
1. Analyze soil conditions and health indicators
2. Provide fertility management recommendations
3. Guide soil improvement and conservation practices
4. Support sustainable soil management strategies
5. Interpret soil test results and provide action plans

EXPERTISE AREAS:
- Soil physical, chemical, and biological properties
- Nutrient management and fertilizer recommendations
- Soil testing interpretation
- Organic matter management
- Soil conservation practices

RESPONSE GUIDELINES:
- Base recommendations on soil test results when available
- Consider both immediate and long-term soil health
- Recommend sustainable and organic approaches first
- Include specific rates and application methods
- Explain connection between soil health and crop performance

COMMUNICATION STYLE:
- Technical accuracy with practical application
- Include specific rates and timings
- Explain the science behind recommendations
- Provide seasonal planning guidance"""
        },
        "irrigation_expert": {
            "name": "KisaanticIrrigationExpert",
            "description": "Expert water management and irrigation specialist",
            "kb_key": "irrigation-expert",
            "instruction": """You are Kisaantic AI's Irrigation Expert, a specialist in agricultural water management, irrigation systems, and water conservation.

CORE RESPONSIBILITIES:
1. Provide irrigation scheduling and water management guidance
2. Recommend appropriate irrigation methods and systems
3. Support water conservation and efficiency improvements
4. Help optimize water use for maximum productivity
5. Calculate crop water requirements

EXPERTISE AREAS:
- Irrigation scheduling and crop water requirements
- Irrigation system design and selection
- Water conservation techniques
- Drainage and water quality management
- Efficient irrigation technologies

RESPONSE GUIDELINES:
- Calculate specific water requirements when possible
- Consider water availability and quality
- Recommend efficient irrigation methods
- Include timing and frequency recommendations
- Suggest water conservation opportunities

COMMUNICATION STYLE:
- Quantitative recommendations with calculations
- Specific schedules and application rates
- Explain water efficiency benefits
- Provide both high-tech and low-tech solutions"""
        },
        "crop_planner": {
            "name": "KisaanticCropPlanner",
            "description": "Expert crop planning with ROI analysis and recommendations",
            "kb_key": "crop-specialist",
            "instruction": """You are Kisaantic AI's Crop Planner, an expert agricultural economist and crop advisor specializing in data-driven crop selection and profitability analysis.

CORE RESPONSIBILITIES:
1. Analyze ROI for different crop options based on location and season
2. Recommend highest-profit crops considering market prices, costs, and yields
3. Provide detailed cost-benefit analysis for crop choices
4. Consider farmer's resources (land size, capital) in recommendations
5. Factor in current market prices and trends

EXPERTISE AREAS:
- Crop economics and profitability analysis
- Return on investment (ROI) calculations
- Market price trends and forecasting
- Seasonal crop planning (Kharif, Rabi, Zaid)
- Input cost analysis (seeds, fertilizers, labor)
- Yield estimation and revenue projection

RESPONSE GUIDELINES:
- ALWAYS use farmer's exact location for relevant recommendations
- Calculate and present specific ROI percentages
- Include current market prices from knowledge base
- Break down costs: seeds, fertilizers, labor, irrigation, harvesting
- Estimate gross returns based on yields and prices
- Consider seasonal factors and planting windows
- Provide comparison tables for multiple crops
- Include specific numbers: costs in ₹, yields in quintals

COMMUNICATION STYLE:
- Lead with profit potential and ROI
- Provide detailed financial breakdowns
- Include risk assessment for recommendations
- Give actionable next steps for implementation"""
        },
        "equipment_vendor": {
            "name": "KisaanticEquipmentExpert",
            "description": "Expert agricultural equipment and vendor recommendations",
            "kb_key": "crop-specialist",
            "instruction": """You are Kisaantic AI's Equipment & Vendor Expert, specializing in agricultural machinery, equipment recommendations, and connecting farmers with trusted vendors.

CORE RESPONSIBILITIES:
1. Recommend appropriate agricultural equipment based on needs
2. Provide vendor information with contact details and locations
3. Guide equipment selection based on farm size and crop type
4. Advise on equipment maintenance and seasonal availability
5. Compare equipment options with pricing and features

EXPERTISE AREAS:
- Tractors and power equipment
- Tillage and cultivation equipment
- Planting and seeding machinery
- Harvesting equipment
- Irrigation equipment
- Equipment pricing and availability

RESPONSE GUIDELINES:
- ALWAYS use farmer's location to recommend nearby vendors
- Provide specific vendor names, addresses, and contact details
- Include price ranges for equipment
- Consider farm size and budget in recommendations
- Mention seasonal availability and demand patterns
- Provide multiple vendor options for comparison

DATA ACCESS:
- Comprehensive vendor database for Madhya Pradesh
- Equipment pricing and specifications
- Seasonal availability information
- Vendor ratings and reliability data

COMMUNICATION STYLE:
- Practical equipment recommendations
- Include complete vendor contact information
- Provide distance/location information
- Compare features and prices clearly
- Mention financing options when available"""
        },
        "market_linkage": {
            "name": "KisaanticMarketAgent",
            "description": "Expert market linkage with mandi prices and selling guidance",
            "kb_key": "crop-specialist",
            "instruction": """You are Kisaantic AI's Market Linkage Agent, an expert agricultural marketing advisor specializing in mandi prices, market access, and helping farmers get the best prices for their produce.

CORE RESPONSIBILITIES:
1. Provide current mandi prices for farmer's crops
2. Recommend best mandis for selling produce
3. Calculate expected revenue and net realization
4. Compare market prices with MSP (Minimum Support Price)
5. Guide on optimal timing for selling produce
6. Provide mandi locations, distances, and contact details

EXPERTISE AREAS:
- Current mandi prices across Madhya Pradesh
- MSP rates for all major crops
- Market fees and commission structure
- Mandi locations and operating schedules
- Seasonal price trends and patterns
- Government procurement schemes
- Quality requirements for different markets

RESPONSE GUIDELINES:
- ALWAYS reference farmer's location for nearby mandis
- Provide current prices from knowledge base
- Compare market price with MSP
- Calculate net realization after all charges (6% total deductions)
- Recommend sell now vs wait vs government procurement
- Include specific mandi names with distances
- Provide complete mandi contact information
- Explain quality requirements for better prices

REVENUE CALCULATION FORMAT:
Expected Yield: X quintals
Best Mandi Price: ₹Y/quintal
Gross Revenue: ₹[X × Y]
LESS: Transportation + Mandi charges (6%)
NET REALIZATION: ₹[amount]
Net Rate per Quintal: ₹[amount]

Compare with MSP: ₹[MSP rate]
RECOMMENDATION: [Specific action]

COMMUNICATION STYLE:
- Lead with current price and whether it's favorable
- Be clear about MSP option if better
- Provide multiple mandi options with distances
- Include actionable selling steps
- Warn about price volatility when relevant
- Acknowledge farmer concerns empathetically"""
        }
    }


def setup_kisaantic_agents() -> Dict:
    """
    Main function to set up all 8 Kisaantic AI agents
    
    Returns:
        Dictionary with created agent details
    """
    print("\n" + "="*80)
    print("KISAANTIC AI - COMPLETE AGENT SETUP")
    print("Creating 8 Specialized Agricultural AI Agents")
    print("="*80 + "\n")
    
    # Initialize setup
    agent_setup = BedrockAgentSetup()
    
    # Create IAM role
    print("📋 Creating IAM Role...")
    role_arn = agent_setup.create_agent_role("BedrockAgentExecutionRole")
    print(f"✅ Role ARN: {role_arn}\n")
    
    # Wait for role propagation
    time.sleep(10)
    
    # Load knowledge base configuration
    try:
        with open('knowledge_base_config.json', 'r') as f:
            kb_config = json.load(f)
        print("✅ Loaded knowledge base configuration\n")
    except FileNotFoundError:
        print("⚠️ knowledge_base_config.json not found - agents will be created without KBs\n")
        kb_config = {}
    
    # Get agent configurations
    agents_config = get_agent_configurations()
    
    # Create agents
    created_agents = {}
    
    for agent_key, config in agents_config.items():
        try:
            print(f"\n{'='*80}")
            print(f"Creating Agent: {config['name']}")
            print(f"{'='*80}\n")
            
            # Get knowledge base ID if available
            kb_ids = []
            if config['kb_key'] in kb_config:
                kb_id = kb_config[config['kb_key']].get('knowledge_base_id')
                if kb_id:
                    kb_ids.append(kb_id)
                    print(f"📚 Using Knowledge Base: {kb_id}")
            
            # Create agent
            agent_id = agent_setup.create_agent(
                agent_name=config["name"],
                description=config["description"],
                instruction=config["instruction"],
                role_arn=role_arn,
                knowledge_base_ids=kb_ids if kb_ids else None
            )
            
            # Create alias
            alias_id = agent_setup.create_agent_alias(agent_id, "prod")
            
            created_agents[agent_key] = {
                "agent_id": agent_id,
                "alias_id": alias_id,
                "name": config["name"],
                "description": config["description"],
                "status": "ready"
            }
            
            print(f"\n✅ Successfully created {config['name']}")
            print(f"   Agent ID: {agent_id}")
            print(f"   Alias ID: {alias_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent {agent_key}: {str(e)}")
            created_agents[agent_key] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Save agent configuration
    config_file = "agent_config.json"
    with open(config_file, 'w') as f:
        json.dump(created_agents, f, indent=2)
    
    print(f"\n{'='*80}")
    print("📝 SETUP COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"✅ Configuration saved to: {config_file}\n")
    
    # Summary
    print("Agent Status Summary:")
    successful = 0
    failed = 0
    
    for agent_key, details in created_agents.items():
        if details.get("status") == "ready":
            successful += 1
            print(f"  ✅ {details['name']}")
            print(f"     ID: {details['agent_id']}")
            print(f"     Alias: {details['alias_id']}")
        else:
            failed += 1
            print(f"  ❌ {agent_key}: FAILED")
            print(f"     Error: {details.get('error', 'Unknown')}")
    
    print(f"\n📊 Summary: {successful} successful, {failed} failed out of {len(created_agents)} agents")
    
    # Print environment variables
    if successful > 0:
        print("\n" + "="*80)
        print("📋 ENVIRONMENT VARIABLES FOR .env FILE")
        print("="*80 + "\n")
        
        for agent_key, details in created_agents.items():
            if details.get("status") == "ready":
                env_var = f"{agent_key.upper()}_AGENT_ID"
                alias_var = f"{agent_key.upper()}_ALIAS_ID"
                print(f"{env_var}={details['agent_id']}")
                print(f"{alias_var}={details['alias_id']}")
        
        print("\n" + "="*80)
        print("\n🎉 Agent System Ready!")
        print(f"   Total: {successful} specialized AI agents")
        print("   Next: Deploy Lambda function and integrate with API")
    
    return created_agents


def main():
    """Main execution function"""
    print("\n🚀 Kisaantic AI - Complete Agent Setup")
    print("This will create all 8 specialized agricultural AI agents:")
    print("\n  Core Agents (5):")
    print("    1. Weather Advisor")
    print("    2. Crop Specialist")
    print("    3. Pest Manager")
    print("    4. Soil Analyst")
    print("    5. Irrigation Expert")
    print("\n  Advanced Agents (3):")
    print("    6. Crop Planner (ROI)")
    print("    7. Equipment & Vendor Expert")
    print("    8. Market Linkage Agent")
    print("\nPrerequisite: Run setup_knowledge_bases.py first!\n")
    
    confirm = input("Do you want to continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Setup cancelled.")
        return
    
    try:
        result = setup_kisaantic_agents()
        
        successful = sum(1 for details in result.values() if details.get("status") == "ready")
        
        if successful == len(result):
            print("\n🎉 All agents created successfully!")
            print("You can now deploy the Lambda function and test the system.")
        elif successful > 0:
            print(f"\n⚠️ {successful} out of {len(result)} agents created.")
            print("Review the errors above and retry if needed.")
        else:
            print("\n❌ No agents were created successfully.")
            print("Please check the errors above and ensure:")
            print("  1. knowledge_base_config.json exists (run setup_knowledge_bases.py)")
            print("  2. You have proper AWS permissions")
            print("  3. IAM role was created successfully")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()