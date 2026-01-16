import streamlit as st

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= TITLE =================
st.title("🏚️ Fixer-Upper Rental Deal Analyzer")

# ================= LAYOUT =================
left_col, right_col = st.columns([1, 1])

# ================= LEFT COLUMN =================
with left_col:
    st.header("🔢 Deal Inputs")

    purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, step=1000.0)
    rehab_cost = st.number_input("Rehab Cost ($)", min_value=0.0, step=1000.0)
    arv = st.number_input("After Repair Value (ARV) ($)", min_value=0.0, step=1000.0)

    monthly_rent = st.number_input("Monthly Rent ($)", min_value=0.0, step=100.0)

    property_tax = st.number_input("Annual Property Tax ($)", min_value=0.0)
    insurance = st.number_input("Annual Insurance ($)", min_value=0.0)
    maintenance = st.number_input("Annual Maintenance ($)", min_value=0.0)

    vacancy_rate = st.number_input("Vacancy Rate (%)", min_value=0.0, max_value=100.0) / 100
    management_fee = st.number_input("Management Fee (%)", min_value=0.0, max_value=100.0) / 100

    down_payment_pct = st.number_input("Down Payment (%)", min_value=0.0, max_value=100.0) / 100
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=15.0) / 100
    loan_term = st.number_input("Loan Term (Years)", min_value=1, max_value=40)

    analyze = st.button("📊 Analyze Deal")

# ================= CALCULATIONS =================
if analyze:
    total_investment = purchase_price + rehab_cost
    annual_rent = monthly_rent * 12

    vacancy_loss = annual_rent * vacancy_rate
    management_cost = annual_rent * management_fee

    expense_breakdown_annual = {
        "Property Tax": property_tax,
        "Insurance": insurance,
        "Maintenance": maintenance,
        "Vacancy Loss": vacancy_loss,
        "Management Fee": management_cost
    }

    total_operating_expenses_annual = sum(expense_breakdown_annual.values())

    noi_annual = annual_rent - total_operating_expenses_annual

    loan_amount = purchase_price * (1 - down_payment_pct)
    cash_invested = purchase_price * down_payment_pct + rehab_cost

    monthly_rate = interest_rate / 12
    total_payments = loan_term * 12

    if interest_rate > 0:
        monthly_payment = (
            loan_amount *
            (monthly_rate * (1 + monthly_rate) ** total_payments) /
            ((1 + monthly_rate) ** total_payments - 1)
        )
    else:
        monthly_payment = loan_amount / total_payments

    annual_debt = monthly_payment * 12
    cash_flow_annual = noi_annual - annual_debt

    cap_rate = noi_annual / total_investment if total_investment else 0
    coc_return = cash_flow_annual / cash_invested if cash_invested else 0
    equity_pct = (arv - total_investment) / arv if arv else 0

    deal_score = min(
        100,
        (coc_return / 0.15 * 40) +
        (cap_rate / 0.10 * 30) +
        (equity_pct / 0.20 * 30)
    )

    if deal_score >= 85:
        rating = "🔥 Excellent Deal"
    elif deal_score >= 70:
        rating = "✅ Strong Deal"
    elif deal_score >= 50:
        rating = "⚠️ Marginal Deal"
    else:
        rating = "❌ Weak Deal"

    st.session_state.results = {
        "Annual Rent": annual_rent,
        "Monthly Rent": monthly_rent,
        "NOI Annual": noi_annual,
        "NOI Monthly": noi_annual / 12,
        "Cash Flow Annual": cash_flow_annual,
        "Cash Flow Monthly": cash_flow_annual / 12,
        "Debt Annual": annual_debt,
        "Debt Monthly": monthly_payment,
        "Cap Rate": cap_rate,
        "CoC": coc_return,
        "Equity": equity_pct,
        "Score": deal_score,
        "Rating": rating,
        "Expenses Annual": expense_breakdown_annual,
        "Expenses Monthly": {k: v / 12 for k, v in expense_breakdown_annual.items()},
        "Total Expenses Annual": total_operating_expenses_annual,
        "Total Expenses Monthly": total_operating_expenses_annual / 12
    }

# ================= RIGHT COLUMN =================
with right_col:
    st.header("📈 Deal Results")

    if "results" in st.session_state:
        r = st.session_state.results

        view = st.radio(
            "View Mode",
            ["Annual", "Monthly"],
            horizontal=True
        )

        if view == "Annual":
            st.metric("Gross Rent", f"${r['Annual Rent']:,.0f}")
            st.metric("NOI", f"${r['NOI Annual']:,.0f}")
            st.metric("Cash Flow", f"${r['Cash Flow Annual']:,.0f}")
            st.metric("Debt Service", f"${r['Debt Annual']:,.0f}")
            expenses = r["Expenses Annual"]
            total_exp = r["Total Expenses Annual"]
            rent_base = r["Annual Rent"]
        else:
            st.metric("Gross Rent", f"${r['Monthly Rent']:,.0f}")
            st.metric("NOI", f"${r['NOI Monthly']:,.0f}")
            st.metric("Cash Flow", f"${r['Cash Flow Monthly']:,.0f}")
            st.metric("Debt Service", f"${r['Debt Monthly']:,.0f}")
            expenses = r["Expenses Monthly"]
            total_exp = r["Total Expenses Monthly"]
            rent_base = r["Monthly Rent"]

        st.metric("Cap Rate", f"{r['Cap Rate']:.2%}")
        st.metric("Cash-on-Cash Return", f"{r['CoC']:.2%}")
        st.metric("Equity Percentage", f"{r['Equity']:.2%}")
        st.metric("Rental Deal Score", f"{r['Score']:.0f}/100")
        st.subheader(r["Rating"])

        st.markdown("### 💸 Expense Breakdown")

        for name, value in expenses.items():
            pct = (value / rent_base * 100) if rent_base else 0
            st.write(f"**{name}**: ${value:,.0f} ({pct:.1f}%)")

        st.write(f"**Total Operating Expenses:** ${total_exp:,.0f}")

    else:
        st.info("Enter inputs and click **Analyze Deal**")

# ================= DISCLAIMER =================
st.markdown("---")
st.caption(
    "Disclaimer: This tool is provided for educational and informational purposes only and does not constitute "
    "financial, investment, legal, or tax advice. All calculations are estimates and for illustrative purposes only. "
    "Users should perform their own due diligence and consult with licensed professionals in the United States or Canada."
)
