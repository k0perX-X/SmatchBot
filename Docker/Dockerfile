FROM python:alpine

MAINTAINER k0perXD@ya.ru

RUN mkdir /app
COPY . /app/

RUN apk add tree
RUN cd /app/

RUN pip install -r /app/requirements.txt

ENTRYPOINT cd /app; python main.py