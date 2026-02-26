from mangum import Mangum

from main import app

# AWS Lambda handler instead of Gunicorn/ASGI server. Mangum adapts FastAPI to Lambda's event-driven model:
handler = Mangum(app, lifespan="off")
