"""Pydantic models for the Expense Tracker API."""
from datetime import date as date_type
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    """Payload for creating a new expense. `id` is assigned by the server."""

    title: str = Field(..., min_length=1, max_length=200, description="Short description of the expense")
    amount: float = Field(..., gt=0, description="Expense amount, must be greater than 0")
    category: str = Field(..., min_length=1, max_length=100, description="Category, e.g. Food, Transport")
    date: date_type = Field(..., description="Date the expense occurred (YYYY-MM-DD)")

    @field_validator("title", "category")
    @classmethod
    def strip_and_validate_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank or whitespace only")
        return v


class Expense(ExpenseCreate):
    """A stored expense, includes the server-assigned id."""

    id: int


class ExpenseTotalResponse(BaseModel):
    filters_applied: dict
    count: int
    total_amount: float
    by_category: dict[str, float]
