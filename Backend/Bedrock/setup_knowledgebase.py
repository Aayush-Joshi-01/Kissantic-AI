"""
Kisaantic AI - Complete Knowledge Base Setup
Creates and manages AWS Bedrock Knowledge Bases with comprehensive agricultural data

This script sets up:
- OpenSearch Serverless collections
- S3 buckets for knowledge storage
- IAM roles and permissions
- Knowledge bases with embeddings
- Complete agricultural knowledge including:
  * Weather patterns and climate data
  * Crop varieties and cultivation practices
  * Pest and disease management
  * Soil health and fertility
  * Irrigation and water management
  * Equipment vendors and pricing (Madhya Pradesh)
  * Market prices and mandi information
  * ROI calculations and crop economics
"""

import boto3
import json
import time
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeBaseConfig:
    """Configuration for a Knowledge Base"""
    name: str
    description: str
    role_arn: str
    s3_bucket: str
    s3_prefix: str
    embedding_model: str = "amazon.titan-embed-text-v2:0"


class BedrockKnowledgeBaseManager:
    """
    Manages Bedrock Knowledge Bases for Kisaantic AI Agents
    Handles creation of OpenSearch collections, S3 buckets, and knowledge bases
    """
    
    def __init__(self, region_name: str = "ap-south-1"):
        """Initialize AWS clients"""
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.iam_client = boto3.client('iam', region_name=region_name)
        self.aoss_client = boto3.client('opensearchserverless', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)
        self.region = region_name
        self.account_id = self.sts_client.get_caller_identity()['Account']
        logger.info(f"Initialized in region: {region_name}, Account: {self.account_id}")
    
    def create_knowledge_base_role(self, role_name: str) -> str:
        """
        Create or update IAM role for Knowledge Base with required permissions
        
        Args:
            role_name: Name of the IAM role to create
            
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
                    Description="Role for Bedrock Knowledge Base access"
                )
                role_arn = response['Role']['Arn']
                logger.info(f"Created role: {role_name}")
            
            # Update/create inline policy
            custom_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:ListBucket"],
                        "Resource": [
                            "arn:aws:s3:::kisaantic-knowledge-*",
                            "arn:aws:s3:::kisaantic-knowledge-*/*",
                            "arn:aws:s3:::kisaantic-kb-*",
                            "arn:aws:s3:::kisaantic-kb-*/*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["aoss:APIAccessAll"],
                        "Resource": [f"arn:aws:aoss:{self.region}:{self.account_id}:collection/*"]
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["bedrock:InvokeModel"],
                        "Resource": [f"arn:aws:bedrock:{self.region}::foundation-model/*"]
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="KnowledgeBaseCustomPolicy",
                PolicyDocument=json.dumps(custom_policy)
            )
            logger.info(f"Updated policy for role: {role_name}")
            
            # Wait for role to propagate
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            logger.error(f"Error managing role: {str(e)}")
            raise
    
    def create_opensearch_collection(self, collection_name: str, role_arn: str) -> str:
        """
        Create OpenSearch Serverless collection for Knowledge Base
        
        Args:
            collection_name: Name of the collection
            role_arn: IAM role ARN for access
            
        Returns:
            Collection ARN
        """
        collection_name_lower = collection_name.lower().replace('_', '-')
        
        try:
            # Check if collection exists
            try:
                response = self.aoss_client.batch_get_collection(names=[collection_name_lower])
                if response['collectionDetails']:
                    logger.info(f"Collection {collection_name_lower} already exists")
                    return response['collectionDetails'][0]['arn']
            except:
                pass
            
            # Create encryption policy
            encryption_policy = {
                "Rules": [{
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name_lower}"]
                }],
                "AWSOwnedKey": True
            }
            
            try:
                self.aoss_client.create_security_policy(
                    name=f"{collection_name_lower}-encryption",
                    type='encryption',
                    policy=json.dumps(encryption_policy)
                )
                logger.info(f"Created encryption policy for {collection_name_lower}")
            except self.aoss_client.exceptions.ConflictException:
                logger.info(f"Encryption policy already exists for {collection_name_lower}")
            
            # Create network policy (public access for testing)
            network_policy = [{
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name_lower}"]
                    },
                    {
                        "ResourceType": "dashboard",
                        "Resource": [f"collection/{collection_name_lower}"]
                    }
                ],
                "AllowFromPublic": True
            }]
            
            try:
                self.aoss_client.create_security_policy(
                    name=f"{collection_name_lower}-network",
                    type='network',
                    policy=json.dumps(network_policy)
                )
                logger.info(f"Created network policy for {collection_name_lower}")
            except self.aoss_client.exceptions.ConflictException:
                logger.info(f"Network policy already exists for {collection_name_lower}")
            
            # Wait for policies to propagate
            time.sleep(5)
            
            # Create data access policy
            data_policy = [{
                "Rules": [{
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name_lower}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ]
                },
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{collection_name_lower}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ]
                }],
                "Principal": [role_arn, self.sts_client.get_caller_identity()['Arn']]
            }]
            
            try:
                self.aoss_client.create_access_policy(
                    name=f"{collection_name_lower}-access",
                    type='data',
                    policy=json.dumps(data_policy)
                )
                logger.info(f"Created data access policy for {collection_name_lower}")
            except self.aoss_client.exceptions.ConflictException:
                logger.info(f"Data access policy already exists for {collection_name_lower}")
            
            # Wait for policies to propagate
            time.sleep(10)
            
            # Create collection
            response = self.aoss_client.create_collection(
                name=collection_name_lower,
                type='VECTORSEARCH',
                description=f'Vector collection for {collection_name}'
            )
            
            collection_id = response['createCollectionDetail']['id']
            logger.info(f"Creating collection {collection_name_lower} with ID: {collection_id}")
            
            # Wait for collection to be active
            max_attempts = 40
            for attempt in range(max_attempts):
                response = self.aoss_client.batch_get_collection(names=[collection_name_lower])
                if response['collectionDetails']:
                    status = response['collectionDetails'][0]['status']
                    logger.info(f"Collection status: {status} (Attempt {attempt + 1}/{max_attempts})")
                    
                    if status == 'ACTIVE':
                        collection_arn = response['collectionDetails'][0]['arn']
                        endpoint = response['collectionDetails'][0]['collectionEndpoint']
                        logger.info(f"✅ Collection is ACTIVE")
                        logger.info(f"Endpoint: {endpoint}")
                        
                        # Create index in the collection
                        self._create_vector_index(endpoint, collection_name_lower)
                        
                        return collection_arn
                    elif status == 'FAILED':
                        raise Exception("Collection creation failed")
                
                time.sleep(15)
            
            raise Exception("Collection creation timed out")
            
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    def _create_vector_index(self, endpoint: str, collection_name: str):
        """Create vector index in OpenSearch collection"""
        try:
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, self.region, 'aoss')
            
            client = OpenSearch(
                hosts=[{'host': endpoint.replace('https://', ''), 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=300
            )
            
            index_name = f"{collection_name}-index"
            index_body = {
                "settings": {
                    "index.knn": True
                },
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                                "name": "hnsw",
                                "engine": "nmslib",
                                "parameters": {}
                            }
                        },
                        "text": {"type": "text"},
                        "metadata": {"type": "text"}
                    }
                }
            }
            
            if not client.indices.exists(index=index_name):
                client.indices.create(index=index_name, body=index_body)
                logger.info(f"✅ Created index: {index_name}")
            else:
                logger.info(f"Index {index_name} already exists")
                
        except Exception as e:
            logger.warning(f"Index creation note: {str(e)}")
    
    def create_s3_bucket(self, bucket_name: str) -> str:
        """
        Create S3 bucket for knowledge documents
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Bucket name
        """
        try:
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"Bucket {bucket_name} already exists")
                return bucket_name
            except:
                pass
            
            # Create bucket
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            logger.info(f"✅ Created bucket: {bucket_name}")
            return bucket_name
            
        except Exception as e:
            logger.error(f"Error creating bucket: {str(e)}")
            raise
    
    def upload_knowledge_documents(
        self, 
        bucket_name: str, 
        prefix: str, 
        documents: Dict[str, str]
    ):
        """
        Upload knowledge documents to S3
        
        Args:
            bucket_name: S3 bucket name
            prefix: S3 key prefix
            documents: Dictionary of filename -> content
        """
        try:
            for filename, content in documents.items():
                key = f"{prefix}{filename}"
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=content,
                    ContentType='text/plain'
                )
                logger.info(f"Uploaded: {key}")
                
        except Exception as e:
            logger.error(f"Error uploading documents: {str(e)}")
            raise
    
    def create_knowledge_base(self, config: KnowledgeBaseConfig) -> str:
        """
        Create a Bedrock Knowledge Base
        
        Args:
            config: KnowledgeBaseConfig object
            
        Returns:
            Knowledge base ID
        """
        try:
            # Get collection endpoint
            collection_name = f"{config.name.lower()}-collection"
            response = self.aoss_client.batch_get_collection(names=[collection_name])
            
            if not response['collectionDetails']:
                raise Exception(f"Collection {collection_name} not found")
            
            collection_arn = response['collectionDetails'][0]['arn']
            
            # Create knowledge base
            kb_config = {
                'name': config.name,
                'description': config.description,
                'roleArn': config.role_arn,
                'knowledgeBaseConfiguration': {
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{self.region}::foundation-model/{config.embedding_model}'
                    }
                },
                'storageConfiguration': {
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': collection_arn,
                        'vectorIndexName': f'{collection_name}-index',
                        'fieldMapping': {
                            'vectorField': 'vector',
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            }
            
            response = self.bedrock_agent.create_knowledge_base(**kb_config)
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            
            logger.info(f"✅ Created knowledge base: {config.name} (ID: {kb_id})")
            
            # Wait for knowledge base to be ready
            time.sleep(10)
            
            return kb_id
            
        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            raise
    
    def create_data_source(self, kb_id: str, config: KnowledgeBaseConfig) -> str:
        """
        Create data source for knowledge base
        
        Args:
            kb_id: Knowledge base ID
            config: KnowledgeBaseConfig object
            
        Returns:
            Data source ID
        """
        try:
            ds_config = {
                'knowledgeBaseId': kb_id,
                'name': f'{config.name}-DataSource',
                'description': f'S3 data source for {config.name}',
                'dataSourceConfiguration': {
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{config.s3_bucket}',
                        'inclusionPrefixes': [config.s3_prefix]
                    }
                }
            }
            
            response = self.bedrock_agent.create_data_source(**ds_config)
            ds_id = response['dataSource']['dataSourceId']
            
            logger.info(f"✅ Created data source (ID: {ds_id})")
            return ds_id
            
        except Exception as e:
            logger.error(f"Error creating data source: {str(e)}")
            raise
    
    def ingest_data_source(self, kb_id: str, ds_id: str) -> bool:
        """
        Start ingestion job for data source
        
        Args:
            kb_id: Knowledge base ID
            ds_id: Data source ID
            
        Returns:
            Success status
        """
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            logger.info(f"Started ingestion job: {job_id}")
            
            # Wait for ingestion to complete
            max_attempts = 30
            for attempt in range(max_attempts):
                response = self.bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id,
                    ingestionJobId=job_id
                )
                
                status = response['ingestionJob']['status']
                logger.info(f"Ingestion status: {status} (Attempt {attempt + 1}/{max_attempts})")
                
                if status == 'COMPLETE':
                    stats = response['ingestionJob'].get('statistics', {})
                    logger.info(f"✅ Ingestion complete: {stats}")
                    return True
                elif status == 'FAILED':
                    logger.error("❌ Ingestion failed")
                    return False
                
                time.sleep(15)
            
            logger.warning("Ingestion timed out")
            return False
            
        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
            return False


def get_comprehensive_knowledge_documents() -> Dict[str, Dict[str, str]]:
    """
    Get comprehensive agricultural knowledge documents for each agent type
    Includes all sample data, equipment vendors, and market/mandi information
    
    Returns:
        Dictionary mapping agent types to their documents
    """
    return {
        "weather-advisor": {
            "weather_patterns.txt": """
