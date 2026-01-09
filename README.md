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