import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union

import streamlit as st


# ----------------------------
# Better visuals (safe CSS)
# ----------------------------

CSS = """
<style>
.main .block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1200px; }

.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 16px 16px 14px 16px;
  margin-bottom: 14px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.18);
}

.small-muted { opacity: 0.75; font-size: 0.92rem; }
.big-title { font-size: 1.35rem; font-weight: 700; margin-bottom: 0.25rem; }
.subtitle { opacity: 0.78; margin-top: 0; margin-bottom: 0.75rem; }

.pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  font-size: 0.85rem;
  margin-right: 8px;
  margin-bottom: 6px;
}

.stButton button { border-radius: 10px; padding: 0.55rem 0.9rem; }

.metric-wrap { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 10px; }
.metric {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 10px 12px;
  min-width: 160px;
}
.metric .label { opacity: 0.75; font-size: 0.85rem; margin-bottom: 4px; }
.metric .value { font-size: 1.2rem; font-weight: 700; }

hr { border: none; border-top: 1px solid rgba(255,255,255,0.10); margin: 14px 0; }

div[data-testid="stExpander"] details {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 4px 8px;
}
div[data-testid="stExpander"] summary { font-weight: 650; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------
# Models
# ----------------------------

@dataclass(frozen=True)
class Posting:
    account: str
    side: str  # "DR" or "CR"
    amount: int
    narrative: str = ""


@dataclass
class LedgerAccount:
    name: str
    debits: List[Tuple[str, int]] = field(default_factory=list)   # (narrative, amount)
    credits: List[Tuple[str, int]] = field(default_factory=list)

    def post(self, side: str, amount: int, narrative: str = "") -> None:
        s = side.upper().strip()
        if s == "DR":
            self.debits.append((narrative, amount))
        elif s == "CR":
            self.credits.append((narrative, amount))
        else:
            raise ValueError("Side must be DR or CR")

    def totals(self) -> Tuple[int, int]:
        return sum(a for _, a in self.debits), sum(a for _, a in self.credits)

    def balance(self) -> Tuple[str, int]:
        dr, cr = self.totals()
        if dr > cr:
            return "DR", dr - cr
        if cr > dr:
            return "CR", cr - dr
        return "", 0


class Ledger:
    def __init__(self) -> None:
        self.accounts: Dict[str, LedgerAccount] = {}

    def get(self, name: str) -> LedgerAccount:
        key = name.strip()
        if key not in self.accounts:
            self.accounts[key] = LedgerAccount(name=key)
        return self.accounts[key]

    def post_many(self, postings: List[Posting]) -> None:
        for p in postings:
            self.get(p.account).post(p.side, p.amount, p.narrative)

    def used_account_names(self) -> List[str]:
        names: List[str] = []
        for n, a in self.accounts.items():
            if a.debits or a.credits:
                names.append(n)
        return sorted(names)

    def trial_balance_rows(self) -> List[Dict[str, Union[str, int]]]:
        rows: List[Dict[str, Union[str, int]]] = []

        for name in self.used_account_names():
            side, amt = self.accounts[name].balance()
            dr = amt if side == "DR" else 0
            cr = amt if side == "CR" else 0
            rows.append({"Account": name, "Debit (£)": int(dr), "Credit (£)": int(cr)})

        total_dr = sum(int(r["Debit (£)"]) for r in rows) if rows else 0
        total_cr = sum(int(r["Credit (£)"]) for r in rows) if rows else 0
        rows.append({"Account": "TOTAL", "Debit (£)": int(total_dr), "Credit (£)": int(total_cr)})
        return rows

    # ---- Visual T accounts: rows for a combined Debit/Credit table ----
    def t_account_table_rows(self, name: str, include_balance_lines: bool = True) -> List[Dict[str, Union[str, int]]]:
        acc = self.accounts[name]
        dr_total, cr_total = acc.totals()
        bal_side, bal_amt = acc.balance()

        debits = list(acc.debits)
        credits = list(acc.credits)

        rows: List[Dict[str, Union[str, int]]] = []

        max_len = max(len(debits), len(credits))
        for i in range(max_len):
            dr_ref, dr_amt = ("", 0)
            cr_ref, cr_amt = ("", 0)

            if i < len(debits):
                dr_ref, dr_amt = debits[i]
            if i < len(credits):
                cr_ref, cr_amt = credits[i]

            rows.append({
                "Debit (ref)": dr_ref,
                "Debit (£)": dr_amt if dr_amt else "",
                "Credit (ref)": cr_ref,
                "Credit (£)": cr_amt if cr_amt else ""
            })

        if include_balance_lines and bal_side and bal_amt:
            # Bal c/d so totals agree
            if bal_side == "DR":
                # debit balance means balance carried down appears on credit side
                rows.append({"Debit (ref)": "", "Debit (£)": "", "Credit (ref)": "Bal c/d", "Credit (£)": bal_amt})
                cr_total += bal_amt
            else:
                rows.append({"Debit (ref)": "Bal c/d", "Debit (£)": bal_amt, "Credit (ref)": "", "Credit (£)": ""})
                dr_total += bal_amt

        # Totals row
        rows.append({
            "Debit (ref)": "Total",
            "Debit (£)": dr_total,
            "Credit (ref)": "Total",
            "Credit (£)": cr_total
        })

        if include_balance_lines and bal_side and bal_amt:
            # Bal b/d line
            if bal_side == "DR":
                rows.append({"Debit (ref)": "Bal b/d", "Debit (£)": bal_amt, "Credit (ref)": "", "Credit (£)": ""})
            else:
                rows.append({"Debit (ref)": "", "Debit (£)": "", "Credit (ref)": "Bal b/d", "Credit (£)": bal_amt})

        return rows


# ----------------------------
# Question generator
# ----------------------------

@dataclass(frozen=True)
class Question:
    prompt: str
    expected: List[Posting]


def _p(account: str, side: str, amount: int) -> Posting:
    return Posting(account=account, side=side, amount=amount, narrative="")


def build_round(round_no: int, n: int = 10) -> List[Question]:
    rng = random.Random(1000 + round_no)
    vat_rate = 20

    A = {
        "BANK": "Bank",
        "CAP": "Capital",
        "DRAW": "Drawings",
        "SALES": "Sales",
        "PUR": "Purchases",
        "RENT": "Rent expense",
        "WAGES": "Wages expense",
        "UTIL": "Utilities expense",
        "EQUIP": "Equipment",
        "AR": "Trade receivables",
        "AP": "Trade payables",
        "RET_IN": "Sales returns",
        "RET_OUT": "Purchase returns",
        "VAT_IN": "VAT input",
        "VAT_OUT": "VAT output",
        "DISC_REC": "Discount received",
        "DISC_ALL": "Discount allowed",
        "DEP": "Depreciation expense",
        "ACCDEP": "Accumulated depreciation",
        "BAD": "Bad debt expense",
        "ALLOW": "Allowance for doubtful debts",
        "ACCR": "Accruals",
        "PREP": "Prepayments",
        "SUSP": "Suspense",
    }

    def amt(lo: int, hi: int, step: int = 100) -> int:
        return rng.randrange(lo, hi + step, step)

    def add_vat(net: int) -> Tuple[int, int, int]:
        vat = (net * vat_rate) // 100
        gross = net + vat
        return net, vat, gross

    diff = round_no
    templates = []

    if diff <= 4:
        templates = [
            ("Owner introduced funds into the business £{x}.",
             lambda x: [_p(A["BANK"], "DR", x), _p(A["CAP"], "CR", x)]),
            ("Paid rent from bank £{x}.",
             lambda x: [_p(A["RENT"], "DR", x), _p(A["BANK"], "CR", x)]),
            ("Paid wages from bank £{x}.",
             lambda x: [_p(A["WAGES"], "DR", x), _p(A["BANK"], "CR", x)]),
            ("Bought equipment and paid immediately by bank £{x}.",
             lambda x: [_p(A["EQUIP"], "DR", x), _p(A["BANK"], "CR", x)]),
            ("Made a sale and received the money in bank £{x}.",
             lambda x: [_p(A["BANK"], "DR", x), _p(A["SALES"], "CR", x)]),
        ]
    elif diff <= 8:
        templates = [
            ("Sold goods on credit £{x}.",
             lambda x: [_p(A["AR"], "DR", x), _p(A["SALES"], "CR", x)]),
            ("Bought goods on credit £{x}.",
             lambda x: [_p(A["PUR"], "DR", x), _p(A["AP"], "CR", x)]),
            ("Customer returned goods worth £{x}.",
             lambda x: [_p(A["RET_IN"], "DR", x), _p(A["AR"], "CR", x)]),
            ("Returned goods to supplier worth £{x}.",
             lambda x: [_p(A["AP"], "DR", x), _p(A["RET_OUT"], "CR", x)]),
            ("Received money from a customer into bank £{x}.",
             lambda x: [_p(A["BANK"], "DR", x), _p(A["AR"], "CR", x)]),
            ("Paid a supplier from bank £{x}.",
             lambda x: [_p(A["AP"], "DR", x), _p(A["BANK"], "CR", x)]),
        ]
    elif diff <= 12:
        templates = [
            ("Bought utilities, net £{x} plus VAT 20%, paid by bank.",
             lambda x: (lambda net, vat, gross: [
                 _p(A["UTIL"], "DR", net),
                 _p(A["VAT_IN"], "DR", vat),
                 _p(A["BANK"], "CR", gross)
             ])(*add_vat(x))),
            ("Made a credit sale, net £{x} plus VAT 20%.",
             lambda x: (lambda net, vat, gross: [
                 _p(A["AR"], "DR", gross),
                 _p(A["SALES"], "CR", net),
                 _p(A["VAT_OUT"], "CR", vat)
             ])(*add_vat(x))),
            ("Bought goods on credit, net £{x} plus VAT 20%.",
             lambda x: (lambda net, vat, gross: [
                 _p(A["PUR"], "DR", net),
                 _p(A["VAT_IN"], "DR", vat),
                 _p(A["AP"], "CR", gross)
             ])(*add_vat(x))),
            ("Record depreciation for the period £{x}.",
             lambda x: [_p(A["DEP"], "DR", x), _p(A["ACCDEP"], "CR", x)]),
            ("Allowed a customer discount £{x}.",
             lambda x: [_p(A["DISC_ALL"], "DR", x), _p(A["AR"], "CR", x)]),
            ("Received a supplier discount £{x}.",
             lambda x: [_p(A["AP"], "DR", x), _p(A["DISC_REC"], "CR", x)]),
        ]
    elif diff <= 16:
        templates = [
            ("At period end, rent of £{x} is owing (accrual).",
             lambda x: [_p(A["RENT"], "DR", x), _p(A["ACCR"], "CR", x)]),
            ("At period end, utilities of £{x} were paid in advance (prepayment).",
             lambda x: [_p(A["PREP"], "DR", x), _p(A["UTIL"], "CR", x)]),
            ("Write off an irrecoverable debt £{x}.",
             lambda x: [_p(A["BAD"], "DR", x), _p(A["AR"], "CR", x)]),
            ("Create an allowance for doubtful debts £{x}.",
             lambda x: [_p(A["BAD"], "DR", x), _p(A["ALLOW"], "CR", x)]),
            ("Owner took drawings £{x} from bank.",
             lambda x: [_p(A["DRAW"], "DR", x), _p(A["BANK"], "CR", x)]),
        ]
    else:
        templates = [
            ("Correct this error: equipment £{x} was wrongly debited to purchases.",
             lambda x: [_p(A["EQUIP"], "DR", x), _p(A["PUR"], "CR", x)]),
            ("A one sided error: bank was credited £{x} but the debit entry was missing. Use suspense.",
             lambda x: [_p(A["SUSP"], "DR", x), _p(A["BANK"], "CR", x)]),
            ("Clear suspense: the missing debit was rent expense £{x}.",
             lambda x: [_p(A["RENT"], "DR", x), _p(A["SUSP"], "CR", x)]),
            ("Customer pays £{x} and we allow a discount of £{d}.",
             lambda x: (lambda disc: [
                 _p(A["BANK"], "DR", x),
                 _p(A["DISC_ALL"], "DR", disc),
                 _p(A["AR"], "CR", x + disc)
             ])(max(50, x // 10))),
            ("We pay a supplier £{x} and receive a discount of £{d}.",
             lambda x: (lambda disc: [
                 _p(A["AP"], "DR", x + disc),
                 _p(A["BANK"], "CR", x),
                 _p(A["DISC_REC"], "CR", disc)
             ])(max(50, x // 10))),
        ]

    questions: List[Question] = []
    for i in range(n):
        temp, builder = rng.choice(templates)

        if diff <= 4:
            x = amt(200, 3000, 100)
        elif diff <= 8:
            x = amt(300, 6000, 100)
        elif diff <= 12:
            x = amt(500, 10000, 100)
        elif diff <= 16:
            x = amt(200, 8000, 100)
        else:
            x = amt(500, 12000, 100)

        d = max(50, x // 10)
        prompt = f"Q{i+1}. " + temp.format(x=x, d=d)
        expected = builder(x)
        questions.append(Question(prompt=prompt, expected=expected))

    return questions


# ----------------------------
# Dropdown option banks
# ----------------------------

def account_options_for_round(round_no: int) -> List[str]:
    base = [
        "Bank", "Capital", "Drawings", "Sales", "Purchases",
        "Rent expense", "Wages expense", "Utilities expense", "Equipment",
        "Trade receivables", "Trade payables",
        "Sales returns", "Purchase returns",
    ]
    vat = ["VAT input", "VAT output"]
    discounts = ["Discount allowed", "Discount received"]
    adjustments = [
        "Accruals", "Prepayments", "Depreciation expense", "Accumulated depreciation",
        "Bad debt expense", "Allowance for doubtful debts"
    ]
    suspense = ["Suspense"]

    if round_no <= 4:
        return base
    if round_no <= 8:
        return base
    if round_no <= 12:
        return base + vat + discounts + ["Depreciation expense", "Accumulated depreciation"]
    if round_no <= 16:
        return base + vat + discounts + adjustments
    return base + vat + discounts + adjustments + suspense


def amount_options(expected: List[Posting], rng: random.Random) -> List[int]:
    correct = sorted(set(p.amount for p in expected))
    distractors: List[int] = []
    for a in correct:
        for delta in (50, 100, 200):
            if a - delta > 0:
                distractors.append(a - delta)
            distractors.append(a + delta)

    if correct:
        lo = max(50, min(correct) - 500)
        hi = max(correct) + 500
        for _ in range(3):
            distractors.append(rng.randrange(lo, hi + 50, 50))

    merged = sorted(set(correct + distractors))
    return merged[:18]


# ----------------------------
# Marking + hints
# ----------------------------

def canonical(postings: List[Posting]) -> List[Tuple[str, str, int]]:
    return sorted((p.account.strip(), p.side.upper().strip(), p.amount) for p in postings)


def mark(student: List[Posting], expected: List[Posting]) -> Tuple[bool, str]:
    s = canonical(student)
    e = canonical(expected)
    if s == e:
        return True, ""

    s_set = set(s)
    e_set = set(e)

    missing = sorted(list(e_set - s_set))
    extra = sorted(list(s_set - e_set))

    lines: List[str] = []
    if missing:
        lines.append("Missing lines")
        for a, side, amt in missing:
            lines.append(f"{side} {a} {amt:,}")
    if extra:
        lines.append("Incorrect extra lines")
        for a, side, amt in extra:
            lines.append(f"{side} {a} {amt:,}")

    return False, "\n".join(lines)


def generate_hint(student: List[Posting], expected: List[Posting]) -> Optional[str]:
    s_acc = sorted([p.account for p in student])
    e_acc = sorted([p.account for p in expected])

    if sorted(set(s_acc)) == sorted(set(e_acc)):
        s_pairs = sorted((p.account, p.side) for p in student)
        e_pairs = sorted((p.account, p.side) for p in expected)
        if sorted(set(a for a, _ in s_pairs)) == sorted(set(a for a, _ in e_pairs)) and s_pairs != e_pairs:
            return "Hint: You have the right accounts, but one or more are on the wrong side (Dr or Cr)."
        return "Hint: The right accounts are there, but check amounts and whether VAT or discounts are treated correctly."

    e_has_vat = any("VAT" in p.account for p in expected)
    s_has_vat = any("VAT" in p.account for p in student)
    if e_has_vat and not s_has_vat:
        return "Hint: This looks like a VAT question. Are you missing VAT input or VAT output?"

    return None


# ----------------------------
# Narratives: show from/to contra accounts
# ----------------------------

def _compact(accounts: List[str], limit: int = 2) -> str:
    uniq: List[str] = []
    for a in accounts:
        if a not in uniq:
            uniq.append(a)
    if not uniq:
        return ""
    if len(uniq) <= limit:
        return " & ".join(uniq)
    return "Various"


def annotate_with_from_to(postings: List[Posting], q_no: int) -> List[Posting]:
    debits = [p.account for p in postings if p.side.upper() == "DR"]
    credits = [p.account for p in postings if p.side.upper() == "CR"]

    cr_text = _compact(credits)
    dr_text = _compact(debits)

    out: List[Posting] = []
    for p in postings:
        side = p.side.upper()
        if side == "DR":
            nar = f"Q{q_no} from {cr_text}" if cr_text else f"Q{q_no}"
        else:
            nar = f"Q{q_no} to {dr_text}" if dr_text else f"Q{q_no}"
        out.append(Posting(account=p.account, side=side, amount=p.amount, narrative=nar))
    return out


def format_journal(postings: List[Posting]) -> str:
    return "\n".join(f"{p.side.title()} {p.account} {p.amount:,}" for p in postings)


# ----------------------------
# Streamlit app
# ----------------------------

st.set_page_config(page_title="Double Entry Game", layout="wide")

st.markdown('<div class="big-title">Double Entry Game</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Dropdown journal entry. Live balancing. Responsive T accounts. Trial balance at the end.</div>', unsafe_allow_html=True)

# Ensure session defaults exist
defaults = {
    "started": False,
    "last_message": "",
    "last_feedback": "",
    "last_journal": "",
    "attempts": 0,
    "score": 0,
    "q_index": 0,
    "lines": 2,
    "last_correct": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.sidebar:
    st.header("Round")
    round_choice = st.selectbox("Choose round (1 to 20)", list(range(1, 21)), index=0)

    st.markdown("")

    if st.button("Start new round", type="primary"):
        st.session_state.started = True
        st.session_state.round_no = int(round_choice)
        st.session_state.questions = build_round(st.session_state.round_no, 10)
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.attempts = 0
        st.session_state.ledger = Ledger()
        st.session_state.last_message = ""
        st.session_state.last_feedback = ""
        st.session_state.last_journal = ""
        st.session_state.lines = 2
        st.session_state.last_correct = None
        st.session_state.current_q_index = -1

    if st.button("Reset everything"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

if not st.session_state.started:
    st.info("Choose a round in the sidebar, then click Start new round.")
    st.stop()

round_no: int = st.session_state.round_no
questions: List[Question] = st.session_state.questions
ledger: Ledger = st.session_state.ledger
q_index: int = st.session_state.q_index

# End of round view
if q_index >= len(questions):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"Round {round_no} complete")
    st.write(f"Final score: **{st.session_state.score} / 10**")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Trial balance")
    tb_rows = ledger.trial_balance_rows()

    if len(tb_rows) == 1:
        st.write("No postings.")
    else:
        st.dataframe(tb_rows, use_container_width=True, hide_index=True)

        total_dr = int(tb_rows[-1]["Debit (£)"])
        total_cr = int(tb_rows[-1]["Credit (£)"])

        if total_dr == total_cr:
            st.success(f"Trial balance agrees £{total_dr:,}")
        else:
            st.warning(f"Trial balance does not agree. Debits £{total_dr:,}. Credits £{total_cr:,}.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("T accounts")
    names = ledger.used_account_names()
    if not names:
        st.write("No postings.")
    else:
        view = st.selectbox("View", ["All accounts"] + names, index=0)
        if view == "All accounts":
            for name in names:
                side, amt = ledger.accounts[name].balance()
                bal_text = f"{side} £{amt:,}" if side else "£0"
                with st.expander(f"{name}  |  Balance {bal_text}", expanded=False):
                    rows = ledger.t_account_table_rows(name)
                    st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            side, amt = ledger.accounts[view].balance()
            bal_text = f"{side} £{amt:,}" if side else "£0"
            st.markdown(f"**{view}**  |  Balance **{bal_text}**")
            rows = ledger.t_account_table_rows(view)
            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Main layout
left, right = st.columns([1.05, 0.95])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        f'<span class="pill">Round {round_no}</span>'
        f'<span class="pill">Question {q_index + 1} of 10</span>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="metric-wrap">', unsafe_allow_html=True)
    st.markdown(f"""
      <div class="metric"><div class="label">Score</div><div class="value">{st.session_state.score} / {q_index}</div></div>
      <div class="metric"><div class="label">Attempts used</div><div class="value">{st.session_state.attempts} / 2</div></div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    q = questions[q_index]

    expected_lines = max(2, min(6, len(q.expected)))
    if st.session_state.get("current_q_index", -1) != q_index:
        st.session_state.current_q_index = q_index
        st.session_state.lines = expected_lines
        st.session_state.last_message = ""
        st.session_state.last_feedback = ""
        st.session_state.last_journal = ""
        st.session_state.last_correct = None
        st.session_state.attempts = 0

    st.markdown(f"### {q.prompt}")
    st.markdown('<div class="small-muted">Build your journal entry using dropdowns</div>', unsafe_allow_html=True)

    accounts = account_options_for_round(round_no)
    rng = random.Random(5000 + round_no + q_index)
    amounts = amount_options(q.expected, rng)

    rows: List[Tuple[str, str, int]] = []
    for i in range(st.session_state.lines):
        c1, c2, c3 = st.columns([1, 3, 2])
        with c1:
            side = st.selectbox(
                f"Side {i+1}",
                ["DR", "CR"],
                key=f"side_{round_no}_{q_index}_{i}"
            )
        with c2:
            account = st.selectbox(
                f"Account {i+1}",
                [""] + accounts,
                key=f"acct_{round_no}_{q_index}_{i}"
            )
        with c3:
            amount = st.selectbox(
                f"Amount {i+1}",
                [0] + amounts,
                format_func=lambda x: "Select amount" if x == 0 else f"£{x:,}",
                key=f"amt_{round_no}_{q_index}_{i}"
            )

        if account and amount > 0:
            rows.append((side, account, amount))

    dr_total = sum(a for s, _, a in rows if s == "DR")
    cr_total = sum(a for s, _, a in rows if s == "CR")
    diff = dr_total - cr_total

    st.markdown("#### Live balance check")
    if diff == 0 and rows:
        st.success(f"Balanced. Debits £{dr_total:,} equal Credits £{cr_total:,}.")
    else:
        direction = "Dr too high" if diff > 0 else "Cr too high" if diff < 0 else "No lines yet"
        st.warning(f"Not balanced. Total Dr £{dr_total:,}. Total Cr £{cr_total:,}. Difference £{abs(diff):,}. {direction}.")

    add_col, remove_col = st.columns([1, 1])
    with add_col:
        if st.button("Add a line"):
            if st.session_state.lines < 8:
                st.session_state.lines += 1
                st.rerun()
    with remove_col:
        if st.button("Remove a line"):
            if st.session_state.lines > 2:
                st.session_state.lines -= 1
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        submitted = st.button("Submit entry", type="primary")
    with col_b:
        show_answer = st.button("Show model answer and post it")

    if submitted:
        if not rows:
            st.session_state.last_correct = False
            st.session_state.last_message = "Not marked. Please select at least two lines with accounts and amounts."
            st.session_state.last_feedback = ""
        elif dr_total != cr_total:
            st.session_state.last_correct = False
            st.session_state.last_message = "Not marked. Your entry must balance before you submit."
            st.session_state.last_feedback = ""
        else:
            student_postings = [Posting(account=a, side=s, amount=amt, narrative="") for (s, a, amt) in rows]
            ok, feedback = mark(student_postings, q.expected)

            if ok:
                ledger.post_many(annotate_with_from_to(student_postings, q_index + 1))
                st.session_state.score += 1
                st.session_state.last_correct = True
                st.session_state.last_message = "Correct"
                st.session_state.last_feedback = ""
                st.session_state.last_journal = format_journal(student_postings)

                st.session_state.q_index += 1
                st.session_state.attempts = 0
                st.rerun()
            else:
                st.session_state.attempts += 1
                st.session_state.last_correct = False
                st.session_state.last_message = "Not quite"
                st.session_state.last_feedback = feedback

                hint = generate_hint(student_postings, q.expected)
                if hint:
                    st.session_state.last_feedback = st.session_state.last_feedback + "\n\n" + hint

                if st.session_state.attempts >= 2:
                    ledger.post_many(annotate_with_from_to(q.expected, q_index + 1))
                    st.session_state.last_message = "Two attempts used. Model answer posted."
                    st.session_state.last_journal = format_journal(q.expected)
                    st.session_state.last_feedback = ""
                    st.session_state.q_index += 1
                    st.session_state.attempts = 0
                    st.rerun()

    if show_answer:
        ledger.post_many(annotate_with_from_to(q.expected, q_index + 1))
        st.session_state.last_correct = None
        st.session_state.last_message = "Model answer posted."
        st.session_state.last_feedback = ""
        st.session_state.last_journal = format_journal(q.expected)

        st.session_state.q_index += 1
        st.session_state.attempts = 0
        st.rerun()

    if st.session_state.get("last_message", ""):
        if st.session_state.last_correct is True:
            st.success(st.session_state.last_message)
        elif st.session_state.last_correct is False:
            st.warning(st.session_state.last_message)
        else:
            st.info(st.session_state.last_message)

    if st.session_state.get("last_feedback", ""):
        st.code(st.session_state.get("last_feedback", ""), language="text")

    if st.session_state.get("last_journal", ""):
        st.markdown("#### Double entry posted")
        st.code(st.session_state.get("last_journal", ""), language="text")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("T accounts")
    st.markdown('<div class="small-muted">Use the selector to focus on one account on mobile. Expanders keep the page tidy on PC.</div>', unsafe_allow_html=True)

    names = ledger.used_account_names()
    if not names:
        st.write("No postings yet.")
    else:
        view = st.selectbox("View", ["All accounts"] + names, index=0, key="t_view_in_round")

        if view == "All accounts":
            for name in names:
                side, amt = ledger.accounts[name].balance()
                bal_text = f"{side} £{amt:,}" if side else "£0"
                with st.expander(f"{name}  |  Balance {bal_text}", expanded=False):
                    rows = ledger.t_account_table_rows(name)
                    st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            side, amt = ledger.accounts[view].balance()
            bal_text = f"{side} £{amt:,}" if side else "£0"
            st.markdown(f"**{view}**  |  Balance **{bal_text}**")
            rows = ledger.t_account_table_rows(view)
            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
