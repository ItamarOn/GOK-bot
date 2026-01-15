FROM python:3.11-slim

#  zbar
RUN apt-get update && apt-get install -y libzbar0

# coppying the application files
WORKDIR /app
COPY . .

# dependencies installation
RUN pip install --no-cache-dir -r requirements.txt

# running the application
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--timeout", "60"]
