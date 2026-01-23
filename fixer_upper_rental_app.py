import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import streamlit.components.v1 as components

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= GOOGLE ANALYTICS =================
components.html(
    """
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-DMLKRR0K9P"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-DMLKRR0K9P', { 'send_page_view': true });
    </script>
    """,
    height=0,
)

# ================= ANALYZE BUTTON STATE (FIX) =================
if "analyze_clicked" not in st.session_state:
    st.session_state.analyze_clicked = False

# ================= TOP BAR =================
top_left, top_middle, top_right = st.columns([5, 2, 2])

with top_left:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:14px; margin:8px 0;">
          <svg width="48" height="48" viewBox="0 0 64 64">
            <path d="M8 30L32 10L56 30V54H38V40H26V54H8V30Z"
                  fill="rgba(29,161,242,0.25)" stroke="#EAF0FF" stroke-width="2"/>
            <rect x="22" y="34" width="5" height="10" fill="#1DA1F2"/>
            <rect x="30" y="30" width="5" height="14" fill="#1DA1F2"/>
            <rect x="38" y="26" width="5" height="18" fill="#1DA1F2"/>
          </svg>
          <span style="font-size:30px; font-weight:800;">Rental Deal Analyzer</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("""
### Know if a rental deal works — Fast & Free  
Get **cash flow, cap rate, cash-on-cash return, deal score and more** instantly.
""")

with top_middle:
    breakdown_view = st.selectbox("📊 View Mode", ["Annual", "Monthly"], index=0)

with top_right:
    excel_btn = st.empty()
    pdf_btn = st.empty()
    st.markdown(
        "📧 Email: <a href='mailto:email@rentaldealanalyzer.com'>email@rentaldealanalyzer.com</a>",
        unsafe_allow_html=True
    )

# ================= PRIVACY =================
st.markdown("""
🔒 **Privacy Notice:**  
*We do not store or track your deal data. All calculations reset on refresh.*
""")

# ================= MAIN LAYOUT =================
col1, spacer1, col2, spacer2, col3 = st.columns([1.2, 0.15, 1, 0.15, 1])

# ================= DEAL INPUTS =================
with col1:
    st.header("🔢 Deal Inputs")

    purchase_price = st.number_input("Purchase Price ($)", min_value=0, step=1000, value=0)
    rehab_cost = st.number_input("Rehab Cost ($)", min_value=0, step=1000, value=0)
    arv = st.number_input("After Repair Value (ARV) ($)", min_value=0, step=1000, value=0)

    monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, step=100, value=0)

    property_tax = st.number_input("Annual Property Tax ($)", min_value=0, step=100, value=0)
    insurance = st.number_input("Annual Insurance ($)", min_value=0, step=100, value=0)
    maintenance = st.number_input("Annual Maintenance ($)", min_value=0, step=100, value=0)

    vacancy_rate = st.number_input("Vacancy Rate (%)", 0, 100, value=0) / 100
    management_fee = st.number_input("Management Fee (%)", 0, 100, value=0) / 100

    down_payment_pct = st.number_input("Down Payment (%)", 0, 100, value=0) / 100
    interest_rate = st.number_input("Interest Rate (%)", 0, 15, value=0) / 100
    loan_term = st.number_input("Loan Term (Years)", 1, 40, value=30)

    closing_cost_pct = st.number_input(
        "Estimated Closing Costs (% of Purchase Price)",
        min_value=0, max_value=10, value=3
    ) / 100

    if st.button("📊 Analyze Deal"):
        st.session_state.analyze_clicked = True

# ================= CALCULATIONS =================
if st.session_state.analyze_clicked:

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

    down_payment = purchase_price * down_payment_pct
    closing_costs = purchase_price * closing_cost_pct
    total_cash_needed = down_payment + rehab_cost + closing_costs

    st.session_state.results = {
        "Annual Rent": annual_rent,
        "NOI": noi_annual,
        "Cash Flow": cash_flow_annual,
        "Cap Rate": cap_rate,
        "Cash-on-Cash Return": coc_return,
        "Equity %": equity_pct,
        "Deal Score": deal_score,
        "Rating": rating,
        "Total Cash Needed": total_cash_needed,
        "Expenses": expenses_annual
    }

# ================= RESULTS =================
with col2:
    st.header("📈 Deal Results")
    if "results" in st.session_state:
        r = st.session_state.results
        st.metric("Cash Flow (Annual)", f"${r['Cash Flow']:,.0f}")
        st.metric("Cap Rate", f"{r['Cap Rate']:.2%}")
        st.metric("Cash-on-Cash Return", f"{r['Cash-on-Cash Return']:.2%}")
        st.metric("Equity %", f"{r['Equity %']:.2%}")
        st.metric("Deal Score", f"{r['Deal Score']:.0f}/100")
        st.subheader(r["Rating"])

# ================= DISCLAIMER =================
st.markdown("---")
st.caption(
    "This tool is for educational purposes only and does not constitute financial, legal, or investment advice."
)
