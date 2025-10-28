# fast api application with a single POST endpoint get json, make some request and return json
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from engine import check_barcode
from config import logger

app = FastAPI()

@app.get("/health_check")
async def health_check():
    return {"status": "ok1"}


@app.post("/process")
async def process(request: Request):
    logger.debug('start process')
    form = await request.form()
    data = dict(form)
    logger.debug(f'massage from: {data.get("From", "")}')
    resp = MessagingResponse()
    if data.get('MessageType', '') == 'image':
        img_link = data['MediaUrl0']
        bc = check_barcode(img_link)
        resp.message(bc)
    else:
        logger.debug('not a pic, checking if text include barcode digits')
        # get 13 digits number from the text
        text = data.get('Body', '')
        digits = ''.join(filter(str.isdigit, text))
        if digits:
            bc = check_barcode(digits, text=True)
            resp.message(bc)
        else:
            resp.message("Not a pic and no digits found in the text 😢")
    logger.debug('end process')
    return Response(content=str(resp), media_type="application/xml")
