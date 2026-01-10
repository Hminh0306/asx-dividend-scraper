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

### General
- Python >= **3.9+**
- Git
- Internet connection

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

*The generated CSV file will be saved to the default output directory defined in the script.*

---

# Docker Installation
Running via Docker ensures:

- No local dependency conflicts

- Identical behaviour across machines

- Easy repeatability

## 1. Pull image down 
```
    docker pull nddminhh/asx-dividend-scraper:latest
```

## 2. Execute docker
### Notes
- .csv file will be saved inside your machine Downloads directory by default
- Please take a look at your Downloads directory after the code completion for your long desired file
### MacOS/ Linux (bash/ zsh)
```
    docker run --rm \
        -v "$HOME/Downloads:/root/Downloads" \
        nddminhh/asx-dividend-scraper:latest
```

### Windows PowerShell
```
    docker run --rm `
        -v "$env:USERPROFILE\Downloads:/root/Downloads" `
        nddminhh/asx-dividend-scraper:latest
```

### Windows CMD
```
    docker run --rm ^
        -v "%USERPROFILE%\Downloads:/root/Downloads" ^
        nddminhh/asx-dividend-scraper:latest
```