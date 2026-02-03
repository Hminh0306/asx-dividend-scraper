import asyncio
import sys
import io
import random
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from bs4 import BeautifulSoup

# Set encoding for Windows Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

UPCOMING_URL = "https://www.marketindex.com.au/upcoming-dividends"
ASX_URL = "https://www.marketindex.com.au/asx/{}"

# --- HELPER FUNCTIONS ---
def parse_international_date(date_str):
    """Converts date formats to YYYY-MM-DD."""
    if not date_str or date_str == "N/A":
        return "N/A"
    current_year = datetime.now().year
    try:
        return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {current_year}", "%d %b %Y").strftime("%Y-%m-%d")
        except:
            return date_str

def clean_to_number(text):
    """Removes symbols and converts string to float."""
    if not text or text in ['\u2010', '-', 'N/A', '']:
        return None
    try:
        return float(text.replace(',', '').replace('$', '').replace('%', '').strip())
    except:
        return None

def clean_percent_to_decimal(text):
    """Converts percentage string to decimal (e.g., 100% -> 1.0)."""
    val = clean_to_number(text)
    return val / 100 if val is not None else None

# --- MAIN SCRAPE FUNCTION --- 
async def scraper():
    """
    Scrape information from marketindex.com.au/upcoming-dividends and individual codes
    Return list of dictionary containing information of each code in the columns:
        Code
        Company
        Ex_date
        Pay_date
        Franking
        Yield
        Price
        Amount
        4W Volume 
        Total Value
        Last_updated
    """
    results = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Configure the browser once for the entire session
    browser_config = BrowserConfig(headless=True, verbose=False)

    # Configuration for main list page
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="table tbody tr",
        page_timeout=60000,
    )

    # Parallel pages fetching - cap at 10 to avoid rate limiting
    semaphore = asyncio.Semaphore(10)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print(f"🌐 Fetching main list: {UPCOMING_URL}")
        result = await crawler.arun(url=UPCOMING_URL, config=run_config)

        if not result.success:
            print(f"❌ Failed to crawl: {result.error_message}")
            return []

        soup = BeautifulSoup(result.html, "html.parser")
        rows = soup.select("table tbody tr")
        print(f"📊 Found {len(rows)} potential rows.")

        async def fetch_detail_info(row_idx, row_data):
            """Helper function to fetch detail info with concurrency control"""
            async with semaphore:
                code = row_data['Code']
                detail_url = ASX_URL.format(code.lower())
                # Pick a session_id for a detail page thread
                session_id = f"session_{row_idx % 5}" # use 5 persistent browser tabs and cycle through them - reduce RAM usage, speed up crawl, keep cookies/ states if site required

                # Retry logic for detail page
                for attempt in range(2):
                    detail_result = await crawler.arun(
                        url=detail_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS if attempt > 0 else CacheMode.ENABLED,
                            wait_for="span[data-quoteapi*='monthAverageVolume']",
                            page_timeout=30000,
                            js_code="window.scrollBy(0, 300);",
                        ),
                        session_id = session_id
                    )

                    if detail_result.success:
                        d_soup = BeautifulSoup(detail_result.html, "html.parser")
                        
                        vol_elem = d_soup.select_one("span[data-quoteapi*='monthAverageVolume']")
                        price_elem = d_soup.select_one("span[data-quoteapi='price']")
                        
                        vol_num = clean_to_number(vol_elem.get_text(strip=True)) if vol_elem else None
                        price_num = clean_to_number(price_elem.get_text(strip=True)) if price_elem else None
                        total_value = (vol_num * price_num) if (vol_num and price_num) else None

                        return {**row_data, "Price": price_num, "4w Volume": vol_num, "Total Value": total_value}
                    
                    await asyncio.sleep(2 ** attempt) # Exponential backoff
                return {**row_data, "Price": None, "4w Volume": None, "Total Value": None}

        # 1. Parse the main table first
        tasks = []
        for i, row in enumerate(rows):
            cells = row.find_all("td")
            if not cells: continue
            
            code = cells[0].get_text(strip=True)
            amount_val = clean_to_number(cells[4].get_text(strip=True))
            
            if amount_val and amount_val > 0:
                row_data = {
                    "Crawl Date": today_str,
                    "Code": code,
                    "Company": cells[1].get_text(strip=True),
                    "Ex Date": parse_international_date(cells[3].get_text(strip=True)),
                    "Amount": amount_val,
                    "Franking": clean_percent_to_decimal(cells[5].get_text(strip=True)),
                    "Pay Date": parse_international_date(cells[7].get_text(strip=True)),
                    "Yield": clean_percent_to_decimal(cells[8].get_text(strip=True)),
                }
                # Create a task for concurrent execution
                tasks.append(fetch_detail_info(i, row_data))

        # 2. Run all detail fetches concurrently
        results = await asyncio.gather(*tasks)

    # 3. Add consistent timestamp
    fixed_time = datetime.now().isoformat()
    for item in results:
        item["Last Updated"] = fixed_time
    
    print(f"[CRAWL4AI] Completed scraping at {datetime.now()}")
    return results
        

