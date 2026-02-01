import streamlit as st
import pandas as pd

# 1. Page Config & Professional UI Styling
st.set_page_config(page_title="Accounting Mastery Pro", layout="wide")

st.markdown("""
    <style>
    /* Global Styles */
    .main { background-color: #f8f9fa; }
    h1 { color: #1e3a8a; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    
    /* Formal UK T-Account Styling */
    .t-account-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #ffffff;
        color: #111827;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .t-title {
        text-align: center; font-weight: 800; font-size: 1.4rem; color: #1e3a8a;
        border-bottom: 3px solid #1e3a8a; padding-bottom: 8px; margin-bottom: 10px;
    }
    .t-labels { display: flex; justify-content: space-between; font-weight: 700; color: #6b7280; font-size: 0.85rem; text-transform: uppercase; }
    .t-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .t-table td { vertical-align: top; padding: 6px 12px; font-size: 1rem; }
    .left-col { border-right: 2px solid #1e3a8a; }
    .row-flex { display: flex; justify-content: space-between; align-items: center; width: 100%; }
    
    /* Balancing Lines */
    .total-line { border-top: 2px solid #000; border-bottom: 5px double #000; font-weight: 800; margin-top: 15px; padding: 5px 0; }
    .bal-bf { font-weight: 800; margin-top: 15px; color: #1e3a8a; border-top: 1px dashed #d1d5db; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. State Management
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger_data' not in st.session_state: st.session_state.ledger_data = {}
if 'attempts' not in st.session_state: st.session_state.attempts = 0

# 3. UK Curriculum Data with Adaptive Hints
tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000, 
     "hint": "The business is receiving 'Bank' (Asset). Assets are DEAD items. To increase, we Debit. The owner provided the money (Capital)."},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000,
     "hint": "The business got a 'Van' (Asset). Assets are DEAD—so Debit. The money left the 'Bank' (Asset). To decrease an Asset, we Credit it."},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200,
     "hint": "Rent is an 'Expense'. Expenses are DEAD. To increase, we Debit. The payment came from the 'Bank'."},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150,
     "hint": "Stationery is an 'Expense' (DEAD). We owe money now, so we have a 'Liability' (Payable). Liabilities are CLIC—so Credit to increase."},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000,
     "hint": "Money in the 'Bank' (Asset) increases. 'Sales' is Income. Income is CLIC—Credit to increase."},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500,
     "hint": "This is 'Drawings' (DEAD). Debit to increase. The 'Bank' (Asset) decreases—so Credit."}
]

# --- UI Setup ---
st.title("💷 The Professional Accounting Lab")
st.sidebar.markdown("### 🎓 DEADCLIC Mastery")
st.sidebar.info("**D**ebit: Expenses, Assets, Drawings\n\n**C**redit: Liabilities, Income, Capital")

if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.info(f"**Level {st.session_state.level + 1}:** {task['q']}")

    col1, col2, col3 = st.columns(3)
    with col1: dr = st.selectbox("Debit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"dr_{st.session_state.level}")
    with col2: cr = st.selectbox("Credit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"cr_{st.session_state.level}")
    with col3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.session_state.attempts >= 2:
        st.warning(f"💡 **Professor's Hint:** {task['hint']}")

    if st.button("Post Transaction 🚀"):
        if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
            st.success("Correct! Well done.")
            st.session_state.attempts = 0
            for side, acc, ref in [('Dr', dr, cr), ('Cr', cr, dr)]:
                if acc not in st.session_state.ledger_data: st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append((ref, amt))
            st.session_state.level += 1
            st.rerun()
        else:
            st.session_state.attempts += 1
            st.error("Incorrect. Check your DEADCLIC logic!")
else:
    st.balloons()
    st.success("Mastery Achieved! All accounts balanced.")
    if st.button("Restart Session"):
        st.session_state.level = 0
        st.session_state.ledger_data = {}
        st.rerun()

# --- THE VISUAL LEDGER ---
st.subheader("📖 Formal General Ledger")
if st.session_state.ledger_data:
    acc_list = list(st.session_state.ledger_data.items())
    for i in range(0, len(acc_list), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(acc_list):
                acc_name, entries = acc_list[i + j]
                dr_sum, cr_sum = sum(x[1] for x in entries['Dr']), sum(x[1] for x in entries['Cr'])
                total, bal_cf = max(dr_sum, cr_sum), max(dr_sum, cr_sum) - min(dr_sum, cr_sum)
                
                with cols[j]:
                    html = f'<div class="t-account-container"><div class="t-labels"><span>Dr</span><span>Cr</span></div><div class="t-title">{acc_name}</div><table class="t-table"><tr><td class="left-col">'
                    for ref, val in entries['Dr']: html += f'<div class="row-flex"><span>{ref}</span><span>{val:,.0f}</span></div>'
                    if cr_sum > dr_sum: html += f'<div class="row-flex"><span>Balance c/f</span><span>{bal_cf:,.0f}</span></div>'
                    html += '</td><td>'
                    for ref, val in entries['Cr']: html += f'<div class="row-flex"><span>{ref}</span><span>{val:,.0f}</span></div>'
                    if dr_sum > cr_sum: html += f'<div class="row-flex"><span>Balance c/f</span><span>{bal_cf:,.0f}</span></div>'
                    html += f'</td></tr><tr><td class="left-col"><div class="total-line row-flex"><span>Total</span><span>{total:,.0f}</span></div></td><td><div class="total-line row-flex"><span>Total</span><span>{total:,.0f}</span></div></td></tr></table>'
                    if dr_sum > cr_sum: html += f'<div class="bal-bf">Balance b/f: £{bal_cf:,.0f}</div>'
                    elif cr_sum > dr_sum: html += f'<div style="text-align: right;" class="bal-bf">Balance b/f: £{bal_cf:,.0f}</div>'
                    st.markdown(html + "</div>", unsafe_allow_html=True)