Weather Patterns and Agricultural Decision Making

TEMPERATURE EFFECTS ON CROPS:
- Optimal temperatures for wheat: 15-25°C during vegetative growth, 20-25°C during grain filling
- Rice thrives in 20-35°C, requires 25°C+ for flowering
- Corn needs 18-27°C for optimal growth, sensitive to frost
- Heat stress above 35°C reduces photosynthesis and yield

PRECIPITATION GUIDELINES:
- Wheat requires 400-600mm annual rainfall
- Rice needs 1000-2000mm, distributed throughout growing season
- Corn requires 500-800mm, critical during tasseling and silking
- Drought stress indicators: leaf curling, reduced growth, early senescence

SEASONAL PLANNING:
- Kharif season (June-October): Monsoon-dependent crops like rice, cotton, soybean
- Rabi season (November-March): Winter crops like wheat, gram, mustard
- Zaid season (March-June): Summer crops like watermelon, cucumber
""",
            "climate_adaptation.txt": """
Climate Change Adaptation Strategies for Farmers

CHANGING WEATHER PATTERNS:
- Increased temperature variability
- Irregular rainfall patterns
- More frequent extreme weather events
- Shifting growing seasons

ADAPTATION TECHNIQUES:
1. Crop Selection:
   - Heat-tolerant varieties
   - Drought-resistant cultivars
   - Short-duration crops for changed seasons

