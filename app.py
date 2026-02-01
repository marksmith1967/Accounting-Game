import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# 1. Professional Styling
st.set_page_config(page_title="Accounting Masterclass", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .t-account-container { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #d1d5db; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .t-title { text-align: center; font-weight: 800; border-bottom: 3px solid #1e3a8a; color: #1e3a8a; margin-bottom: 10px; text-transform: uppercase; }
    .t-table { width: 100%; border-collapse: collapse; }
    .left-col { border-right: 2px solid #1e3a8a; width: 50%; padding: 5px 10px; }
    .right-col { width: 50%; padding: 5px 10px; }
    .total-line { border-top: 1px solid #000; border-bottom: 4px double #000; font-weight: bold; margin-top: 10px; }
    .score-card { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. State Initialization
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger' not in st.session_state: st.session_state.ledger = {}
if 'score' not in st.session_state: st.session_state.score = 0
if 'mistakes' not in st.session_state: st.session_state.mistakes = 0

# 3. 20-Round Data (Progressive Difficulty)
tasks = [
    {"q": "Owner invests £50,000 cash to start the business.", "dr": "Bank", "cr": "Capital", "amt": 50000},
    {"q": "Purchased premises for £30,000 cash.", "dr": "Premises", "cr": "Bank", "amt": 30000},
    {"q": "Bought office furniture for £2,000 cash.", "dr": "Fixtures", "cr": "Bank", "amt": 2000},
    {"q": "Paid insurance premium of £1,200 via bank.", "dr": "Insurance", "cr": "Bank", "amt": 1200},
    {"q": "Purchased inventory for £5,000 cash.", "dr": "Inventory", "cr": "Bank", "amt": 5000},
    {"q": "Bought inventory for £4,000 on credit from 'SupplyCo'.", "dr": "Inventory", "cr": "Payables", "amt": 4000},
    {"q": "Sold goods for £6,000 on credit to 'RetailPlus'.", "dr": "Receivables", "cr": "Sales", "amt": 6000},
    {"q": "Returned £500 of faulty inventory to 'SupplyCo'.", "dr": "Payables", "cr": "Inventory", "amt": 500},
    {"q": "Customer 'RetailPlus' returned £300 of goods.", "dr": "Sales", "cr": "Receivables", "amt": 300},
    {"q": "Paid 'SupplyCo' £3,500 by cheque.", "dr": "Payables", "cr": "Bank", "amt": 3500},
    {"q": "Received £5,700 from customer 'RetailPlus' in settlement.", "dr": "Bank", "cr": "Receivables", "amt": 5700},
    {"q": "Paid monthly staff wages of £2,500.", "dr": "Wages", "cr": "Bank", "amt": 2500},
    {"q": "Took out a bank loan for £10,000.", "dr": "Bank", "cr": "Loan", "amt": 10000},
    {"q": "Paid bank loan interest of £100.", "dr": "Interest", "cr": "Bank", "amt": 100},
    {"q": "Owner withdrew £1,000 for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 1000},
    {"q": "Year-End: Accrue for unpaid electricity £200.", "dr": "Electricity", "cr": "Accruals", "amt": 200},
    {"q": "Year-End: Prepayment for Rent £1,500.", "dr": "Prepayments", "cr": "Rent", "amt": 1500},
    {"q": "Year-End: Record depreciation on fixtures £200.", "dr": "Depreciation", "cr": "Fixtures", "amt": 200},
    {"q": "Year-End: Write off a bad debt £400.", "dr": "Bad Debts", "cr": "Receivables", "amt": 400},
    {"q": "Record final cash sales for the year £2,000.", "dr": "Bank", "cr": "Sales", "amt": 2000}
]

# 4. Certificate Generator Function
def create_certificate(name, score, grade):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(5)
    pdf.rect(5, 5, 287, 200) # Border
    
    pdf.set_font("Helvetica", "B", 40)
    pdf.cell(0, 60, "CERTIFICATE OF ACHIEVEMENT", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 20)
    pdf.cell(0, 20, "This is to certify that", ln=True, align="C")
    
    pdf.set_font("Helvetica", "B", 35)
    pdf.cell(0, 25, name.upper(), ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 20)
    pdf.cell(0, 20, f"has successfully completed the Accounting Masterclass", ln=True, align="C")
    pdf.cell(0, 15, f"with a Final Grade of: {grade}", ln=True, align="C")
    
    pdf.set_font("Helvetica", "I", 12)
    date_str = datetime.now().strftime("%d %B %Y")
    pdf.cell(0, 30, f"Issued on {date_str} | Score: {score}", ln=True, align="C")
    
    return pdf.output()

# --- MAIN UI ---
st.title("🎓 Accounting Masterclass: 20-Round Challenge")
c1, c2 = st.columns([3, 1])
with c2:
    st.markdown(f'<div class="score-card"><h3>Score: {st.session_state.score}</h3></div>', unsafe_allow_html=True)
with c1:
    prog = st.session_state.level / len(tasks)
    st.progress(prog)
    st.write(f"Level {st.session_state.level + 1} of 20")

if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.info(f"**Transaction:** {task['q']}")

    i1, i2, i3 = st.columns(3)
    accounts = ["Select...", "Bank", "Capital", "Premises", "Fixtures", "Insurance", "Inventory", "Payables", "Receivables", "Sales", "Wages", "Loan", "Interest", "Drawings", "Electricity", "Accruals", "Prepayments", "Rent", "Depreciation", "Bad Debts"]
    with i1: dr = st.selectbox("Debit", accounts, key=f"dr_{st.session_state.level}")
    with i2: cr = st.selectbox("Credit", accounts, key=f"cr_{st.session_state.level}")
    with i3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.button("Post Transaction 🚀"):
        if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
            st.success("Correct! +100 Points")
            st.session_state.score += 100
            for side, acc, ref in [('Dr', dr, cr), ('Cr', cr, dr)]:
                if acc not in st.session_state.ledger: st.session_state.ledger[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger[acc][side].append((ref, amt))
            st.session_state.level += 1
            st.rerun()
        else:
            st.session_state.score -= 20
            st.session_state.mistakes += 1
            st.error("Incorrect. Remember DEADCLIC! (-20 Points)")
else:
    # FINAL RESULTS & CERTIFICATE
    st.balloons()
    accuracy = (len(tasks) / (len(tasks) + st.session_state.mistakes)) * 100
    grade = 'Distinction (A+)' if accuracy > 90 else 'Merit (A)' if accuracy > 80 else 'Pass (B)'
    
    st.success(f"### Final Grade: {grade} ({accuracy:.1f}% Accuracy)")
    
    st.divider()
    st.subheader("🏆 Claim Your Reward")
    student_name = st.text_input("Enter your full name for the certificate:")
    if student_name:
        pdf_bytes = create_certificate(student_name, st.session_state.score, grade)
        st.download_button(label="Download Certificate 🎓", data=pdf_bytes, file_name="Accounting_Certificate.pdf", mime="application/pdf")

    # TRIAL BALANCE & LEDGER (Same logic as before...)
    st.divider()
    st.subheader("⚖️ Final Trial Balance")
    tb = []
    t_dr, t_cr = 0, 0
    for acc, data in st.session_state.ledger.items():
        bal = sum(x[1] for x in data['Dr']) - sum(x[1] for x in data['Cr'])
        if bal > 0: tb.append([acc, bal, 0]); t_dr += bal
        elif bal < 0: tb.append([acc, 0, abs(bal)]); t_cr += abs(bal)
    st.table(pd.DataFrame(tb, columns=["Account", "Debit (£)", "Credit (£)"]))
    st.markdown(f"**Totals:** Debit £{t_dr:,.0f} | Credit £{t_cr:,.0f}")
