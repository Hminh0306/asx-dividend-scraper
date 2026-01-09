# Crawl4ai ASX Upcoming Dividends 

## Command for Docker
### MacOS/ Linux (bash/ zsh)
```
    mkdir -p output
    docker run --rm -v "$(pwd)/output:/output" asx-scraper
```

### Windows PowerShell
```
    mkdir output -ea 0
    docker run --rm -v "${PWD}\output:/output" asx-scraper
```

### Windows CMD
```
    mkdir output
    docker run --rm -v "%cd%\output:/output" asx-scraper
```