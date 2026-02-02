import requests
import os
from dotenv import load_dotenv

load_dotenv()

VERCEL_WEBSITE_URL= os.getenv("VERCEL_WEBSITE_NAME")
REVALIDATE_SECRET = os.getenv("VERCEL_REVALIATE_SECRET")


def notify_frontend_for_refresh():
    """
    Calls the Next.js API route to purge the cache and refresh the sheet view
    """
    if not VERCEL_WEBSITE_URL:
        print("⚠️ VERCEL_WEBSITE_URL is not set. Skipping frontend notification...")
        return

    url = f"{VERCEL_WEBSITE_URL}/api/revalidate"

    try:
        response = requests.post(
            url,
            json={"secret": REVALIDATE_SECRET},
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Frontend notified successfully")
        else:
            print(f"⚠️ Frontend failed to notified ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Signal error: {e}")