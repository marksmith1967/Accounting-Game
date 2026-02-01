import streamlit as st
import pandas as pd

# 1. Page Config & Professional UI Styling
st.set_page_config(page_title="Accounting Mastery Lab", layout="wide")

st.markdown("""
    <style>
    /* Global Styles */
    .main { background-color: #f8f9fa; }
    h1 { color: #1e3a8a; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    
    /* Scoring & Progress Card */
    .score-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 20px; border-radius: 12px;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

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
    
    /* Trial Balance Styling */
    .tb-table { width: 100%; border: 1px solid #000; background: white; }
    .tb-header { background: #1e3a8a; color: white; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. State Management
if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger_data' not in st.session_state: st.session_state.ledger_data = {}
if 'score' not in st.session_state: st.session_state.score = 0
if 'attempts' not in st.session_state: st.session_state.attempts = 0
if 'wrong_total' not in st.session_state: st.session_state.wrong_total = 0

# 3. UK Curriculum Data
tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000, 
     "hint": "The business receives 'Bank' (Asset). Assets are DEAD—Debit to increase. Who gave it? Capital."},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000,
     "hint": "The 'Van' (Asset) is DEAD—Debit. Money left 'Bank' (Asset)—Credit to decrease."},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200,
     "hint": "Rent is an 'Expense' (DEAD)—Debit. Payment from 'Bank'—Credit."},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150,
     "hint": "Stationery is an 'Expense' (DEAD). You owe money (Liability/Payable). Liabilities are CLIC—Credit to increase."},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000,
     "hint": "Money in 'Bank' (Asset) increases. 'Sales' is Income (CLIC)—Credit to increase."},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500,
     "hint": "This is 'Drawings' (DEAD)—Debit. 'Bank' (Asset) decreases—Credit."}
]

# --- UI Header & Score ---
st.title("💷 The Interactive Accounting Lab")

score_col, progress_col = st.columns([1, 2])
with score_col:
    st.markdown(f'<div class="score-card"><h3>Score: {st.session_state.score}</h3></div>', unsafe_allow_html=True)
with progress_col:
    prog = st.session_state.level / len(tasks)
    st.write(f"Course Completion: {int(prog*100)}%")
    st.progress(prog)

# --- Gameplay Section ---
if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.info(f"**Current Task:** {task['q']}")

    c1, c2, c3 = st.columns(3)
    with c1: dr = st.selectbox("Debit Account (DEAD)", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"dr_{st.session_state.level}")
    with c2: cr = st.selectbox("Credit Account (CLIC)", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"cr_{st.session_state.level}")
    with c3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.session_state.attempts >= 2:
        st.warning(f"💡 **Professor's Hint:** {task['hint']}")

    if st.button("Post Transaction 🚀"):
        if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
            st.success("✅ Correct! +100 Points")
            st.session_state.score += 100
            st.session_state.attempts = 0
            # CROSS-REFERENCING LOGIC
            for side, acc, ref in [('Dr', dr, cr), ('Cr', cr, dr)]:
                if acc not in st.session_state.ledger_data: st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append((ref, amt))
            st.session_state.level += 1
            st.rerun()
        else:
            st.session_state.attempts += 1
            st.session_state.wrong_total += 1
            st.session_state.score -= 20
            st.error("❌ Incorrect logic. DEADCLIC check failed! (-20 Points)")

else:
    # --- Final Results & Trial Balance ---
    st.balloons()
    acc_rate = (len(tasks) / (len(tasks) + st.session_state.wrong_total)) * 100
    grade = "A+" if acc_rate > 95 else "A" if acc_rate > 85 else "B" if acc_rate > 70 else "C"
    
    st.markdown(f"""
        <div style="background: white; padding: 30px; border-radius: 15px; border: 2px solid #1e3a8a; text-align: center; margin-bottom:30px;">
            <h1 style="margin:0; color:#1e3a8a;">Final Grade: {grade}</h1>
            <p style="font-size:1.2rem;">Accuracy: {acc_rate:.1f}% | Total Mistakes: {st.session_state.wrong_total}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- TRIAL BALANCE ---
    st.subheader("⚖️ Formal Trial Balance")
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
    st.markdown(f"**Final Audit Totals:** Debit £{t_dr:,.0f} | Credit £{t_cr:,.0f}")
    
    if st.button("Start New Session"):
        st.session_state.level = 0
        st.session_state.ledger_data = {}
        st.session_state.score = 0
        st.session_state.wrong_total = 0
        st.rerun()

# --- THE VISUAL LEDGER ---
st.divider()
st.subheader("📖 Formal General Ledger (T-Accounts)")
if st.session_state.ledger_data:
    acc_items = list(st.session_state.ledger_data.items())
    for i in range(0, len(acc_items), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(acc_items):
                name, data = acc_items[i+j]
                dr_s, cr_s = sum(x[1] for x in data['Dr']), sum(x[1] for x in data['Cr'])
                tot, b_cf = max(dr_s, cr_s), max(dr_s, cr_s) - min(dr_s, cr_s)
                with cols[j]:
                    h = f'<div class="t-account-container"><div class="t-labels"><span>Dr</span><span>Cr</span></div><div class="t-title">{name}</div><table class="t-table"><tr><td class="left-col">'
                    for r, v in data['Dr']: h += f'<div class="row-flex"><span>{r}</span><span>{v:,.0f}</span></div>'
                    if cr_s > dr_s: h += f'<div class="row-flex" style="font-style:italic;"><span>Balance c/f</span><span>{b_cf:,.0f}</span></div>'
                    h += '</td><td>'
                    for r, v in data['Cr']: h += f'<div class="row-flex"><span>{r}</span><span>{v:,.0f}</span></div>'
                    if dr_s > cr_s: h += f'<div class="row-flex" style="font-style:italic;"><span>Balance c/f</span><span>{b_cf:,.0f}</span></div>'
                    h += f'</td></tr><tr><td class="left-col"><div class="total-line row-flex"><span>Total</span><span>{tot:,.0f}</span></div></td><td><div class="total-line row-flex"><span>Total</span><span>{tot:,.0f}</span></div></td></tr></table>'
                    if dr_s > cr_s: h += f'<div class="bal-bf">Balance b/f: £{b_cf:,.0f}</div>'
                    elif cr_s > dr_s: h += f'<div style="text-align: right;" class="bal-bf">Balance b/f: £{bal_cf:,.0f}</div>'
                    st.markdown(h + "</div>", unsafe_allow_html=True)
