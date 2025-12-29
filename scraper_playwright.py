import sys
import random
import time
import pandas as pd
from playwright.sync_api import sync_playwright
import io
from datetime import datetime

# Fix encoding cho Windows Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

UPCOMING_URL = "https://www.marketindex.com.au/upcoming-dividends"
ASX_URL = "https://www.marketindex.com.au/asx/{}"
USER_DATA_DIR = "./browser_session"

def parse_international_date(date_str):
    """Chuyển đổi các định dạng ngày sang YYYY-MM-DD."""
    if not date_str or date_str == "N/A":
        return "N/A"
    
    current_year = datetime.now().year
    try:
        # Thử định dạng: 29 Dec 2025 hoặc 9 Jan 2026
        return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Thử định dạng không có năm: 29 Dec (tự hiểu là năm hiện tại)
            return datetime.strptime(f"{date_str} {current_year}", "%d %b %Y").strftime("%Y-%m-%d")
        except:
            return date_str

def clean_to_number(text):
    """Xóa $, dấu phẩy và chuyển về float."""
    if not text or text in ['\u2010', '-', 'N/A']:
        return None
    try:
        return float(text.replace(',', '').replace('$', '').replace('%', '').strip())
    except:
        return None

def clean_percent_to_decimal(text):
    """Chuyển 100% thành 1.0, 1.66% thành 0.0166."""
    val = clean_to_number(text)
    return val / 100 if val is not None else None

def get_element_text_with_retry(page, selector, max_attempts=10):
    for attempt in range(2):
        try:
            page.wait_for_selector(selector, timeout=7000)
            for _ in range(max_attempts):
                raw_val = page.locator(selector).first.inner_text().strip()
                if raw_val and raw_val not in ['\u2010', '-', '']:
                    return raw_val
                time.sleep(0.5)
            if attempt == 0: page.reload(wait_until="domcontentloaded")
        except:
            if attempt == 0: page.reload(wait_until="domcontentloaded")
    return "N/A"

def main():
    results = []
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False, channel="chrome", 
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0]
        
        try:
            page.goto(UPCOMING_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("table tbody tr")
        except Exception as e:
            print(f"Lỗi: {e}")
            context.close()
            return

        rows = page.locator("table tbody tr")
        count = rows.count()
        detail_page = context.new_page()

        for i in range(count):
            try:
                cells = rows.nth(i).locator("td")
                code = cells.nth(0).inner_text().strip()
                
                # Kiểm tra Amount trước để lọc
                amount_raw = cells.nth(4).inner_text().strip()
                amount_val = clean_to_number(amount_raw)
                
                if amount_val is None or amount_val == 0:
                    continue

                # Lấy các thông tin khác từ bảng
                company = cells.nth(1).inner_text().strip()
                ex_date = parse_international_date(cells.nth(3).inner_text().strip())
                franking = clean_percent_to_decimal(cells.nth(5).inner_text().strip())
                pay_date = parse_international_date(cells.nth(7).inner_text().strip())
                yield_val = clean_percent_to_decimal(cells.nth(8).inner_text().strip())

                # Vào trang chi tiết lấy Volume và Price
                detail_page.goto(ASX_URL.format(code.lower()), wait_until="domcontentloaded")
                vol_str = get_element_text_with_retry(detail_page, "span[data-quoteapi*='monthAverageVolume']")
                price_str = get_element_text_with_retry(detail_page, "span[data-quoteapi='price']")

                vol_num = clean_to_number(vol_str)
                price_num = clean_to_number(price_str)
                total_value = vol_num * price_num if vol_num and price_num else None

                print(f"[{i+1}] {code}: Amount={amount_val}, Value={total_value}")

                results.append({
                    "Code": code,
                    "Company": company,
                    "Ex Date": ex_date,
                    "Amount": amount_val,
                    "Franking": franking,
                    "Pay Date": pay_date,
                    "Yield": yield_val,
                    "Price": price_num,
                    "4W Volume": vol_num,
                    "Total Value": total_value
                })
                time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print(f"Bỏ qua dòng {i}: {e}")

        context.close()

    if results:
        df = pd.DataFrame(results)
        # Lưu file
        output = "asx_dividends_machine_ready.csv"
        df.to_csv(output, index=False, encoding='utf-8-sig')
        print(f"\nThành công! File '{output}' đã sẵn sàng cho máy đọc.")

if __name__ == "__main__":
    main()