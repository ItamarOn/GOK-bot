#!/bin/bash

set -e  # Exit on error

# Configuration
LAMBDA_FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-gok-bot-lambda}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO_NAME="${ECR_REPO_NAME:-gok-bot-lambda}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
LAMBDA_ROLE_NAME="${LAMBDA_ROLE_NAME:-lambda-execution-role}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AWS Lambda deployment...${NC}"

# Get AWS account ID
echo -e "${YELLOW}📋 Getting AWS account information...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Failed to get AWS account ID. Make sure AWS CLI is configured.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${GREEN}✅ AWS Region: ${AWS_REGION}${NC}"

# ECR repository URI
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

# Step 1: Create ECR repository if it doesn't exist
echo -e "${YELLOW}📦 Checking ECR repository...${NC}"
if aws ecr describe-repositories --repository-names "${ECR_REPO_NAME}" --region "${AWS_REGION}" 2>/dev/null; then
    echo -e "${GREEN}✅ ECR repository '${ECR_REPO_NAME}' already exists${NC}"
else
    echo -e "${YELLOW}📦 Creating ECR repository '${ECR_REPO_NAME}'...${NC}"
    aws ecr create-repository \
        --repository-name "${ECR_REPO_NAME}" \
        --region "${AWS_REGION}" \
        --image-scanning-configuration scanOnPush=true \
        --image-tag-mutability MUTABLE
    echo -e "${GREEN}✅ ECR repository created${NC}"
fi

# Step 2: Login to ECR
echo -e "${YELLOW}🔐 Logging in to ECR...${NC}"
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${ECR_REPO_URI}"
echo -e "${GREEN}✅ Logged in to ECR${NC}"

# Step 2.5: Optional - Clean up old images with the same tag
echo -e "${YELLOW}🧹 Cleaning up old images with tag '${IMAGE_TAG}'...${NC}"
aws ecr batch-delete-image \
    --repository-name "${ECR_REPO_NAME}" \
    --image-ids imageTag="${IMAGE_TAG}" \
    --region "${AWS_REGION}" 2>/dev/null || echo -e "${YELLOW}   No existing images to clean up${NC}"

# Step 3: Build Docker image (disable BuildKit to avoid manifest list on Mac)
echo -e "${YELLOW}🔨 Building Docker image for linux/amd64...${NC}"
# Disable BuildKit to avoid manifest list creation on Docker Desktop for Mac
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
export DOCKER_DEFAULT_PLATFORM=linux/amd64

# Build the image
docker build --platform linux/amd64 -f Dockerfile.lambda -t "${ECR_REPO_URI}:${IMAGE_TAG}" .
echo -e "${GREEN}✅ Docker image built${NC}"

# Step 4: Push image to ECR
echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
docker push "${ECR_REPO_URI}:${IMAGE_TAG}"
echo -e "${GREEN}✅ Image pushed to ECR${NC}"

# Step 3.5: Check and fix manifest list if it exists (Lambda doesn't support them)
echo -e "${YELLOW}🔍 Verifying image manifest type...${NC}"
MANIFEST_TYPE=$(aws ecr describe-images \
    --repository-name "${ECR_REPO_NAME}" \
    --image-ids imageTag="${IMAGE_TAG}" \
    --region "${AWS_REGION}" \
    --query 'imageDetails[0].imageManifestMediaType' \
    --output text 2>/dev/null || echo "unknown")

if [ "$MANIFEST_TYPE" == "application/vnd.oci.image.index.v1+json" ] || [ "$MANIFEST_TYPE" == "application/vnd.docker.distribution.manifest.list.v2+json" ]; then
    echo -e "${YELLOW}⚠️  Manifest list detected. This won't work with Lambda.${NC}"
    echo -e "${YELLOW}💡 Trying to extract single architecture manifest...${NC}"
    
    # Use a Python script to extract the amd64 manifest
    export ECR_REPO_NAME AWS_REGION IMAGE_TAG
    python3 << 'PYTHON_SCRIPT'
import json
import subprocess
import sys
import os

repo_name = os.environ.get("ECR_REPO_NAME")
image_tag = os.environ.get("IMAGE_TAG")
region = os.environ.get("AWS_REGION")

# Get image details
result = subprocess.run(
    ["aws", "ecr", "describe-images", "--repository-name", repo_name, 
     "--image-ids", f"imageTag={image_tag}", "--region", region],
    capture_output=True, text=True
)
images = json.loads(result.stdout)["imageDetails"]
if not images:
    print("No images found")
    sys.exit(1)

image_digest = images[0]["imageDigest"]

# Get the manifest
result = subprocess.run(
    ["aws", "ecr", "batch-get-image", "--repository-name", repo_name,
     "--image-ids", f"imageDigest={image_digest}", "--region", region],
    capture_output=True, text=True
)
manifest_data = json.loads(result.stdout)
manifest_json = json.loads(manifest_data["images"][0]["imageManifest"])

