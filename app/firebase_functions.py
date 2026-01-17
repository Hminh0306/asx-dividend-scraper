import os
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

# Firebase Key fetch
PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSON_KEY_PATH = PROJECT_ROOT / "serviceAccountKey.json"

# --- FIREBASE INITIALIZATION ---
def init_firebase():
    try:
        # Get key
        json_path = JSON_KEY_PATH
        if not json_path.exists():
            print(f"⚠️ Firebase Key not found at {json_path}. Firestore sync disabled.")
            return None
        
        cred = credentials.Certificate(str(json_path))

        # Prevent "default app already exists"
        if not firebase_admin._apps:    
            firebase_admin.initialize_app(cred)

        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase error: {e}")
        return None
    
db = init_firebase()

def upload_to_firebase(items: list[dict], today_str: str):
    if not db:
        print("⚠️ Firestore disabled.")
        return

    for item in items:
        code = item["Code"]
        doc_ref = db.collection("asx_dividends").document(code)

        update_payload = {k: v for k, v in item.items() if v is not None}

        try:
            doc_snap = doc_ref.get()
            if doc_snap.exists:
                old_data = doc_snap.to_dict()
                for key in ["Price", "4W Volume", "Total Value"]:
                    if item.get(key) is None and old_data.get(key) is not None:
                        item[key] = old_data.get(key)
                        update_payload[key] = old_data.get(key)

                doc_ref.update(update_payload)
            else:
                doc_ref.set(item)

            # Save daily snapshot (history)
            doc_ref.collection("history").document(today_str).set(update_payload)
            print(f"🔥 [Firestore] Synced {code} & Saved History {today_str}")

        except Exception as e:
            print(f"❌ Error at {code}: {e}")

def fetch_data_from_firebase(date_str, collection_name: str = "asx_dividends") -> list[dict]:
    """
    Returns list of dicts from Firestore (latest docs).
    Ensures 'Code' exists (uses doc.id if missing).
    Converts Firestore Timestamp/datetime to strings for Sheets.
    """
    if not db:
        print("⚠️ Firestore disabled.")
        return []

    # Output of list of dict
    data_list = []

    # Reference the collection
    doc_ref = db.collection(collection_name)

    # Stream document
    docs = doc_ref.stream()

    try:
        for doc in docs:
            code = doc.id

            # Read history doc for the date_str
            hist_ref = db.collection(collection_name).document(code).collection('history').document(date_str)
            hist_snap = hist_ref.get()

            if not hist_snap.exists:
                continue
                
            row = hist_snap.to_dict() or {}
            row.setdefault("Code", code)  # ensure Code exists

            # Convert Firestore Timestamp/datetime to string for printing/sheets
            for k, v in list(row.items()):
                if hasattr(v, "isoformat"):
                    try:
                        row[k] = v.isoformat(sep=" ", timespec="seconds")
                    except TypeError:
                        row[k] = v.isoformat()

            data_list.append(row)

        print(f"📥 Fetched {len(data_list)} rows for date {date_str}")
        return data_list
    except Exception as e:
        print(f"❌ fetch_data_from_firebase_by_date error: {e}")
        return []
    
    
