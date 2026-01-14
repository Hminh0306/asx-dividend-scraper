# This script acts as a bridge between n8n and Docker
from flask import Flask, request
import subprocess
import threading

app = Flask(__name__)

def run_scraper():
    # The exact command you used to run the crawler
    command = 'docker run --rm --shm-size=2gb -v "%cd%:/app" asx-crawl-4ai'
    print(f"🚀 Starting Crawler: {command}")
    subprocess.run(command, shell=True)
    print("✅ Crawling finished!")

@app.route('/trigger-crawl', methods=['POST'])
def trigger():
    # Run the scraper in a separate thread so n8n doesn't timeout
    thread = threading.Thread(target=run_scraper)
    thread.start()
    return {"status": "Job started"}, 200

if __name__ == '__main__':
    # Run the server on port 5000
    print("📡 Bridge Server is running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)