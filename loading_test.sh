#!/bin/bash

# הגדרת המשתנים
URL="https://81vk6yr8bi.execute-api.us-east-1.amazonaws.com/prod/webhook-green"
API_KEY="HU7NTnkm1P6c8mPcSEyhq1NLEgkMTBlP4JKuCrur"

# מערך של ה-downloadUrls לגיוון
URLS=(
    "https://do-media-7105.fra1.digitaloceanspaces.com/7105398750/f72650c1-29bd-4811-83cb-f528b64a68a0.jpg"
    "https://do-media-7105.fra1.digitaloceanspaces.com/7105398750/8e8e6a11-11c8-45a3-946f-75c5dac3e4b8.jpg"
)

echo "Starting sequential load test: 100 requests..."

for i in {1..100}
do
    # יצירת מזהה הודעה עם סיומת עוקבת (001, 002...)
    SEQ_NUM=$(printf "%03d" $i)
    MESSAGE_ID="AC03621899FF3C451E4B46FAATEST$SEQ_NUM"
    
    # בחירת URL תמונה לסירוגין
    IMG_URL=${URLS[$((i % 2))]}

    echo "[$i/100] Sending ID: $MESSAGE_ID"

    curl -s -X POST "$URL" \
      -H "x-api-key: $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
      "typeWebhook": "incomingMessageReceived",
      "instanceData": {
        "idInstance": 7105398750,
        "wid": "972556815085@c.us",
        "typeInstance": "whatsapp"
      },
      "timestamp": '$(date +%s)',
      "idMessage": "'$MESSAGE_ID'",
      "senderData": {
        "chatId": "120363406797759840@g.us",
        "chatName": "Load Test Group",
        "sender": "972547271571@c.us",
        "senderName": "😎",
        "senderContactName": ""
      },
      "messageData": {
        "typeMessage": "imageMessage",
        "fileMessageData": {
          "downloadUrl": "'$IMG_URL'",
          "caption": "Sequential Test #'$SEQ_NUM'",
          "fileName": "test_'$SEQ_NUM'.jpg",
          "jpegThumbnail": "",
          "isAnimated": false,
          "mimeType": "image/jpeg",
          "forwardingScore": 0,
          "isForwarded": false
        }
      }
    }'
    
    echo -e "\n----------------------------"
done

echo "Finished 100 sequential requests."
