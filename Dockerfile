FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OUT_DIR=/output
RUN mkdir -p /output

CMD ["python", "scraper_playwright.py"]
