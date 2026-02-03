# Function Documentation: scraper()
The *scraper()* function is an asynchronous web crawler designed to extract upcoming dividend data and real-time market metrics from Market Index. It utilizes Crawl4AI for high-performance scraping and asyncio for concurrent data retrieval.

--- 

## Overview
The function operates in a two-stage process:

Index Crawl: Fetches the primary list of upcoming dividends.

Parallel Detail Crawl: Concurrently visits individual stock pages to gather 4-week average volume and current share prices.

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

### 2. Primary List Extraction
*The function targets the UPCOMING_URL. It parses the HTML table to extract:*

- Company Name & Ticker Code

- Ex-Dividend & Pay Dates

- Dividend Amount & Yield

- Franking Percentage

### 3. Concurrent Detail Enrichment
For every valid stock found, it spawns an asynchronous task (fetch_detail_info).
- Session IDs: It uses session_idx % 5 to distribute tasks across 5 persistent browser tabs. This significantly reduces the overhead of opening/closing the browser.JS Execution: 
- Each detail page executes a small JavaScript snippet *(window.scrollBy(0, 300))* to ensure lazy-loaded data attributes like monthAverageVolume are triggered.Calculations:
- It derives the Total Value (Daily Liquidity) by calculating $Price \times 4W Average Volume$.

### 4. Data Standardization
Finally, the function appends a last_updated ISO timestamp to every record to ensure data consistency when saved to S3 or Redshift.

--- 

## Performance Notes
*Sequential Time: ~180-240 seconds (for 50 stocks).*

_Current Asynchronous Time: ~20-30 seconds._

- Optimization: The speed is achieved by treating network I/O as non-blocking; the CPU initiates a request and immediately moves to the next without waiting for the website to respond.