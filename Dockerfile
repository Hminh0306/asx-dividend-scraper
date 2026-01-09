# Use the correct version we identified earlier
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install all required libraries
RUN pip install --no-cache-dir pandas crawl4ai beautifulsoup4 lxml html5lib playwright-stealth

# FIX: Use the new setup command instead of the old module path
RUN crawl4ai-setup

# Ensure Playwright browsers are ready
RUN playwright install chromium --with-deps

COPY . .

CMD ["python", "-u", "scraper_playwright.py"]