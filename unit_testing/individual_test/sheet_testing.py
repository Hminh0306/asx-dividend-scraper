from app.sheet_functions import get_worksheet

def test_sheet_access():
    """
    Test for whether the service account can access the Google Sheet
    Raises a clear error if permission or config are wrong
    """
    ws = get_worksheet()

    if not ws:
        return False

    title = ws.title
    rows = ws.row_count
    cols = ws.col_count

    print("✅ Google Sheets access OK")
    print(f"   Sheet title : {title}")
    print(f"   Size        : {rows} rows × {cols} columns")
    return True