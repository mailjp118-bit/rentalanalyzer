import streamlit as st
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= PRIVACY MESSAGE =================
st.markdown(
    """
    🔒 **Privacy Notice:**  
    *We do not store or track your deal data. All calculations are performed in real-time and reset when you refresh the page.*
    """
)

# ================= TOP HEADER WITH DOWNLOAD BUTTONS (ADDED) =================
title_col, download_col = st.columns([3, 1])

with title_col:
    st.title("🏚️ Fixer-Upper Rental Deal Analyzer")

with download_col:
    if "results" in st.session_state:
        excel_download = st.button("⬇️ Excel")
        pdf_download = st.button("⬇️ PDF")

# ================= LAYOUT =================
left_col, right_col = st.columns([1, 1])

# ================= LEFT COLUMN =================
with left_col:
    st.header("🔢 Deal Inputs")

    purchase_price = st.number_input(
        "Purchase Price ($)", value=None, placeholder="Enter amount", step=1000.0
    )
    rehab_cost = st.number_input(
        "Rehab Cost ($)", value=None, placeholder="Enter amount", step=1000.0
    )
    arv = st.number_input(
        "After Repair Value (ARV) ($)", value=None, placeholder="Enter amount", step=1000.0
    )

    monthly_rent = st.number_input(
        "Monthly Rent ($)", value=None, placeholder="Enter amount", step=100.0
    )

    property_tax = st.number_input(
        "Annual Property Tax ($)", value=None, placeholder="Enter amount"
    )
    insurance = st.number_input(
        "Annual Insurance ($)", value=None, placeholder="Enter amount"
    )
    maintenance = st.number_input(
        "Annual Maintenance ($)", value=None, placeholder="Enter amount"
    )

    vacancy_rate = st.number_input(
        "Vacancy Rate (%)", value=None, placeholder="e.g. 5"
    ) / 100
    management_fee = st.number_input(
        "Management Fee (%)", value=None, placeholder="e.g. 8"
    ) / 100

    down_payment_pct = st.number_input(
        "Down Payment (%)", value=None, placeholder="e.g. 20"
    ) / 100
    interest_rate = st.number_input(
        "Interest Rate (%)", value=None, placeholder="e.g. 6.5"
    ) / 100
    loan_term = st.number_input("Loan Term (Years)", value=30)

    closing_cost_pct = st.number_input(
        "Estimated Closing Costs (% of Purchase Price)",
        value=3.0
    ) / 100

    analyze = st.button("📊 Analyze Deal")

# ================= CALCULATIONS (UNCHANGED) =================
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

    monthly_payment = loan_amount * (
        monthly_rate * (1 + monthly_rate) ** total_payments
    ) / ((1 + monthly_rate) ** total_payments - 1)

    annual_debt = monthly_payment * 12
    cash_flow_annual = noi_annual - annual_debt

    total_investment = purchase_price + rehab_cost
    cash_invested = purchase_price * down_payment_pct + rehab_cost

    cap_rate = noi_annual / total_investment
    coc_return = cash_flow_annual / cash_invested
    equity_pct = (arv - total_investment) / arv

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

    st.session_state.results = {
        "NOI": noi_annual,
        "Cash Flow": cash_flow_annual,
        "Cap Rate": cap_rate,
        "CoC": coc_return,
        "Equity": equity_pct,
        "Score": deal_score,
        "Rating": rating
    }

# ================= RIGHT COLUMN =================
with right_col:
    st.header("📈 Deal Results")

    if "results" in st.session_state:
        r = st.session_state.results

        st.metric("NOI", f"${r['NOI']:,.0f}")
        st.metric("Annual Cash Flow", f"${r['Cash Flow']:,.0f}")
        st.metric("Cap Rate", f"{r['Cap Rate']:.2%}")
        st.metric("Cash-on-Cash Return", f"{r['CoC']:.2%}")
        st.metric("Equity Percentage", f"{r['Equity']:.2%}")
        st.metric("Rental Deal Score", f"{r['Score']:.0f}/100")
        st.subheader(r["Rating"])

# ================= DOWNLOAD LOGIC (ADDED) =================
if "results" in st.session_state:

    if excel_download:
        wb = Workbook()
        ws = wb.active
        ws.title = "Deal Summary"
        for k, v in st.session_state.results.items():
            ws.append([k, v])

        excel_data = BytesIO()
        wb.save(excel_data)

        st.download_button(
            "Download Excel File",
            excel_data.getvalue(),
            file_name="rental_deal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if pdf_download:
        pdf_data = BytesIO()
        doc = SimpleDocTemplate(pdf_data)
        styles = getSampleStyleSheet()
        content = [
            Paragraph(f"<b>{k}:</b> {v}", styles["Normal"])
            for k, v in st.session_state.results.items()
        ]
        doc.build(content)

        st.download_button(
            "Download PDF File",
            pdf_data.getvalue(),
            file_name="rental_deal.pdf",
            mime="application/pdf"
        )

# ================= DISCLAIMER =================
st.markdown("---")
st.caption(
    "Disclaimer: This tool is for educational and informational purposes only and does not "
    "constitute financial, investment, legal, tax, or real estate advice. "
    "All results are estimates. Users should conduct their own due diligence."
)
