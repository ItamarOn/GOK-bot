#!/bin/bash

set -e

# Configuration
ROLE_NAME="${LAMBDA_ROLE_NAME:-lambda-execution-role}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔐 Setting up IAM role for Lambda...${NC}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Failed to get AWS account ID. Make sure AWS CLI is configured.${NC}"
    exit 1
fi

# Trust policy for Lambda
TRUST_POLICY='{
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
}'

# Check if role exists
if aws iam get-role --role-name "${ROLE_NAME}" 2>/dev/null; then
    echo -e "${GREEN}✅ IAM role '${ROLE_NAME}' already exists${NC}"
else
    echo -e "${YELLOW}📝 Creating IAM role '${ROLE_NAME}'...${NC}"
    aws iam create-role \
        --role-name "${ROLE_NAME}" \
        --assume-role-policy-document "${TRUST_POLICY}" \
        --description "Execution role for GOK Bot Lambda function"
    echo -e "${GREEN}✅ IAM role created${NC}"
fi

# Attach basic Lambda execution policy
echo -e "${YELLOW}📎 Attaching AWS managed policy...${NC}"
aws iam attach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# If you need VPC access, ECR access, or other permissions, add them here
# For example, if your Lambda needs to access VPC resources:
# aws iam attach-role-policy \
#     --role-name "${ROLE_NAME}" \
#     --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

echo -e "${GREEN}✅ IAM role setup complete!${NC}"
echo -e "${GREEN}Role ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}${NC}"

