import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="Accounting Pro", layout="wide")

# Custom CSS for T-Accounts
st.markdown("""
    <style>
    .t-account { border: 2px solid #333; margin-bottom: 20px; }
    .t-header { text-align: center; border-bottom: 2px solid #333; font-weight: bold; background-color: #f0f2f6; }
    .t-grid { display: grid; grid-template-columns: 1fr 1fr; }
    .t-cell { padding: 5px; border-right: 1px solid #ccc; min-height: 50px; }
    .t-cell-right { padding: 5px; min-height: 50px; }
    .dr-label { color: green; font-weight: bold; }
    .cr-label { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'level' not in st.session_state:
    st.session_state.level = 0
if 'ledger_data' not in st.session_state:
    st.session_state.ledger_data = {} # {AccountName: {'Dr': [], 'Cr': []}}

# Transaction Database (UK Examples)
tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500}
]

# --- UI Layout ---
st.title("💷 The Interactive Accounting Lab")
st.sidebar.header("DEADCLIC Reminder")
st.sidebar.info("**D**ebit: **E**xpenses, **A**ssets, **D**rawings\n\n**C**redit: **L**iabilities, **I**ncome, **C**apital")

if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    
    st.subheader(f"Level {st.session_state.level + 1}: The Transaction")
    st.warning(f"**Scenario:** {task['q']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        dr_choice = st.selectbox("Debit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"])
    with col2:
        cr_choice = st.selectbox("Credit Account", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"])
    with col3:
        amount_input = st.number_input("Amount (£)", value=0)

    if st.button("Post Transaction 🚀"):
        if dr_choice == task['dr'] and cr_choice == task['cr'] and amount_input == task['amt']:
            st.success("Correct! Transaction Posted to T-Accounts.")
            # Update Ledger
            for side, acc in [('Dr', dr_choice), ('Cr', cr_choice)]:
                if acc not in st.session_state.ledger_data:
                    st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append(amount_input)
            
            st.session_state.level += 1
            st.rerun()
        else:
            st.error("Incorrect. Check your DEADCLIC rules and the amount!")

else:
    st.balloons()
    st.success("Full Marks! You've successfully balanced the books.")
    if st.button("Restart Game"):
        st.session_state.level = 0
        st.session_state.ledger_data = {}
        st.rerun()

# --- Visual T-Accounts Section ---
st.divider()
st.subheader("📖 Visual General Ledger (T-Accounts)")

if not st.session_state.ledger_data:
    st.write("No transactions posted yet. Complete Level 1 to see the magic!")
else:
    cols = st.columns(3)
    idx = 0
    for acc_name, entries in st.session_state.ledger_data.items():
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="t-account">
                    <div class="t-header">{acc_name}</div>
                    <div class="t-grid">
                        <div class="t-cell"><span class="dr-label">Dr</span><br>{'<br>'.join([f'£{x}' for x in entries['Dr']])}</div>
                        <div class="t-cell-right"><span class="cr-label">Cr</span><br>{'<br>'.join([f'£{x}' for x in entries['Cr']])}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        idx += 1

# --- Trial Balance Section ---
st.divider()
st.subheader("⚖️ Final Trial Balance")
tb_list = []
total_dr = 0
total_cr = 0

for acc, entries in st.session_state.ledger_data.items():
    balance = sum(entries['Dr']) - sum(entries['Cr'])
    if balance > 0:
        tb_list.append([acc, f"£{balance}", ""])
        total_dr += balance
    elif balance < 0:
        tb_list.append([acc, "", f"£{abs(balance)}"])
        total_cr += abs(balance)

if tb_list:
    df = pd.DataFrame(tb_list, columns=["Account", "Debit", "Credit"])
    st.table(df)
    st.markdown(f"**Total Debits:** £{total_dr} | **Total Credits:** £{total_cr}")
