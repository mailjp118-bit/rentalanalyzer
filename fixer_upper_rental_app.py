import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import streamlit.components.v1 as components
if "flip_analyzed" not in st.session_state:
    st.session_state.flip_analyzed = False


# ================= PAGE CONFIG (MUST BE FIRST STREAMLIT CALL) =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")
# ================= TAB SIZE STYLING =================
st.markdown("""
<style>
/* Remove top padding from main container */
.block-container {
    padding-top: 2rem !important;
}

/* Remove margin above tabs */
div[data-testid="stTabs"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Remove extra spacing above first element */
section.main > div {
    padding-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# st.image("assets/logo2.png", use_container_width=True)

# ================= GOOGLE ANALYTICS =================
components.html(
    """
    <!-- Google tag (gtag.js) -->
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

# ================= EXPORT HELPERS (USED BY RENTAL + FLIP) =================
LOGO_PATH = "assets/logo2.png"
APP_TITLE = "Rental Deal Analyzer"
APP_TAGLINE = "Know if a rental deal works — Fast & Free."

def _is_percent_field(key: str) -> bool:
    k = str(key).lower()
    return any(x in k for x in [
        "cap rate", "coc", "cash-on-cash", "equity", "vacancy", "management fee",
        "down payment", "cash % arv", "interest rate", "roi", "margin", "%"
    ])

def _is_money_field(key: str) -> bool:
    k = str(key).lower()
    return any(x in k for x in [
        "rent", "noi", "cash flow", "debt", "down payment", "closing", "total",
        "expense", "tax", "insurance", "maintenance", "rehab", "loan", "investment",
        "price", "arv", "profit", "cost"
    ])

def _fmt_value(key, val):
    # Keep strings as-is (e.g., Rating)
    if isinstance(val, str):
        return val

    # Dicts handled elsewhere
    if isinstance(val, dict):
        return ""

    # Numbers formatting
    try:
        num = float(val)
    except Exception:
        return str(val)

    if _is_percent_field(str(key)):
        return f"{num * 100:.2f}%"
    if _is_money_field(str(key)):
        return f"${num:,.2f}"
    return f"{num:,.2f}"

def _build_export_rows(results: dict):
    rows = []
    for k, v in results.items():
        if isinstance(v, dict):
            rows.append((str(k), ""))  # section label
            for kk, vv in v.items():
                rows.append((f"  - {kk}", _fmt_value(kk, vv)))
        else:
            rows.append((str(k), _fmt_value(k, v)))
    return rows

def export_excel_pdf(results_dict: dict, excel_placeholder, pdf_placeholder, excel_filename: str, pdf_filename: str):
    export_rows = _build_export_rows(results_dict)
    export_df = pd.DataFrame(export_rows, columns=["Metric", "Value"])

    # -------- Excel (with logo + title) --------
    excel_buffer = BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Results", startrow=6)
            ws = writer.book["Results"]

            # Title + tagline
            ws["A1"] = APP_TITLE
            ws["A2"] = APP_TAGLINE
            try:
                ws["A1"].font = ws["A1"].font.copy(bold=True, size=16)
                ws["A2"].font = ws["A2"].font.copy(size=11)
            except Exception:
                pass

            # Merge title cells
            try:
                ws.merge_cells("A1:D1")
                ws.merge_cells("A2:D2")
            except Exception:
                pass

            # Insert logo
            try:
                from openpyxl.drawing.image import Image as XLImage
                logo = XLImage(LOGO_PATH)
                logo.width = 140
                logo.height = 40
                ws.add_image(logo, "E1")
            except Exception:
                pass

            # Column widths
            try:
                ws.column_dimensions["A"].width = 30
                ws.column_dimensions["B"].width = 22
            except Exception:
                pass
    except Exception:
        # fallback without styling if openpyxl isn't available
        export_df.to_excel(excel_buffer, index=False)

    excel_buffer.seek(0)
    excel_placeholder.download_button(
        "⬇️ Download Excel",
        excel_buffer,
        excel_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # -------- PDF (with logo + title) --------
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    top_y = 760
    try:
        logo_img = ImageReader(LOGO_PATH)
        c.drawImage(logo_img, 40, top_y - 35, width=120, height=35, mask="auto")
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 16)
    c.drawString(170, top_y - 15, APP_TITLE)
    c.setFont("Helvetica", 10)
    c.drawString(170, top_y - 30, APP_TAGLINE)

    y = 700
    c.setFont("Helvetica", 10)

    for metric, value in export_rows:
        if value == "" and not str(metric).startswith("  - "):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y, str(metric))
            y -= 16
            c.setFont("Helvetica", 10)
        else:
            c.drawString(50, y, f"{metric}: {value}")
            y -= 14

        if y < 60:
            c.showPage()
            y = 750
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, APP_TITLE)
            y -= 20
            c.setFont("Helvetica", 10)

    c.save()
    pdf_buffer.seek(0)

    pdf_placeholder.download_button(
        "⬇️ Download PDF",
        pdf_buffer,
        pdf_filename,
        mime="application/pdf"
    )

