import os


# Export functions to Downloads directory
def export_to_downloads(results):
    return

# Update results to Google Sheet:
def update_to_google_sheets(db_query):
    return

# Save results to database
def save_to_db(results):
    import sqlite3
    conn = sqlite3.connect('scraped_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dividends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            company TEXT,
            ex_date TEXT,
            amount REAL,
            pay_date TEXT,
            yield REAL,
            price REAL,
            volume REAL
        )
    ''')

    for item in results:
        cursor.execute('''
            INSERT INTO dividends (code, company, ex_date, amount, pay_date, yield, price, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('Code'),
            item.get('Company'),
            item.get('Ex Date'),
            item.get('Amount'),
            item.get('Pay Date'),
            item.get('Yield'),
            item.get('Price'),
            item.get('4W Volume') # Key must match your output exactly
        ))
    
    conn.commit()
    conn.close()