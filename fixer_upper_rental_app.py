import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ================= PAGE CONFIG (MUST BE FIRST STREAMLIT CALL) =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")
#st.image("assets/logo2.png", use_container_width=True)
st.markdown(
    """
    <style>
    .thin-logo img {
        height: 200px;      /* adjust: 40–70px works well */
        width: 100%;
        object-fit: contain;
        margin-bottom: 50px;
    }
    </style>

    <div class="thin-logo">
        <img src="assets/logo2.png">
    </div>
    """,
    unsafe_allow_html=True
)


# ================= GOOGLE ANALYTICS =================
st.markdown("""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-DMLKRR0K9P"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-DMLKRR0K9P');
</script>
""", unsafe_allow_html=True)

# ================= PAGE CONFIG =================
#st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= TOP BAR =================
top_left, top_middle, top_right = st.columns([5, 2, 2])

with top_left:
    st.markdown(
        """
        <h1 style="font-weight:700; margin-bottom:0;">
            <span style="color:#E53935;">Rental</span>
            <span style="color:#1E88E5;">Deal</span>
            <span style="color:#2E7D32;">Analyzer</span>
        </h1>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
### Know if a rental deal works — Fast & Free.  
Get **cash flow, cap rate, cash-on-cash return, deal score and much more** instantly.
""")



with top_middle:
    breakdown_view = st.selectbox(
        "📊 View Mode",
        ["Annual", "Monthly"],
        index=0
    )

with top_right:
    excel_btn = st.empty()
    pdf_btn = st.empty()
    st.markdown(
        "<div style='font-size:14px; margin-top:4px;'>"
        "📧 Email: <a href='mailto:email@rentaldealanalyzer.com'>"
        "email@rentaldealanalyzer.com</a></div>",
        unsafe_allow_html=True
    )

# ================= PRIVACY MESSAGE =================
st.markdown(
    """
    🔒 **Privacy Notice:**  
    *We do not store or track your deal data. All calculations are performed in real-time and reset when you refresh the page.*
    """
)

# ================= MAIN LAYOUT =================
col1, spacer1, col2, spacer2, col3 = st.columns([1.2, 0.15, 1, 0.15, 1])

# ================= LEFT COLUMN — DEAL INPUTS =================
with col1:
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

    down_payment = purchase_price * down_payment_pct
    closing_costs = purchase_price * closing_cost_pct
    total_cash_needed = down_payment + rehab_cost + closing_costs
    cash_pct_arv = total_cash_needed / arv if arv else 0

    st.session_state.results = {
        "Annual Rent": annual_rent,
        "Monthly Rent": monthly_rent,
        "NOI Annual": noi_annual,
        "Cash Flow Annual": cash_flow_annual,
        "Debt Annual": annual_debt,
        "Debt Monthly": monthly_payment,
        "Cap Rate": cap_rate,
        "CoC": coc_return,
        "Equity": equity_pct,
        "Score": deal_score,
        "Rating": rating,
        "Expenses Annual": expenses_annual,
        "Total Expenses Annual": total_expenses_annual,
        "Down Payment": down_payment,
        "Closing Costs": closing_costs,
        "Total Cash Needed": total_cash_needed,
        "Cash % ARV": cash_pct_arv
    }

# ================= MIDDLE COLUMN — DEAL RESULTS =================
with col2:
    st.header("📈 Deal Results")

    if "results" in st.session_state:
        r = st.session_state.results

        if breakdown_view == "Annual":
            st.metric("Rent", f"${r['Annual Rent']:,.0f}", help="Total gross rental income per year.")
            st.metric("NOI", f"${r['NOI Annual']:,.0f}", help="Net Operating Income before debt service.")
            st.metric("Cash Flow", f"${r['Cash Flow Annual']:,.0f}", help="Annual cash remaining after all expenses and debt service.")
            st.metric("Debt Service", f"${r['Debt Annual']:,.0f}", help="Total annual mortgage payments (principal + interest).")
        else:
            st.metric("Rent", f"${r['Monthly Rent']:,.0f}", help="Gross rental income per month.")
            st.metric("NOI", f"${r['NOI Annual']/12:,.0f}", help="Monthly Net Operating Income before debt service.")
            st.metric("Cash Flow", f"${r['Cash Flow Annual']/12:,.0f}", help="Monthly cash remaining after expenses and debt service.")
            st.metric("Debt Service", f"${r['Debt Monthly']:,.0f}", help="Monthly mortgage payment (principal + interest).")

        st.metric("Cap Rate", f"{r['Cap Rate']:.2%}", help="NOI divided by total investment cost.")
        st.metric("Cash-on-Cash Return", f"{r['CoC']:.2%}", help="Annual cash flow divided by cash invested.")
        st.metric("Equity %", f"{r['Equity']:.2%}", help="Percentage of property value owned after purchase and rehab.")
        st.metric("Rental Deal Score", f"{r['Score']:.0f}/100", help="Overall deal strength score based on returns and equity.")
        st.subheader(r["Rating"])

# ================= RIGHT COLUMN — EXPENSES + CASH =================
with col3:
    st.header("💸 Expense Breakdown")

    if "results" in st.session_state:
        r = st.session_state.results

        if breakdown_view == "Annual":
            for name, value in r["Expenses Annual"].items():
                st.write(f"**{name}**: ${value:,.0f}")
            st.write(f"**Total Expenses:** ${r['Total Expenses Annual']:,.0f}")
        else:
            for name, value in r["Expenses Annual"].items():
                st.write(f"**{name}**: ${value/12:,.0f}")
            st.write(f"**Total Expenses:** ${r['Total Expenses Annual']/12:,.0f}")

        st.subheader("💰 Cash Required at Closing")

        st.write(f"Down Payment: ${r['Down Payment']:,.0f}")
        st.write(f"Rehab Budget: ${rehab_cost:,.0f}")
        st.write(f"Closing Costs: ${r['Closing Costs']:,.0f}")
        st.write(f"**Total Cash Needed:** ${r['Total Cash Needed']:,.0f}")
        st.write(f"Cash Needed as % of ARV: {r['Cash % ARV']:.1%}")

# ================= DOWNLOAD BUTTONS =================
if "results" in st.session_state:
    df = pd.DataFrame.from_dict(st.session_state.results, orient="index", columns=["Value"])

    excel_buffer = BytesIO()
    df.to_excel(excel_buffer)
    excel_buffer.seek(0)

    excel_btn.download_button(
        "⬇️ Download Excel",
        excel_buffer,
        "rental_deal_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    y = 750

    for k, v in st.session_state.results.items():
        c.drawString(40, y, f"{k}: {v}")
        y -= 18
        if y < 50:
            c.showPage()
            y = 750

    c.save()
    pdf_buffer.seek(0)

    pdf_btn.download_button(
        "⬇️ Download PDF",
        pdf_buffer,
        "rental_deal_analysis.pdf",
        mime="application/pdf"
    )

# ================= DISCLAIMER =================
st.markdown("---")
st.caption(
    "Disclaimer: This tool is for educational and informational purposes only and does not "
    "constitute financial, investment, legal, tax, or real estate advice. "
    "All outputs are estimates, and use of this tool is at your own risk."
)