2. Water Management:
   - Efficient irrigation systems
   - Rainwater harvesting
   - Mulching for moisture retention

3. Soil Management:
   - Organic matter addition
   - Cover cropping
   - Conservation tillage
"""
        },
        "crop-specialist": {
            "crop_varieties.txt": """
Crop Varieties and Selection Guide for Madhya Pradesh

WHEAT VARIETIES:
- HD 2967: High yielding, disease resistant, 135-140 days maturity
- PBW 343: Semi-dwarf, rust resistant, suitable for late sowing
- MP 3288: Madhya Pradesh special, drought tolerant
- Yield: 25-35 quintals/acre

RICE VARIETIES:
- Pusa Basmati 1121: Premium quality, 145-150 days, export grade
- IR 64: High yield, disease resistant, 120-125 days
- Swarna: Popular variety, 135-140 days
- Yield: 20-30 quintals/acre

SOYBEAN VARIETIES (Major MP Crop):
- JS 335: High yielding, 95-100 days, oil content 20%
- JS 9305: Early maturing, 85-90 days
- JS 20-29: New high-yielding variety
- Yield: 10-15 quintals/acre

GRAM (CHICKPEA) VARIETIES:
- JG 11: High yielding, wilt resistant
- JG 130: Early maturing, 95-100 days
- Yield: 6-8 quintals/acre

COTTON VARIETIES:
- Bt Cotton varieties: Bollworm resistant
- Yield: 8-12 quintals/acre
""",
            "cropping_systems.txt": """
Sustainable Cropping Systems

CROP ROTATION PRINCIPLES:
- Rotate cereals with legumes
- Avoid same family crops consecutively
- Include deep and shallow rooted crops

INTERCROPPING SYSTEMS FOR MP:
- Wheat + Gram: Complementary growth
- Cotton + Green gram: Space optimization
- Soybean + Maize: Risk diversification

CROP ECONOMICS - ROI ANALYSIS:

GRAM (CHICKPEA) - Highest ROI:
- Total Cost: ₹11,800/acre
- Expected Yield: 6.3 quintals/acre
- Market Price: ₹5,650/quintal
- Gross Return: ₹35,595
- Net Profit: ₹23,795/acre
- ROI: 201%

COTTON:
- Total Cost: ₹15,100/acre
- Expected Yield: 5.6 quintals/acre
- Market Price: ₹6,761/quintal
- Gross Return: ₹37,862
- Net Profit: ₹22,762/acre
- ROI: 150%

SOYBEAN:
- Total Cost: ₹12,500/acre
- Expected Yield: 12 quintals/acre
- Market Price: ₹3,988/quintal (current) / MSP: ₹4,892
- Gross Return: ₹47,856 (at current) / ₹58,704 (at MSP)
- Net Profit: ₹35,356 / ₹46,204
- ROI: 283% / 370%

WHEAT:
- Total Cost: ₹14,200/acre
- Expected Yield: 28 quintals/acre
- Market Price: ₹2,513/quintal
- Gross Return: ₹70,364
- Net Profit: ₹56,164/acre
- ROI: 395%
"""
        },
        "pest-manager": {
            "pest_identification.txt": """
Common Agricultural Pests and Diseases

MAJOR INSECT PESTS:

1. Aphids:
   - Symptoms: Yellowing leaves, sticky honeydew, stunted growth
   - Management: Neem spray, predatory insects, resistant varieties

2. Bollworm (Cotton):
   - Symptoms: Circular holes in leaves, damaged bolls
   - Management: Bt cotton, pheromone traps, biological control

3. Stem Borer (Rice/Maize):
   - Symptoms: Dead hearts, white ears in paddy
   - Management: Light traps, egg removal, resistant varieties

4. Pod Borer (Gram):
   - Symptoms: Damaged pods, holes in flowers
   - Management: NPV spray, early sowing, pheromone traps
""",
            "biological_control.txt": """
Biological Pest Control Methods

BENEFICIAL INSECTS:
1. Predators:
   - Ladybird beetles: Control aphids, scale insects
   - Lacewings: Feed on aphids, thrips, mites
   - Spiders: General pest control

2. Parasitoids:
   - Trichogramma: Parasitizes moth eggs
   - Braconid wasps: Attack caterpillars

ORGANIC PEST MANAGEMENT:
- Neem-based products
- Garlic-chili spray
- Marigold as trap crop
- Intercropping with repellent plants
"""
        },
        "soil-analyst": {
            "soil_health.txt": """
Soil Health Assessment and Management for Madhya Pradesh

SOIL HEALTH INDICATORS:
1. Physical Properties:
   - Soil structure and aggregation
   - Bulk density and porosity
   - Water infiltration rate

2. Chemical Properties:
   - pH levels (6.0-7.5 optimal for most crops)
   - Organic carbon content (>0.75% desirable)
   - NPK availability

3. Biological Properties:
   - Microbial biomass
   - Earthworm population
   - Enzyme activities

MP SOIL TYPES:
- Black Cotton Soil (Vertisols): High clay content, good for cotton, soybean
- Red and Yellow Soil: Found in eastern MP, needs organic matter
- Alluvial Soil: River valleys, high fertility
""",
            "organic_matter.txt": """
Organic Matter Management in Agriculture

IMPORTANCE OF ORGANIC MATTER:
- Improves soil structure and aggregation
- Enhances water retention capacity
- Provides slow-release nutrients
- Increases microbial activity

MANAGEMENT PRACTICES:
- Green manuring with Dhaincha, Sesbania
- FYM and compost application (10-15 tons/ha)
- Crop residue incorporation
- Cover cropping

FERTILIZER RECOMMENDATIONS FOR MP:
Wheat: 120:60:40 (N:P:K) kg/ha
Soybean: 20:60:20 + Rhizobium culture
Gram: 20:40:20 (legume needs less N)
Rice: 100:50:50 kg/ha
"""
        },
        "irrigation-expert": {
            "irrigation_scheduling.txt": """
Irrigation Scheduling and Water Management

WATER REQUIREMENT CALCULATION:
Crop Water Requirement (CWR) = ETo × Kc × Area

IRRIGATION METHODS:
1. Surface Irrigation:
   - Border irrigation: 60-70% efficiency
   - Basin irrigation: 50-60% efficiency
   - Furrow irrigation: 50-70% efficiency

2. Drip Irrigation:
   - Efficiency: 85-95%
   - Water saving: 30-50%
   - Best for: Vegetables, orchards, cotton
   - Subsidy available in MP: 50-60%

3. Sprinkler Irrigation:
   - Efficiency: 70-80%
   - Suitable for: All crops, undulating land
   - Subsidy: 50% under PMKSY

