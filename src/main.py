"""Smart Expense Tracker API.

Endpoints:
    POST   /expenses            -> add a new expense
    GET    /expenses            -> list expenses (supports filters)
    GET    /expenses/{id}       -> get a single expense
    DELETE /expenses/{id}       -> delete an expense
    GET    /expenses/total      -> total (overall + by category), same filters as list
"""
from datetime import date as date_type
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status

from src.models import Expense, ExpenseCreate, ExpenseTotalResponse
from src.storage import ExpenseStore

app = FastAPI(
    title="Smart Expense Tracker API",
    description=(
        "A simple REST API for tracking personal expenses. Supports adding, "
        "listing, filtering (by category, title search, date range, amount "
        "range), totaling, and deleting expenses."
    ),
    version="1.0.0",
)

store = ExpenseStore()


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "Smart Expense Tracker API",
        "docs": "/docs",
        "endpoints": ["/expenses", "/expenses/{id}", "/expenses/total"],
    }


@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED, tags=["expenses"])
def add_expense(payload: ExpenseCreate):
    """Add a new expense. `id` is assigned automatically."""
    return store.add(payload)


@app.get("/expenses", response_model=list[Expense], tags=["expenses"])
def list_expenses(
    category: Optional[str] = Query(None, description="Filter by exact category (case-insensitive)"),
    q: Optional[str] = Query(None, description="Search: case-insensitive substring match on title"),
    date_from: Optional[date_type] = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
    date_to: Optional[date_type] = Query(None, description="Inclusive end date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Inclusive minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Inclusive maximum amount"),
):
    """List all expenses. All filters are optional and combine with AND logic.

    Examples:
      - /expenses?category=Food
      - /expenses?q=coffee
      - /expenses?date_from=2026-01-01&date_to=2026-01-31
      - /expenses?category=Food&date_from=2026-01-01&min_amount=10
    """
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be on or before date_to")
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=400, detail="min_amount must be <= max_amount")

    return store.filter(
        category=category,
        q=q,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
    )


@app.get("/expenses/total", response_model=ExpenseTotalResponse, tags=["expenses"])
def get_total(
    category: Optional[str] = Query(None, description="Filter by exact category (case-insensitive)"),
    q: Optional[str] = Query(None, description="Search: case-insensitive substring match on title"),
    date_from: Optional[date_type] = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
    date_to: Optional[date_type] = Query(None, description="Inclusive end date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Inclusive minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Inclusive maximum amount"),
):
    """Calculate total expenses. With no filters, totals everything.

    Applying any filter (category, q, date range, amount range) totals only
    the matching subset -- e.g. /expenses/total?category=Food&date_from=2026-01-01
    gives the total spent on Food since Jan 1, 2026.

    The response always includes a `by_category` breakdown of the *filtered*
    result set, plus an overall `total_amount` and `count`.
    """
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be on or before date_to")
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=400, detail="min_amount must be <= max_amount")

    matched = store.filter(
        category=category,
        q=q,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
    )

    total_amount = round(sum(e.amount for e in matched), 2)
    by_category: dict[str, float] = {}
    for e in matched:
        by_category[e.category] = round(by_category.get(e.category, 0.0) + e.amount, 2)

    return ExpenseTotalResponse(
        filters_applied={
            "category": category,
            "q": q,
            "date_from": date_from,
            "date_to": date_to,
            "min_amount": min_amount,
            "max_amount": max_amount,
        },
        count=len(matched),
        total_amount=total_amount,
        by_category=by_category,
    )


@app.get("/expenses/{expense_id}", response_model=Expense, tags=["expenses"])
def get_expense(expense_id: int):
    expense = store.get_by_id(expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail=f"Expense with id {expense_id} not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_200_OK, tags=["expenses"])
def delete_expense(expense_id: int):
    deleted = store.delete(expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Expense with id {expense_id} not found")
    return {"message": f"Expense {expense_id} deleted successfully"}
