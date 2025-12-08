# user_store.py
import json
import os
from typing import Dict, Any, List

STORE_PATH = os.path.join(os.path.dirname(__file__), "user_loans.json")

def _load_store() -> Dict[str, Any]:
    if not os.path.exists(STORE_PATH):
        return {}
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_store(data: Dict[str, Any]) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_application(user_id: str, application: Dict[str, Any]) -> None:
    """
    user_id: email or phone
    application: dict with fields like:
      {
        "id": "...",
        "created_at": "...",
        "status": "APPROVED",
        "amount": 400000,
        "tenure": 24,
        "emi": 18744,
        "sanction_letter_path": "sanctions/Riya_2025....pdf"
      }
    """
    data = _load_store()
    apps: List[Dict[str, Any]] = data.get(user_id, [])
    apps.append(application)
    data[user_id] = apps
    _save_store(data)

def get_applications(user_id: str) -> List[Dict[str, Any]]:
    data = _load_store()
    return data.get(user_id, [])
