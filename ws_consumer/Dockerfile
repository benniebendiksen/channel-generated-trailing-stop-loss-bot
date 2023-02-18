FROM python:3.8.10-alpine

WORKDIR /code

COPY ./ws_consumer ./ws_consumer/

# RUN pip install --upgrade pip
RUN apk add build-base linux-headers
RUN python -m pip install psutil
RUN apk add --no-cache --virtual .build-deps gcc musl-dev g++

RUN cd ws_consumer && pip install -r requirements.txt

RUN chmod +x ./ws_consumer/docker-entrypoint.sh
ENTRYPOINT ["./ws_consumer/docker-entrypoint.sh"]
