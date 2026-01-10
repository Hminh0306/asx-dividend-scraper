# Crawl4ai ASX Upcoming Dividends 
## Note
- Login to Docker before reading further
```
    docker login
```

# Local machine Installation
## 1. Pull repository down
```
    git pull origin https://github.com/Hminh0306/asx-dividend-scraper
```

## 2. Create virtual environment
```
    python -m venv venv
```
## 3. Enter the venv
- MacOS
```
    source venv/bin/activate
```
- Windows
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

# Docker Installation

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