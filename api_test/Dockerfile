# syntax=docker/dockerfile:1
FROM python:3.8 as builder

WORKDIR /tmp
COPY requirements.txt .
RUN pip3 install -r requirements.txt && rm requirements.txt

FROM builder
WORKDIR /app
COPY . .
CMD ["python", "-m", "pytest", "-v"]
