# syntax=docker/dockerfile:1
FROM python:3.8 as builder

WORKDIR /tmp
COPY requirements.txt .
RUN pip3 install -r requirements.txt && rm requirements.txt


FROM builder
WORKDIR /app
COPY . .
CMD ["gunicorn", "api.app:create_app", "--bind=0.0.0.0:3000", "--worker-class=aiohttp.GunicornWebWorker"]
