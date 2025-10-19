"""
Create Lambda execution role with proper trust policy
"""

import boto3
import json
import time
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_lambda_execution_role():
    """Create IAM role for Lambda with proper trust relationship"""
    
    iam_client = boto3.client('iam')
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    
    role_name = 'KisaanticLambdaExecutionRole'
    
    # Trust policy allowing Lambda to assume the role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Permissions policy
    permissions_policy = {
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
                    "bedrock:InvokeAgent",
                    "bedrock:InvokeModel"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Try to get existing role
        response = iam_client.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        logger.info(f"✅ Using existing role: {role_arn}")
        return role_arn
        
    except iam_client.exceptions.NoSuchEntityException:
        logger.info(f"Creating new role: {role_name}")
        
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Execution role for Kisaantic Lambda functions'
        )
        
        role_arn = response['Role']['Arn']
        logger.info(f"✅ Created role: {role_arn}")
        
        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='KisaanticLambdaPermissions',
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        logger.info("✅ Attached permissions policy")
        
        # Wait for role to propagate
        logger.info("⏳ Waiting 10 seconds for role to propagate...")
        time.sleep(10)
        
        return role_arn

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔐 Creating Lambda Execution Role")
    print("="*70 + "\n")
    
    role_arn = create_lambda_execution_role()
    
    print("\n" + "="*70)
    print("✅ Role Ready")
    print("="*70)
    print(f"\nRole ARN: {role_arn}")
    print("\nUse this role in setup_agent_core.py")