# Check if it's a manifest list
if "manifests" in manifest_json:
    # Find amd64 manifest
    amd64_digest = None
    for manifest in manifest_json["manifests"]:
        platform = manifest.get("platform", {})
        if platform.get("architecture") == "amd64":
            amd64_digest = manifest["digest"]
            break
    
    if amd64_digest:
        # Get the actual amd64 manifest
        result = subprocess.run(
            ["aws", "ecr", "batch-get-image", "--repository-name", repo_name,
             "--image-ids", f"imageDigest={amd64_digest}", "--region", region],
            capture_output=True, text=True
        )
        amd64_manifest_data = json.loads(result.stdout)
        amd64_manifest = amd64_manifest_data["images"][0]["imageManifest"]
        
        # Put the single-arch manifest
        subprocess.run(
            ["aws", "ecr", "put-image", "--repository-name", repo_name,
             "--image-tag", image_tag, "--image-manifest", amd64_manifest,
             "--region", region],
            check=True
        )
        print("✅ Replaced manifest list with single architecture manifest")
    else:
        print("❌ Could not find amd64 manifest in the list")
        sys.exit(1)
else:
    print("✅ Image is already a single architecture manifest")
PYTHON_SCRIPT

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to fix manifest list${NC}"
        echo -e "${YELLOW}💡 Consider building on a Linux machine or using GitHub Actions/CI${NC}"
        exit 1
    fi
fi

# Verify the image exists in ECR
echo -e "${YELLOW}🔍 Verifying image in ECR...${NC}"
if ! aws ecr describe-images --repository-name "${ECR_REPO_NAME}" --image-ids imageTag="${IMAGE_TAG}" --region "${AWS_REGION}" > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to verify image in ECR!${NC}"
    exit 1
fi

# Verify it's not a manifest list
FINAL_MANIFEST_TYPE=$(aws ecr describe-images \
    --repository-name "${ECR_REPO_NAME}" \
    --image-ids imageTag="${IMAGE_TAG}" \
    --region "${AWS_REGION}" \
    --query 'imageDetails[0].imageManifestMediaType' \
    --output text 2>/dev/null || echo "unknown")

if [ "$FINAL_MANIFEST_TYPE" == "application/vnd.oci.image.index.v1+json" ]; then
    echo -e "${RED}❌ Image is still a manifest list. Lambda cannot use this.${NC}"
    echo -e "${YELLOW}💡 Try building on a Linux machine or using a CI/CD pipeline.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image verified in ECR (type: ${FINAL_MANIFEST_TYPE})${NC}"

# Step 6: Read environment variables from env-vars.json
echo -e "${YELLOW}📝 Reading environment variables...${NC}"
if [ ! -f "env-vars.json" ]; then
    echo -e "${RED}❌ env-vars.json not found!${NC}"
    exit 1
fi
ENV_VARS=$(cat env-vars.json)

# Step 7: Create or update Lambda function
echo -e "${YELLOW}⚡ Creating/updating Lambda function...${NC}"
IMAGE_URI="${ECR_REPO_URI}:${IMAGE_TAG}"

# Check if Lambda function exists
if aws lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" --region "${AWS_REGION}" 2>/dev/null; then
    echo -e "${YELLOW}🔄 Updating existing Lambda function...${NC}"
    aws lambda update-function-code \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --image-uri "${IMAGE_URI}" \
        --region "${AWS_REGION}" > /dev/null
    
    # Wait for update to complete
    echo -e "${YELLOW}⏳ Waiting for function update to complete...${NC}"
    aws lambda wait function-updated \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --region "${AWS_REGION}"
    
    # Update environment variables
    echo -e "${YELLOW}🔄 Updating environment variables...${NC}"
    aws lambda update-function-configuration \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --environment "${ENV_VARS}" \
        --region "${AWS_REGION}" > /dev/null
    
    echo -e "${GREEN}✅ Lambda function updated${NC}"
else
    echo -e "${YELLOW}🆕 Creating new Lambda function...${NC}"
    
    # Check if IAM role exists
    ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
    if ! aws iam get-role --role-name "${LAMBDA_ROLE_NAME}" 2>/dev/null; then
        echo -e "${RED}❌ IAM role '${LAMBDA_ROLE_NAME}' not found!${NC}"
        echo -e "${YELLOW}💡 Run './setup-lambda-role.sh' first to create the IAM role, or set LAMBDA_ROLE_NAME to an existing role.${NC}"
        exit 1
    fi
    
    # Create the function (you may need to adjust memory and timeout)
    aws lambda create-function \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --package-type Image \
        --code ImageUri="${IMAGE_URI}" \
        --role "${ROLE_ARN}" \
        --timeout 300 \
        --memory-size 512 \
        --architectures x86_64 \
        --environment "${ENV_VARS}" \
        --region "${AWS_REGION}" > /dev/null || {
        echo -e "${RED}❌ Failed to create Lambda function.${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Lambda function created${NC}"
fi

# Step 8: Get function URL or ARN
echo -e "${YELLOW}📋 Getting function information...${NC}"
FUNCTION_ARN=$(aws lambda get-function \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --region "${AWS_REGION}" \
    --query 'Configuration.FunctionArn' \
    --output text)

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Function Name: ${LAMBDA_FUNCTION_NAME}${NC}"
echo -e "${GREEN}Function ARN:  ${FUNCTION_ARN}${NC}"
echo -e "${GREEN}Image URI:     ${IMAGE_URI}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "   1. Create an API Gateway or Function URL to expose your Lambda"
echo -e "   2. Test the function: aws lambda invoke --function-name ${LAMBDA_FUNCTION_NAME} --region ${AWS_REGION} output.json"
echo -e "   3. View logs: aws logs tail /aws/lambda/${LAMBDA_FUNCTION_NAME} --follow --region ${AWS_REGION}"