CROP-WISE WATER REQUIREMENTS (MP):
- Wheat: 400-500 mm (4-5 irrigations)
- Soybean: Rainfed, 1-2 protective irrigations
- Cotton: 600-700 mm (6-8 irrigations)
- Gram: 1-2 irrigations at critical stages
""",
            "water_conservation.txt": """
Water Conservation Techniques in Agriculture

WATER HARVESTING:
1. Rainwater Harvesting:
   - Farm ponds: 5,000-10,000 cubic meters
   - Check dams for groundwater recharge
   - Rooftop collection

2. Soil Moisture Conservation:
   - Mulching: Reduces evaporation by 50-70%
   - Ridge and furrow system
   - Conservation tillage

EFFICIENT IRRIGATION:
- Deficit irrigation strategies
- Alternate wetting and drying (AWD) in rice
- Critical stage irrigation
- Drip irrigation for water-intensive crops
"""
        }
    }


def get_equipment_vendor_data() -> str:
    """
    Get comprehensive equipment vendor data for Madhya Pradesh
    
    Returns:
        Complete equipment vendor knowledge as string
    """
    return """
COMPREHENSIVE AGRICULTURAL EQUIPMENT & VENDOR DATABASE - MADHYA PRADESH

This knowledge base contains detailed vendor information, equipment pricing, and seasonal availability across Madhya Pradesh including Dewas, Indore, Ujjain, Bhopal, Jabalpur, Panna, and Jaora.

========================================
VENDOR DATABASE BY LOCATION
========================================

DEWAS VENDORS (7 vendors):

1. Shree Gayatri Tractors
Address: Makan No 01, Vrindavan Colony Maxi Road, Dewas 455001
Contact: +91-9516319499, +91-9926086994, +91-8458888336
Email: Pawanchoudhary336@gmail.com
Equipment: Mahindra Tractors & Implements
Price Range: ₹3.5-8 Lakh
Seasonality: Peak demand March-June, Oct-Nov (pre-sowing)

2. MAA ANNAPURNA TRACTORS & MOTORS
Address: 115, Neori Bagli Marg, Opp Tehsil Office, Hatpiplia 455223
Contact: +91-9977753177
Email: lokendrasinghsendhav@gmail.com
Equipment: Mahindra Tractors
Price Range: ₹5-10 Lakh

3. Krushi Tech (Manufacturer)
Address: Industrial Area, Dewas
Equipment: Rotavator, Ploughs, Seeders, Rotary Tiller, Puddler, Gyrovator
Price Range: ₹20,000-1.5 Lakh
Seasonality: Peak during tillage season

4. SAWARIYA MOTORS
Address: Indore-Bhopal Bypass Road, Pragti Nagar, Sonkutch 455118
Contact: +91-9770018984, +91-9424028493
Email: sanwariyamotors95@gmail.com
Equipment: Mahindra Tractors & Implements
Price Range: ₹4-10 Lakh

INDORE VENDORS (8 vendors):

1. Cropking / Kirloskar / Kartar Suppliers
Equipment: Rotavator (Mini to Heavy-Duty 6ft)
Price Range: ₹42,000 (mini) - ₹1.4 Lakh (6ft heavy-duty)
Seasonality: High demand pre-sowing (March-June, Oct-Nov)

2. Satyam Sales India
Address: 26, Gadi Adda Juni, Indore - 452001
Contact: +91-7949329543
GST: Verified
Equipment: Agriculture Machine Parts, Rotavator Parts
Price Range: ₹975-50,000

3. Harsh Trading Corporation
Address: 34/2, Chhotigwaltoli, Indore - 452001
Contact: +91-7948547176
GST: Verified Plus
Equipment: Rotavator Yoke, Tractor Spare Parts, Reaper Parts
Price Range: ₹100-50,000

4. T K Agro Pvt. Ltd.
Address: Sanwer Road, Indore
Equipment: Garden Tractor Cultivator, Soybean Dora Cultivator, V-Blade Cultivator
Price Range: ₹22,375-40,500

5. Dev Enterprise
Address: 57 Bhagwandeen Nagar, New Agrawal Nagar, Indore - 452001
Contact: +91-8047301719
Equipment: Seed Drill Box, Farm Cultivator
Price Range: ₹66-2 Lakh

6. FARMSTEEL MACHINERY PVT. LTD.
Address: A.B. Road, Near Rau Circle, Rau, Indore
Equipment: Powertrac Tractors
Price Range: ₹5-12 Lakh

UJJAIN VENDORS (7 vendors):

1. Shiv Shakti Agroes
Address: Maxi Road, Panwasa Pawasa, Ujjain Town - 456010
Contact: +91-8044464592
Equipment: Agricultural Equipment & Machinery
Price Range: ₹80,400-80,700

2. Patel Brothers
Address: 97, Nikas Road, Patel Nagar, Ujjain - 456006
Contact: +91-8046041616
Equipment: Earth Auger (Red Iron 43x6", 52x10")
Price Range: ₹11,000-12,000
Years in Business: 12+ years

3. Jay Kisan Krishi Yantra
Address: 84, Village Bhomalwas Tehsil Barnagar, Badnagar - 456771
Contact: +91-7942709295
Equipment: Bund Maker (7ft foldable, 25 HP)
Price Range: ₹14,000+

4. Hari Om Krishi Yantra
Address: Hasra No 441, Sub Health Centre Sodang, Ujjain - 456003
Contact: +91-8045206981
Equipment: Agricultural Ridger (Tractor Mounted, 12 inches)
Price Range: ₹25,000+

5. Kamdhenu Agro Industries
Address: 78, State Highway No. 18, Court Chauraha, Barnagar - 456771
Contact: +91-7942616566
Equipment: Land Leveler, Disc Harrow, Agricultural Implements
Price Range: ₹30,000-1 Lakh
Years in Business: 12+ years

6. Pooja Engineering Corporation
Address: 103, Kshir Sagar Complex, Ujjain New Road, Ujjain - 456001
Contact: +91-8046072435
Equipment: Iron Agricultural Equipment, Farm Cultivator
Price Range: ₹1,00,000

7. Balaji Engineering Works
Address: Kanasiya Naka, Maksi, Ujjain - 456770
Contact: +91-8041014050
Equipment: All Agriculture Equipment, Leveller
Years in Business: 14+ years

BHOPAL VENDORS (11 vendors):

1. Shiv Shakti Motors (New Holland)
Address: B-45, Rajdev Colony, Shanti Nagar Road, Bhopal 462001
Equipment: New Holland Tractors
Price Range: ₹5-15 Lakh

2. SAMARTH SERVICES
Address: 892/56/2, Lambakheda, Berasia Road, Bhopal - 468038
GST: Verified (19 years)
Equipment: New Holland Square Baler, Paddy Transplanter
Price Range: ₹2.85 Lakh (transplanter) - ₹14.75 Lakh (baler)

