import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

import streamlit as st


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
        names = []
        for n, a in self.accounts.items():
            if a.debits or a.credits:
                names.append(n)
        return sorted(names)

    def render_all_t_accounts(self, max_accounts: int = 18) -> str:
        names = self.used_account_names()
        if not names:
            return "(No postings yet)"
        names = names[:max_accounts]
        return "\n\n".join(self._render_single_t(self.accounts[n]) for n in names)

    @staticmethod
    def _render_single_t(acc: LedgerAccount) -> str:
        width = 70
        left_w = 34
        right_w = 35

        top = f" {acc.name} ".center(width, "=")
        header = f"{'DR'.ljust(left_w)}|{'CR'.ljust(right_w)}"
        sep = "-" * left_w + "+" + "-" * right_w

        dr_total, cr_total = acc.totals()
        bal_side, bal_amt = acc.balance()

        rows: List[Tuple[str, str]] = []
        max_len = max(len(acc.debits), len(acc.credits))
        for i in range(max_len):
            l = ""
            r = ""
            if i < len(acc.debits):
                nar, amt = acc.debits[i]
                label = (nar or "").strip()[:10]
                l = f"{label:10} {amt:>12,}"
            if i < len(acc.credits):
                nar, amt = acc.credits[i]
                label = (nar or "").strip()[:10]
                r = f"{label:10} {amt:>12,}"
            rows.append((l, r))

        # add balance c/d so totals agree
        if bal_side and bal_amt:
            if bal_side == "DR":
                rows.append(("", f"{'Bal c/d':10} {bal_amt:>12,}"))
                cr_total += bal_amt
            else:
                rows.append((f"{'Bal c/d':10} {bal_amt:>12,}", ""))
                dr_total += bal_amt

        rows.append((f"{'Total':10} {dr_total:>12,}", f"{'Total':10} {cr_total:>12,}"))

        # balance b/d line (teaching hint)
        if bal_side and bal_amt:
            if bal_side == "DR":
                rows.append((f"{'Bal b/d':10} {bal_amt:>12,}", ""))
            else:
                rows.append(("", f"{'Bal b/d':10} {bal_amt:>12,}"))

        rendered = [f"{l.ljust(left_w)}|{r.ljust(right_w)}" for l, r in rows]
        bottom = "=" * width
        return "\n".join([top, header, sep, *rendered, bottom])


# ----------------------------
# Question generator
# ----------------------------

@dataclass(frozen=True)
class Question:
    prompt: str
    expected: List[Posting]


