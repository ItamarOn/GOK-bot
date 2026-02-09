# 📱 GOK Bot
## WhatsApp Integration Using Green-API

---

### Project Site: [GOK-Bot-Website](https://itamaron.github.io/gok-bot-website/)

---
This project integrates the GOK Bot with **Green-API**, enabling automatic processing of incoming WhatsApp messages (text and images), barcode extraction, and smart replies directly inside WhatsApp.

The bot is built with **FastAPI**, deployed on Render, and supports real WhatsApp **reply-to threading**.

---

## 🚀 Features

* Receive WhatsApp messages via **Green-API Webhooks**
* Handle both **text messages** and **image messages**
* Download and process images directly from Green-API’s `downloadUrl`
* Extract barcodes using the existing `check_barcode()` engine
* Send responses back to users through Green-API’s `sendMessage` endpoint
* Full **WhatsApp threaded reply** support (messages appear as replies to the user’s original message)
* Duplicate message filtering using Redis
* Production-ready FastAPI backend

---

## 🧰 Tech Stack

* **FastAPI** – Web framework
* **Redis** – Duplicate message filtering
* **Green-API** – WhatsApp integration
* **Pillow** – Image handling
* **pyzbar** – Barcode decoding
* **Render** – Deployment platform

---

## 📦 Endpoints

### Health Checks

```
GET /health
GET /health/redis
GET /health/redis/count
```

### Webhooks

```
POST /webhook-green     # Green-API incoming messages
POST /webhook           # (Old Version) Meta Cloud API webhook
```

---

---

### Dev Info

Local development:
```bash
.venv/bin/uvicorn main:app --reload
# Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

ngrok http 8000
# Forwarding   https://someurl.ngrok-free.dev -> http://localhost:8000
```

For production:

Old deploy: [Render.com deployment guide](https://render.com/docs/deploys) for more details.

New deploy: [Fly.io](https://fly.io/). The deployment is from the root of the project:

```bash
# brew install flyctl  # only for install
# fly auth login  # only for install
# fly launch  # only for create new app after install
fly secrets set X=123 # set env vars
fly secrets list
fly machines list
fly deploy --build-arg GIT_SHA=$(git rev-parse HEAD) --app gok-bot
fly ssh console --app gok-bot
fly logs
```


