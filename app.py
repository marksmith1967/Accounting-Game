import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="Accounting Pro", layout="wide")

# IMPROVED CSS for Visibility
st.markdown("""
    <style>
    .t-account { border: 2px solid #4A90E2; margin-bottom: 20px; border-radius: 5px; background-color: #1E1E1E; }
    .t-header { 
        text-align: center; 
        border-bottom: 2px solid #4A90E2; 
        font-weight: bold; 
        padding: 10px;
        color: #FFFFFF !important;  /* Pure white text */
        background-color: #4A90E2; /* Blue background for headers */
        font-size: 1.2rem;
    }
    .t-grid { display: grid; grid-template-columns: 1fr 1fr; }
    .t-cell { padding: 10px; border-right: 1px solid #4A90E2; min-height: 80px; text-align: left; color: #00FF00; }
    .t-cell-right { padding: 10px; min-height: 80px; text-align: right; color: #FF4B4B; }
    .dr-label { font-size: 0.8rem; opacity: 0.7; color: white; }
    .cr-label { font-size: 0.8rem; opacity: 0.7; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'level' not in st.session_state:
    st.session_state.level = 0
if 'ledger_data' not in st.session_state:
    st.session_state.ledger_data = {}

tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500}
]

st.title("💷 The Interactive Accounting Lab")
st.sidebar.header("DEADCLIC Reminder")
st.sidebar.markdown("""
- **D**ebit: **E**xpenses, **A**ssets, **D**rawings
- **C**redit: **L**iabilities, **I**ncome, **C**apital
""")

if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.subheader(f"Level {st.session_state.level + 1}: The Transaction")
    st.info(f"**Scenario:** {task['q']}")

    # Form using columns
    col1, col2, col3 = st.columns(3)
    
    # The 'key' uses the level number to ensure it resets when the level changes
    with col1:
        dr_choice = st.selectbox("Debit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"dr_{st.session_state.level}")
    with col2:
        cr_choice = st.selectbox("Credit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"cr_{st.session_state.level}")
    with col3:
        amount_input = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.button("Post Transaction 🚀"):
        if dr_choice == task['dr'] and cr_choice == task['cr'] and amount_input == task['amt']:
            st.success("Correct! Well done.")
            for side, acc in [('Dr', dr_choice), ('Cr', cr_choice)]:
                if acc not in st.session_state.ledger_data:
                    st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append(amount_input)
            st.session_state.level += 1
            st.rerun()
        else:
            st.error("Incorrect. Check your DEADCLIC logic!")
            if dr_choice != "Select..." and dr_choice != task['dr']:
                st.write(f"💡 Hint: Is {dr_choice} really a 'DEAD' item (Expense, Asset, or Drawing) that is increasing?")

else:
    st.balloons()
    st.success("Mastery Achieved! All accounts balanced.")
    if st.button("Restart Session"):
        st.session_state.level = 0
        st.session_state.ledger_data = {}
        st.rerun()

# --- T-Accounts ---
st.divider()
st.subheader("📖 Visual General Ledger (T-Accounts)")

if st.session_state.ledger_data:
    cols = st.columns(3)
    for i, (acc_name, entries) in enumerate(st.session_state.ledger_data.items()):
        with cols[i % 3]:
            dr_content = '<br>'.join([f"£{x}" for x in entries['Dr']]) if entries['Dr'] else ""
            cr_content = '<br>'.join([f"£{x}" for x in entries['Cr']]) if entries['Cr'] else ""
            st.markdown(f"""
                <div class="t-account">
                    <div class="t-header">{acc_name}</div>
                    <div class="t-grid">
                        <div class="t-cell"><span class="dr-label">Dr</span><br>{dr_content}</div>
                        <div class="t-cell-right"><span class="cr-label">Cr</span><br>{cr_content}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- Trial Balance ---
st.divider()
st.subheader("⚖️ Trial Balance Summary")
if st.session_state.ledger_data:
    tb_data = []
    t_dr, t_cr = 0, 0
    for acc, entries in st.session_state.ledger_data.items():
        bal = sum(entries['Dr']) - sum(entries['Cr'])
        if bal > 0:
            tb_data.append({"Account": acc, "Debit": f"£{bal}", "Credit": ""})
            t_dr += bal
        elif bal < 0:
            tb_data.append({"Account": acc, "Debit": "", "Credit": f"£{abs(bal)}"})
            t_cr += abs(bal)
    
    st.table(pd.DataFrame(tb_data))
    st.write(f"**Total Debits:** £{t_dr} | **Total Credits:** £{t_cr}")
