FROM python:3.8

WORKDIR /api
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

CMD [ "python", "-u", "./server.py"]