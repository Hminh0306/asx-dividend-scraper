import os
import redshift_connector
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """
    Connects to Redshift
    """
    port_env = os.getenv('REDSHIFT_PORT') or '5439'

    try:
        conn = redshift_connector.connect(
            host=os.getenv('REDSHIFT_HOST'),
            database=os.getenv('REDSHIFT_DATABASE'),
            user=os.getenv('REDSHIFT_USER'),
            password=os.getenv('REDSHIFT_PASSWORD'),
            port=int(port_env) if os.getenv('REDSHIFT_PORT') else 5439,
            ssl=True
        )
        conn.autocommit = True
        print("✅ Successfully connected to Redshift Database")
        return conn
    except ValueError:
        print(f"⚠️ Invalid REDSHIFT_PORT: '{port_env}'. Defaulting to 5439.")
        # Optional: retry connection with 5439 here or just fail
        return None
    except Exception as e:
        print(f"❌ Redshift Error: {e}")
        return None

def update_to_redshift(data_results):
    if not data_results:
        print("⚠️ No data results provided to update_to_redshift.")
        return
    conn = get_connection()
    if not conn:
        print("❌ Could not establish Redshift connection. Data not saved.")
        return
    
    try:
        cursor = conn.cursor()
        # We map your scraper keys to the SQL column names
        # Note: We use "4w_volume" with quotes because it starts with a number
        sql = """
            INSERT INTO public.dividend_data 
            (crawl_date, code, company, ex_date, pay_date, amount, franking, yield, price, "4w_volume", total_value, last_update)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Convert list of dicts to list of tuples for the connector
        rows_to_insert = [
            (
                item.get("Crawl Date"),
                item.get("Code"),
                item.get("Company"),
                item.get("Ex Date"),
                item.get("Pay Date"),
                item.get("Amount"),
                item.get("Franking"),
                item.get("Yield"),
                item.get("Price"),
                item.get("4W Volume"),
                item.get("Total Value"),
                item.get("last_updated")
            )
            for item in data_results
        ]

        # 3. Execute Bulk Insert
        # executemany() is optimized for batching rows in one network trip
        cursor.executemany(sql, rows_to_insert)
        
        print(f"🚀 Successfully inserted {len(rows_to_insert)} rows into Redshift.")    
    except Exception as e:
        print(f"❌ Data Insertion Error: {e}")
    finally:
        conn.close() # Close after use - prevent resource leakage
        print("🔌 Redshift connection closed.")

def fetch_latest_data_from_redshift_on(time_stamp):
    
    return