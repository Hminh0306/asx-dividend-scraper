import asyncio
import pandas as pd
import sys
import io
import random
import os
import requests
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

# Thiết lập bảng mã cho Terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- CẤU HÌNH ---
UPCOMING_URL = "https://www.marketindex.com.au/upcoming-dividends"
ASX_URL = "https://www.marketindex.com.au/asx/{}"
# URL Webhook của n8n (Dùng host.docker.internal để Docker gọi được máy chủ n8n local)
N8N_WEBHOOK_URL = "http://host.docker.internal:5678/webhook-test/asx-data"

def parse_international_date(date_str):
    """Chuyển đổi định dạng ngày sang YYYY-MM-DD."""
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
    """Xóa ký tự tiền tệ và chuyển sang số thực."""
    if not text or text in ['\u2010', '-', 'N/A', '']:
        return None
    try:
        return float(text.replace(',', '').replace('$', '').replace('%', '').strip())
    except:
        return None

def clean_percent_to_decimal(text):
    """Chuyển 100% thành 1.0."""
    val = clean_to_number(text)
    return val / 100 if val is not None else None

async def main():
    results = []
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="table tbody tr",
        page_timeout=60000,
        js_code="window.scrollTo(0, document.body.scrollHeight/2);", 
        wait_for_images=True
    )

    async with AsyncWebCrawler() as crawler:
        print(f"🌐 Đang lấy danh sách từ: {UPCOMING_URL}")
        result = await crawler.arun(url=UPCOMING_URL, config=run_config)
        
        if not result.success:
            print(f"❌ Lỗi crawl: {result.error_message}")
            return

        soup = BeautifulSoup(result.html, 'html.parser')
        rows = soup.select("table tbody tr")
        print(f"📊 Tìm thấy {len(rows)} hàng tiềm năng.")

        for i, row in enumerate(rows):
            try:
                cells = row.find_all("td")
                if not cells: continue

                code = cells[0].get_text(strip=True)
                amount_val = clean_to_number(cells[4].get_text(strip=True))

                # Chỉ lấy những mã có chia cổ tức > 0
                if amount_val is None or amount_val == 0:
                    continue

                company = cells[1].get_text(strip=True)
                ex_date = parse_international_date(cells[3].get_text(strip=True))
                franking = clean_percent_to_decimal(cells[5].get_text(strip=True))
                pay_date = parse_international_date(cells[7].get_text(strip=True))
                yield_val = clean_percent_to_decimal(cells[8].get_text(strip=True))

                # Bước 2: Truy cập trang chi tiết để lấy Price và Volume
                detail_url = ASX_URL.format(code.lower())
                vol_num, price_num = None, None
                
                for attempt in range(2):
                    detail_result = await crawler.arun(
                        url=detail_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS if attempt > 0 else CacheMode.ENABLED,
                            wait_for="span[data-quoteapi='price']",
                            js_code="window.scrollBy(0, 300);"
                        )
                    )

                    if detail_result.success:
                        d_soup = BeautifulSoup(detail_result.html, 'html.parser')
                        vol_elem = d_soup.select_one("span[data-quoteapi*='monthAverageVolume']")
                        price_elem = d_soup.select_one("span[data-quoteapi='price']")
                        
                        vol_num = clean_to_number(vol_elem.get_text(strip=True)) if vol_elem else None
                        price_num = clean_to_number(price_elem.get_text(strip=True)) if price_elem else None
                        
                        if vol_num and price_num:
                            break
                        await asyncio.sleep(4)

                total_value = vol_num * price_num if vol_num and price_num else None
                print(f"✅ [{i+1}] {code:5} | price: {price_num:6} | Vol: {vol_num}")

                # Lưu vào list kết quả
                results.append({
                    "Code": code, "Company": company, "Ex_Date": ex_date,
                    "Amount": amount_val, "Franking": franking, "Pay_Date": pay_date,
                    "Yield": yield_val, "Price": price_num, "Vol_4W": vol_num,
                    "Total_Value": total_value
                })

                # Nghỉ giữa mỗi lần crawl để tránh bị chặn
                await asyncio.sleep(random.uniform(5.0, 6.0))

            except Exception as e:
                print(f"⚠️ Lỗi tại hàng {i}: {e}")

    # --- XUẤT DỮ LIỆU ---
    if results:
        # 1. Lưu file CSV cục bộ dự phòng
        if not os.path.exists('output'):
            os.makedirs('output')
            
        df = pd.DataFrame(results)
        file_path = "output/asx_dividends.csv"
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"\n💾 Đã lưu file dự phòng tại: {file_path}")

        # 2. Gửi dữ liệu sang n8n qua Webhook
        print(f"📡 Đang gửi {len(results)} dòng dữ liệu sang n8n...")
        try:
            response = requests.post(
                N8N_WEBHOOK_URL, 
                json=results, 
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            if response.status_code == 200:
                print("🎉 THÀNH CÔNG: n8n đã nhận dữ liệu!")
            else:
                print(f"❌ Thất bại: n8n trả về mã {response.status_code}")
        except Exception as e:
            print(f"⚠️ Không thể kết nối tới n8n: {e}")

if __name__ == "__main__":
    asyncio.run(main())