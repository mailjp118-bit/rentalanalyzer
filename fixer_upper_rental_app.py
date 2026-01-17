import streamlit as st
import pandas as pd

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= PRIVACY MESSAGE =================
st.markdown(
    "🔒 **Privacy Notice:** *We do not store or track your deal data. "
    "All calculations run locally and reset when you refresh the page.*"
)

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

    vacancy_rate = st.number_input("Vacancy Rate (%)", 0.0, 100.0) / 100
    management_fee = st.number_input("Management Fee (%)", 0.0, 100.0) / 100

    down_payment_pct = st.number_input("Down Payment (%)", 0.0, 100.0) / 100
    interest_rate = st.number_input("Interest Rate (%)", 0.0, 15.0) / 100
    loan_term = st.number_input("Loan Term (Years)", 1, 40)

    closing_cost_pct = st.number_input(
        "Estimated Closing Costs (% of Purchase Price)",
        min_value=0.0,
        max_value=10.0,
        value=3.0
    ) / 100

    analyze = st.button("📊 Analyze Deal")

# ================= CALCULATIONS =================
if analyze:
    annual_rent = monthly_rent * 12

    vacancy_loss = annual_rent * vacancy_rate
    management_cost = annual_rent * management_fee

    expenses_annual = {
        "Property Tax": property_tax,
        "Insurance": insurance,
        "Maintenance": maintenance,
        "Vacancy Loss": vacancy_loss,
        "Management Fee": management_cost
    }

    total_expenses_annual = sum(expenses_annual.values())
    noi_annual = annual_rent - total_expenses_annual

    loan_amount = purchase_price * (1 - down_payment_pct)
    monthly_rate = interest_rate / 12
    total_payments = loan_term * 12

    if interest_rate > 0:
        monthly_payment = loan_amount * (
            monthly_rate * (1 + monthly_rate) ** total_payments
        ) / ((1 + monthly_rate) ** total_payments - 1)
    else:
        monthly_payment = loan_amount / total_payments

    annual_debt = monthly_payment * 12
    cash_flow_annual = noi_annual - annual_debt

    total_investment = purchase_price + rehab_cost
    cash_invested = purchase_price * down_payment_pct + rehab_cost

    cap_rate = noi_annual / total_investment if total_investment else 0
    coc_return = cash_flow_annual / cash_invested if cash_invested else 0
    equity_pct = (arv - total_investment) / arv if arv else 0

    deal_score = min(
        100,
        (coc_return / 0.15 * 40) +
        (cap_rate / 0.10 * 30) +
        (equity_pct / 0.20 * 30)
    )

    rating = (
        "🔥 Excellent Deal" if deal_score >= 85 else
        "✅ Strong Deal" if deal_score >= 70 else
        "⚠️ Marginal Deal" if deal_score >= 50 else
        "❌ Weak Deal"
    )

    # Cash Required at Closing
    down_payment = purchase_price * down_payment_pct
    closing_costs = purchase_price * closing_cost_pct
    total_cash_needed = down_payment + rehab_cost + closing_costs
    cash_pct_arv = total_cash_needed / arv if arv else 0

    st.session_state.results = {
        "Annual Rent": annual_rent,
        "Monthly Rent": monthly_rent,
        "NOI": noi_annual,
        "Cash Flow": cash_flow_annual,
        "Debt": annual_debt,
        "Cap Rate": cap_rate,
        "CoC": coc_return,
        "Equity": equity_pct,
        "Score": deal_score,
        "Rating": rating,
        "Expenses": expenses_annual,
        "Total Expenses": total_expenses_annual,
        "Cash Needed": total_cash_needed,
        "Down Payment": down_payment,
        "Closing Costs": closing_costs,
        "Cash % ARV": cash_pct_arv
    }

# ================= RIGHT COLUMN =================
with right_col:
    st.header("📈 Deal Results")

    if "results" in st.session_state:
        r = st.session_state.results

        view = st.radio("View Mode", ["Annual", "Monthly"], horizontal=True)

        factor = 1 if view == "Annual" else 1 / 12

        # ================= DEAL SUMMARY CARD =================
        st.markdown("### 🧾 Deal Summary")
        st.markdown(
            f"""
            **Deal Rating:** {r['Rating']}  
            **Rental Deal Score:** {r['Score']:.0f}/100  
            **Cap Rate:** {r['Cap Rate']:.2%}  
            **Cash-on-Cash Return:** {r['CoC']:.2%}  
            **Total Cash Needed:** ${r['Cash Needed']:,.0f}  
            """
        )

        # ================= METRICS =================
        st.metric("Gross Rent", f"${r['Annual Rent'] * factor:,.0f}")
        st.metric("NOI", f"${r['NOI'] * factor:,.0f}")
        st.metric("Cash Flow", f"${r['Cash Flow'] * factor:,.0f}")
        st.metric("Debt Service", f"${r['Debt'] * factor:,.0f}")

        # ================= CASH FLOW CHART =================
        st.markdown("### 📊 Cash Flow Overview")

        cashflow_df = pd.DataFrame({
            "Category": ["Rent", "Expenses", "Debt", "Cash Flow"],
            "Amount": [
                r["Annual Rent"] * factor,
                r["Total Expenses"] * factor,
                r["Debt"] * factor,
                r["Cash Flow"] * factor
            ]
        })

        st.bar_chart(cashflow_df.set_index("Category"))

        # ================= EXPENSE PIE CHART =================
        st.markdown("### 🧩 Expense Breakdown")

        expense_df = pd.DataFrame.from_dict(
            {k: v * factor for k, v in r["Expenses"].items()},
            orient="index",
            columns=["Amount"]
        )

        st.bar_chart(expense_df)

        # ================= CASH REQUIRED =================
        st.markdown("### 💰 Cash Required at Closing")
        st.write(f"Down Payment: ${r['Down Payment']:,.0f}")
        st.write(f"Rehab Budget: ${rehab_cost:,.0f}")
        st.write(f"Closing Costs: ${r['Closing Costs']:,.0f}")
        st.write(f"**Total Cash Needed:** ${r['Cash Needed']:,.0f}")
        st.write(f"Cash Needed as % of ARV: {r['Cash % ARV']:.1%}")

    else:
        st.info("Enter inputs and click **Analyze Deal**")

# ================= DISCLAIMER =================
st.markdown("---")
st.caption(
    "Disclaimer: This tool is for educational and informational purposes only and does not "
    "constitute financial, investment, legal, tax, or real estate advice. "
    "All results are estimates. Users should conduct their own due diligence."
)


