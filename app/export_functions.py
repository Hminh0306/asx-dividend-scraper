import pandas as pd 
from pathlib import Path

DOWNLOAD_PATH = Path.home() / 'Downloads'

def _get_timestamp(data_results):
    _timestamp = data_results[0]['Last Updated']
    return _timestamp

def export_to_downloads(data_results, name=""):
    _timestamp = _get_timestamp(data_results)
    
    filename = f"asx-dividend-{name}-{_timestamp}.csv"
    filepath = DOWNLOAD_PATH / filename

    df = pd.DataFrame(data_results)
    df.to_csv(filepath, index=False)

    print("Downloaded csv file to Download folder")