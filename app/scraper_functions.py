import asyncio
import pandas as pd
import sys
import io
import os
import random
import datetime
from datetime import datetime, timezone
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

async def scraper_single_code(crawler, code):
    """Scraper function for single error code"""
    detail_url = ASX_URL.format(code.lower())
    vol_num, price_num = None, None

    for attempt in range(2):
        detail_result = await crawler.arun(
            url=detail_url,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS if attempt > 0 else CacheMode.ENABLED,
                wait_for="span[data-quoteapi*='monthAverageVolume']",
                js_code="window.scrollBy(0, 300);",
            ),
        )

        if detail_result.success:
            d_soup = BeautifulSoup(detail_result.html, "html.parser")
            vol_elem = d_soup.select_one("span[data-quoteapi*='monthAverageVolume']")
            price_elem = d_soup.select_one("span[data-quoteapi='price']")

            vol_num = clean_to_number(vol_elem.get_text(strip=True)) if vol_elem else None
            price_num = clean_to_number(price_elem.get_text(strip=True)) if price_elem else None

            if vol_num is not None and price_num is not None:
                return vol_num, price_num # Success

        await asyncio.sleep(2)
    return None, None

# --- MAIN SCRAPE FUNCTION --- 
async def scraper():
    results = []
    # Limit concurrent detail fetches to 5
    semaphore = asyncio.Semaphore(5)

    async with AsyncWebCrawler() as crawler:
        print(f"🌐 Fetching main list: {UPCOMING_URL}")
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, wait_for="table tbody tr")
        result = await crawler.arun(url=UPCOMING_URL, config=run_config)

        if not result.success:
            print(f"❌ Failed to crawl: {result.error_message}")
            return []

        soup = BeautifulSoup(result.html, "html.parser")
        rows = soup.select("table tbody tr")
        print(f"📊 Found {len(rows)} potential rows. Starting concurrent scrape...")

        # --- PHASE 1: Concurrent Bulk Processing ---
        async def process_row(row, index):
            async with semaphore:
                try:
                    cells = row.find_all("td")
                    if not cells: return None
                    
                    code = cells[0].get_text(strip=True)
                    amount_val = clean_to_number(cells[4].get_text(strip=True))
                    # Skip if no dividend amount
                    if amount_val is None or amount_val == 0: return None

                    # Extract primary data
                    data_item = {
                        "Crawl Date": datetime.now().strftime("%Y-%m-%d"),
                        "Code": code,
                        "Company": cells[1].get_text(strip=True),
                        "Ex Date": parse_international_date(cells[3].get_text(strip=True)),
                        "Amount": amount_val,
                        "Franking": clean_percent_to_decimal(cells[5].get_text(strip=True)),
                        "Pay Date": parse_international_date(cells[7].get_text(strip=True)),
                        "Yield": clean_percent_to_decimal(cells[8].get_text(strip=True)),
                        "Price": None, "4w Volume": None, "Total Value": None # Placeholders
                    }

                    # Initial attempt to get Price/Vol
                    vol_num, price_num = await scraper_single_code(crawler, code)
                    data_item.update({
                        "Price": price_num,
                        "4w Volume": vol_num,
                        "Total Value": (vol_num * price_num) if (vol_num and price_num) else None
                    })
                    
                    status = "✅" if price_num and vol_num else "⏳ (Queued for retry)"
                    print(f"{status} [{index+1}] {code:5} | Price: {price_num}")
                    return data_item
                except Exception as e:
                    print(f"⚠️ Error processing {index}: {e}")
                    return None

        tasks = [process_row(row, i) for i, row in enumerate(rows)]
        all_results = await asyncio.gather(*tasks)
        results = [r for r in all_results if r is not None]
        
        while True:
            # --- PHASE 2: Targeted Retry for Errors ---
            errors = [item for item in results if item['Price'] is None or item['4w Volume'] is None]

            if not errors:
                print("\n💎 All data successfully retrieved!")
                break
            
            # Shuffle to prevent hitting specific IP rate limits
            random.shuffle(errors)

            print(f"\n🕵️ Phase 2: Attempting to fix {len(errors)} failed lookups...")
            for item in errors[:]:
                # We still use the semaphore logic indirectly by calling the helper
                code = item['Code']
                async with semaphore:
                    vol, price = await scraper_single_code(crawler, item['Code'])
                    if price is not None and vol is not None:
                        item['Price'] = price
                        item['4w Volume'] = vol
                        item["Total Value"] = (vol * price) if vol and price else None

                        print(f"✅ Fixed {item['Code']}")

                        # Remove item from errors list
                        errors.remove(item)
                    else:
                        print(f"❌ Failed again: {code}")
                await asyncio.sleep(1) # Small gap between retries

    # --- PHASE 3: Finalizing ---
    fixed_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for item in results:
        item["Last Updated"] = fixed_time

    print(f"\n[CRAWL4AI] Completed at {datetime.now()}")
    return results # list[dict]


