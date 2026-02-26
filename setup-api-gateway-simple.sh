#!/bin/bash

set -e

# Configuration
LAMBDA_FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-gok-bot-lambda}"
AWS_REGION="${AWS_REGION:-us-east-1}"
API_NAME="${API_NAME:-gok-bot-api}"
STAGE_NAME="${STAGE_NAME:-prod}"
API_KEY_NAME="${API_KEY_NAME:-gok-bot-api-key}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🌐 Setting up API Gateway for public access with API key authentication...${NC}"

# Verify Lambda exists
echo -e "${YELLOW}🔍 Verifying Lambda function exists...${NC}"
if ! aws lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" --region "${AWS_REGION}" > /dev/null 2>&1; then
    echo -e "${RED}❌ Lambda function '${LAMBDA_FUNCTION_NAME}' not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Lambda function found${NC}"

# Get AWS account ID and Lambda ARN
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_FUNCTION_NAME}"

# Step 1: Create or get REST API
echo -e "${YELLOW}📝 Step 1: Creating REST API...${NC}"
EXISTING_API_ID=$(aws apigateway get-rest-apis \
    --region "${AWS_REGION}" \
    --query "items[?name=='${API_NAME}'].id" \
    --output text | head -1)

if [ -n "$EXISTING_API_ID" ] && [ "$EXISTING_API_ID" != "None" ]; then
    echo -e "${YELLOW}⚠️  API '${API_NAME}' already exists, using existing API${NC}"
    API_ID="$EXISTING_API_ID"
else
    API_ID=$(aws apigateway create-rest-api \
        --name "${API_NAME}" \
        --description "API Gateway for GOK Bot Lambda" \
        --endpoint-configuration types=REGIONAL \
        --region "${AWS_REGION}" \
        --query 'id' \
        --output text)
fi

echo -e "${GREEN}✅ API ID: ${API_ID}${NC}"

# Step 2: Get root resource ID
echo -e "${YELLOW}📝 Step 2: Getting root resource...${NC}"
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "${API_ID}" \
    --region "${AWS_REGION}" \
    --query 'items[?path==`/`].id' \
    --output text)

# Step 3: Create proxy resource (catches all paths)
echo -e "${YELLOW}📝 Step 3: Creating proxy resource...${NC}"
EXISTING_PROXY=$(aws apigateway get-resources \
    --rest-api-id "${API_ID}" \
    --region "${AWS_REGION}" \
    --query "items[?path=='/{proxy+}'].id" \
    --output text | head -1)

if [ -n "$EXISTING_PROXY" ] && [ "$EXISTING_PROXY" != "None" ]; then
    PROXY_RESOURCE_ID="$EXISTING_PROXY"
    echo -e "${YELLOW}⚠️  Proxy resource already exists${NC}"
else
    PROXY_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id "${API_ID}" \
        --parent-id "${ROOT_RESOURCE_ID}" \
        --path-part "{proxy+}" \
        --region "${AWS_REGION}" \
        --query 'id' \
        --output text)
fi

# Also create root method for direct root access
echo -e "${YELLOW}📝 Step 4: Setting up methods...${NC}"

# Setup ANY method on proxy
aws apigateway put-method \
    --rest-api-id "${API_ID}" \
    --resource-id "${PROXY_RESOURCE_ID}" \
    --http-method ANY \
    --authorization-type NONE \
    --api-key-required \
    --region "${AWS_REGION}" > /dev/null 2>&1 || echo "Method might already exist"

# Setup integration for proxy
aws apigateway put-integration \
    --rest-api-id "${API_ID}" \
    --resource-id "${PROXY_RESOURCE_ID}" \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region "${AWS_REGION}" > /dev/null

# Setup root method (for /health, etc.)
aws apigateway put-method \
    --rest-api-id "${API_ID}" \
    --resource-id "${ROOT_RESOURCE_ID}" \
    --http-method ANY \
    --authorization-type NONE \
    --api-key-required \
    --region "${AWS_REGION}" > /dev/null 2>&1 || echo "Root method might already exist"

aws apigateway put-integration \
    --rest-api-id "${API_ID}" \
    --resource-id "${ROOT_RESOURCE_ID}" \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region "${AWS_REGION}" > /dev/null

# Step 5: Grant API Gateway permission to invoke Lambda
echo -e "${YELLOW}📝 Step 5: Granting API Gateway permission to invoke Lambda...${NC}"
SOURCE_ARN="arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*"
aws lambda add-permission \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --statement-id "apigateway-invoke-$(date +%s)" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "${SOURCE_ARN}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || echo "Permission might already exist"

# Step 6: Deploy API
echo -e "${YELLOW}📝 Step 6: Deploying API...${NC}"
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id "${API_ID}" \
    --stage-name "${STAGE_NAME}" \
    --description "Deployment $(date +%Y-%m-%d-%H-%M-%S)" \
    --region "${AWS_REGION}" \
    --query 'id' \
    --output text 2>/dev/null)

