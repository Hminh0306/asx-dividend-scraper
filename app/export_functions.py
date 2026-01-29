import os
from pathlib import Path
import pandas as pd
from datetime import datetime

DOWNLOAD_PATHS = Path.home() / 'Downloads'

# Testing functions to pull to local database
def save_to_download(data_results):
    df = pd.DataFrame(data_results)

    formatted_time = str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    file_name = f"output_csv_{formatted_time}.csv"

    full_path = DOWNLOAD_PATHS/ file_name

    # Write to csv and save to Download
    df.to_csv(full_path, index=False)

    print(f"✅ Local test file saved: {full_path}")

