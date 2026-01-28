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
with tab_flip:
    # ================= TOP BAR (KEEP SAME BRANDING) =================
    top_left_f, top_middle_f, top_right_f = st.columns([5, 2, 2])

    with top_left_f:
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

              <span style="font-size:30px; font-weight:800;">Fix & Flip Deal Analyzer</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("""
### Know if a flip works — Fast & Free.  
Get **profit, ROI, annualized ROI, selling costs, and flip score** instantly.
""")

    with top_middle_f:
        st.selectbox("📊 View Mode", ["Project"], index=0, key="flip_view_mode", disabled=True)

    with top_right_f:
        flip_excel_btn = st.empty()
        flip_pdf_btn = st.empty()
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
    fcol1, fsp1, fcol2, fsp2, fcol3 = st.columns([1.2, 0.15, 1, 0.15, 1])

    # ================= LEFT COLUMN — FLIP INPUTS =================
    with fcol1:
        st.header("🔢 Flip Inputs")

        flip_purchase_price = st.number_input("Purchase Price ($)", min_value=0, step=1000, value=0, key="flip_purchase_price")
        flip_rehab_cost = st.number_input("Rehab Cost ($)", min_value=0, step=1000, value=0, key="flip_rehab_cost")
        flip_arv = st.number_input("After Repair Value (ARV) ($)", min_value=0, step=1000, value=0, key="flip_arv")

        flip_holding_months = st.number_input("Holding Period (Months)", min_value=1, step=1, value=6, key="flip_holding_months")

        flip_financing_costs = st.number_input("Financing Costs ($)", min_value=0, step=100, value=0, key="flip_financing_costs")
        flip_misc_costs = st.number_input("Misc / Contingency ($)", min_value=0, step=100, value=0, key="flip_misc_costs")

        flip_selling_cost_pct = st.number_input(
            "Selling Costs (% of ARV)",
            min_value=0,
            max_value=15,
            value=8,
            key="flip_selling_cost_pct"
        ) / 100

        if st.button("📊 Analyze Flip", key="analyze_flip"):
            st.session_state.flip_analyzed = True


# ================= FLIP CALCULATIONS (ENHANCED) =================
    # ================= FLIP CALCULATIONS (CLEAN & SAFE) =================
if st.session_state.flip_analyzed:

    # 1️⃣ Buying & Selling Costs
    buying_costs = flip_purchase_price * 0.025  # estimated title/escrow/origination
    selling_costs = flip_arv * flip_selling_cost_pct

    # 2️⃣ Estimated Monthly Holding Costs
    # Includes property tax, insurance, utilities (assumption-based)
    estimated_monthly_holding = ((flip_arv * 0.015) / 12) + 250
    total_holding_costs = estimated_monthly_holding * flip_holding_months

    # 3️⃣ Total Project Cost
    total_project_cost = (
        flip_purchase_price
        + flip_rehab_cost
        + buying_costs
        + flip_financing_costs
        + flip_misc_costs
        + total_holding_costs
        + selling_costs
    )

    # 4️⃣ Profit & Returns
    net_profit = flip_arv - total_project_cost

    roi = net_profit / total_project_cost if total_project_cost else 0
    annualized_roi = (roi / flip_holding_months) * 12 if flip_holding_months else 0
    profit_margin = net_profit / flip_arv if flip_arv else 0

    # 5️⃣ 70% Rule – Maximum Allowable Offer
    mao_70_rule = (flip_arv * 0.70) - flip_rehab_cost

    # 6️⃣ Flip Deal Score (0–100)
    # Weighting:
    # 40% ROI (target 20%)
    # 30% Profit Margin (target 15%)
    # 30% 70% Rule Compliance

    rule_adherence = mao_70_rule / flip_purchase_price if flip_purchase_price else 0

    flip_score_raw = (
        (roi / 0.20 * 40) +
        (profit_margin / 0.15 * 30) +
        (min(1.0, rule_adherence) * 30)
    )

    # Risk penalty for heavy rehab
    if flip_rehab_cost > (flip_purchase_price * 0.5):
        flip_score_raw -= 5

    flip_score = max(0, min(100, flip_score_raw))

    flip_rating = (
        "🔥 Home Run Flip" if flip_score >= 85 else
        "✅ Solid Flip" if flip_score >= 70 else
        "⚠️ High Risk / Marginal" if flip_score >= 50 else
        "❌ Avoid Deal"
    )

    # 7️⃣ Store Results (EXPORT-SAFE)
    st.session_state.flip_results = {
        "Purchase Price": flip_purchase_price,
        "Rehab Cost": flip_rehab_cost,
        "After Repair Value (ARV)": flip_arv,
        "Holding Period (Months)": flip_holding_months,
        "Estimated Buying Costs": buying_costs,
        "Total Holding Costs": total_holding_costs,
        "Financing Costs": flip_financing_costs,
        "Misc / Contingency": flip_misc_costs,
        "Selling Costs": selling_costs,
        "Total Project Cost": total_project_cost,
        "Net Profit": net_profit,
        "ROI": roi,
        "Annualized ROI": annualized_roi,
        "Profit Margin": profit_margin,
        "Max Allowable Offer (70% Rule)": mao_70_rule,
        "Flip Deal Score": flip_score,
        "Rating": flip_rating
    }

    # ================= MIDDLE COLUMN — FLIP RESULTS =================
    with fcol2:
        st.header("📈 Flip Results")

        if "flip_results" in st.session_state:
            r = st.session_state.flip_results
            st.metric("Net Profit", f"${r['Net Profit']:,.0f}")
            st.metric("ROI", f"{r['ROI']:.2%}")
            st.metric("Annualized ROI", f"{r['Annualized ROI']:.2%}")
            st.metric("Profit Margin", f"{r['Profit Margin']:.2%}")
            st.metric("Flip Deal Score", f"{r['Flip Deal Score']:.0f}/100")
            st.subheader(r["Rating"])
        else:
            st.info("Enter inputs and click **Analyze Flip**")

    # ================= RIGHT COLUMN — COST BREAKDOWN =================
    with fcol3:
        st.header("💸 Cost Breakdown")

        if "flip_results" in st.session_state:
            r = st.session_state.flip_results
            st.write(f"Purchase Price: ${r['Purchase Price']:,.0f}")
            st.write(f"Rehab Cost: ${r['Rehab Cost']:,.0f}")
            st.write(f"Financing Costs: ${r['Financing Costs']:,.0f}")
            st.write(f"Misc / Contingency: ${r['Misc / Contingency']:,.0f}")
            st.write(f"Selling Costs: ${r['Selling Costs']:,.0f}")
            st.markdown("---")
            st.write(f"**Total Project Cost:** ${r['Total Project Cost']:,.0f}")
            st.write(f"**ARV:** ${r['After Repair Value (ARV)']:,.0f}")

    # ================= FLIP DOWNLOAD BUTTONS (MATCH RENTAL STYLE) =================
    if "flip_results" in st.session_state:
        export_excel_pdf(
            st.session_state.flip_results,
            flip_excel_btn,
            flip_pdf_btn,
            excel_filename="flip_deal_analysis.xlsx",
            pdf_filename="flip_deal_analysis.pdf"
        )

    # ================= DISCLAIMER =================
    st.markdown("---")
    st.caption(
        "Disclaimer: This tool is for educational and informational purposes only and does not "
        "constitute financial, investment, legal, tax, or real estate advice. "
        "All outputs are estimates, and use of this tool is at your own risk."
    )