3. Mahaveer Agro Sales
Address: 699, Vir Sawarkar Chowk, Bhopal - 462001
Equipment: Massey Ferguson Tractors
Price Range: ₹6-12 Lakh

4. Shri Dayoday Sales Organisation (Sonalika)
Address: H No 86, Opposite Putthamil Gate, Huzur, Bhopal - 462001
Contact: +91-9893038395
Equipment: Sonalika Tractors & Implements
Price Range: ₹4-10 Lakh
Hours: Mon-Sat 10 AM - 7 PM

5. Pitambara Motors (Mahindra)
Address: Ground Floor, Islam Nagar, Bhopal - 462038
Contact: +91-8037908209
Equipment: Mahindra Tractors & Implements
Rating: 4.9/5 (38 reviews)
Price Range: ₹5-12 Lakh

JABALPUR VENDORS (19+ dealers):

1. Multiple Tractor Dealers:
- TractorJunction lists 19+ authorized dealers
- All major brands: Mahindra, John Deere, New Holland, Sonalika
- Price Range: ₹3.5-20 Lakh

EQUIPMENT RENTAL SERVICES:

Available across all major cities:
- Tractor rental: ₹600-1,200/day
- Rotavator rental: ₹800-1,500/acre
- Harvester rental: ₹1,200-1,800/acre
- Minimum booking: 4-8 hours

========================================
EQUIPMENT CATEGORIES & PRICING
========================================

TRACTORS:
Mini Tractors (15-25 HP): ₹2.5-4.5 Lakh
Small Tractors (25-35 HP): ₹4-6.5 Lakh
Medium Tractors (35-50 HP): ₹6-10 Lakh
Large Tractors (50-60 HP): ₹10-15 Lakh
Premium Tractors (60+ HP): ₹15-25 Lakh

Major Brands: Mahindra, Sonalika, New Holland, John Deere, Massey Ferguson, Powertrac

TILLAGE EQUIPMENT:
Rotavator Mini: ₹42,000-70,000
Rotavator Standard: ₹70,000-1.4 Lakh
Cultivator (5 Tynes): ₹22,375
Cultivator (7-9 Tynes): ₹38,000-55,000
Disc Harrow: ₹30,000-80,000
Land Leveler: ₹30,000-1 Lakh
Ploughs: ₹15,000-45,000

SEEDING EQUIPMENT:
Seed Drill Manual: ₹38,000-55,000
Seed Drill Tractor (7-9 tine): ₹50,000-75,000
Seed Drill Box: ₹66+
Rice Transplanter (4-row): ₹2.85 Lakh
Rice Transplanter (6-row): ₹3.95 Lakh

CROP PROTECTION:
Manual Sprayer: ₹2,500-8,000
Knapsack Sprayer: ₹5,000-20,000
Motorized Sprayer: ₹77,000-1,05,000
Tractor Mounted Sprayer: ₹1.5-5 Lakh

HARVESTING EQUIPMENT:
Combine Harvester: ₹10-25 Lakh
Reaper: ₹80,000-2.5 Lakh
Square Baler: ₹11-16 Lakh

WATER MANAGEMENT:
Water Pump (5 HP): ₹15,000-30,000
Drip System (per acre): ₹35,000-60,000
Sprinkler System (per acre): ₹25,000-45,000

========================================
SEASONALITY & BUYING GUIDE
========================================

PEAK DEMAND PERIODS (Higher Prices 10-15%):
- March-June: Pre-Kharif preparation
- October-November: Pre-Rabi preparation
- May-June: Highest prices

OFF-SEASON (Best Prices 15-20% savings):
- January-February
- August
- Post-monsoon (September)

FESTIVE OFFERS:
- Diwali (October): Up to 15% discounts
- Year-end clearance: December

FINANCING OPTIONS:
Available from:
- Mahindra Finance
- John Deere Financial
- Bank loans (7-9% interest)
- Manufacturer schemes during peak seasons

========================================
SUBSIDY INFORMATION (MADHYA PRADESH)
========================================

ELIGIBILITY:
- Small & Marginal Farmers: Up to 60% subsidy
- Other Farmers: Up to 40% subsidy
- Women Farmers: Additional 5-10% subsidy

EQUIPMENT COVERED:
- Tractors: 25-40% subsidy
- Drip/Sprinkler: 50-60% subsidy
- Farm Implements: 40-50% subsidy
- Processing Equipment: 40-50% subsidy

APPLICATION:
- Online Portal: Krishiyantra Anudan Portal (MP Government)
- Windows: Typically May-July (Kharif), November-January (Rabi)
- Documents Required: Land records, Aadhaar, Bank details

CONTACT FOR SUBSIDY:
- District Agriculture Office
- Krishi Vigyan Kendra (KVK)
- Mandi Office

========================================
FARM SIZE-WISE RECOMMENDATIONS
========================================

SMALL FARMERS (Under 5 acres, Budget: ₹50,000-3 Lakh):
Priority Equipment:
1. Mini Power Tiller (5-8 HP): ₹49,000-70,000
2. Manual Seed Drill: ₹38,000-55,000
3. Knapsack Sprayer: ₹5,000-20,000
4. Manual Weeder: ₹2,500-5,000
Best Time: Off-season (Feb-March, August)
Subsidy: 50-60%
Consider: Used equipment, rental services

MEDIUM FARMERS (5-15 acres, Budget: ₹3-10 Lakh):
Priority Equipment:
1. Mini Tractor (25-35 HP): ₹3-6 Lakh
2. Standard Rotavator: ₹45,000-80,000
3. Seed Drill (7-9 tine): ₹50,000-75,000
4. Power Weeder (5-7 HP): ₹32,500-66,000
5. Motorized Sprayer: ₹77,000-1,05,000
Best Time: Festive season (October), Off-season
Vendors: Mahindra, Sonalika, Indo Farm dealers

LARGE FARMERS (Over 15 acres, Budget: ₹10 Lakh+):
Priority Equipment:
1. Tractor (45-60 HP): ₹8-15 Lakh
2. Combine Harvester: ₹10-25 Lakh
3. Rice Transplanter (6-row): ₹3.95 Lakh
4. Tractor Mounted Sprayer: ₹1.5-5 Lakh
5. Balers/Processing: ₹11-16 Lakh
Best Time: Off-season, bulk discounts
Vendors: New Holland, John Deere (Bhopal, Indore)

========================================
IMPORTANT GUIDANCE FOR RECOMMENDATIONS
========================================

When recommending equipment:
1. ALWAYS use farmer's GPS coordinates to find nearest vendors
2. Consider farm size and budget constraints
3. Mention current season and optimal buying time
4. Include subsidy information prominently
5. Provide purchase vs rental economics
6. Give complete vendor contact details
7. Include specific models and prices
8. Warn about price increases during peak seasons
9. Suggest multiple vendors for comparison
10. Consider crop type and farming practices

