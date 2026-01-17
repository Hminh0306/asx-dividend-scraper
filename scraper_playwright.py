import asyncio
import pandas as pd
import sys
import io
import os
import random
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from pathlib import Path
from bs4 import BeautifulSoup
from app.sheet_functions import overwrite_sheet_with_df, test_sheet_access

# Set encoding for Windows Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- CONFIGURATION ---
UPCOMING_URL = "https://www.marketindex.com.au/upcoming-dividends"
ASX_URL = "https://www.marketindex.com.au/asx/{}"

# --- FIREBASE INITIALIZATION ---
def init_firebase():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "serviceAccountKey.json")
        if not os.path.exists(json_path):
            print(f"⚠️ Firebase Key not found at {json_path}. Firestore sync disabled.")
            return None
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase error: {e}")
        return None

db = init_firebase()

def get_history_record_dir():
    env_dir = os.getenv("HISTORY_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (Path.home() / "Downloads").resolve()

out_dir = get_history_record_dir()
out_dir.mkdir(parents=True, exist_ok=True)

# --- UTILS ---
def parse_international_date(date_str):
    if not date_str or date_str == "N/A": return "N/A"
    current_year = datetime.now().year
    try:
        return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {current_year}", "%d %b %Y").strftime("%Y-%m-%d")
        except: return date_str

def clean_to_number(text):
    if not text or text in ['\u2010', '-', 'N/A', '']: return None
    try:
        return float(text.replace(',', '').replace('$', '').replace('%', '').strip())
    except: return None

def clean_percent_to_decimal(text):
    val = clean_to_number(text)
    return val / 100 if val is not None else None

# --- MAIN SCRAPER ---
async def scraper():
    results = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="table tbody tr",
        page_timeout=60000,
        js_code="window.scrollTo(0, document.body.scrollHeight/2);", 
        wait_for_images=True
    )

    async with AsyncWebCrawler() as crawler:
        print(f"🌐 Fetching main list: {UPCOMING_URL}")
        result = await crawler.arun(url=UPCOMING_URL, config=run_config)
        
        if not result.success:
            print(f"❌ Failed to crawl: {result.error_message}")
            return []

        soup = BeautifulSoup(result.html, 'html.parser')
        rows = soup.select("table tbody tr")
        print(f"📊 Found {len(rows)} potential rows.")

        for i, row in enumerate(rows):
            code = "Unknown"
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

                # Step 2: Detail Page
                detail_url = ASX_URL.format(code.lower())
                vol_num, price_num = None, None
                
                for attempt in range(2):
                    detail_result = await crawler.arun(
                        url=detail_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS if attempt > 0 else CacheMode.ENABLED,
                            wait_for="span[data-quoteapi*='monthAverageVolume']",
                            js_code="window.scrollBy(0, 300);" 
                        )
                    )

                    if detail_result.success:
                        d_soup = BeautifulSoup(detail_result.html, 'html.parser')
                        vol_elem = d_soup.select_one("span[data-quoteapi*='monthAverageVolume']")
                        price_elem = d_soup.select_one("span[data-quoteapi='price']")
                        
                        vol_num = clean_to_number(vol_elem.get_text(strip=True)) if vol_elem else None
                        price_num = clean_to_number(price_elem.get_text(strip=True)) if price_elem else None
                        
                        if vol_num is not None and price_num is not None:
                            break
                        await asyncio.sleep(5)

                total_value = vol_num * price_num if vol_num and price_num else None
                
                # Dữ liệu vừa crawl được
                data_item = {
                    "Crawl Date": today_str,
                    "Code": code, 
                    "Company": company, 
                    "Ex Date": ex_date,
                    "Amount": amount_val, 
                    "Franking": franking, 
                    "Pay Date": pay_date,
                    "Yield": yield_val, 
                    "Price": price_num, 
                    "4W Volume": vol_num,
                    "Total Value": total_value,
                    "last_updated": firestore.SERVER_TIMESTAMP if db else datetime.now().isoformat()
                }

                # --- FIREBASE SYNC (SMART UPDATE) ---
                # --- FIREBASE SYNC (CÁCH 2: LƯU LỊCH SỬ THEO NGÀY & VÁ DỮ LIỆU) ---
                if db:
                    # 1. Tham chiếu đến Document chính của mã chứng khoán
                    doc_ref = db.collection("asx_dividends").document(code)
                    
                    # Lọc bỏ các giá trị None cho payload cập nhật
                    update_payload = {k: v for k, v in data_item.items() if v is not None}
                    
                    try:
                        doc_snap = doc_ref.get()
                        if doc_snap.exists:
                            # A. VÁ DỮ LIỆU: Nếu bản crawl hôm nay bị None, lấy dữ liệu cũ từ Firebase đắp vào
                            old_data = doc_snap.to_dict()
                            for key in ["Price", "4W Volume", "Total Value"]:
                                if data_item.get(key) is None and old_data.get(key) is not None:
                                    data_item[key] = old_data.get(key)
                                    # Cập nhật luôn vào payload để lưu lịch sử hôm nay có số đẹp
                                    update_payload[key] = old_data.get(key)
                            
                            # B. Cập nhật Document chính (Latest Data)
                            doc_ref.update(update_payload)
                        else:
                            # C. Mã mới hoàn toàn
                            doc_ref.set(data_item)

                        # 2. LƯU LỊCH SỬ: Tạo một bản ghi riêng trong sub-collection 'history'
                        # Dùng ngày hôm nay làm ID document để không bị trùng
                        doc_ref.collection("history").document(today_str).set(update_payload)
                        
                        print(f"🔥 [Firestore] Synced {code} & Saved History for {today_str}")

                    except Exception as fe:
                        print(f"❌ Firestore error for {code}: {fe}")

                results.append(data_item)
                print(f"✅ [{i+1}] {code:5} | Price: {data_item['Price']} | Vol: {data_item['4W Volume']}")

                await asyncio.sleep(random.uniform(3.0, 5.0))

            except Exception as e:
                print(f"⚠️ Error at row {i} ({code}): {e}")
    
    return results

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        df = pd.DataFrame(data_results)
        
        # 2. Save Local History (CSV)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = out_dir / f"asx_dividends_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"📍 Saved CSV to: {csv_path}")

        # 3. Overwrite Google Sheet
        try:
            sheet_df = df.copy()
            # Xử lý cột last_updated cho Google Sheets (vì Sheets không hiểu Firestore Timestamp)
            if 'last_updated' in sheet_df.columns:
                sheet_df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            overwrite_sheet_with_df(sheet_df)
            print("🚀 Google Sheets updated successfully!")
        except Exception as e:
            print(f"❌ Google Sheets update failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())