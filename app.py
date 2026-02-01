import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Accounting Masterclass", layout="wide")

# 2. Professional CSS (Formal T-Accounts)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .score-card { 
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
        color: white; padding: 15px; border-radius: 10px; 
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    }
    .t-account-container { 
        background-color: white; padding: 15px; border-radius: 8px; 
        border: 2px solid #333; margin-bottom: 20px; 
        box-shadow: 3px 3px 0px rgba(0,0,0,0.1); 
    }
    .t-title { 
        text-align: center; font-weight: 800; border-bottom: 2px solid #000; 
        color: #000; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;
    }
    .t-table { width: 100%; border-collapse: collapse; font-family: 'Courier New', monospace; font-size: 0.9rem; }
    .left-col { border-right: 2px solid #000; width: 50%; padding: 4px; vertical-align: top; }
    .right-col { width: 50%; padding: 4px; vertical-align: top; }
    .row-flex { display: flex; justify-content: space-between; }
    .total-line { border-top: 1px solid #000; border-bottom: 4px double #000; font-weight: bold; margin-top: 8px; }
    .bal-bf { font-weight: bold; margin-top: 5px; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# 3. State Management
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger' not in st.session_state: st.session_state.ledger = {}
if 'score' not in st.session_state: st.session_state.score = 0
if 'mistakes' not in st.session_state: st.session_state.mistakes = 0
if 'round_complete' not in st.session_state: st.session_state.round_complete = False

# 4. 20-Round Progression Data
tasks = [
    # SPRINT 1: THE FOUNDATION
    {"q": "Owner invests £50,000 cash to start the business.", "dr": "Bank", "cr": "Capital", "amt": 50000},
    {"q": "Purchased premises for £30,000 cash.", "dr": "Premises", "cr": "Bank", "amt": 30000},
    {"q": "Bought office furniture for £2,000 cash.", "dr": "Fixtures", "cr": "Bank", "amt": 2000},
    {"q": "Paid insurance premium of £1,200 via bank.", "dr": "Insurance", "cr": "Bank", "amt": 1200},
    {"q": "Purchased inventory for £5,000 cash.", "dr": "Inventory", "cr": "Bank", "amt": 5000},
    # SPRINT 2: CREDIT TRANSACTIONS
    {"q": "Bought inventory for £4,000 on credit from 'SupplyCo'.", "dr": "Inventory", "cr": "Payables", "amt": 4000},
    {"q": "Sold goods for £6,000 on credit to 'RetailPlus'.", "dr": "Receivables", "cr": "Sales", "amt": 6000},
    {"q": "Returned £500 of faulty inventory to 'SupplyCo'.", "dr": "Payables", "cr": "Inventory", "amt": 500},
    {"q": "Customer 'RetailPlus' returned £300 of goods.", "dr": "Sales", "cr": "Receivables", "amt": 300},
    {"q": "Paid 'SupplyCo' £3,500 by cheque.", "dr": "Payables", "cr": "Bank", "amt": 3500},
    # SPRINT 3: OPERATIONS & LOANS
    {"q": "Received £5,700 from customer 'RetailPlus' in settlement.", "dr": "Bank", "cr": "Receivables", "amt": 5700},
    {"q": "Paid monthly staff wages of £2,500.", "dr": "Wages", "cr": "Bank", "amt": 2500},
    {"q": "Took out a bank loan for £10,000.", "dr": "Bank", "cr": "Loan", "amt": 10000},
    {"q": "Paid bank loan interest of £100.", "dr": "Interest", "cr": "Bank", "amt": 100},
    {"q": "Owner withdrew £1,000 for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 1000},
    # SPRINT 4: YEAR-END ADJUSTMENTS
    {"q": "Year-End: Accrue for unpaid electricity £200.", "dr": "Electricity", "cr": "Accruals", "amt": 200},
    {"q": "Year-End: Prepayment for Rent £1,500.", "dr": "Prepayments", "cr": "Rent", "amt": 1500},
    {"q": "Year-End: Record depreciation on fixtures £200.", "dr": "Depreciation", "cr": "Fixtures", "amt": 200},
    {"q": "Year-End: Write off a bad debt £400.", "dr": "Bad Debts", "cr": "Receivables", "amt": 400},
    {"q": "Record final cash sales for the year £2,000.", "dr": "Bank", "cr": "Sales", "amt": 2000}
]

# 5. Certificate Logic (PDF)
def create_pdf(name, score, grade, email):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(5)
    pdf.rect(5, 5, 287, 200)
    pdf.set_font("Helvetica", "B", 40)
    pdf.cell(0, 60, "CERTIFICATE OF COMPETENCY", ln=True, align="C")
    pdf.set_font("Helvetica", "", 20)
    pdf.cell(0, 20, "This certifies that", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 30)
    pdf.cell(0, 25, name.upper(), ln=True, align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 15, f"Email: {email}", ln=True, align="C")
    pdf.cell(0, 15, f"Has passed the Accounting Masterclass with Grade: {grade}", ln=True, align="C")
    return pdf.output()

# --- HEADER SECTION ---
st.title("🎓 Accounting Masterclass: 20-Round Challenge")
c1, c2 = st.columns([3, 1])
with c2:
    st.markdown(f'<div class="score-card"><h3>Score: {st.session_state.score}</h3></div>', unsafe_allow_html=True)
with c1:
    prog = st.session_state.level / len(tasks)
    st.progress(prog)
    st.write(f"Round {st.session_state.level + 1} of {len(tasks)}")

# --- GAMEPLAY LOGIC ---
if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    
    # If round is NOT complete, show the question
    if not st.session_state.round_complete:
        st.info(f"**Transaction:** {task['q']}")
        
        i1, i2, i3 = st.columns(3)
        accounts = ["Select...", "Bank", "Capital", "Premises", "Fixtures", "Insurance", "Inventory", "Payables", "Receivables", "Sales", "Wages", "Loan", "Interest", "Drawings", "Electricity", "Accruals", "Prepayments", "Rent", "Depreciation", "Bad Debts"]
        
        with i1: dr = st.selectbox("Debit (DEAD)", accounts, key=f"dr_{st.session_state.level}")
        with i2: cr = st.selectbox("Credit (CLIC)", accounts, key=f"cr_{st.session_state.level}")
        with i3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

        if st.button("Post Transaction 🚀"):
            if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
                st.success("✅ Correct! The Ledger has been updated.")
                st.session_state.score += 100
                
                # UPDATE LEDGER
                for side, acc, ref in [('Dr', dr, cr), ('Cr', cr, dr)]:
                    if acc not in st.session_state.ledger: st.session_state.ledger[acc] = {'Dr': [], 'Cr': []}
                    st.session_state.ledger[acc][side].append((ref, amt))
                
                # Mark round as complete to trigger "Next" button
                st.session_state.round_complete = True
                st.rerun()
            else:
                st.session_state.score -= 20
                st.session_state.mistakes += 1
                st.error(f"❌ Incorrect. Hint: You need to Debit '{task['dr']}' and Credit '{task['cr']}'. Try again!")
    
    # If round IS complete, show the "Next" button
    else:
        st.success("Transaction posted successfully! Review the T-Accounts below, then click Next.")
        if st.button("➡️ Start Next Round"):
            st.session_state.level += 1
            st.session_state.round_complete = False
            st.rerun()

else:
    # --- FINAL SCREEN ---
    st.balloons()
    accuracy = (len(tasks) / (len(tasks) + st.session_state.mistakes)) * 100
    grade = 'Distinction' if accuracy > 90 else 'Merit' if accuracy > 75 else 'Pass'
    
    st.markdown(f"""
    <div style="background-color:#dcfce7; padding:20px; border-radius:10px; border:2px solid #166534; text-align:center;">
        <h1 style="color:#14532d; margin:0;">Course Completed!</h1>
        <h3>Final Grade: {grade} ({accuracy:.0f}%)</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🏆 Download Your Certificate"):
        name_in = st.text_input("Full Name")
        email_in = st.text_input("Email Address (for our records)")
        if name_in and email_in:
            pdf_data = create_pdf(name_in, st.session_state.score, grade, email_in)
            st.download_button("📥 Download PDF Certificate", data=pdf_data, file_name="Certificate.pdf", mime="application/pdf")

# --- VISUAL LEDGER (ALWAYS VISIBLE) ---
st.divider()
st.subheader("📖 General Ledger (Live View)")

if not st.session_state.ledger:
    st.info("T-Accounts will appear here automatically after your first correct entry.")
else:
    # Grid Logic: Display accounts in rows of 2
    acc_items = list(st.session_state.ledger.items())
    for i in range(0, len(acc_items), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(acc_items):
                name, data = acc_items[i+j]
                dr_s, cr_s = sum(x[1] for x in data['Dr']), sum(x[1] for x in data['Cr'])
                tot, b_cf = max(dr_s, cr_s), max(dr_s, cr_s) - min(dr_s, cr_s)
                
                with cols[j]:
                    # HTML Construction for T-Account
                    h = f'<div class="t-account-container"><div class="t-title">{name}</div><table class="t-table"><tr><td class="left-col">'
                    for r, v in data['Dr']: h += f'<div class="row-flex"><span>{r}</span><span>{v}</span></div>'
                    if cr_s > dr_s: h += f'<div class="row-flex" style="font-style:italic; color:#666;"><span>Bal c/f</span><span>{b_cf}</span></div>'
                    h += '</td><td class="right-col">'
                    for r, v in data['Cr']: h += f'<div class="row-flex"><span>{r}</span><span>{v}</span></div>'
                    if dr_s > cr_s: h += f'<div class="row-flex" style="font-style:italic; color:#666;"><span>Bal c/f</span><span>{b_cf}</span></div>'
                    h += f'</td></tr><tr><td class="left-col"><div class="total-line row-flex"><span>Total</span><span>{tot}</span></div></td><td><div class="total-line row-flex"><span>Total</span><span>{tot}</span></div></td></tr></table>'
                    
                    # Balance Brought Forward Logic
                    if dr_s > cr_s: h += f'<div class="bal-bf">Bal b/f: £{b_cf}</div>'
                    elif cr_s > dr_s: h += f'<div class="bal-bf" style="text-align:right;">Bal b/f: £{b_cf}</div>'
                    
                    st.markdown(h + "</div>", unsafe_allow_html=True)
