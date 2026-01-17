import streamlit as st
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

# ================= HEADER WITH DOWNLOAD AREA =================
title_col, download_col = st.columns([3, 1])
with title_col:
    st.title("🏚️ Fixer-Upper Rental Deal Analyzer")

pdf_btn = download_col.empty()
excel_btn = download_col.empty()

# ================= LAYOUT =================
left_col, right_col = st.columns([1, 1])

# ================= LEFT COLUMN (INPUTS) =================
with left_col:
    st.header("🔢 Deal Inputs")

    purchase_price = st.number_input("Purchase Price ($)", value=None, step=1000.0)
    rehab_cost = st.number_input("Rehab Cost ($)", value=None, step=1000.0)
    arv = st.number_input("After Repair Value (ARV) ($)", value=None, step=1000.0)

    monthly_rent = st.number_input("Monthly Rent ($)", value=None, step=100.0)

    property_tax = st.number_input("Annual Property Tax ($)", value=None)
    insurance = st.number_input("Annual Insurance ($)", value=None)
    maintenance = st.number_input("Annual Maintenance ($)", value=None)

    vacancy_rate = st.number_input(
        "Vacancy Rate (%)",
        value=None,
        help="Vacancy accounts for months the unit is empty or tenants don’t pay."
    )

    management_fee = st.number_input("Management Fee (%)", value=None)

    down_payment_pct = st.number_input("Down Payment (%)", value=None)
    interest_rate = st.number_input("Interest Rate (%)", value=None)
    loan_term = st.number_input("Loan Term (Years)", value=None, min_value=1)

    closing_cost_pct = st.number_input(
        "Estimated Closing Costs (% of Purchase Price)",
        value=3.0
    )

    analyze = st.button("📊 Analyze Deal")

# ================= CALCULATIONS =================
if analyze and all(v is not None for v in [
    purchase_price, rehab_cost, arv, monthly_rent,
    property_tax, insurance, maintenance,
    vacancy_rate, management_fee,
    down_payment_pct, interest_rate, loan_term
]):

    vacancy_rate /= 100
    management_fee /= 100
    down_payment_pct /= 100
    interest_rate /= 100
    closing_cost_pct /= 100

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

    monthly_payment = (
        loan_amount *
        (monthly_rate * (1 + monthly_rate) ** total_payments) /
        ((1 + monthly_rate) ** total_payments - 1)
        if interest_rate > 0 else loan_amount / total_payments
    )

    annual_debt = monthly_payment * 12
    cash_flow = noi - annual_debt

    total_investment = purchase_price + rehab_cost
    cash_invested = purchase_price * down_payment_pct + rehab_cost

    cap_rate = noi / total_investment
    coc = cash_flow / cash_invested
    equity = (arv - total_investment) / arv

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
        "Cap Rate": cap_rate,
        "CoC": coc,
        "Cash Flow": cash_flow,
        "Score": deal_score,
        "Rating": rating,
        "Cash Needed": cash_needed
    }

    # ================= PDF =================
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("Rental Deal Summary", styles["Title"]),
        Paragraph(f"Rating: {rating}", styles["Normal"]),
        Paragraph(f"Cap Rate: {cap_rate:.2%}", styles["Normal"]),
        Paragraph(f"Cash-on-Cash Return: {coc:.2%}", styles["Normal"]),
        Paragraph(f"Annual Cash Flow: ${cash_flow:,.0f}", styles["Normal"]),
        Paragraph(f"Cash Needed: ${cash_needed:,.0f}", styles["Normal"]),
    ]

    doc.build(content)
    pdf_buffer.seek(0)

    pdf_btn.download_button(
        "📄 PDF",
        data=pdf_buffer,
        file_name="rental_deal_summary.pdf",
        mime="application/pdf"
    )

    # ================= EXCEL =================
    wb = Workbook()
    ws = wb.active
    ws.append(["Metric", "Value"])
    ws.append(["Cap Rate", cap_rate])
    ws.append(["Cash-on-Cash Return", coc])
    ws.append(["Annual Cash Flow", cash_flow])
    ws.append(["Cash Needed", cash_needed])

    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)

    excel_btn.download_button(
        "📊 Excel",
        data=excel_buffer,
        file_name="rental_deal_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ================= RIGHT COLUMN =================
with right_col:
    st.header("📈 Deal Results")

    if "results" in st.session_state:
        r = st.session_state.results

        st.metric("Cap Rate ℹ️", f"{r['Cap Rate']:.2%}",
                  help="Cap Rate = NOI ÷ Total Investment. Shows return ignoring financing.")
        st.metric("Cash-on-Cash ℹ️", f"{r['CoC']:.2%}",
                  help="Measures return on actual cash invested.")
        st.metric("Annual Cash Flow", f"${r['Cash Flow']:,.0f}")
        st.metric("Deal Score", f"{r['Score']:.0f}/100")
        st.subheader(r["Rating"])
    else:
        st.info("Enter all inputs and click **Analyze Deal**")

# ================= SMALL DISCLAIMER =================
st.markdown("---")
st.caption(
    "Disclaimer: Educational tool only. Results are estimates and not financial advice. "
    "Perform your own due diligence."
)
