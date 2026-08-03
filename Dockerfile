# Deploy Streamlit on Railway (alternative HTTPS host when Streamlit Cloud
# interactive deploy is unavailable). Primary docs still in DEMO.md.

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

CMD streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
