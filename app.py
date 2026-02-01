import streamlit as st
import pandas as pd

st.set_page_config(page_title="Accounting Pro", layout="wide")

# CSS to mimic the formal T-account structure in your image
st.markdown("""
    <style>
    .t-account-container {
        font-family: 'Courier New', Courier, monospace;
        background-color: white;
        color: black;
        padding: 15px;
        border: 1px solid #000;
        margin-bottom: 20px;
        min-width: 400px;
    }
    .t-title {
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        border-bottom: 2px solid black;
        margin-bottom: 0;
    }
    .t-labels {
        display: flex;
        justify-content: space-between;
        font-weight: bold;
        padding: 0 5px;
    }
    .t-table {
        width: 100%;
        border-collapse: collapse;
    }
    .t-table td {
        width: 50%;
        vertical-align: top;
        padding: 2px 5px;
    }
    .left-col { border-right: 2px solid black; }
    .row-flex { display: flex; justify-content: space-between; width: 100%; }
    .total-line { border-top: 1px solid black; border-bottom: 4px double black; font-weight: bold; margin-top: 5px; }
    .bal-bf { font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'level' not in st.session_state: st.session_state.level = 0
if 'ledger_data' not in st.session_state: st.session_state.ledger_data = {}

tasks = [
    {"q": "Owner starts business with £20,000 cash.", "dr": "Bank", "cr": "Capital", "amt": 20000},
    {"q": "Bought a delivery van for £8,000 via bank transfer.", "dr": "Van", "cr": "Bank", "amt": 8000},
    {"q": "Paid office rent of £1,200 by cheque.", "dr": "Rent Expense", "cr": "Bank", "amt": 1200},
    {"q": "Bought stationery for £150 on credit from 'Office Supplies Ltd'.", "dr": "Stationery", "cr": "Payables", "amt": 150},
    {"q": "Sold services for £3,000; customer paid immediately.", "dr": "Bank", "cr": "Sales Income", "amt": 3000},
    {"q": "Owner withdrew £500 cash for personal use.", "dr": "Drawings", "cr": "Bank", "amt": 500}
]

st.title("💷 The Interactive Accounting Lab")

# --- Form Section ---
if st.session_state.level < len(tasks):
    task = tasks[st.session_state.level]
    st.info(f"**Level {st.session_state.level + 1}:** {task['q']}")
    
    col1, col2, col3 = st.columns(3)
    # Selection resets to "Select..." every level because 'key' changes with level
    with col1: dr = st.selectbox("Debit", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"dr_{st.session_state.level}")
    with col2: cr = st.selectbox("Credit", ["Select...", "Bank", "Capital", "Van", "Rent Expense", "Stationery", "Payables", "Sales Income", "Drawings"], key=f"cr_{st.session_state.level}")
    with col3: amt = st.number_input("Amount (£)", value=0, key=f"amt_{st.session_state.level}")

    if st.button("Post Transaction 🚀"):
        if dr == task['dr'] and cr == task['cr'] and amt == task['amt']:
            st.success("Correct!")
            for side, acc in [('Dr', dr), ('Cr', cr)]:
                if acc not in st.session_state.ledger_data: st.session_state.ledger_data[acc] = {'Dr': [], 'Cr': []}
                st.session_state.ledger_data[acc][side].append((task['q'][:15], amt))
            st.session_state.level += 1
            st.rerun()
        else:
            st.error("Incorrect. Use DEADCLIC logic!")

# --- Visual T-Accounts (The Requested Style) ---
st.subheader("📖 Visual General Ledger")
if st.session_state.ledger_data:
    cols = st.columns(2)
    for i, (acc_name, entries) in enumerate(st.session_state.ledger_data.items()):
        dr_sum = sum(x[1] for x in entries['Dr'])
        cr_sum = sum(x[1] for x in entries['Cr'])
        total = max(dr_sum, cr_sum)
        bal_cf = total - min(dr_sum, cr_sum)
        
        with cols[i % 2]:
            html = f"""<div class="t-account-container">
                <div class="t-labels"><span>Dr</span><span>Cr</span></div>
                <div class="t-title">{acc_name}</div>
                <table class="t-table"><tr><td class="left-col">"""
            
            # Left Side (Dr)
            for desc, val in entries['Dr']:
                html += f'<div class="row-flex"><span>{desc}</span><span>{val}</span></div>'
            if cr_sum > dr_sum:
                html += f'<div class="row-flex"><span>Balance c/f</span><span>{bal_cf}</span></div>'
            
            html += '</td><td>' # Switch to Credit Side
            
            # Right Side (Cr)
            for desc, val in entries['Cr']:
                html += f'<div class="row-flex"><span>{desc}</span><span>{val}</span></div>'
            if dr_sum > cr_sum:
                html += f'<div class="row-flex"><span>Balance c/f</span><span>{bal_cf}</span></div>'
            
            # Totals and Balance b/f
            html += f"""</td></tr>
                <tr><td class="left-col"><div class="total-line row-flex"><span>Total</span><span>{total}</span></div></td>
                <td><div class="total-line row-flex"><span>Total</span><span>{total}</span></div></td></tr>
            </table>"""
            
            if dr_sum > cr_sum:
                html += f'<div class="bal-bf">Balance b/f: £{bal_cf}</div>'
            elif cr_sum > dr_sum:
                html += f'<div style="text-align: right;" class="bal-bf">Balance b/f: £{bal_cf}</div>'
            
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
