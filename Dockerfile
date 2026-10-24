FROM python:3.11-slim

RUN apt-get update && apt-get install -y util-linux procps && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user || true
WORKDIR /app

COPY app /app
RUN chown -R 1000:1000 /app

USER 1000
