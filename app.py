import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Accounting Masterclass", layout="wide")

# 2. Professional CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .score-card { 
        background: #1e3a8a; color: white; padding: 15px; 
        border-radius: 8px; text-align: center; font-weight: bold; 
    }
    .t-container {
        background-color: white; border: 2px solid #000; margin-bottom: 20px; font-family: 'Arial', sans-serif;
    }
    .t-header {
        background-color: #1e3a8a; color: white; text-align: center; font-weight: bold;
        padding: 5px; text-transform: uppercase; border-bottom: 2px solid #000;
    }
    .t-body { display: flex; width: 100%; }
    .t-side { width: 50%; padding: 5px; }
    .t-left { border-right: 2px solid #000; }
    .t-row { display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding: 2px 0; font-size: 0.9rem; }
    .t-total {
        border-top: 2px solid #000; border-bottom: 5px double #000; font-weight: bold;
        display: flex; justify-content: space-between; margin-top: 5px; padding-top: 2px;
    }
    .bal-bf { color: #1e3a8a; font-weight: bold; margin-top: 5px; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# 3. State Management
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger' not in st.session_state: st.session_state.ledger = {}
if 'score' not in st.session_state: st.session_state.score = 0
if 'mistakes' not in st.session_state: st.session_state.mistakes = 0
if 'round_complete' not in st.session_state: st.session_state.round_complete = False

# 4. 20-Round Data
tasks = [
    # SPRINT 1
    {"q": "Owner invests £50,000 cash to start business.", "dr": "Bank", "cr": "Capital", "amt": 50000},
    {"q": "Purchased premises for £30,000 cash.", "dr": "Premises", "cr": "Bank", "amt": 30000},
    {"q": "Bought office furniture for £2,000 cash.", "dr": "Fixtures", "cr": "Bank", "amt": 2000},
    {"q": "Paid insurance premium £1,200 via bank.", "dr": "Insurance", "cr": "Bank", "amt": 1200},
    {"q": "Purchased inventory for £5,000 cash.", "dr": "Inventory", "cr": "Bank", "amt": 5000},
    # SPRINT 2
    {"q": "Bought goods £4,000 on credit from SupplyCo.", "dr": "Inventory", "cr": "Payables", "amt": 4000},
    {"q": "Sold goods £6,000 on credit to RetailPlus.", "dr": "Receivables", "cr": "Sales", "amt": 6000},
    {"q": "Returned £500 faulty goods to SupplyCo.", "dr": "Payables", "cr": "Inventory", "amt": 500},
    {"q": "RetailPlus returned £300 goods to us.", "dr": "Sales", "cr": "Receivables", "amt": 300},
    {"q": "Paid SupplyCo £3,500 by cheque.", "dr": "Payables", "cr": "Bank", "amt": 3500},
    # SPRINT 3
    {"q": "Received £5,700 from RetailPlus.", "dr": "Bank", "cr": "Receivables", "amt": 5700},
    {"q": "Paid staff wages £2,500.", "dr": "Wages", "cr": "Bank", "amt": 2500},
    {"q": "Took Bank Loan £10,000.", "dr": "Bank", "cr": "Loan", "amt": 10000},
    {"q": "Paid loan interest £100.", "dr": "Interest", "cr": "Bank", "amt": 100},
    {"q": "Owner withdrew £1,000 cash.", "dr": "Drawings", "cr": "Bank", "amt": 1000},
    # SPRINT 4
    {"q": "Accrue unpaid electricity £200.", "dr": "Electricity", "cr": "Accruals", "amt": 200},
    {"q": "Prepay Rent £1,500.", "dr": "Prepayments", "cr": "Rent", "amt": 1500},
    {"q": "Depreciate Fixtures £200.", "dr": "Depreciation", "cr": "Fixtures", "amt": 200},
    {"q": "Write off Bad Debt £400.", "dr": "Bad Debts", "cr": "Receivables", "amt": 400},
    {"q": "Cash Sales for final week £2,000.", "dr": "Bank", "cr": "Sales", "amt": 2000}
]

# 5. T-Account Renderer
def render_t_account(name, data):
    dr_rows = "".join([f'<div class="t-row"><span>{r}</span><span>{v:,.0f}</span></div>' for r, v in data['Dr']])
    cr_rows = "".join([f'<div class="t-row"><span>{r}</span><span>{v:,.0f}</span></div>' for r, v in data['Cr']])
    
    dr_sum = sum(x[1] for x in data['Dr'])
    cr_sum = sum(x[1] for x in data['Cr'])
    total = max(dr_sum, cr_sum)
    bal_cf = total - min(dr_sum, cr_sum)
    
    dr_extra = f'<div class="t-row" style="color:#666; font-style:italic;"><span>Bal c/f</span><span>{bal_cf:,.0f}</span></div>' if cr_sum > dr_sum else ""
    cr_extra = f'<div class="t-row" style="color:#666; font-style:italic;"><span>Bal c/f</span><span>{bal_cf:,.0f}</span></div>' if dr_sum > cr_sum else ""

    bal_bf = ""
    if dr_sum > cr_sum: bal_bf = f'<div class="bal-bf">Bal b/f: £{bal_cf:,.0f}</div>'
    elif cr_sum > dr_sum: bal_bf = f'<div class="bal-bf" style="text-align:right;">Bal b/f: £{bal_cf:,.0f}</div>'

    return f"""
    <div class="t-container">
        <div class="t-header">{name}</div>
        <div class="t-body">
            <div class="t-side t-left">{dr_rows}{dr_extra}<div class="t-total"><span>Total</span><span>{total:,.0f}</span></div>{bal_bf if dr_sum > cr_sum else ""}</div>
            <div class="t-side">{cr_rows}{cr_extra}<div class="t-total"><span>Total</span><span>{total:,.0f}</span></div>{bal_bf if cr_sum > dr_sum else ""}</div>
        </div>
    </div>
    """

# 6. PDF Generator
def create_pdf(name, score, grade, email):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(5)
    pdf.rect(5, 5, 287, 200)
    pdf.set_font("Helvetica", "B", 40)
    pdf.cell(0, 60, "CERTIFICATE OF ACHIEVEMENT", ln=True, align="C")
    pdf.set_font("Helvetica", "", 20)
    pdf.cell(0, 20, "Awarded to", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 30)
    pdf.cell(0, 25, name.upper(), ln=True, align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 15, f"Account: {email}", ln=True, align="C")
    pdf.cell(0, 15, f"Grade: {grade} | Score: {score}", ln=True, align="C")
    return pdf.output()

# --- APP LAYOUT ---
st.title("🎓 Accounting Masterclass")
col_score, col_prog = st.columns([1, 4])
with col_score: st.markdown(f'<div class="score-card">Score: {st.session_state.score}</div>', unsafe_allow_html=True)
with col_prog: 
    st.progress(st.session_state.level / len(tasks))
    st.caption(f"Round {st.session_state.level + 1} of 20")

# --- GAME LOGIC ---
if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    
    if not st.session_state.round_complete:
        st.info(f"**Transaction:** {task['q']}")
        c1, c2, c3 = st.columns(3)
        acc_opts = ["Select...", "Bank", "Capital", "Premises", "Fixtures", "Insurance", "Inventory", "Payables", "Receivables", "Sales", "Wages", "Loan", "Interest", "Drawings", "Electricity", "Accruals", "Prepayments", "Rent", "Depreciation", "Bad Debts"]
        
        with c1: dr = st.selectbox("Debit (DEAD)", acc_opts, key=f"d{st.session_state.level}")
        with c2: cr = st.selectbox("Credit (CLIC)", acc_opts, key=f"c{st.session_state.level}")
        with c3: amt = st.number_input("Amount (£)", step=10, key=f"a{st.session_state.level}")
        
        if st.button("Post Transaction"):
            if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
                st.session_state.score += 100
                st.session_state.round_complete = True
                if dr not in st.session_state.ledger: st.session_state.ledger[dr] = {'Dr': [], 'Cr': []}
                if cr not in st.session_state.ledger: st.session_state.ledger[cr] = {'Dr': [], 'Cr': []}
                # Narrative Logic: The narrative is the OTHER account name
                st.session_state.ledger[dr]['Dr'].append((cr, amt))
                st.session_state.ledger[cr]['Cr'].append((dr, amt))
                st.rerun()
            else:
                st.session_state.score -= 20
                st.session_state.mistakes += 1
                st.error("Incorrect posting. Check your DEADCLIC logic!")
    else:
        st.success("✅ Transaction Posted! Review the T-Accounts below.")
        c_a, c_b = st.columns(2)
        with c_a: st.markdown(render_t_account(task['dr'], st.session_state.ledger[task['dr']]), unsafe_allow_html=True)
        with c_b: st.markdown(render_t_account(task['cr'], st.session_state.ledger[task['cr']]), unsafe_allow_html=True)

        if st.button("➡️ Proceed to Next Round"):
            st.session_state.level += 1
            st.session_state.round_complete = False
            st.rerun()
else:
    st.balloons()
    acc = (len(tasks) / (len(tasks) + st.session_state.mistakes)) * 100
    grade = 'Distinction' if acc > 90 else 'Merit' if acc > 75 else 'Pass'
    st.success(f"### Course Complete! Final Grade: {grade}")
    with st.expander("🎓 Download Certificate"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        if name and email:
            pdf = create_pdf(name, st.session_state.score, grade, email)
            st.download_button("Download PDF", pdf, "Certificate.pdf", "application/pdf")

if st.session_state.ledger:
    st.divider()
    with st.expander("📖 View Full General Ledger", expanded=False):
        keys = list(st.session_state.ledger.keys())
        for i in range(0, len(keys), 2):
            c1, c2 = st.columns(2)
            with c1: st.markdown(render_t_account(keys[i], st.session_state.ledger[keys[i]]), unsafe_allow_html=True)
            if i+1 < len(keys):
                with c2: st.markdown(render_t_account(keys[i+1], st.session_state.ledger[keys[i+1]]), unsafe_allow_html=True)
