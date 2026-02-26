# Shell Scripts Summary

## ✅ KEEP - Production Scripts

### Deployment & Setup
- **`setup-lambda-role.sh`** - Creates IAM role for Lambda (run once, keep for reference)
- **`deploy-lambda.sh`** - Main deployment script - **USE THIS FOR ALL DEPLOYMENTS**
- **`setup-api-gateway-simple.sh`** - Sets up API Gateway with API keys (run once, keep for reference)

### Testing
- **`test-webhook.sh`** - Test webhook endpoint with sample data
- **`test-lambda.sh`** - Test Lambda function directly (alternative testing method)

## 🗑️ DELETE - Discovery/Debugging Scripts (One-time use)

These were used during setup/debugging and are no longer needed:

- `check-function-url.sh` - Debugging Function URL config
- `cleanup-ecr.sh` - One-time ECR cleanup
- `debug-api-gateway.sh` - Debugging API Gateway issues
- `fix-api-gateway-integration.sh` - One-time fix for API Gateway
- `fix-function-url-auth.sh` - One-time fix (we used API Gateway instead)
- `invoke-webhook.sh` - Replaced by `test-webhook.sh`
- `setup-api-gateway.sh` - Replaced by `setup-api-gateway-simple.sh`
- `setup-function-url-permissions.sh` - Not used (we used API Gateway instead)
- `setup-function-url.sh` - Not used (we used API Gateway instead)

## 📝 Usage

### First Time Setup (already done):
```bash
./setup-lambda-role.sh          # Creates IAM role
./setup-api-gateway-simple.sh   # Creates API Gateway
```

### Regular Deployment:
```bash
./deploy-lambda.sh              # Build and deploy Lambda
```

### Testing:
```bash
./test-webhook.sh               # Test webhook endpoint
./test-lambda.sh                # Test Lambda directly
```

## 🔑 Important URLs & Keys

- **API Endpoint**: `https://81vk6yr8bi.execute-api.us-east-1.amazonaws.com/prod`
- **API Key**: `HU7NTnkm1P6c8mPcSEyhq1NLEgkMTBlP4JKuCrur`
- **Lambda Function**: `gok-bot-lambda`
- **Region**: `us-east-1`

## 🧹 Cleanup Command

To remove all debugging scripts:
```bash
rm check-function-url.sh cleanup-ecr.sh debug-api-gateway.sh \
   fix-api-gateway-integration.sh fix-function-url-auth.sh \
   invoke-webhook.sh setup-api-gateway.sh setup-function-url-permissions.sh \
   setup-function-url.sh
```

