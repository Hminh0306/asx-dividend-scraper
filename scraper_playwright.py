import asyncio
import pandas as pd
import sys
import io
import random
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

# Set encoding for Windows Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

UPCOMING_URL = "https://www.marketindex.com.au/upcoming-dividends"
ASX_URL = "https://www.marketindex.com.au/asx/{}"

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

async def main():
    results = []
    
    # Configure crawler settings with more "patience"
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="table tbody tr",
        page_timeout=60000,
        # Action: Scroll down to trigger lazy-loaded elements
        js_code="window.scrollTo(0, document.body.scrollHeight/2);", 
        wait_for_images=True
    )

    async with AsyncWebCrawler() as crawler:
        print(f"🌐 Fetching main list: {UPCOMING_URL}")
        result = await crawler.arun(url=UPCOMING_URL, config=run_config)
        
        if not result.success:
            print(f"❌ Failed to crawl: {result.error_message}")
            return

        soup = BeautifulSoup(result.html, 'html.parser')
        rows = soup.select("table tbody tr")
        print(f"📊 Found {len(rows)} potential rows.")

        for i, row in enumerate(rows):
            try:
                cells = row.find_all("td")
                if not cells: continue

                code = cells[0].get_text(strip=True)
                amount_val = clean_to_number(cells[4].get_text(strip=True))

                if amount_val is None or amount_val == 0:
                    continue

                company = cells[1].get_text(strip=True)
                ex_date = parse_international_date(cells[3].get_text(strip=True))
                franking = clean_percent_to_decimal(cells[5].get_text(strip=True))
                pay_date = parse_international_date(cells[7].get_text(strip=True))
                yield_val = clean_percent_to_decimal(cells[8].get_text(strip=True))

                # Step 2: Detail Page with Retry Logic
                detail_url = ASX_URL.format(code.lower())
                vol_num, price_num = None, None
                
                # Try up to 2 times if data is missing
                for attempt in range(2):
                    detail_result = await crawler.arun(
                        url=detail_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS if attempt > 0 else CacheMode.ENABLED,
                            # Wait longer for JS to fill the spans
                            wait_for="span[data-quoteapi='price']",
                            js_code="window.scrollBy(0, 300);" # Small scroll to trigger render
                        )
                    )

                    if detail_result.success:
                        d_soup = BeautifulSoup(detail_result.html, 'html.parser')
                        vol_elem = d_soup.select_one("span[data-quoteapi*='monthAverageVolume']")
                        price_elem = d_soup.select_one("span[data-quoteapi='price']")
                        
                        vol_num = clean_to_number(vol_elem.get_text(strip=True)) if vol_elem else None
                        price_num = clean_to_number(price_elem.get_text(strip=True)) if price_elem else None
                        
                        if vol_num and price_num: # If we got data, break retry loop
                            break
                        
                        # If data still missing, wait a bit before retry
                        await asyncio.sleep(2)

                total_value = vol_num * price_num if vol_num and price_num else None
                print(f"✅ [{i+1}] {code:5} | Price: {price_num:6} | Vol: {vol_num}")

                results.append({
                    "Code": code, "Company": company, "Ex Date": ex_date,
                    "Amount": amount_val, "Franking": franking, "Pay Date": pay_date,
                    "Yield": yield_val, "Price": price_num, "4W Volume": vol_num,
                    "Total Value": total_value
                })

                # Human-like delay between stocks
                await asyncio.sleep(random.uniform(3.0, 5.0))

            except Exception as e:
                print(f"⚠️ Error at row {i} ({code if 'code' in locals() else 'unknown'}): {e}")

    # Export results
    if results:
        df = pd.DataFrame(results)
        df.to_csv("asx_dividends_crawl4ai.csv", index=False, encoding='utf-8-sig')
        print(f"\n🎉 Success! Processed {len(results)} companies.")

if __name__ == "__main__":
    asyncio.run(main())