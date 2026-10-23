import os
from mcp.server.fastmcp import FastMCP

from finance import init_db, add_expense, get_summary

mcp = FastMCP("Pocket Friend")

# For the demo, keep the budget configurable.
DEFAULT_BUDGET = float(os.getenv("POCKET_FRIEND_BUDGET", "5000"))


@mcp.tool()
def get_budget_status() -> dict:
    """Get the user's recorded spending and remaining budget."""
    init_db()
    summary = get_summary(DEFAULT_BUDGET)

    return {
        "currency": "INR",
        "monthly_budget": summary["monthly_budget"],
        "total_spent": summary["total_spent"],
        "remaining": summary["remaining"],
        "note": (
            "Spending currently includes all saved expenses, "
            "not only the current month."
        ),
    }


@mcp.tool()
def record_expense(
    amount: float,
    category: str,
    note: str = ""
) -> dict:
    """Record a positive expense in Indian rupees."""
    init_db()

    allowed_categories = {
        "Food", "Travel", "Education", "Shopping",
        "Entertainment", "Health", "Other"
    }

    if amount <= 0 or amount > 1_000_000:
        return {"success": False, "message": "Enter a valid amount."}

    if category not in allowed_categories:
        return {
            "success": False,
            "message": "Please choose a valid expense category."
        }

    if len(note) > 200:
        return {
            "success": False,
            "message": "Keep the note under 200 characters."
        }

    add_expense(amount, category, note)

    return {
        "success": True,
        "message": f"Recorded ₹{amount:.2f} for {category}.",
        "category": category,
        "amount": amount,
    }


@mcp.tool()
def check_affordability(price: float) -> dict:
    """Check how a purchase would affect the entered budget."""
    init_db()

    if price <= 0 or price > 1_000_000:
        return {
            "success": False,
            "message": "Enter a positive price up to ₹10,00,000."
        }

    summary = get_summary(DEFAULT_BUDGET)
    remaining = summary["remaining"]
    after_purchase = remaining - price

    return {
        "currency": "INR",
        "price": price,
        "remaining_before": remaining,
        "remaining_after": after_purchase,
        "fits_budget": after_purchase >= 0,
        "message": (
            "The purchase fits within your entered budget."
            if after_purchase >= 0
            else "The purchase would exceed your entered budget."
        ),
        "note": (
            "This checks your recorded expenses and entered budget, "
            "not your actual bank balance or upcoming bills."
        ),
    }


if __name__ == "__main__":
    init_db()
    mcp.run(transport="streamable-http")