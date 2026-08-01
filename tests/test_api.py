"""Test suite for the Smart Expense Tracker API."""


SAMPLE_EXPENSES = [
    {"title": "Coffee at Blue Bottle", "amount": 5.50, "category": "Food", "date": "2026-01-05"},
    {"title": "Grocery run", "amount": 64.20, "category": "Food", "date": "2026-01-10"},
    {"title": "Metro card", "amount": 30.00, "category": "Transport", "date": "2026-01-12"},
    {"title": "Uber to airport", "amount": 45.75, "category": "Transport", "date": "2026-02-01"},
    {"title": "Movie night", "amount": 20.00, "category": "Entertainment", "date": "2026-02-14"},
]


def seed(client):
    ids = []
    for payload in SAMPLE_EXPENSES:
        r = client.post("/expenses", json=payload)
        assert r.status_code == 201
        ids.append(r.json()["id"])
    return ids


# ---------------------------------------------------------------------------
# Add expense
# ---------------------------------------------------------------------------
def test_add_expense_success(client):
    payload = {"title": "Lunch", "amount": 12.5, "category": "Food", "date": "2026-01-01"}
    r = client.post("/expenses", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Lunch"
    assert body["amount"] == 12.5
    assert body["category"] == "Food"
    assert body["date"] == "2026-01-01"
    assert isinstance(body["id"], int)


def test_add_expense_negative_amount_rejected(client):
    payload = {"title": "Bad expense", "amount": -5, "category": "Food", "date": "2026-01-01"}
    r = client.post("/expenses", json=payload)
    assert r.status_code == 422


def test_add_expense_zero_amount_rejected(client):
    payload = {"title": "Free item", "amount": 0, "category": "Food", "date": "2026-01-01"}
    r = client.post("/expenses", json=payload)
    assert r.status_code == 422


def test_add_expense_missing_field_rejected(client):
    payload = {"title": "Missing amount", "category": "Food", "date": "2026-01-01"}
    r = client.post("/expenses", json=payload)
    assert r.status_code == 422


def test_add_expense_blank_title_rejected(client):
    payload = {"title": "   ", "amount": 5, "category": "Food", "date": "2026-01-01"}
    r = client.post("/expenses", json=payload)
    assert r.status_code == 422


def test_add_expense_bad_date_rejected(client):
    payload = {"title": "Bad date", "amount": 5, "category": "Food", "date": "not-a-date"}
    r = client.post("/expenses", json=payload)
    assert r.status_code == 422


def test_ids_auto_increment(client):
    ids = seed(client)
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# View all / list
# ---------------------------------------------------------------------------
def test_list_expenses_empty(client):
    r = client.get("/expenses")
    assert r.status_code == 200
    assert r.json() == []


def test_list_all_expenses(client):
    seed(client)
    r = client.get("/expenses")
    assert r.status_code == 200
    assert len(r.json()) == len(SAMPLE_EXPENSES)


def test_get_single_expense(client):
    ids = seed(client)
    r = client.get(f"/expenses/{ids[0]}")
    assert r.status_code == 200
    assert r.json()["title"] == SAMPLE_EXPENSES[0]["title"]


def test_get_single_expense_not_found(client):
    r = client.get("/expenses/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
def test_filter_by_category(client):
    seed(client)
    r = client.get("/expenses", params={"category": "Food"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert all(e["category"] == "Food" for e in results)


def test_filter_by_category_case_insensitive(client):
    seed(client)
    r = client.get("/expenses", params={"category": "fOOd"})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_by_title_search(client):
    seed(client)
    r = client.get("/expenses", params={"q": "uber"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert "Uber" in results[0]["title"]


def test_filter_by_date_range(client):
    seed(client)
    r = client.get("/expenses", params={"date_from": "2026-01-01", "date_to": "2026-01-31"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 3  # coffee, grocery, metro card (all in January)


def test_filter_by_amount_range(client):
    seed(client)
    r = client.get("/expenses", params={"min_amount": 20, "max_amount": 50})
    assert r.status_code == 200
    results = r.json()
    amounts = sorted(e["amount"] for e in results)
    assert amounts == [20.00, 30.00, 45.75]


def test_filter_combined_category_and_date(client):
    seed(client)
    r = client.get(
        "/expenses",
        params={"category": "Transport", "date_from": "2026-02-01", "date_to": "2026-02-28"},
    )
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["title"] == "Uber to airport"


def test_filter_no_matches_returns_empty_list(client):
    seed(client)
    r = client.get("/expenses", params={"category": "Nonexistent"})
    assert r.status_code == 200
    assert r.json() == []


def test_filter_invalid_date_range_rejected(client):
    seed(client)
    r = client.get("/expenses", params={"date_from": "2026-02-01", "date_to": "2026-01-01"})
    assert r.status_code == 400


def test_filter_invalid_amount_range_rejected(client):
    seed(client)
    r = client.get("/expenses", params={"min_amount": 100, "max_amount": 10})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Totals
# ---------------------------------------------------------------------------
def test_total_overall(client):
    seed(client)
    r = client.get("/expenses/total")
    assert r.status_code == 200
    body = r.json()
    expected_total = round(sum(e["amount"] for e in SAMPLE_EXPENSES), 2)
    assert body["total_amount"] == expected_total
    assert body["count"] == len(SAMPLE_EXPENSES)


def test_total_by_category_breakdown(client):
    seed(client)
    r = client.get("/expenses/total")
    body = r.json()
    assert body["by_category"]["Food"] == round(5.50 + 64.20, 2)
    assert body["by_category"]["Transport"] == round(30.00 + 45.75, 2)
    assert body["by_category"]["Entertainment"] == 20.00


def test_total_filtered_by_category(client):
    seed(client)
    r = client.get("/expenses/total", params={"category": "Food"})
    body = r.json()
    assert body["total_amount"] == round(5.50 + 64.20, 2)
    assert body["count"] == 2
    assert body["by_category"] == {"Food": round(5.50 + 64.20, 2)}


def test_total_filtered_by_date_range(client):
    seed(client)
    r = client.get("/expenses/total", params={"date_from": "2026-02-01", "date_to": "2026-02-28"})
    body = r.json()
    assert body["total_amount"] == round(45.75 + 20.00, 2)
    assert body["count"] == 2


def test_total_filtered_by_search(client):
    seed(client)
    r = client.get("/expenses/total", params={"q": "grocery"})
    body = r.json()
    assert body["total_amount"] == 64.20
    assert body["count"] == 1


def test_total_combined_filters(client):
    seed(client)
    r = client.get(
        "/expenses/total",
        params={"category": "Transport", "date_from": "2026-01-01", "date_to": "2026-01-31"},
    )
    body = r.json()
    # Only the Metro card falls in Transport + January
    assert body["total_amount"] == 30.00
    assert body["count"] == 1


def test_total_no_expenses(client):
    r = client.get("/expenses/total")
    body = r.json()
    assert body["total_amount"] == 0
    assert body["count"] == 0
    assert body["by_category"] == {}


def test_total_reflects_filters_applied_field(client):
    seed(client)
    r = client.get("/expenses/total", params={"category": "Food"})
    body = r.json()
    assert body["filters_applied"]["category"] == "Food"
    assert body["filters_applied"]["q"] is None


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------
def test_delete_expense(client):
    ids = seed(client)
    r = client.delete(f"/expenses/{ids[0]}")
    assert r.status_code == 200

    r2 = client.get(f"/expenses/{ids[0]}")
    assert r2.status_code == 404

    r3 = client.get("/expenses")
    assert len(r3.json()) == len(SAMPLE_EXPENSES) - 1


def test_delete_nonexistent_expense_returns_404(client):
    r = client.delete("/expenses/9999")
    assert r.status_code == 404


def test_delete_then_total_updates(client):
    ids = seed(client)
    client.delete(f"/expenses/{ids[0]}")  # remove the $5.50 coffee
    r = client.get("/expenses/total")
    expected = round(sum(e["amount"] for e in SAMPLE_EXPENSES) - 5.50, 2)
    assert r.json()["total_amount"] == expected


# ---------------------------------------------------------------------------
# Data persistence sanity (isolation between store instances backed by
# the same file path)
# ---------------------------------------------------------------------------
def test_data_persists_across_store_reload(tmp_path):
    from src.storage import ExpenseStore
    from src.models import ExpenseCreate
    import datetime

    data_file = tmp_path / "persist_test.json"
    store1 = ExpenseStore(data_file=data_file)
    store1.add(ExpenseCreate(title="Persisted item", amount=9.99, category="Misc", date=datetime.date(2026, 1, 1)))

    store2 = ExpenseStore(data_file=data_file)  # simulate a fresh process reading the same file
    all_expenses = store2.get_all()
    assert len(all_expenses) == 1
    assert all_expenses[0].title == "Persisted item"