if [ -z "$DEPLOYMENT_ID" ]; then
    echo -e "${YELLOW}⚠️  Creating new deployment...${NC}"
    DEPLOYMENT_ID=$(aws apigateway create-deployment \
        --rest-api-id "${API_ID}" \
        --stage-name "${STAGE_NAME}" \
        --description "Updated $(date +%Y-%m-%d-%H-%M-%S)" \
        --region "${AWS_REGION}" \
        --query 'id' \
        --output text)
fi

# Step 7: Create API key
echo -e "${YELLOW}📝 Step 7: Creating API key...${NC}"
EXISTING_KEY_ID=$(aws apigateway get-api-keys \
    --region "${AWS_REGION}" \
    --query "items[?name=='${API_KEY_NAME}'].id" \
    --output text | head -1)

if [ -n "$EXISTING_KEY_ID" ] && [ "$EXISTING_KEY_ID" != "None" ]; then
    echo -e "${YELLOW}⚠️  API key already exists, getting value...${NC}"
    API_KEY_ID="$EXISTING_KEY_ID"
    # Try to get the value (might fail if key was created before)
    API_KEY_VALUE=$(aws apigateway get-api-key \
        --api-key "${API_KEY_ID}" \
        --include-value \
        --region "${AWS_REGION}" \
        --query 'value' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$API_KEY_VALUE" ] || [ "$API_KEY_VALUE" == "None" ]; then
        echo -e "${RED}⚠️  Cannot retrieve existing API key value. Creating new key...${NC}"
        API_KEY_ID=$(aws apigateway create-api-key \
            --name "${API_KEY_NAME}-$(date +%s)" \
            --enabled \
            --region "${AWS_REGION}" \
            --query 'id' \
            --output text)
        API_KEY_VALUE=$(aws apigateway get-api-key \
            --api-key "${API_KEY_ID}" \
            --include-value \
            --region "${AWS_REGION}" \
            --query 'value' \
            --output text)
    fi
else
    API_KEY_ID=$(aws apigateway create-api-key \
        --name "${API_KEY_NAME}" \
        --enabled \
        --region "${AWS_REGION}" \
        --query 'id' \
        --output text)
    
    API_KEY_VALUE=$(aws apigateway get-api-key \
        --api-key "${API_KEY_ID}" \
        --include-value \
        --region "${AWS_REGION}" \
        --query 'value' \
        --output text)
fi

echo -e "${GREEN}✅ API Key created${NC}"

# Step 8: Create usage plan
echo -e "${YELLOW}📝 Step 8: Creating usage plan...${NC}"
EXISTING_PLAN_ID=$(aws apigateway get-usage-plans \
    --region "${AWS_REGION}" \
    --query "items[?name=='${API_NAME}-usage-plan'].id" \
    --output text | head -1)

if [ -n "$EXISTING_PLAN_ID" ] && [ "$EXISTING_PLAN_ID" != "None" ]; then
    USAGE_PLAN_ID="$EXISTING_PLAN_ID"
    echo -e "${YELLOW}⚠️  Usage plan already exists${NC}"
else
    USAGE_PLAN_ID=$(aws apigateway create-usage-plan \
        --name "${API_NAME}-usage-plan" \
        --description "Usage plan for ${API_NAME}" \
        --api-stages "[{\"apiId\":\"${API_ID}\",\"stage\":\"${STAGE_NAME}\"}]" \
        --throttle burstLimit=10,rateLimit=5 \
        --quota limit=10000,period=DAY \
        --region "${AWS_REGION}" \
        --query 'id' \
        --output text)
fi

# Step 9: Associate API key with usage plan
echo -e "${YELLOW}📝 Step 9: Associating API key with usage plan...${NC}"
aws apigateway create-usage-plan-key \
    --usage-plan-id "${USAGE_PLAN_ID}" \
    --key-type API_KEY \
    --key-id "${API_KEY_ID}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || echo "Association might already exist"

# Get the API endpoint URL
API_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/${STAGE_NAME}"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ API Gateway setup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🌐 API Endpoint: ${API_URL}${NC}"
echo -e "${GREEN}🔑 API Key: ${API_KEY_VALUE}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}💡 Test from anywhere in the world:${NC}"
echo ""
echo -e "   # Health check"
echo -e "   curl -X GET ${API_URL}/health \\"
echo -e "     -H \"x-api-key: ${API_KEY_VALUE}\""
echo ""
echo -e "   # Webhook"
echo -e "   curl -X POST ${API_URL}/webhook-green \\"
echo -e "     -H \"x-api-key: ${API_KEY_VALUE}\" \\"
echo -e "     -H \"Content-Type: application/json\" \\"
echo -e "     -d '{\"typeWebhook\":\"incomingMessageReceived\",...}'"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Save your API key securely!${NC}"
echo -e "${YELLOW}   You can use this URL and API key from any computer in the world.${NC}"

