FROM python:3.9.1-alpine3.12

WORKDIR /app

RUN mkdir data

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
