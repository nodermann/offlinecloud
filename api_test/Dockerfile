FROM python:3.8

WORKDIR /api_test
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

CMD [ "python", "-u", "./api_test.py"]