CRITICAL: Provide specific vendor names, addresses, phone numbers, and current prices from this database. Do not make estimates - use actual data provided here.

Data Current as of: October 2024-2025
Source: Vendor listings, market surveys, government schemes
"""


def get_market_mandi_data() -> str:
    """
    Get comprehensive market and mandi price data for Madhya Pradesh
    
    Returns:
        Complete market data as string
    """
    return """
COMPREHENSIVE MARKET & MANDI PRICE DATA - MADHYA PRADESH

Current mandi prices, market locations, MSP rates, and selling strategies for farmers across Madhya Pradesh.

========================================
CURRENT MANDI PRICES (October 2024-2025)
========================================

MAJOR CROPS - CURRENT MARKET RATES:

WHEAT:
- Average Price: ₹2,513/quintal
- Price Range: ₹2,400-3,000/quintal
- MSP 2024-25: ₹2,425/quintal
- Status: Trading ABOVE MSP ✓
- Recommendation: Sell in open market for better price
- Market Trend: Stable to slightly increasing

SOYBEAN (CRITICAL ALERT):
- Average Price: ₹3,988/quintal
- Price Range: ₹3,700-4,230/quintal
- MSP 2024-25: ₹4,892/quintal
- Status: Trading 18% BELOW MSP ⚠️
- Market Arrivals: Down 56% from Oct 2023
- Recommendation: WAIT for government procurement
- Farmer Alert: DO NOT sell at current distressed prices
- Expected Government Action: MSP procurement likely to start soon

COTTON (Without Ginned):
- Average Price: ₹6,761/quintal
- Price Range: ₹6,200-7,585/quintal
- MSP 2024-25: ₹7,121/quintal
- Status: Trading BELOW MSP
- Recommendation: Government procurement via CCI advisable
- Quality Requirements: Ensure proper ginning and grading

GRAM (Chickpea):
- Average Price: ₹5,650/quintal
- Price Range: ₹5,000-6,860/quintal
- MSP 2024-25: ₹5,650/quintal
- Status: Trading AT MSP
- Recommendation: Either market or government option viable
- Market Trend: Stable demand

KABULI CHANA:
- Average Price: ₹7,504/quintal
- Price Range: ₹4,305-9,600/quintal (wide variation)
- High price variation across markets
- Recommendation: Compare 3-4 mandis before selling

RICE (Paddy):
- Common Variety: ₹2,300/quintal
- Grade A: ₹2,320/quintal
- MSP 2024-25: ₹2,300/quintal
- Status: Trading AT MSP
- Recommendation: Government procurement reliable

MAIZE:
- Average Price: ₹1,651/quintal
- Price Range: ₹1,200-2,600/quintal
- No MSP
- Recommendation: Sell at highest available mandi

JOWAR (Sorghum):
- Average Price: ₹2,400/quintal
- Hybrid MSP: ₹3,180/quintal
- Maldandi MSP: ₹3,300/quintal
- Check variety before selling

BAJRA:
- Average Price: ₹2,625/quintal
- MSP 2024-25: ₹2,625/quintal
- Status: Trading AT MSP

========================================
MSP RATES 2024-2025 (Complete List)
========================================

KHARIF CROPS:
- Paddy (Common): ₹2,300/quintal
- Paddy (Grade A): ₹2,320/quintal
- Jowar (Hybrid): ₹3,180/quintal
- Jowar (Maldandi): ₹3,300/quintal
- Bajra: ₹2,625/quintal
- Maize: ₹2,225/quintal
- Ragi: ₹4,290/quintal
- Arhar (Tur): ₹7,550/quintal
- Moong: ₹8,682/quintal
- Urad: ₹7,400/quintal
- Cotton (Medium Staple): ₹7,121/quintal
- Cotton (Long Staple): ₹7,521/quintal
- Groundnut: ₹6,783/quintal
- Sunflower: ₹7,280/quintal
- Soybean (Yellow): ₹4,892/quintal
- Soybean (Black): ₹5,361/quintal
- Sesamum: ₹8,635/quintal
- Niger Seed: ₹8,027/quintal

RABI CROPS:
- Wheat: ₹2,425/quintal
- Barley: ₹1,980/quintal
- Gram: ₹5,650/quintal
- Masoor (Lentil): ₹6,700/quintal
- Rapeseed/Mustard: ₹5,650/quintal
- Safflower: ₹5,800/quintal

========================================
MAJOR MANDI LOCATIONS (MADHYA PRADESH)
========================================

BHOPAL REGION:

1. Bhopal Mandi
Address: Govindpura, Bhopal
Contact: +91-755-2764222
Distance from city: 8 km
Operating Days: Monday to Saturday
Major Crops: Wheat, Gram, Soybean
Facilities: Warehousing, Quality testing
Market Fee: 2.5%

2. Berasia Mandi
Distance from Bhopal: 35 km
Crops: Wheat, Soybean, Gram
Operating Days: Daily except Sunday

INDORE REGION:

1. Indore Mandi (Main)
Address: Agricultural Produce Market Committee, Indore
Contact: +91-731-2720001
Distance: City center
Major Crops: Wheat, Soybean, Cotton, Gram
Facilities: Modern infrastructure, electronic weighing
Market Fee: 2.5%
Commission: 2%

2. Mhow Mandi
Distance from Indore: 23 km
Crops: Wheat, Soybean, Vegetables

UJJAIN REGION:

1. Ujjain Mandi
Contact: +91-734-2511111
Major Crops: Soybean, Wheat, Gram
Facilities: Cold storage, processing units

DEWAS REGION:

1. Dewas Mandi
Distance from Bhopal: 140 km
Crops: Soybean, Wheat, Gram
Known for: High soybean arrivals

JABALPUR REGION:

1. Jabalpur Mandi
Major Crops: Rice, Wheat, Pulses
Facilities: Government procurement center

========================================
GOVERNMENT PROCUREMENT CENTERS
========================================

MADHYA PRADESH STATE WAREHOUSING CORPORATION:

Major Centers:
- Bhopal
- Indore
- Jabalpur
- Gwalior
- Ujjain

Contact: +91-755-2578742
Website: mpwc.mp.gov.in

NAFED (National Agricultural Cooperative):
- Procurement of pulses, oilseeds
- Contact through district cooperative offices

COTTON CORPORATION OF INDIA (CCI):
- Cotton procurement at MSP
- Operating in all major cotton growing districts
- Contact: District CCI offices

FOOD CORPORATION OF INDIA (FCI):
- Wheat and rice procurement
- Registration through gram panchayat
- Payment within 48-72 hours

========================================
MANDI COMMISSION & CHARGES
========================================

