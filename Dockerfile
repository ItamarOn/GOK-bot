FROM python:3.11-slim

# setting gir last commit env var, deploy with --build-arg GIT_SHA=$(git rev-parse HEAD)
ARG GIT_SHA=unknown
ENV APP_GIT_SHA=$GIT_SHA

#  zbar
RUN apt-get update && apt-get install -y libzbar0

# coppying the application files
WORKDIR /app
COPY . .

# dependencies installation
RUN pip install --no-cache-dir -r requirements.txt

# running the application
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--timeout", "60"]
