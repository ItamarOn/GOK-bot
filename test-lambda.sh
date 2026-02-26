#!/bin/bash

set -e

# Configuration
LAMBDA_FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-gok-bot-lambda}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧪 Testing Lambda function...${NC}"

# Test 1: Health endpoint
echo -e "${YELLOW}📋 Test 1: Health endpoint${NC}"
aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --region "${AWS_REGION}" \
    --payload '{"version":"2.0","routeKey":"GET /health","rawPath":"/health","rawQueryString":"","headers":{"host":"test"},"requestContext":{"accountId":"123456789012","apiId":"test","domainName":"test","domainPrefix":"test","http":{"method":"GET","path":"/health","protocol":"HTTP/1.1","sourceIp":"127.0.0.1","userAgent":"test"},"requestId":"test-request-id","routeKey":"GET /health","stage":"$default","time":"09/Feb/2024:00:00:00 +0000","timeEpoch":1707446400000},"isBase64Encoded":false}' \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda-response.json

echo -e "${GREEN}✅ Response:${NC}"
cat /tmp/lambda-response.json | python3 -m json.tool 2>/dev/null || cat /tmp/lambda-response.json
echo ""

# Test 2: Redis health
echo -e "${YELLOW}📋 Test 2: Redis health endpoint${NC}"
aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --region "${AWS_REGION}" \
    --payload '{"version":"2.0","routeKey":"GET /health/redis","rawPath":"/health/redis","rawQueryString":"","headers":{"host":"test"},"requestContext":{"accountId":"123456789012","apiId":"test","domainName":"test","domainPrefix":"test","http":{"method":"GET","path":"/health/redis","protocol":"HTTP/1.1","sourceIp":"127.0.0.1","userAgent":"test"},"requestId":"test-request-id","routeKey":"GET /health/redis","stage":"$default","time":"09/Feb/2024:00:00:00 +0000","timeEpoch":1707446400000},"isBase64Encoded":false}' \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda-response.json

echo -e "${GREEN}✅ Response:${NC}"
cat /tmp/lambda-response.json | python3 -m json.tool 2>/dev/null || cat /tmp/lambda-response.json
echo ""

echo -e "${GREEN}✅ Testing complete!${NC}"
echo -e "${YELLOW}💡 View logs: aws logs tail /aws/lambda/${LAMBDA_FUNCTION_NAME} --follow --region ${AWS_REGION}${NC}"

