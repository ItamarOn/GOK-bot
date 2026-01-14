"""
data from:
```
@app.post("/webhook-green", tags=["whatsapp"])
async def green_webhook(request: Request):
    data = await request.json()
    logger.debug(f"Green incoming: {data}")
```
"""