FROM python:3.9.1-alpine3.12 as base
RUN apk add --update \
    tzdata

FROM python:3.9.1-alpine3.12 as production
WORKDIR /app
RUN mkdir data
COPY --from=base /usr/share/zoneinfo /usr/share/zoneinfo
ENV TZ=Europe/Kiev
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