STANDARD CHARGES:

Market Fee (Mandi Tax): 2-3% of sale value
Commission Agent (Arhatiya): 2-2.5%
Loading/Unloading: ₹10-20/quintal
Weighing Charges: ₹5-10/quintal
Cleaning Charges: ₹15-25/quintal (if needed)

Total Deductions: 5-8% of gross sale value

EXAMPLE CALCULATION:
Sale of 20 quintals Soybean @ ₹4,000/quintal
Gross Value: ₹80,000
Market Fee (2.5%): ₹2,000
Commission (2%): ₹1,600
Other Charges: ₹500
Total Deductions: ₹4,100
Net Realization: ₹75,900
Net Rate: ₹3,795/quintal

========================================
QUALITY REQUIREMENTS FOR BETTER PRICES
========================================

WHEAT:
- Moisture: Maximum 12%
- Foreign Matter: Maximum 2%
- Damaged/Shrivelled: Maximum 3%
- Minimum Test Weight: 78 kg/hl

SOYBEAN:
- Moisture: Maximum 12%
- Oil Content: Minimum 18%
- Split/Broken: Maximum 10%
- Foreign Matter: Maximum 2%

GRAM:
- Moisture: Maximum 12%
- Foreign Matter: Maximum 2%
- Damaged: Maximum 3%
- Bold grain preferred

COTTON:
- Moisture: 8-10%
- Trash Content: Minimum
- Staple Length: As per variety
- Color: Bright white preferred

========================================
SEASONAL PRICE PATTERNS
========================================

POST-HARVEST (Immediate):
- Prices 10-15% lower due to high supply
- Duration: 2-4 weeks after harvest
- Strategy: Avoid selling if possible

MID-SEASON (2-3 months):
- Prices stabilize or improve
- Market arrivals reduce
- Good time for selling if cash needed

PRE-NEXT-SEASON (4-6 months):
- Prices often 15-25% higher
- Lower market supply
- Best time for stored produce

========================================
CURRENT MARKET ALERTS (Oct 2024-2025)
========================================

SOYBEAN CRISIS:
⚠️ Arrivals down 56% from Oct 2023
⚠️ Prices 18% below MSP
⚠️ Farmers holding stock for government intervention
✓ Recommendation: WAIT for MSP procurement announcement
✓ Do NOT panic sell at current prices

COTTON ADVISORY:
⚠️ Prices ₹300-400 below MSP
⚠️ Government procurement expected soon
✓ Ensure proper quality for best CCI rates
✓ Register with nearest CCI center

WHEAT OPPORTUNITY:
✓ Market trading above MSP
✓ Good time to sell stored wheat
✓ Stable prices expected through November
✓ High demand from private buyers

========================================
TRANSPORTATION COSTS
========================================

WITHIN DISTRICT (0-50 km):
- Small vehicle (1-2 quintals): ₹500-1,000
- Tractor trolley (20-30 quintals): ₹800-1,500
- Truck (100+ quintals): ₹3,000-5,000

INTER-DISTRICT (50-150 km):
- Tractor trolley: ₹2,000-3,500
- Small truck: ₹5,000-8,000
- Large truck: ₹10,000-15,000

========================================
STORAGE OPTIONS
========================================

GOVERNMENT WAREHOUSES:
- Rent: ₹2-3/quintal/month
- Location: District headquarters
- Booking: FCI or State Warehousing Corp
- Security: Government backed

PRIVATE WAREHOUSES:
- Rent: ₹3-5/quintal/month
- Better availability
- Flexible terms
- Insurance available

ON-FARM STORAGE:
- Investment: ₹5,000-20,000
- Saves transportation and rent
- Requires pest control
- Risk of quality deterioration

========================================
GOVERNMENT SCHEMES
========================================

PM-AASHA (Price Support Scheme):
- MSP procurement for all notified crops
- No quantity limit for small farmers
- Direct bank payment
- Registration through e-NAM

PRICE DEFICIENCY PAYMENT:
- Compensates MSP-market difference
- No need to sell to government
- Available in select states
- Register through e-NAM portal

MARKET INTERVENTION SCHEME:
- For crops without MSP
- Government procures when prices crash
- Request through District Collector

e-NAM PLATFORM:
- Online trading platform
- Transparent price discovery
- Wider market access
- Registration through mandi office
- Benefits: Better prices, reduced intermediaries

========================================
DIRECT BUYER OPTIONS
========================================

CORPORATE BUYERS:

ITC e-Choupal:
- Crops: Wheat, Soybean
- Minimum: 10 quintals
- Payment: Within 48 hours
- Quality premium available

Adani Wilmar:
- Crops: Soybean, Mustard
- Direct procurement centers
- Quality-based pricing

Cargill India:
- Crops: Wheat, Soybean, Maize
- Bulk procurement
- Contract farming available

FARMER PRODUCER ORGANIZATIONS (FPOs):
- Better price negotiation
- Reduced costs
- Lower commission: 1-2% vs 3-5%
- Contact District Agriculture Office

========================================
SELLING STRATEGY GUIDE
========================================

BEFORE HARVEST:
1. Monitor daily mandi prices
2. Understand quality parameters
3. Plan harvest timing
4. Arrange storage if needed
5. Register for govt procurement

DURING HARVEST:
1. Ensure proper drying
2. Grade produce properly
3. Avoid damaged lots
4. Harvest in dry weather

SELLING DECISION:
1. Compare 3-4 nearby mandis
2. Check market vs MSP price
3. Consider all charges
4. Calculate net realization
5. Decide: Sell/Store/Govt procurement

AT MANDI:
1. Reach early morning
2. Accurate weighing
3. Proper quality sampling
4. Get receipt/SMS
5. Verify bank credit

========================================
REVENUE CALCULATOR
========================================

FORMAT FOR FARMERS:

Expected Yield: [X] quintals
Best Mandi Price: ₹[Y]/quintal
Gross Revenue: ₹[X × Y]

LESS: Costs
- Transportation: ₹[amount]
- Mandi Charges (6%): ₹[0.06 × gross]
- Total Deductions: ₹[sum]

NET REALIZATION: ₹[gross - deductions]
Net Rate/Quintal: ₹[net/quintals]

COMPARE WITH:
- MSP: ₹[MSP rate]
- Govt Procurement Net: ₹[MSP - minimal charges]

RECOMMENDATION: [Specific action]

========================================
CRITICAL GUIDANCE FOR RESPONSES
========================================

When providing market guidance:

1. ALWAYS mention current price vs MSP
2. Provide specific mandi names with distances
3. Calculate net realization after charges
4. Give revenue estimates based on yield
5. Explain WHY a strategy is recommended
6. Mention quality requirements prominently
7. Alert about market distress situations
8. Provide govt procurement details if needed
9. Include contact numbers
10. Consider seasonal timing

