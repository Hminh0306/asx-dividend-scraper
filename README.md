# Crawl4ai ASX Upcoming Dividends 
## Note
- Login to Docker before reading further
```
    docker login
```

## 1. Pull image down 
```
    docker pull nddminhh/asx-dividend-scraper:latest
```

## 2. Execute docker
### MacOS/ Linux (bash/ zsh)
```
    mkdir -p output
    docker run --rm -v "$(pwd)/output:/output" asx-scraper
```

### Windows PowerShell
```
    mkdir output -ea 0
    docker run --rm `
        -v "${PWD}\output:/output" `
        -e OUT_DIR=/output `
        nddminhh/asx-dividend-scraper:latest
```

### Windows CMD
```
    mkdir output
    docker run --rm \
        -v "$(pwd)/output:/output" \
        -e OUT_DIR=/output \
        nddminhh/asx-dividend-scraper:latest
```