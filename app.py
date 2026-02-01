import streamlit as st
import pandas as pd

# 1. Page Config & Visual Branding
st.set_page_config(page_title="Accounting Mastery Lab", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .t-account-container {
        background-color: white; padding: 20px; border-radius: 12px;
        border: 1px solid #d1d5db; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .t-title { text-align: center; font-weight: 800; border-bottom: 3px solid #1e3a8a; color: #1e3a8a; margin-bottom: 10px; }
    .t-table { width: 100%; border-collapse: collapse; }
    .left-col { border-right: 2px solid #1e3a8a; width: 50%; padding: 5px 10px; }
    .right-col { width: 50%; padding: 5px 10px; }
    .total-line { border-top: 1px solid #000; border-bottom: 4px double #000; font-weight: bold; margin-top: 10px; }
    .score-card { background: #1e3a8a; color: white; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. State Initialization
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger_data' not in st.session_state: st.session_state.ledger_data = {}
if 'score' not in st.session_state: st.session_state.score = 0
if 'wrong_attempts' not in st.session_state: st.session_state.wrong_attempts = 0

tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500}
]

# --- UI Header ---
st.title("💷 The Interactive Accounting Lab")
cols = st.columns([3, 1])
with cols[1]:
    st.markdown(f'<div class="score-card"><h3>Score: {st.session_state.score}</h3></div>', unsafe_allow_html=True)

# --- Gameplay Section ---
if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.info(f"**Level {st.session_state.level + 1}:** {task['q']}")

    c1, c2, c3 = st.columns(3)
    with c1: dr = st.selectbox("Debit (DEAD)", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"dr_{st.session_state.level}")
    with c2: cr = st.selectbox("Credit (CLIC)", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"cr_{st.session_state.level}")
    with c3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.button("Post Transaction 🚀"):
        if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
            st.success("Correct!")
            st.session_state.score += 100
            for side, acc, ref in [('Dr', dr, cr), ('Cr', cr, dr)]:
                if acc not in st.session_state.ledger_data: st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append((ref, amt))
            st.session_state.level += 1
            st.rerun()
        else:
            st.session_state.score -= 20
            st.session_state.wrong_attempts += 1
            st.error("Incorrect. Check your DEADCLIC logic! (-20 points)")

else:
    # --- Final Results & Trial Balance ---
    st.balloons()
    accuracy = (len(tasks) / (len(tasks) + st.session_state.wrong_attempts)) * 100
    grade = "A+" if accuracy > 90 else "A" if accuracy > 80 else "B" if accuracy > 70 else "C"
    
    st.markdown(f"""
        <div style="background: white; padding: 30px; border-radius: 15px; border: 2px solid #1e3a8a; text-align: center;">
            <h1 style="margin:0;">Final Grade: {grade}</h1>
            <p>Accuracy: {accuracy:.1f}% | Total Mistakes: {st.session_state.wrong_attempts}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TRIAL BALANCE ---
    st.subheader("⚖️ Formal Trial Balance as at Today")
    tb_rows = []
    total_dr, total_cr = 0, 0
    for acc, entries in st.session_state.ledger_data.items():
        bal = sum(x[1] for x in entries['Dr']) - sum(x[1] for x in entries['Cr'])
        if bal > 0:
            tb_rows.append({"Account": acc, "Debit (£)": f"{bal:,.0f}", "Credit (£)": ""})
            total_dr += bal
        elif bal < 0:
            tb_rows.append({"Account": acc, "Debit (£)": "", "Credit (£)": f"{abs(bal):,.0f}"})
            total_cr += abs(bal)
    
    df = pd.DataFrame(tb_rows)
    st.table(df)
    st.markdown(f"**Final Totals:** Debit £{total_dr:,.0f} | Credit £{total_cr:,.0f}")

# --- THE LEDGER VIEW (REMAINING SAME AS PREVIOUS) ---
if st.session_state.ledger_data:
    st.divider()
    st.subheader("📖 General Ledger T-Accounts")
    acc_items = list(st.session_state.ledger_data.items())
    for i in range(0, len(acc_items), 2):
        l_cols = st.columns(2)
        for j in range(2):
            if i + j < len(acc_items):
                name, data = acc_items[i+j]
                dr_s, cr_s = sum(x[1] for x in data['Dr']), sum(x[1] for x in data['Cr'])
                tot, b_cf = max(dr_s, cr_s), max(dr_s, cr_s) - min(dr_s, cr_s)
                with l_cols[j]:
                    h = f'<div class="t-account-container"><div class="t-title">{name}</div><table class="t-table"><tr><td class="left-col">'
                    for r, v in data['Dr']: h += f'<div>{r} <span style="float:right;">{v}</span></div>'
                    if cr_s > dr_s: h += f'<div style="font-style:italic;">Bal c/f <span style="float:right;">{b_cf}</span></div>'
                    h += '</td><td class="right-col">'
                    for r, v in data['Cr']: h += f'<div>{r} <span style="float:right;">{v}</span></div>'
                    if dr_s > cr_s: h += f'<div style="font-style:italic;">Bal c/f <span style="float:right;">{b_cf}</span></div>'
                    h += f'</td></tr><tr class="total-line"><td>Total <span style="float:right;">{tot}</span></td><td>Total <span style="float:right;">{tot}</span></td></tr></table>'
                    if dr_s > cr_s: h += f'<div style="font-weight:bold; margin-top:5px;">Bal b/f: £{b_cf}</div>'
                    elif cr_s > dr_s: h += f'<div style="font-weight:bold; margin-top:5px; text-align:right;">Bal b/f: £{b_cf}</div>'
                    st.markdown(h + "</div>", unsafe_allow_html=True)
