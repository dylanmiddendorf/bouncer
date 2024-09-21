# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app
ENTRYPOINT ["python3", "bouncer/__main__.py"]