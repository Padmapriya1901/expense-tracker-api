"""Simple JSON-file backed storage for expenses.

Chosen over a database because the assignment explicitly allows in-memory or
local-file storage and this is a small personal-expense tool. A threading
lock guards reads/writes since FastAPI can serve requests concurrently
(e.g. via multiple worker threads for sync-style access).
"""
import json
import threading
from datetime import date as date_type
from pathlib import Path
from typing import Optional

from src.models import Expense, ExpenseCreate

DEFAULT_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "expenses.json"


class ExpenseStore:
    def __init__(self, data_file: Path = DEFAULT_DATA_FILE):
        self._data_file = Path(data_file)
        self._lock = threading.Lock()
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self._data_file.exists():
            self._write_raw({"next_id": 1, "expenses": []})

    # ---------- low-level persistence ----------
    def _read_raw(self) -> dict:
        with open(self._data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_raw(self, data: dict) -> None:
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    # ---------- CRUD ----------
    def add(self, payload: ExpenseCreate) -> Expense:
        with self._lock:
            data = self._read_raw()
            new_id = data["next_id"]
            expense = Expense(id=new_id, **payload.model_dump())
            record = json.loads(expense.model_dump_json())
            data["expenses"].append(record)
            data["next_id"] = new_id + 1
            self._write_raw(data)
            return expense

    def get_all(self) -> list[Expense]:
        with self._lock:
            data = self._read_raw()
            return [Expense(**e) for e in data["expenses"]]

    def get_by_id(self, expense_id: int) -> Optional[Expense]:
        for e in self.get_all():
            if e.id == expense_id:
                return e
        return None

    def delete(self, expense_id: int) -> bool:
        with self._lock:
            data = self._read_raw()
            before = len(data["expenses"])
            data["expenses"] = [e for e in data["expenses"] if e["id"] != expense_id]
            deleted = len(data["expenses"]) != before
            if deleted:
                self._write_raw(data)
            return deleted

    def clear(self) -> None:
        """Used by tests to reset state between test cases."""
        with self._lock:
            self._write_raw({"next_id": 1, "expenses": []})

    # ---------- filtering ----------
    def filter(
        self,
        category: Optional[str] = None,
        q: Optional[str] = None,
        date_from: Optional[date_type] = None,
        date_to: Optional[date_type] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> list[Expense]:
        """Return expenses matching all provided filters (AND semantics).

        - category: case-insensitive exact match
        - q: case-insensitive substring match against title
        - date_from / date_to: inclusive date range
        - min_amount / max_amount: inclusive amount range
        """
        results = self.get_all()

        if category is not None:
            cat_lower = category.strip().lower()
            results = [e for e in results if e.category.strip().lower() == cat_lower]

        if q is not None:
            q_lower = q.strip().lower()
            results = [e for e in results if q_lower in e.title.lower()]

        if date_from is not None:
            results = [e for e in results if e.date >= date_from]

        if date_to is not None:
            results = [e for e in results if e.date <= date_to]

        if min_amount is not None:
            results = [e for e in results if e.amount >= min_amount]

        if max_amount is not None:
            results = [e for e in results if e.amount <= max_amount]

        return results
