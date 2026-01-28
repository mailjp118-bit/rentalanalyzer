import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import streamlit.components.v1 as components
from datetime import datetime

# ================= SESSION STATE INITIALIZATION =================
if "flip_analyzed" not in st.session_state:
    st.session_state.flip_analyzed = False

if "results" not in st.session_state:
    st.session_state.results = {}

# ================= PAGE CONFIG (MUST BE FIRST STREAMLIT CALL) =================
st.set_page_config(page_title="Fixer-Upper Rental Analyzer", layout="wide")

# ================= TAB SIZE STYLING & DARK MODE =================
st.markdown("""
<style>
/* Remove top padding from main container */
.block-container {
    padding-top: 2rem !important;
}

/* Tab/Metric Styling */
div[data-testid="stTabs"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.stApp { background-color: #0b1020; color: #eaf0ff; }
div[data-testid="stMetricValue"] { color: #1DA1F2; }
label { color: #b9c3ff !important; }

/* Button Styling */
.stButton>button {
    background-color: #1DA1F2;
    color: white;
    border-radius: 8px;
    border: none;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

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

# ================= EXPORT HELPERS =================
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
    if isinstance(val, str): return val
    if isinstance(val, dict): return ""
    try:
        num = float(val)
    except Exception:
        return str(val)

    if _is_percent_field(str(key)):
        # Handle cases where percent is already 0.XX or XX.X
        return f"{num * 100:.2f}%" if abs(num) <= 1 else f"{num:.2f}%"
    if _is_money_field(str(key)):
        return f"${num:,.2f}"
    return f"{num:,.2f}"

def _build_export_rows(results: dict):
    rows = []
    for k, v in results.items():
        if isinstance(v, dict):
            rows.append((str(k), ""))
            for kk, vv in v.items():
                rows.append((f"  - {kk}", _fmt_value(kk, vv)))
        else:
            rows.append((str(k), _fmt_value(k, v)))
    return rows

def export_excel_pdf(results_dict: dict, excel_placeholder, pdf_placeholder, excel_filename: str, pdf_filename: str):
    export_rows = _build_export_rows(results_dict)
    export_df = pd.DataFrame(export_rows, columns=["Metric", "Value"])

    # Excel
    excel_buffer = BytesIO()
    export_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    excel_placeholder.download_button("⬇️ Download Excel", excel_buffer, excel_filename)

    # PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    y = 750
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, APP_TITLE)
    y -= 30
    c.setFont("Helvetica", 10)
    for metric, value in export_rows:
        c.drawString(50, y, f"{metric}: {value}")
        y -= 15
        if y < 50:
            c.showPage()
            y = 750
    c.save()
    pdf_buffer.seek(0)
    pdf_placeholder.download_button("⬇️ Download PDF", pdf_buffer, pdf_filename)

# ================= TABS =================
tab_rental, tab_flip = st.tabs(["🏠 Rental Calculator", "🔨 Flip Calculator"])

# ================= RENTAL TAB =================
with tab_rental:
    top_left, top_middle, top_right = st.columns([5, 2, 2])
    with top_left:
        st.markdown("""
            <div style="display:flex; align-items:center; gap:14px; margin:8px 0 8px;">
              <svg width="48" height="48" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 30L32 10L56 30V54H38V40H26V54H8V30Z" fill="rgba(29,161,242,0.25)" stroke="#EAF0FF" stroke-width="2"/>
                <rect x="22" y="34" width="5" height="10" fill="#1DA1F2"/><rect x="30" y="30" width="5" height="14" fill="#1DA1F2"/><rect x="38" y="26" width="5" height="18" fill="#1DA1F2"/>
              </svg>
              <span style="font-size:30px; font-weight:800;">Rental Deal Analyzer</span>
            </div>
            """, unsafe_allow_html=True)
    
    with top_middle:
        breakdown_view = st.selectbox("📊 View Mode", ["Annual", "Monthly"], key="view_rent")

    with top_right:
        r_excel_btn = st.empty()
        r_pdf_btn = st.empty()

    col1, spacer1, col2, spacer2, col3 = st.columns([1.2, 0.15, 1, 0.15, 1])
    with col1:
        st.header("🔢 Deal Inputs")
        p_price = st.number_input("Purchase Price ($)", value=250000)
        r_cost = st.number_input("Rehab Cost ($)", value=0)
        arv_r = st.number_input("ARV ($)", value=p_price)
        m_rent = st.number_input("Monthly Rent ($)", value=2000)
        p_tax = st.number_input("Annual Taxes ($)", value=3000)
        ins_r = st.number_input("Annual Insurance ($)", value=1200)
        maint_r = st.number_input("Annual Maintenance ($)", value=1200)
        vac_r = st.number_input("Vacancy Rate (%)", value=5) / 100
        mgmt_r = st.number_input("Management (%)", value=8) / 100
        dp_r = st.number_input("Down Payment (%)", value=20) / 100
        ir_r = st.number_input("Interest Rate (%)", value=7.0) / 100
        term_r = st.number_input("Loan Term (Yrs)", value=30)
        if st.button("📊 Analyze Rental"):
            # Logic here...
            st.session_state.results = {"Cash Flow": 500, "Cap Rate": 0.06} # Placeholder for simplicity

# ================= FLIP TAB =================
with tab_flip:
    top_left_f, top_middle_f, top_right_f = st.columns([5, 2, 2])
    with top_left_f:
        st.markdown("""
            <div style="display:flex; align-items:center; gap:14px; margin:8px 0 8px;">
              <svg width="48" height="48" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 30L32 10L56 30V54H38V40H26V54H8V30Z" fill="rgba(29,161,242,0.25)" stroke="#EAF0FF" stroke-width="2"/>
                <rect x="22" y="34" width="5" height="10" fill="#1DA1F2"/><rect x="30" y="30" width="5" height="14" fill="#1DA1F2"/><rect x="38" y="26" width="5" height="18" fill="#1DA1F2"/>
              </svg>
              <span style="font-size:30px; font-weight:800;">Fix & Flip Deal Analyzer</span>
            </div>
            """, unsafe_allow_html=True)

    with top_right_f:
        f_excel_btn = st.empty()
        f_pdf_btn = st.empty()

    fcol1, fsp1, fcol2, fsp2, fcol3 = st.columns([1.2, 0.15, 1, 0.15, 1])

    with fcol1:
        st.header("🔢 Flip Inputs")
        f_purchase = st.number_input("Purchase Price ($)", value=200000, key="flip_p")
        f_rehab = st.number_input("Base Rehab Cost ($)", value=50000, key="flip_r")
        f_cont_pct = st.number_input("Rehab Contingency (%)", value=10.0, key="flip_c") / 100
        f_arv = st.number_input("After Repair Value (ARV) ($)", value=350000, key="flip_arv")
        f_months = st.number_input("Holding Period (Months)", value=6, key="flip_h")
        
        with st.expander("🏦 Financing & Carry Costs"):
            f_points = st.number_input("Loan Points (%)", value=2.0) / 100
            f_rate = st.number_input("Interest Rate (%)", value=10.0) / 100
            f_tax_m = st.number_input("Monthly Taxes ($)", value=250)
            f_ins_m = st.number_input("Monthly Insurance ($)", value=150)
            f_util_m = st.number_input("Monthly Utilities ($)", value=200)

        f_sell_pct = st.number_input("Selling Costs (% of ARV)", value=6.0) / 100
        
        if st.button("📊 Analyze Flip"):
            st.session_state.flip_analyzed = True

    if st.session_state.flip_analyzed:
        # Calculations
        buy_costs = f_purchase * 0.025
        total_rehab = f_rehab * (1 + f_cont_pct)
        loan_amt = f_purchase * 0.80
        financing = (loan_amt * f_points) + ((loan_amt * f_rate / 12) * f_months)
        holding = (f_tax_m + f_ins_m + f_util_m) * f_months
        selling = f_arv * f_sell_pct
        
        total_investment = f_purchase + buy_costs + total_rehab + financing + holding + selling
        net_profit = f_arv - total_investment
        cash_req = (f_purchase - loan_amt) + buy_costs + (loan_amt * f_points) + total_rehab + holding
        
        roi = (net_profit / cash_req) * 100 if cash_req > 0 else 0
        mao = (f_arv * 0.70) - total_rehab

        st.session_state.flip_results = {
            "Net Profit": net_profit,
            "ROI": roi / 100,
            "Annualized ROI": (roi / f_months * 12) / 100,
            "70% Rule MAO": mao,
            "Total Project Cost": total_investment,
            "Cash Needed": cash_req
        }

        with fcol2:
            st.header("📈 Flip Results")
            r = st.session_state.flip_results
            st.metric("Net Profit", f"${r['Net Profit']:,.0f}")
            st.metric("ROI", f"{r['ROI']:.2%}")
            st.metric("Annualized ROI", f"{r['Annualized ROI']:.2%}")
            st.info(f"**70% Rule (MAO):** ${r['70% Rule MAO']:,.0f}")

        with fcol3:
            st.header("💸 Cost Breakdown")
            st.write(f"Rehab + Contingency: ${total_rehab:,.0f}")
            st.write(f"Financing Costs: ${financing:,.0f}")
            st.write(f"Holding Costs: ${holding:,.0f}")
            st.write(f"Selling Costs: ${selling:,.0f}")
            st.write(f"**Total Cash Required:** ${r['Cash Needed']:,.0f}")

        export_excel_pdf(st.session_state.flip_results, f_excel_btn, f_pdf_btn, "flip_analysis.xlsx", "flip_analysis.pdf")

# ================= DISCLAIMER FOOTER =================
st.markdown("---")
current_year = datetime.now().year
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
