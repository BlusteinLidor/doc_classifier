# Multi-stage: React SPA + FastAPI
# rev: stack-toast-money-v3

FROM node:20-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY samples ./samples
COPY backend ./backend
COPY --from=frontend-build /fe/dist ./frontend/dist

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV APP_REV=stack-toast-money-v3

EXPOSE 8000

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
