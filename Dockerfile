FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Minimal OS deps (add more only if your crawler needs them)
RUN apt-get update && apt-get install -y \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OUT_DIR=/output
RUN mkdir -p /output

CMD ["python", "scraper_playwright.py"]
