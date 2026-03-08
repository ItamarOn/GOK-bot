"""
data from:
```
@app.post("/webhook-green", tags=["whatsapp"])
async def green_webhook(request: Request):
    data = await request.json()
    logger.debug(f"Green incoming: {data}")
```
"""
from .jpg_in_group import income_jpg_msg_in_group as group_pic_example
from .text_in_group import income_txt_msg_in_group as group_text_example
from .jpg_personal import jpg_personal as personal_pic_example
from .text_personal import text_personal as personal_text_example