FOR DISTRESSED FARMERS:
- Acknowledge their situation
- Provide clear govt procurement guidance
- Suggest holding if feasible
- Warn against panic selling
- Provide data on price recovery patterns

CRITICAL: Use exact current prices from this database. Always compare with MSP. Provide actionable recommendations based on whether price is above, at, or below MSP.

Data Current as of: October 2024-2025
Source: Official Mandi Data, Government MSP Notifications, Agricultural Market Intelligence
"""


def setup_kisaantic_knowledge_bases() -> Dict:
    """
    Main function to set up all Kisaantic AI Knowledge Bases with comprehensive data
    
    Returns:
        Dictionary with created knowledge base details
    """
    print("\n" + "="*80)
    print("KISAANTIC AI - COMPLETE KNOWLEDGE BASE SETUP")
    print("Creating 5 Agricultural AI Knowledge Bases with Complete Data")
    print("="*80 + "\n")
    
    # Initialize manager
    manager = BedrockKnowledgeBaseManager()
    
    # Create IAM role
    print("📋 Creating IAM Role...")
    role_arn = manager.create_knowledge_base_role("BedrockKnowledgeBaseRole")
    print(f"✅ Role ARN: {role_arn}\n")
    
    # Wait for role propagation
    time.sleep(15)
    
    # Define knowledge bases
    knowledge_bases = {
        "weather-advisor": KnowledgeBaseConfig(
            name="WeatherAdvisor",
            description="Weather patterns, forecasting, and climate adaptation",
            role_arn=role_arn,
            s3_bucket="kisaantic-kb-weather-aps1",
            s3_prefix="weather/"
        ),
        "crop-specialist": KnowledgeBaseConfig(
            name="CropSpecialist",
            description="Crop varieties, cultivation, market prices, equipment vendors, and ROI analysis",
            role_arn=role_arn,
            s3_bucket="kisaantic-kb-crops-aps1",
            s3_prefix="crops/"
        ),
        "pest-manager": KnowledgeBaseConfig(
            name="PestManager",
            description="Pest and disease identification and management",
            role_arn=role_arn,
            s3_bucket="kisaantic-kb-pests-aps1",
            s3_prefix="pests/"
        ),
        "soil-analyst": KnowledgeBaseConfig(
            name="SoilAnalyst",
            description="Soil health, nutrients, and fertility management",
            role_arn=role_arn,
            s3_bucket="kisaantic-kb-soil-aps1",
            s3_prefix="soil/"
        ),
        "irrigation-expert": KnowledgeBaseConfig(
            name="IrrigationExpert",
            description="Water management, irrigation systems, and conservation",
            role_arn=role_arn,
            s3_bucket="kisaantic-kb-irrigation-aps1",
            s3_prefix="irrigation/"
        )
    }
    
    # Get sample documents
    knowledge_documents = get_comprehensive_knowledge_documents()
    
    # Add equipment and market data to crop-specialist
    equipment_data = get_equipment_vendor_data()
    market_data = get_market_mandi_data()
    
    knowledge_documents["crop-specialist"]["equipment_vendors_mp.txt"] = equipment_data
    knowledge_documents["crop-specialist"]["market_mandi_prices_mp.txt"] = market_data
    
    # Create knowledge bases
    created_knowledge_bases = {}
    
    for kb_name, config in knowledge_bases.items():
        try:
            print(f"\n{'='*80}")
            print(f"Creating Knowledge Base: {kb_name}")
            print(f"{'='*80}\n")
            
            # Step 1: Create S3 bucket
            print(f"1️⃣ Creating S3 bucket: {config.s3_bucket}")
            manager.create_s3_bucket(config.s3_bucket)
            
            # Step 2: Upload knowledge documents
            print(f"2️⃣ Uploading knowledge documents")
            if kb_name in knowledge_documents:
                doc_count = len(knowledge_documents[kb_name])
                print(f"   Uploading {doc_count} documents...")
                manager.upload_knowledge_documents(
                    config.s3_bucket,
                    config.s3_prefix,
                    knowledge_documents[kb_name]
                )
            
            # Step 3: Create OpenSearch collection
            print(f"3️⃣ Creating OpenSearch collection")
            collection_arn = manager.create_opensearch_collection(
                f"{config.name}-collection",
                role_arn
            )
            
            # Step 4: Create knowledge base
            print(f"4️⃣ Creating Bedrock Knowledge Base")
            kb_id = manager.create_knowledge_base(config)
            
            # Step 5: Create data source
            print(f"5️⃣ Creating data source")
            ds_id = manager.create_data_source(kb_id, config)
            
            # Step 6: Start ingestion
            print(f"6️⃣ Starting data ingestion")
            success = manager.ingest_data_source(kb_id, ds_id)
            
            if success:
                created_knowledge_bases[kb_name] = {
                    "knowledge_base_id": kb_id,
                    "data_source_id": ds_id,
                    "collection_arn": collection_arn,
                    "s3_bucket": config.s3_bucket,
                    "status": "ready"
                }
                print(f"\n✅ Successfully created knowledge base: {kb_name}")
            else:
                logger.error(f"❌ Failed to ingest data for: {kb_name}")
                
        except Exception as e:
            logger.error(f"❌ Error creating knowledge base {kb_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return created_knowledge_bases


def main():
    """Main execution function"""
    print("\n🚀 Kisaantic AI - Complete Knowledge Base Setup")
    print("This will create 5 specialized knowledge bases including:")
    print("  • Weather patterns and climate data")
    print("  • Crop varieties and cultivation practices")
    print("  • Pest and disease management")
    print("  • Soil health and fertility")
    print("  • Irrigation and water management")
    print("  • Equipment vendors and pricing (Madhya Pradesh)")
    print("  • Market prices and mandi information")
    print("  • ROI calculations and crop economics\n")
    
    confirm = input("Do you want to continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Setup cancelled.")
        return
    
    try:
        result = setup_kisaantic_knowledge_bases()
        
        print("\n" + "="*80)
        print("📋 FINAL RESULTS")
        print("="*80 + "\n")
        
        if result:
            print("✅ Successfully Created Knowledge Bases:")
            for name, details in result.items():
                print(f"  • {name}: {details['knowledge_base_id']}")
            
            # Save configuration
            config_file = "knowledge_base_config.json"
            with open(config_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n✅ Configuration saved to: {config_file}")
            print(f"✅ Total knowledge bases created: {len(result)}/5")
            print("\n📌 Next Steps:")
            print("  1. Run setup_agents.py to create AI agents")
            print("  2. Agents will use these knowledge bases for enhanced responses")
            print("  3. crop-specialist KB includes equipment vendors & market data")
        else:
            print("❌ No knowledge bases were created successfully")
            print("Please check the error messages above")
            
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()