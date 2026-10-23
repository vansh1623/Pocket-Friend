import re
import streamlit as st
from finance import init_db, add_expense, get_expenses, get_summary

st.set_page_config(
    page_title="Pocket Friend",
    page_icon="💚",
    layout="wide"
)

init_db()

# ---------- Helper functions ----------

def find_category(text):
    text = text.lower()

    categories = {
        "Food": ["lunch", "dinner", "breakfast", "food", "snack",
                 "restaurant", "pizza", "chai", "tea", "coffee"],
        "Travel": ["bus", "auto", "cab", "uber", "ola", "petrol",
                   "fuel", "train", "metro", "travel", "fare"],
        "Education": ["book", "books", "college", "course", "exam",
                      "stationery", "tuition"],
        "Shopping": ["shirt", "shoes", "clothes", "shopping", "bag"],
        "Entertainment": ["movie", "game", "gaming", "subscription"],
        "Health": ["medicine", "doctor", "hospital", "health"]
    }

    for category, keywords in categories.items():
        if any(word in text for word in keywords):
            return category

    return "Other"


def extract_amount(text):
    # Supports: ₹120, 120 rupees, Rs. 120, and "spent 120"
    match = re.search(
        r"(?:₹|rs\.?\s*)\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)"
        r"|(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?)?",
        text.lower()
    )

    if not match:
        return None

    value = match.group(1) or match.group(2)
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def expense_note(text, amount):
    note = text.lower()
    note = re.sub(r"(?:₹|rs\.?\s*)\s*\d[\d,]*(?:\.\d+)?", " ", note)
    note = re.sub(r"\d[\d,]*(?:\.\d+)?\s*(?:rupees?|rs\.?)?", " ", note)
    note = re.sub(
        r"\b(i|just|spent|spend|add|added|record|recorded|"
        r"log|paid|pay|for|on|rupees|rs)\b",
        " ",
        note
    )
    note = re.sub(r"\s+", " ", note).strip(" .,-")

    return note or "Expense added through Pocket Friend"


def get_budget_status(budget):
    summary = get_summary(budget)
    spent = summary["total_spent"]
    remaining = budget - spent

    return spent, remaining


def respond(message, budget):
    text = message.lower().strip()
    amount = extract_amount(text)
    spent, remaining = get_budget_status(budget)

    # Check questions before expense-entry commands.
    if any(word in text for word in ["can i afford", "afford", "should i buy"]):
        if amount is None:
            return "Tell me the price, for example: Can I afford ₹500?"

        after_purchase = remaining - amount

        if after_purchase < 0:
            return (
                f"That purchase costs ₹{amount:,.2f}. Your remaining "
                f"budget is ₹{remaining:,.2f}, so it would exceed your "
                f"budget by ₹{abs(after_purchase):,.2f}. I'd suggest "
                "waiting or choosing a cheaper option."
            )

        return (
            f"Your remaining budget is ₹{remaining:,.2f}. After a "
            f"₹{amount:,.2f} purchase, you'd have ₹{after_purchase:,.2f} "
            "left in that budget. Check your actual bank balance before buying."
        )

    if any(word in text for word in ["how much have i spent", "total spent",
                                     "my spending", "my expenses", "spent so far"]):
        return f"You've recorded ₹{spent:,.2f} in expenses. Your remaining budget is ₹{remaining:,.2f}."

    if any(word in text for word in ["remaining", "money left", "budget left",
                                     "how much left", "left in my budget"]):
        return f"You have ₹{remaining:,.2f} remaining in your budget."

    if any(word in text for word in ["save", "saving", "savings"]):
        target = amount if amount is not None else 2000
        if remaining >= target:
            return (
                f"Your target is ₹{target:,.2f}. Based on the budget "
                f"you have left, that target fits on paper, with "
                f"₹{remaining - target:,.2f} remaining afterward. "
                "Set that amount aside only if your essential expenses are covered."
            )

        shortfall = target - remaining
        return (
            f"Your savings target is ₹{target:,.2f}, but only "
            f"₹{remaining:,.2f} remains in your budget. The gap is "
            f"₹{shortfall:,.2f}. Try lowering the target or reducing "
            "non-essential spending. Don't skip essentials to save."
        )

    if any(word in text for word in ["advice", "help me budget", "budget advice",
                                     "what should i do", "analyze"]):
        if remaining < 0:
            return (
                f"You are ₹{abs(remaining):,.2f} over your budget. "
                "Pause non-essential purchases and review recent expenses."
            )

        if budget > 0 and remaining < budget * 0.2:
            return (
                f"You have ₹{remaining:,.2f} left, less than 20% of "
                "your budget. Prioritize essentials and pause optional spending."
            )

        return (
            f"You have ₹{remaining:,.2f} remaining. Keep tracking each "
            "purchase, prioritize essentials, and review your spending "
            "before making larger purchases."
        )

    # Add an expense only when the message looks like an expense command.
    expense_words = ["spent", "spend", "add", "record", "log", "paid for"]
    looks_like_expense = any(word in text for word in expense_words)

    if looks_like_expense and amount is not None and amount > 0:
        category = find_category(text)
        note = expense_note(text, amount)
        add_expense(amount, category, note)

        return (
            f"Done! I recorded ₹{amount:,.2f} for {note} "
            f"under {category}. Your budget totals will update."
        )

    return (
        "I'm your Pocket Friend! Try one of these:\n\n"
        "• I spent ₹120 on lunch\n"
        "• Add 80 rupees for bus fare\n"
        "• How much have I spent?\n"
        "• Can I afford ₹500?\n"
        "• How can I save ₹2,000?\n"
        "• Give me budget advice"
    )


