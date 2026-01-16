import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= PRIVACY MESSAGE =================
st.markdown(
    "🔒 **Privacy Notice:** *We do not store or track your deal data. "
    "All calculations run in real-time and reset when you refresh the page.*"
)

# ================= HEADER + DOWNLOAD AREA =================
title_col, download_col = st.columns([3, 1])
with title_col:
    st.title("🏚️ Fixer-Upper Rental Deal Analyzer")

# Placeholder containers for download buttons
pdf_placeholder = download_col.empty()
excel_placeholder = download_col.empty()

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

    vacancy_rate = st.number_input(
        "Vacancy Rate (%)",
        0.0, 100.0,
        help="Vacancy accounts for time when the property is empty or tenants don’t pay."
    ) / 100

    management_fee = st.number_input("Management Fee (%)", 0.0, 100.0) / 100

    down_payment_pct = st.number_input("Down Payment (%)", 0.0, 100.0) / 100
    interest_rate = st.number_input("Interest Rate (%)", 0.0, 15.0) / 100
    loan_term = st.number_input("Loan Term (Years)", 1, 40)

    closing_cost_pct = st.number_input(
        "Estimated Closing Costs (% of Purchase Price)",
        0.0, 10.0, value=3.0
    ) / 100

    analyze = st.button("📊 Analyze Deal")

# ================= CALCULATIONS =================
if analyze:
    annual_rent = monthly_rent * 12

    vacancy_loss = annual_rent * vacancy_rate
    management_cost = annual_rent * management_fee

    expenses = {
        "Property Tax": property_tax,
        "Insurance": insurance,
        "Maintenance": maintenance,
        "Vacancy Loss": vacancy_loss,
        "Management Fee": management_cost
    }

    total_expenses = sum(expenses.values())
    noi = annual_rent - total_expenses

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
    cash_flow = noi - annual_debt

    total_investment = purchase_price + rehab_cost
    cash_invested = purchase_price * down_payment_pct + rehab_cost

    cap_rate = noi / total_investment if total_investment else 0
    coc = cash_flow / cash_invested if cash_invested else 0
    equity = (arv - total_investment) / arv if arv else 0

    deal_score = min(
        100,
        (coc / 0.15 * 40) +
        (cap_rate / 0.10 * 30) +
        (equity / 0.20 * 30)
    )

    rating = (
        "🔥 Excellent Deal" if deal_score >= 85 else
        "✅ Strong Deal" if deal_score >= 70 else
        "⚠️ Marginal Deal" if deal_score >= 50 else
        "❌ Weak Deal"
    )

    down_payment = purchase_price * down_payment_pct
    closing_costs = purchase_price * closing_cost_pct
    cash_needed = down_payment + rehab_cost + closing_costs

    st.session_state.results = {
        "Annual Rent": annual_rent,
        "NOI": noi,
        "Cash Flow": cash_flow,
        "Debt": annual_debt,
        "Cap Rate": cap_rate,
        "CoC": coc,
        "Equity": equity,
        "Score": deal_score,
        "Rating": rating,
        "Expenses": expenses,
        "Total Expenses": total_expenses,
        "Cash Needed": cash_needed
    }

    # ================= PDF GENERATION =================
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer)
    styles = getSampleStyleSheet()
    content = [
        Paragraph("Fixer-Upper Rental Deal Summary", styles["Title"]),
        Paragraph(f"Deal Rating: {rating}", styles["Normal"]),
        Paragraph(f"Cap Rate: {cap_rate:.2%}", styles["Normal"]),
        Paragraph(f"Cash-on-Cash Return: {coc:.2%}", styles["Normal"]),
        Paragraph(f"Annual Cash Flow: ${cash_flow:,.0f}", styles["Normal"]),
        Paragraph(f"Total Cash Needed: ${cash_needed:,.0f}", styles["Normal"]),
    ]
    doc.build(content)
    pdf_buffer.seek(0)

    pdf_placeholder.download_button(
        "📄 Download PDF",
        data=pdf_buffer,
        file_name="rental_deal_summary.pdf",
        mime="application/pdf"
    )

    # ================= EXCEL GENERATION =================
    wb = Workbook()
    ws = wb.active
    ws.title = "Deal Summary"

    ws.append(["Metric", "Value"])
    ws.append(["Cap Rate", cap_rate])
    ws.append(["Cash-on-Cash Return", coc])
    ws.append(["Annual Cash Flow", cash_flow])
    ws.append(["Total Cash Needed", cash_needed])

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    excel_placeholder.download_button(
        "📊 Download Excel",
        data=excel_buffer,
        file_name="rental_deal_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ================= RIGHT COLUMN =================
with right_col:
    st.header("📈 Deal Results")

    if "results" in st.session_state:
        r = st.session_state.results

        st.metric(
            "Cap Rate",
            f"{r['Cap Rate']:.2%}",
            help="Cap Rate = NOI ÷ Total Purchase + Rehab Cost. "
                 "It measures the property’s return ignoring financing."
        )

        st.metric(
            "Cash-on-Cash Return",
            f"{r['CoC']:.2%}",
            help="Cash-on-Cash shows how hard your actual cash investment is working."
        )

        st.metric(
            "Annual Cash Flow",
            f"${r['Cash Flow']:,.0f}",
            help="Cash Flow is money left after all expenses and mortgage payments."
        )

        st.subheader(r["Rating"])
    else:
        st.info("Enter inputs and click **Analyze Deal**")

# ================= DISCLAIMER =================
st.markdown("---")
st.caption(
    "Disclaimer: This tool is for educational purposes only and does not constitute "
    "financial, investment, legal, or tax advice. Consult licensed professionals in the US or Canada."
)
