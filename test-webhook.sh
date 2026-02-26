#!/bin/bash

# Test webhook endpoint
API_URL="https://81vk6yr8bi.execute-api.us-east-1.amazonaws.com/prod"
API_KEY="HU7NTnkm1P6c8mPcSEyhq1NLEgkMTBlP4JKuCrur"

curl -X POST "${API_URL}/webhook-green" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {
      "idInstance": 7105398750,
      "wid": "972556815085@c.us",
      "typeInstance": "whatsapp"
    },
    "timestamp": 1769409920,
    "idMessage": "ACDA5E57D487EB37B821EE443CF17B1B",
    "senderData": {
      "chatId": "972547271571@c.us",
      "chatName": "😎",
      "sender": "972547271571@c.us",
      "senderName": "😎",
      "senderContactName": ""
    },
    "messageData": {
      "typeMessage": "textMessage",
      "textMessageData": {
        "textMessage": "Ordinary message"
      }
    }
  }'

echo ""

