import sys
from pathlib import Path

# Ensure repo root is importable as `src.*` regardless of where pytest is invoked from.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from src import main as main_module
from src.storage import ExpenseStore


@pytest.fixture()
def client(tmp_path):
    """Fresh FastAPI TestClient backed by an isolated, throwaway JSON file.

    Using a temp file (rather than the real data/expenses.json) means tests
    never touch real user data and each test starts from a clean slate.
    """
    test_data_file = tmp_path / "expenses_test.json"
    main_module.store = ExpenseStore(data_file=test_data_file)
    return TestClient(main_module.app)
