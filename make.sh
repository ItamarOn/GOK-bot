#!/bin/bash

# Local
PROJECT_DIR="/Users/itamar/projects/GOK-bot"
cd $PROJECT_DIR
docker build --platform linux/amd64 -f Dockerfile.lambda -t docker-image:test .
docker run -p 9000:8080 --env-file .env-docker docker-image:test

BASE_URL="http://localhost:9000/2015-03-31/functions/function/invocations"

# test:
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "routeKey": "GET /health",
    "rawPath": "/health",
    "rawQueryString": "",
    "headers": {
      "host": "localhost:9000",
      "user-agent": "curl/7.68.0",
      "accept": "*/*"
    },
    "requestContext": {
      "accountId": "123456789012",
      "apiId": "test",
      "domainName": "localhost",
      "domainPrefix": "localhost",
      "http": {
        "method": "GET",
        "path": "/health",
        "protocol": "HTTP/1.1",
        "sourceIp": "127.0.0.1",
        "userAgent": "curl/7.68.0"
      },
      "requestId": "test-request-id",
      "routeKey": "GET /health",
      "stage": "$default",
      "time": "09/Feb/2024:00:00:00 +0000",
      "timeEpoch": 1707446400000
    },
    "isBase64Encoded": false
  }'