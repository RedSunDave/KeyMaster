FROM python:alpine3.7

RUN adduser -D keymaster

WORKDIR /home/KeyMaster

COPY administrative administrative
COPY backend backend
COPY distribute_keys.py distribute_keys.py
COPY requirements.txt requirements.txt

RUN apt-get install libva-dev git

RUN python3 -m pip install -r requirements.txt

RUN chown -R keymaster:keymaster ./
USER keymaster



