# ASX Upcoming Dividends Scraper  
*A Crawl4AI & Playwright-based data pipeline for scraping ASX upcoming dividend data and exporting it to CSV.*

---

## Overview

This project implements an **end-to-end data scraping pipeline** that:
- Scrapes **upcoming ASX dividend data**
- Cleans and structures the data
- Upload data to Redshift Data Warehouse
- Upload latest data to S3 Bucket for fast retrieval

The pipeline can be run **locally** (via Python) or **containerised** (via Docker) for consistent execution across environments.

---

## Prerequisites

### General (up-to 16/1/2026)
- Python >= **3.12+**
- Git
- Internet connection
- AWS Redshift Workgroup established
- AWS S3 Bucket established

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
