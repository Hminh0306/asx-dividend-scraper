# Function Documentation: scraper()
The *scraper()* function is an asynchronous web crawler designed to extract upcoming dividend data and real-time market metrics from Market Index. It utilizes Crawl4AI for high-performance scraping and asyncio for concurrent data retrieval.

--- 

## Overview
The function operates in a three-stage process:

1. Index Crawl: Fetches the primary list of upcoming dividends.

2. Concurrent Enrichment: Uses an asynchronous semaphore to bulk-fetch real-time price and volume data.

3. Targeted Retry: Identifies failed data points (missing prices) and re-runs those specific codes to ensure 100% data density.


--- 

## Techical Specifications
| Feature | Impelemtation |
| Libraries | crawl4ai, BeautifulSoup4, asyncio |
| Concurrency Strategy | Semaphore-controlled tasks with session multiplexing | 
| Rate Limiting | Max 10 concurrent requests; 5 persistent browser session |
| Retry Logic | 2 attempts per detail page with exponential backoff | 

--- 

## Core Logic Flow
### 1. Initialization
- Sets up a BrowserConfig (headless mode).

- Initializes a Semaphore(10) to prevent IP blocking by limiting concurrent outgoing requests to 10.

- Defines a CrawlerRunConfig to bypass cache for the main list ensuring fresh data.

### 2. Primary List Extraction (Phase 1)
*The function targets the UPCOMING_URL. It parses the HTML table to extract:*

- Company Name & Ticker Code

- Ex-Dividend & Pay Dates

- Dividend Amount & Yield

- Franking Percentage

### 3. Concurrent Detail Enrichment (Phase 2)
For every valid stock found, it spawns an asynchronous task.
- Semaphore Control: The async with semaphore: block ensures that only 5 detail pages are being requested at any given moment.
- JS Execution: Each detail page executes a JavaScript snippet window.scrollBy(0, 300) to trigger the population of lazy-loaded attributes like monthAverageVolume.
- Calculations: It derives the Total Value (Daily Liquidity) using: $$\text{Total Value} = \text{Price} \times \text{4W Average Volume}$$


### 4. Error Mitigation (Phase 2)
Finally, the function appends a last_updated ISO timestamp to every record to ensure data consistency when saved to S3 or Redshift.

--- 

## Performance Notes
*Sequential Time: ~180-240 seconds (for 50 stocks).*

_Current Asynchronous Time: ~20-30 seconds._

- Optimization: The speed is achieved by treating network I/O as non-blocking; the CPU initiates a request and immediately moves to the next without waiting for the website to respond.