# ================= TABS =================
tab_rental, tab_flip = st.tabs(["🏠 Rental Calculator", "🔨 Flip Calculator"])

# =====================================================================
# =========================== RENTAL TAB ===============================
# =====================================================================
with tab_rental:
    # ================= TOP BAR =================
    top_left, top_middle, top_right = st.columns([5, 2, 2])

    with top_left:
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:14px; margin:8px 0 8px;">
              <svg width="48" height="48" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
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
### Know if a rental deal works — Fast & Free.  
Get **cash flow, cap rate, cash-on-cash return, deal score and much more** instantly.
""")

    with top_middle:
        breakdown_view = st.selectbox(
            "📊 View Mode",
            ["Annual", "Monthly"],
            index=0,
            key="breakdown_view_rental"
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

        purchase_price = st.number_input("Purchase Price ($)", min_value=0, step=1000, value=0, key="purchase_price")
        rehab_cost = st.number_input("Rehab Cost ($)", min_value=0, step=1000, value=0, key="rehab_cost")
        arv = st.number_input("After Repair Value (ARV) ($)", min_value=0, step=1000, value=0, key="arv")

        monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, step=100, value=0, key="monthly_rent")

        property_tax = st.number_input("Annual Property Tax ($)", min_value=0, step=100, value=0, key="property_tax")
        insurance = st.number_input("Annual Insurance ($)", min_value=0, step=100, value=0, key="insurance")
        maintenance = st.number_input("Annual Maintenance ($)", min_value=0, step=100, value=0, key="maintenance")

        vacancy_rate = st.number_input("Vacancy Rate (%)", 0, 100, value=0, key="vacancy_rate") / 100
        management_fee = st.number_input("Management Fee (%)", 0, 100, value=0, key="management_fee") / 100

        down_payment_pct = st.number_input("Down Payment (%)", 0, 100, value=0, key="down_payment_pct") / 100
        #interest_rate = st.number_input("Interest Rate (%)", 0, 15, value=0, key="interest_rate") / 100
        interest_rate = st.number_input(
    "Interest Rate (%)",
    min_value=0.0,
    max_value=15.0,
    value=0.0,
    step=0.25,
    format="%.2f"
) / 100
        loan_term = st.number_input("Loan Term (Years)", 1, 40, value=30, key="loan_term")

        closing_cost_pct = st.number_input(
            "Estimated Closing Costs (% of Purchase Price)",
            min_value=0,
            max_value=10,
            value=3,
            key="closing_cost_pct"
        ) / 100

        analyze = st.button("📊 Analyze Deal", key="analyze_rental")

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

    # ================= DOWNLOAD BUTTONS (LOGO + TITLE + FORMATTED VALUES) =================
    if "results" in st.session_state:
        export_excel_pdf(
            st.session_state.results,
            excel_btn,
            pdf_btn,
            excel_filename="rental_deal_analysis.xlsx",
            pdf_filename="rental_deal_analysis.pdf"
        )

    # ================= DISCLAIMER =================
    st.markdown("---")
    st.caption(
        "Disclaimer: This tool is for educational and informational purposes only and does not "
        "constitute financial, investment, legal, tax, or real estate advice. "
        "All outputs are estimates, and use of this tool is at your own risk."
    )

# =====================================================================
# ============================ FLIP TAB ================================
# =====================================================================

# 1. Page Configuration
st.set_page_config(
    page_title="Rental Deal Analyzer | Flip Calculator",
    page_icon="🏠",
    layout="wide"
)

# 2. CSS for Dark Mode & Branding
st.markdown("""
    <style>
    .stApp { background-color: #0b1020; color: #eaf0ff; }
    div[data-testid="stMetricValue"] { color: #1DA1F2; }
    label { color: #b9c3ff !important; }
    .stButton>button {
        background-color: #1DA1F2;
        color: white;
        border-radius: 8px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover { background-color: #1991db; }
    </style>
""", unsafe_allow_html=True)

# ================= TOP BAR =================
# Using [8, 1, 1] ratio to keep title/logo aligned left
top_left, top_middle, top_right = st.columns([8, 1, 1])

with top_left:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:12px; margin:8px 0 8px;">
          <svg width="48" height="48" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 30L32 10L56 30V54H38V40H26V54H8V30Z"
                  fill="rgba(29,161,242,0.25)" stroke="#EAF0FF" stroke-width="2"/>
            <rect x="22" y="34" width="5" height="10" fill="#1DA1F2"/>
            <rect x="30" y="30" width="5" height="14" fill="#1DA1F2"/>
            <rect x="38" y="26" width="5" height="18" fill="#1DA1F2"/>
          </svg>
          <span style="font-size:28px; font-weight:800; white-space:nowrap;">Rental Deal Analyzer</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ================= INPUTS =================
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("💰 Purchase & Rehab")
    purchase_price = st.number_input("Purchase Price ($)", value=250000, step=1000)
    buying_costs_pct = st.number_input("Buying Costs / Closing (%)", value=2.0, step=0.5, help="Title, Escrow, Recording fees (approx 1-3%)")
    rehab_cost = st.number_input("Rehab Budget ($)", value=40000, step=1000)
    contingency_pct = st.number_input("Rehab Contingency (%)", value=10.0, step=5.0, help="Buffer for over-budget repairs")

with col2:
    st.subheader("🏦 Financing & Holding")
    down_payment_pct = st.number_input("Down Payment (%)", value=20.0, step=5.0)
    interest_rate = st.number_input("Interest Rate (%)", value=10.0, step=0.5)
    loan_points = st.number_input("Loan Points (% of Loan)", value=2.0, step=0.5, help="Upfront points paid to hard money lender")
    holding_period = st.number_input("Holding Period (Months)", value=6, step=1)
    
    # New Detailed Carry Costs
    with st.expander("Monthly Carry Details"):
        property_taxes = st.number_input("Property Taxes ($/mo)", value=300)
        insurance = st.number_input("Insurance ($/mo)", value=150)
        utilities = st.number_input("Utilities/HOA ($/mo)", value=250)

with col3:
    st.subheader("📈 Exit Strategy")
    arv = st.number_input("After Repair Value (ARV) ($)", value=400000, step=1000)
    selling_costs_pct = st.number_input("Selling Costs (% of ARV)", value=6.0, step=0.5, help="Agent commissions + closing costs")

# ================= CALCULATIONS =================

# 1. Acquisition
buying_costs_amount = purchase_price * (buying_costs_pct / 100)
loan_amount = purchase_price * (1 - (down_payment_pct / 100))
down_payment_amount = purchase_price - loan_amount

# 2. Rehab
contingency_amount = rehab_cost * (contingency_pct / 100)
total_rehab_budget = rehab_cost + contingency_amount

# 3. Financing (The Cost of Money)
points_amount = loan_amount * (loan_points / 100)
monthly_interest = (loan_amount * (interest_rate / 100)) / 12
total_interest_cost = monthly_interest * holding_period
total_finance_cost = points_amount + total_interest_cost

# 4. Holding (The Monthly Bleed)
monthly_carry = property_taxes + insurance + utilities
total_holding_cost = monthly_carry * holding_period

# 5. Sale
selling_costs_amount = arv * (selling_costs_pct / 100)

# 6. Final Profitability
# Note: Net Profit is ARV minus ALL costs (Buying + Rehab + Holding + Selling)
net_profit = arv - (purchase_price + buying_costs_amount + total_rehab_budget + total_finance_cost + total_holding_cost + selling_costs_amount)

# 7. Cash Requirements (Liquidity Needed)
# Cash Needed = Down Payment + Buying Costs + Loan Points + Rehab + Holding Costs
# (Assumes Rehab and Holding are paid out of pocket. If financed, remove them here.)
total_cash_needed = down_payment_amount + buying_costs_amount + points_amount + total_rehab_budget + total_holding_cost

# 8. ROI
roi = (net_profit / total_cash_needed) * 100 if total_cash_needed > 0 else 0
annualized_roi = (roi / holding_period) * 12 if holding_period > 0 else 0


# ================= OUTPUTS =================
st.divider()

# Top Level Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Net Profit", f"${net_profit:,.0f}")
m2.metric("ROI", f"{roi:.1f}%")
m3.metric("Annualized ROI", f"{annualized_roi:.1f}%")
m4.metric("Cash Needed", f"${total_cash_needed:,.0f}", help="Total cash required (Down Pmt + Rehab + Holding + Closing)")

st.divider()

# Detailed Breakdown
b1, b2 = st.columns([1, 1])

with b1:
    st.subheader("💵 Expense Breakdown")
    breakdown_data = {
        "Category": [
            "Purchase Price",
            "Buying Closing Costs",
            "Rehab (w/ Contingency)",
            "Financing (Points + Int)",
            "Holding (Tax/Ins/Util)",
            "Selling Costs"
        ],
        "Amount": [
            purchase_price,
            buying_costs_amount,
            total_rehab_budget,
            total_finance_cost,
            total_holding_cost,
            selling_costs_amount
        ]
    }
    df = pd.DataFrame(breakdown_data)
    st.dataframe(
        df.style.format({"Amount": "${:,.0f}"}), 
        hide_index=True, 
        use_container_width=True
    )

with b2:
    st.subheader("📊 Visuals & Rules")
    
    # 70% Rule Check
    mao_70_rule = (arv * 0.70) - total_rehab_budget
    st.info(f"**Max Allowable Offer (70% Rule):** ${mao_70_rule:,.0f}")
    
    # Simple Bar Chart of Expenses (excluding Purchase Price to see "Soft Costs" better)
    chart_df = df[df["Category"] != "Purchase Price"].set_index("Category")
    st.bar_chart(chart_df)

# ================= DISCLAIMER =================
st.markdown("---")
current_year = datetime.datetime.now().year
st.markdown(
    f"""
    <div style="text-align: center; color: rgba(255,255,255,0.45); font-size: 12px; margin-top: 20px;">
        © {current_year} RentalDealAnalyzer.com <br>
        Educational purposes only. This tool does not constitute financial, investment, legal, or real estate advice. 
        All outputs are estimates. Use of this tool is at your own risk.
    </div>
    """,
    unsafe_allow_html=True
)