# ---------- App interface ----------

st.title("💚 Pocket Friend")
st.caption("Your money. Your friend. Your friendly money companion.")

st.sidebar.header("⚙️ Budget Settings")
monthly_budget = st.sidebar.number_input(
    "Monthly budget (₹)",
    min_value=0.0,
    value=5000.0,
    step=500.0
)

st.sidebar.info("Track expenses, understand your spending, and plan smarter.")

spent, remaining = get_budget_status(monthly_budget)

st.subheader("💰 Your Financial Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Budget", f"₹{monthly_budget:,.0f}")
col2.metric("Recorded Expenses", f"₹{spent:,.0f}")
col3.metric(
    "Budget Remaining",
    f"₹{remaining:,.0f}",
    delta="Over budget" if remaining < 0 else None,
    delta_color="inverse"
)

st.divider()

st.subheader("➕ Add an Expense")
with st.form("expense_form", clear_on_submit=True):
    amount = st.number_input("Amount (₹)", min_value=1.0, value=50.0, step=10.0)
    category = st.selectbox(
        "Category",
        ["Food", "Travel", "Education", "Shopping",
         "Entertainment", "Health", "Other"]
    )
    note = st.text_input("What did you spend on?", placeholder="e.g. Lunch at college")
    submitted = st.form_submit_button("Save Expense")

    if submitted:
        add_expense(amount, category, note)
        st.success("Expense saved!")
        st.rerun()

st.divider()

st.subheader("🤝 Chat with Pocket Friend")
st.caption("Try natural-language commands. This version uses local rules, not a live AI model.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm Pocket Friend 💚 Tell me about an expense, "
                "ask about your remaining budget, or ask whether you "
                "can afford a purchase."
            )
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("e.g. I spent ₹120 on lunch")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    answer = respond(question, monthly_budget)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
    st.rerun()

st.divider()

st.subheader("📊 Expense History")
expenses = get_expenses()

if not expenses.empty:
    st.dataframe(expenses, use_container_width=True, hide_index=True)

    if "category" in expenses.columns and "amount" in expenses.columns:
        st.bar_chart(expenses.groupby("category")["amount"].sum())
else:
    st.info("No expenses recorded yet. Add your first expense above.")

st.caption("Pocket Friend MVP • Local database • Advice is based on recorded expenses and your entered budget.")