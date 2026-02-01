import streamlit as st
import pandas as pd

# 1. Page Config & Professional Styling
st.set_page_config(page_title="Accounting Mastery Lab", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .score-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 15px; border-radius: 12px;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .t-account-container {
        font-family: 'Arial', sans-serif; background-color: #ffffff;
        color: #111827; padding: 20px; border-radius: 10px;
        border: 1px solid #e5e7eb; margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .t-title {
        text-align: center; font-weight: bold; font-size: 1.3rem; color: #1e3a8a;
        border-bottom: 2px solid #1e3a8a; padding-bottom: 5px; margin-bottom: 10px;
    }
    .t-table { width: 100%; border-collapse: collapse; }
    .t-table td { width: 50%; vertical-align: top; padding: 5px 10px; font-size: 0.95rem; }
    .left-col { border-right: 2px solid #1e3a8a; }
    .row-flex { display: flex; justify-content: space-between; width: 100%; }
    .total-line { border-top: 1px solid #000; border-bottom: 4px double #000; font-weight: bold; margin-top: 10px; }
    .bal-bf { font-weight: bold; margin-top: 10px; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# 2. Session State Management
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger_data' not in st.session_state: st.session_state.ledger_data = {}
if 'score' not in st.session_state: st.session_state.score = 0
if 'attempts' not in st.session_state: st.session_state.attempts = 0
if 'wrong_total' not in st.session_state: st.session_state.wrong_total = 0

tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500}
]

# --- Header & Live Score ---
st.title("💷 The Interactive Accounting Lab")
s_col, p_col = st.columns([1, 3])
with s_col:
    st.markdown(f'<div class="score-card"><h3>Score: {st.session_state.score}</h3></div>', unsafe_allow_html=True)
with p_col:
    prog = st.session_state.level / len(tasks)
    st.write(f"Level: {st.session_state.level} of {len(tasks)}")
    st.progress(prog)

# --- Gameplay ---
if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.info(f"**Transaction:** {task['q']}")

    c1, c2, c3 = st.columns(3)
    with c1: dr = st.selectbox("Debit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"dr_{st.session_state.level}")
    with c2: cr = st.selectbox("Credit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"cr_{st.session_state.level}")
    with c3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.button("Post Transaction 🚀"):
        if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
            st.success("✅ Correct Entry!")
            st.session_state.score += 100
            # Cross-reference names for narrative
            for side, acc, ref in [('Dr', dr, cr), ('Cr', cr, dr)]:
                if acc not in st.session_state.ledger_data: st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append((ref, amt))
            st.session_state.level += 1
            st.rerun()
        else:
            st.session_state.score -= 20
            st.session_state.wrong_total += 1
            st.error("❌ Logic Error! DEADCLIC failed. (-20 points)")

else:
    # Final Grading
    st.balloons()
    acc = (len(tasks) / (len(tasks) + st.session_state.wrong_total)) * 100
    grade = "Distinction (A+)" if acc > 95 else "Merit (A)" if acc > 80 else "Pass (B)" if acc > 60 else "Fail (C)"
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 15px; border: 3px solid #1e3a8a; text-align: center; margin-bottom:20px;">
            <h1 style="margin:0;">Final Grade: {grade}</h1>
            <p>Accuracy Rate: {acc:.1f}% | Performance Score: {st.session_state.score}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TRIAL BALANCE ---
    st.divider()
    st.subheader("⚖️ Final Trial Balance")
    tb_data = []
    t_dr, t_cr = 0, 0
    for acc, data in st.session_state.ledger_data.items():
        bal = sum(x[1] for x in data['Dr']) - sum(x[1] for x in data['Cr'])
        if bal > 0:
            tb_data.append({"Account": acc, "Debit (£)": f"{bal:,.0f}", "Credit (£)": ""})
            t_dr += bal
        elif bal < 0:
            tb_data.append({"Account": acc, "Debit (£)": "", "Credit (£)": f"{abs(bal):,.0f}"})
            t_cr += abs(bal)
    
    st.table(pd.DataFrame(tb_data))
    st.markdown(f"**Final Audit:** Debit £{t_dr:,.0f} | Credit £{t_cr:,.0f}")
    if st.button("Restart Training"):
        st.session_state.level = 0
        st.session_state.ledger_data = {}
        st.session_state.score = 0
        st.session_state.wrong_total = 0
        st.rerun()

# --- THE LEDGER GRID (Shows ALL accounts) ---
st.divider()
st.subheader("📖 General Ledger (All T-Accounts)")
if st.session_state.ledger_data:
    acc_items = list(st.session_state.ledger_data.items())
    for i in range(0, len(acc_items), 2): # Renders accounts 2 by 2
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(acc_items):
                name, data = acc_items[i+j]
                dr_s, cr_s = sum(x[1] for x in data['Dr']), sum(x[1] for x in data['Cr'])
                tot, b_cf = max(dr_s, cr_s), max(dr_s, cr_s) - min(dr_s, cr_s)
                with cols[j]:
                    h = f'<div class="t-account-container"><div class="t-title">{name}</div><table class="t-table"><tr><td class="left-col">'
                    for r, v in data['Dr']: h += f'<div class="row-flex"><span>{r}</span><span>{v:,.0f}</span></div>'
                    if cr_s > dr_s: h += f'<div style="font-style:italic;" class="row-flex"><span>Bal c/f</span><span>{b_cf:,.0f}</span></div>'
                    h += '</td><td>'
                    for r, v in data['Cr']: h += f'<div class="row-flex"><span>{r}</span><span>{v:,.0f}</span></div>'
                    if dr_s > cr_s: h += f'<div style="font-style:italic;" class="row-flex"><span>Bal c/f</span><span>{b_cf:,.0f}</span></div>'
                    h += f'</td></tr><tr><td class="left-col"><div class="total-line row-flex"><span>Total</span><span>{tot:,.0f}</span></div></td><td><div class="total-line row-flex"><span>Total</span><span>{tot:,.0f}</span></div></td></tr></table>'
                    if dr_s > cr_s: h += f'<div class="bal-bf">Balance b/f: £{b_cf:,.0f}</div>'
                    elif cr_s > dr_s: h += f'<div style="text-align: right;" class="bal-bf">Balance b/f: £{b_cf:,.0f}</div>'
                    st.markdown(h + "</div>", unsafe_allow_html=True)
else:
    st.info("The Ledger is currently empty. Post your first transaction above.")