def _p(account: str, side: str, amount: int, nar: str) -> Posting:
    return Posting(account=account, side=side, amount=amount, narrative=nar)


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
             lambda x: [_p(A["BANK"], "DR", x, "Owner"), _p(A["CAP"], "CR", x, "Owner")]),
            ("Paid rent from bank £{x}.",
             lambda x: [_p(A["RENT"], "DR", x, "Rent"), _p(A["BANK"], "CR", x, "Rent")]),
            ("Paid wages from bank £{x}.",
             lambda x: [_p(A["WAGES"], "DR", x, "Wages"), _p(A["BANK"], "CR", x, "Wages")]),
            ("Bought equipment and paid immediately by bank £{x}.",
             lambda x: [_p(A["EQUIP"], "DR", x, "Equip"), _p(A["BANK"], "CR", x, "Equip")]),
            ("Made a sale and received the money in bank £{x}.",
             lambda x: [_p(A["BANK"], "DR", x, "Sale"), _p(A["SALES"], "CR", x, "Sale")]),
        ]
    elif diff <= 8:
        templates = [
            ("Sold goods on credit £{x}.",
             lambda x: [_p(A["AR"], "DR", x, "Cr sale"), _p(A["SALES"], "CR", x, "Cr sale")]),
            ("Bought goods on credit £{x}.",
             lambda x: [_p(A["PUR"], "DR", x, "Cr pur"), _p(A["AP"], "CR", x, "Cr pur")]),
            ("Customer returned goods worth £{x}.",
             lambda x: [_p(A["RET_IN"], "DR", x, "Return"), _p(A["AR"], "CR", x, "Return")]),
            ("Returned goods to supplier worth £{x}.",
             lambda x: [_p(A["AP"], "DR", x, "Return"), _p(A["RET_OUT"], "CR", x, "Return")]),
            ("Received money from a customer into bank £{x}.",
             lambda x: [_p(A["BANK"], "DR", x, "Receipt"), _p(A["AR"], "CR", x, "Receipt")]),
            ("Paid a supplier from bank £{x}.",
             lambda x: [_p(A["AP"], "DR", x, "Pay"), _p(A["BANK"], "CR", x, "Pay")]),
        ]
    elif diff <= 12:
        templates = [
            ("Bought utilities, net £{x} plus VAT 20%, paid by bank.",
             lambda x: (lambda net, vat, gross: [
                 _p(A["UTIL"], "DR", net, "Net"),
                 _p(A["VAT_IN"], "DR", vat, "VAT"),
                 _p(A["BANK"], "CR", gross, "Pay")
             ])(*add_vat(x))),
            ("Made a credit sale, net £{x} plus VAT 20%.",
             lambda x: (lambda net, vat, gross: [
                 _p(A["AR"], "DR", gross, "Gross"),
                 _p(A["SALES"], "CR", net, "Net"),
                 _p(A["VAT_OUT"], "CR", vat, "VAT")
             ])(*add_vat(x))),
            ("Bought goods on credit, net £{x} plus VAT 20%.",
             lambda x: (lambda net, vat, gross: [
                 _p(A["PUR"], "DR", net, "Net"),
                 _p(A["VAT_IN"], "DR", vat, "VAT"),
                 _p(A["AP"], "CR", gross, "Gross")
             ])(*add_vat(x))),
            ("Record depreciation for the period £{x}.",
             lambda x: [_p(A["DEP"], "DR", x, "Dep"), _p(A["ACCDEP"], "CR", x, "Dep")]),
            ("Allowed a customer discount £{x}.",
             lambda x: [_p(A["DISC_ALL"], "DR", x, "Disc"), _p(A["AR"], "CR", x, "Disc")]),
            ("Received a supplier discount £{x}.",
             lambda x: [_p(A["AP"], "DR", x, "Disc"), _p(A["DISC_REC"], "CR", x, "Disc")]),
        ]
    elif diff <= 16:
        templates = [
            ("At period end, rent of £{x} is owing (accrual).",
             lambda x: [_p(A["RENT"], "DR", x, "Accr"), _p(A["ACCR"], "CR", x, "Accr")]),
            ("At period end, utilities of £{x} were paid in advance (prepayment).",
             lambda x: [_p(A["PREP"], "DR", x, "Prep"), _p(A["UTIL"], "CR", x, "Prep")]),
            ("Write off an irrecoverable debt £{x}.",
             lambda x: [_p(A["BAD"], "DR", x, "Bad"), _p(A["AR"], "CR", x, "Bad")]),
            ("Create an allowance for doubtful debts £{x}.",
             lambda x: [_p(A["BAD"], "DR", x, "Allow"), _p(A["ALLOW"], "CR", x, "Allow")]),
            ("Owner took drawings £{x} from bank.",
             lambda x: [_p(A["DRAW"], "DR", x, "Draw"), _p(A["BANK"], "CR", x, "Draw")]),
        ]
    else:
        templates = [
            ("Correct this error: equipment £{x} was wrongly debited to purchases.",
             lambda x: [_p(A["EQUIP"], "DR", x, "Corr"), _p(A["PUR"], "CR", x, "Corr")]),
            ("A one sided error: bank was credited £{x} but the debit entry was missing. Use suspense.",
             lambda x: [_p(A["SUSP"], "DR", x, "Miss"), _p(A["BANK"], "CR", x, "Miss")]),
            ("Clear suspense: the missing debit was rent expense £{x}.",
             lambda x: [_p(A["RENT"], "DR", x, "Clear"), _p(A["SUSP"], "CR", x, "Clear")]),
            ("Customer pays £{x} and we allow a discount of £{d}.",
             lambda x: (lambda disc: [
                 _p(A["BANK"], "DR", x, "Settle"),
                 _p(A["DISC_ALL"], "DR", disc, "Settle"),
                 _p(A["AR"], "CR", x + disc, "Settle")
             ])(max(50, x // 10))),
            ("We pay a supplier £{x} and receive a discount of £{d}.",
             lambda x: (lambda disc: [
                 _p(A["AP"], "DR", x + disc, "Settle"),
                 _p(A["BANK"], "CR", x, "Settle"),
                 _p(A["DISC_REC"], "CR", disc, "Settle")
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
# Dropdown options
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


def format_journal(postings: List[Posting]) -> str:
    return "\n".join(f"{p.side.title()} {p.account} {p.amount:,}" for p in postings)


def tag_with_question(postings: List[Posting], q_no: int) -> List[Posting]:
    tag = f"Q{q_no}"
    return [Posting(account=p.account, side=p.side, amount=p.amount, narrative=tag) for p in postings]


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
        return "Hint: The right accounts are there, but check the amounts and whether VAT or discounts are treated correctly."

    e_has_vat = any("VAT" in p.account for p in expected)
    s_has_vat = any("VAT" in p.account for p in student)
    if e_has_vat and not s_has_vat:
        return "Hint: This looks like a VAT question. Are you missing VAT input or VAT output?"

    return None


# ----------------------------
# Streamlit app
# ----------------------------

st.set_page_config(page_title="Double Entry Game", layout="wide")
st.title("Double Entry Game")
st.caption("Dropdown-based journal entry. Live balancing. Shows the journal and T accounts after each question.")

# Ensure session defaults exist (prevents AttributeError)
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

left, right = st.columns([1, 1])

with left:
    st.subheader(f"Round {round_no}")
    st.write(f"Question {q_index + 1} of 10")
    st.write(f"Score so far {st.session_state.score} of {q_index}")

    if q_index >= len(questions):
        st.success(f"Round complete. Final score {st.session_state.score} out of 10.")
        st.stop()

    q = questions[q_index]

    expected_lines = max(2, min(5, len(q.expected)))
    if st.session_state.get("current_q_index", -1) != q_index:
        st.session_state.current_q_index = q_index
        st.session_state.lines = expected_lines
        st.session_state.last_message = ""
        st.session_state.last_feedback = ""
        st.session_state.last_journal = ""
        st.session_state.last_correct = None

    st.markdown(f"**{q.prompt}**")

    accounts = account_options_for_round(round_no)
    rng = random.Random(5000 + round_no + q_index)
    amounts = amount_options(q.expected, rng)

    st.markdown("Build your journal entry using dropdowns")

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

    st.markdown("Live balance check")
    st.write(f"Total debits £{dr_total:,}")
    st.write(f"Total credits £{cr_total:,}")
    if diff == 0 and rows:
        st.success("Balanced")
    else:
        st.warning(
            f"Not balanced. Difference £{abs(diff):,} "
            f"({'Dr too high' if diff > 0 else 'Cr too high' if diff < 0 else 'no lines yet'})"
        )

    add_col, remove_col = st.columns([1, 1])
    with add_col:
        if st.button("Add a line"):
            if st.session_state.lines < 6:
                st.session_state.lines += 1
                st.rerun()
    with remove_col:
        if st.button("Remove a line"):
            if st.session_state.lines > 2:
                st.session_state.lines -= 1
                st.rerun()

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
                ledger.post_many(tag_with_question(student_postings, q_index + 1))
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
                    ledger.post_many(tag_with_question(q.expected, q_index + 1))
                    st.session_state.last_message = "Two attempts used. Model answer posted."
                    st.session_state.last_journal = format_journal(q.expected)
                    st.session_state.last_feedback = ""
                    st.session_state.q_index += 1
                    st.session_state.attempts = 0
                    st.rerun()

    if show_answer:
        ledger.post_many(tag_with_question(q.expected, q_index + 1))
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
        st.markdown("Double entry posted")
        st.code(st.session_state.get("last_journal", ""), language="text")

with right:
    st.subheader("T accounts")
    st.code(ledger.render_all_t_accounts(max_accounts=18), language="text")
    st.caption("Entries are labelled Q1, Q2, etc so students can link each posting to the question.")
