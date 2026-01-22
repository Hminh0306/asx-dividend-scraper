# ASX Upcoming Dividends Scraper  
*A Crawl4AI & Playwright-based data pipeline for scraping ASX upcoming dividend data and exporting it to CSV.*

---

## Overview

This project implements an **end-to-end data scraping pipeline** that:
- Scrapes **upcoming ASX dividend data**
- Cleans and structures the data
- Exports results into a **readable CSV file**

The pipeline can be run **locally** (via Python) or **containerised** (via Docker) for consistent execution across environments.

---

## Prerequisites

### General (up-to 16/1/2026)
- Python >= **3.12+**
- Git
- Internet connection
- Gcloud-cli with verified Gcloud credentials

## Gcloud CLI Installation & Setup
*This project integrates with Google Cloud services (BigQuery, Cloud Run). You must install and authenticate the Google Cloud CLI (gcloud) before running the pipeline locally or deploying it.*
### 1. Install gcloud CLI (macOS – Homebrew)
```bash
    brew install --cask google-cloud-sdk
```
After installation, restart your terminal or add gcloud to your PATH:
```bash
    export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
```

Make it permanent
```bash
    echo 'export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
```

### 2. Verify gcloud installation
```bash
    gcloud --version
```
Expected output (Example)
```
    Google Cloud SDK    4xx.x.x
    bq                  2.xx.x
    gsutil              5.xx
```

### 3. Set Python for Gcloud (required)
- gcloud requires a supported Python runtime (3.10+).
- If you have Python 3.12 installed via Homebrew:
```bash
    export CLOUDSDK_PYTHON="/opt/homebrew/opt/python@3.12/libexec/bin/python3"
```
- Make it permanent:
```bash
    echo 'export CLOUDSDK_PYTHON="/opt/homebrew/opt/python@3.12/libexec/bin/python3"' >> ~/.zshrc
source ~/.zshrc
```
- Then initialise gcloud's internal environement:
```bash
    gcloud config virtualenv create --python-to-use "$CLOUDSDK_PYTHON"
```
### 4. Initialise & Authenticate Gcloud
```bash
    gcloud init
```
- Authenticate application credentials (required for BigQuery access):
```bash
    gcloud auth application-default login
```
- This will create a application_default_credentials.json file which is automatically used by bigQuery.Client()

### 5. Verify BigQuery Access
- Check for datasetId
```bash
    bq ls
```
- Check for BigQuery connection
```bash
    python -c "from app.bigquery_functions import test_bq_connection; test_bq_connection()"
```

---

### Docker (optional but recommended)
- Docker Desktop installed and running
- Logged in to Docker Hub

```bash
docker login
```

---

# Local Installation
## 1. Clone the repository
```
    git clone https://github.com/Hminh0306/asx-dividend-scraper.git
    cd asx-dividend-scraper
```

## 2. Create virtual environment
```
    python -m venv venv
```
## 3. Enter the venv
MacOS/ Linux
```
    source venv/bin/activate
```
Windows
```
    venv\Scripts\activate
```
## 4. Install dependencies
```
    pip install -r requirements.txt
```
## 5. Run the script
```
    python scraper_playwright.py
```

*The output will be displayed on Google Sheet for specified Sheet. Current implementation is being displayed on **https://docs.google.com/spreadsheets/d/15CQUqo2_K08qqACSgrV9muNYlU2S7yNa9QXJ-YvnVS4/edit?gid=1631965488#gid=1631965488_ **(with restricted access). Please email ==asxdividendproject@gmail.com for preview access.*

---
