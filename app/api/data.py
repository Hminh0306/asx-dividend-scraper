import requests
import os
from dotenv import load_dotenv

load_dotenv()

VERCEL_WEBSITE_NAME = os.getenv("VERCEL_WEBSITE_NAME")

def update_frontend(fetched_data):
    url = f"https://{VERCEL_WEBSITE_NAME}.vercel.app/api/revalidate"

    parameters = {
        "secret": os.getenv("REVALIDATE_SECRET"),
        "tag": "dividends"                              # tag for data group to refresh
    }

    try:
        response = requests.get(url, params=parameters)
        if response.status_code == 200:
            print("Vercel cache refreshed successfully")
        else:
            print(f"Signal failed: {response.text}")
    except Exception as e:
        print(f"Signal error: {e}")
