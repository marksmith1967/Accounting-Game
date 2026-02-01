import re
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

import streamlit as st


# ----------------------------
# Data models
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
        side = side.upper().strip()
        if side == "DR":
            self.debits.append((narrative, amount))
        elif side == "CR":
            self.credits.append((narrative, amount))
        else:
            raise ValueError("Side must be DR or CR")

    def totals(self) -> Tuple[int, int]:
        dr = sum(a for _, a in self.debits)
        cr = sum(a for _, a in self.credits)
        return dr, cr

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

    def render_all_t_accounts(self, max_accounts: int = 16) -> str:
        names = self.used_account_names()
        if not names:
            return "(No postings yet)"

        names = names[:max_accounts]
        blocks = [self.render_single_t_account(self.accounts[n]) for n in names]
        return "\n\n".join(blocks)

    @staticmethod
    def render_single_t_account(acc: LedgerAccount) -> str:
        """
        Teaching-friendly T account view.

        Shows
        - entries on each side with short narrative labels
        - totals
        - balance c/d line if needed
        - balance b/d shown as next line (simplified)
        """
        width = 68
        left_w = 33
        right_w = 33

        title = f" {acc.name} "
        top = title.center(width, "=")

        header = f"{'DR'.ljust(left_w)}|{'CR'.ljust(right_w)}"
        sep = "-" * left_w + "+" + "-" * right_w

        dr_total, cr_total = acc.totals()
        bal_side, bal_amt = acc.balance()

        # Prepare rows for entries
        rows: List[Tuple[str, str]] = []
        max_len = max(len(acc.debits), len(acc.credits))
        for i in range(max_len):
            left = ""
            right = ""
            if i < len(acc.debits):
                nar, amt = acc.debits[i]
                label = (nar or "").strip()[:10]
                left = f"{label:10} {amt:>10,}"
            if i < len(acc.credits):
                nar, amt = acc.credits[i]
                label = (nar or "").strip()[:10]
                right = f"{label:10} {amt:>10,}"
            rows.append((left, right))

        # Add balance c/d line to make totals match, like traditional accounts
        if bal_side and bal_amt:
            if bal_side == "DR":
                # Credit needs balance c/d
                rows.append(("", f"{'Bal c/d':10} {bal_amt:>10,}"))
                cr_total += bal_amt
            else:
                rows.append((f"{'Bal c/d':10} {bal_amt:>10,}", ""))
                dr_total += bal_amt

        # Totals line
        rows.append((f"{'Total':10} {dr_total:>10,}", f"{'Total':10} {cr_total:>10,}"))

        # Balance b/d line for next period (teaching hint)
        if bal_side and bal_amt:
            if bal_side == "DR":
                rows.append((f"{'Bal b/d':10} {bal_amt:>10,}", ""))
            else:
                rows.append(("", f"{'Bal b/d':10} {bal_amt:>10,}"))

        rendered_rows = [
            f"{l.ljust(left_w)}|{r.ljust(right_w)}" for l, r in rows
        ]

        bottom = "=" * width
        return "\n".join([top, header, sep, *rendered_rows, bottom])


# ----------------------------
# Parsing student input
# ----------------------------

AMOUNT_RE = re.compile(r"^£?[\d,]+$")


def parse_amount(token: str) -> int:
    t = token.strip().replace("£", "").replace(",", "")
    if not t.isdigit():
        raise ValueError("Amount must be a whole number, for example 1200 or 1,200")
    return int(t)


def parse_entry(text: str) -> List[Posting]:
    """
    Accepts input like:
      Dr Bank 15000; Cr Capital 15000
      Dr Motor Expenses 1000; Dr VAT Input 200; Cr Bank 1200
    """
    if not text or not text.strip():
        raise ValueError("Entry is empty")

    parts = [p.strip() for p in text.split(";") if p.strip()]
    postings: List[Posting] = []

    for part in parts:
        tokens = part.split()
        if len(tokens) < 3:
            raise ValueError(f"Could not read '{part}'. Use: Dr Account Amount")

        side = tokens[0].upper().strip()
        if side not in {"DR", "CR"}:
            raise ValueError(f"Each line must start with Dr or Cr. Problem: '{part}'")

        amount_token = tokens[-1]
        if not AMOUNT_RE.match(amount_token):
            raise ValueError(f"Last item must be an amount. Problem: '{part}'")

        amount = parse_amount(amount_token)
        account = " ".join(tokens[1:-1]).strip()
        if not account:
            raise ValueError(f"Missing account name in '{part}'")

        postings.append(Posting(account=account, side=side, amount=amount, narrative=""))

    dr_total = sum(p.amount for p in postings if p.side == "DR")
    cr_total = sum(p.amount for p in postings if p.side == "CR")
    if dr_total != cr_total:
        raise ValueError(f"Debits {dr_total:,} do not equal Credits {cr_total:,}")

    return postings


def format_postings_lines(postings: List[Posting]) -> str:
    return "\n".join([f"{p.side.title()} {p.account} {p.amount:,}" for p in postings])


def canonical(postings: List[Posting]) -> List[Tuple[str, str, int]]:
    return sorted([(p.account.strip(), p.side.upper().strip(), p.amount) for p in postings])


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

    def amt(lo: int, hi: int, step: int = 50) -> int:
        return rng.randrange(lo, hi + step, step)

    vat_rate = 20

    def add_vat(net: int) -> Tuple[int, int, int]:
        vat = (net * vat_rate) // 100
        gross = net + vat
        return net, vat, gross

    diff = round_no
    templates = []

    # Rounds 1–4 basics
    if diff <= 4:
        templates = [
            ("Owner introduced funds into the business £{x}.",
             lambda x: [_p(A["BANK"], "DR", x, "Owner"),
                        _p(A["CAP"], "CR", x, "Owner")]),
            ("Paid rent from bank £{x}.",
             lambda x: [_p(A["RENT"], "DR", x, "Rent"),
                        _p(A["BANK"], "CR", x, "Rent")]),
            ("Paid wages from bank £{x}.",
             lambda x: [_p(A["WAGES"], "DR", x, "Wages"),
                        _p(A["BANK"], "CR", x, "Wages")]),
            ("Bought equipment and paid immediately by bank £{x}.",
             lambda x: [_p(A["EQUIP"], "DR", x, "Equip"),
                        _p(A["BANK"], "CR", x, "Equip")]),
            ("Made a sale and received the money in bank £{x}.",
             lambda x: [_p(A["BANK"], "DR", x, "Sale"),
                        _p(A["SALES"], "CR", x, "Sale")]),
        ]

    # Rounds 5–8 credit and returns
    elif diff <= 8:
        templates = [
            ("Sold goods on credit £{x}.",
             lambda x: [_p(A["AR"], "DR", x, "Cr sale"),
                        _p(A["SALES"], "CR", x, "Cr sale")]),
            ("Bought goods on credit £{x}.",
             lambda x: [_p(A["PUR"], "DR", x, "Cr pur"),
                        _p(A["AP"], "CR", x, "Cr pur")]),
            ("Customer returned goods worth £{x}.",
             lambda x: [_p(A["RET_IN"], "DR", x, "Return"),
                        _p(A["AR"], "CR", x, "Return")]),
            ("Returned goods to supplier worth £{x}.",
             lambda x: [_p(A["AP"], "DR", x, "Return"),
                        _p(A["RET_OUT"], "CR", x, "Return")]),
            ("Received money from a customer into bank £{x}.",
             lambda x: [_p(A["BANK"], "DR", x, "Receipt"),
                        _p(A["AR"], "CR", x, "Receipt")]),
            ("Paid a supplier from bank £{x}.",
             lambda x: [_p(A["AP"], "DR", x, "Pay"),
                        _p(A["BANK"], "CR", x, "Pay")]),
        ]

    # Rounds 9–12 VAT and depreciation
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
             lambda x: [
                 _p(A["DEP"], "DR", x, "Dep"),
                 _p(A["ACCDEP"], "CR", x, "Dep")
             ]),
            ("Allowed a customer discount £{x}.",
             lambda x: [
                 _p(A["DISC_ALL"], "DR", x, "Disc"),
                 _p(A["AR"], "CR", x, "Disc")
             ]),
            ("Received a supplier discount £{x}.",
             lambda x: [
                 _p(A["AP"], "DR", x, "Disc"),
                 _p(A["DISC_REC"], "CR", x, "Disc")
             ]),
        ]

    # Rounds 13–16 adjustments
    elif diff <= 16:
        templates = [
            ("At period end, rent of £{x} is owing (accrual).",
             lambda x: [
                 _p(A["RENT"], "DR", x, "Accr"),
                 _p(A["ACCR"], "CR", x, "Accr")
             ]),
            ("At period end, utilities of £{x} were paid in advance (prepayment).",
             lambda x: [
                 _p(A["PREP"], "DR", x, "Prep"),
                 _p(A["UTIL"], "CR", x, "Prep")
             ]),
            ("Write off an irrecoverable debt £{x}.",
             lambda x: [
                 _p(A["BAD"], "DR", x, "Bad"),
                 _p(A["AR"], "CR", x, "Bad")
             ]),
            ("Create an allowance for doubtful debts £{x}.",
             lambda x: [
                 _p(A["BAD"], "DR", x, "Allow"),
                 _p(A["ALLOW"], "CR", x, "Allow")
             ]),
            ("Owner took drawings £{x} from bank.",
             lambda x: [
                 _p(A["DRAW"], "DR", x, "Draw"),
                 _p(A["BANK"], "CR", x, "Draw")
             ]),
        ]

    # Rounds 17–20 suspense and corrections
    else:
        templates = [
            ("Correct this error: equipment £{x} was wrongly debited to purchases.",
             lambda x: [
                 _p(A["EQUIP"], "DR", x, "Corr"),
                 _p(A["PUR"], "CR", x, "Corr")
             ]),
            ("A one sided error: bank was credited £{x} but the debit entry was missing. Use suspense.",
             lambda x: [
                 _p(A["SUSP"], "DR", x, "Miss"),
                 _p(A["BANK"], "CR", x, "Miss")
             ]),
            ("Clear suspense: the missing debit was rent expense £{x}.",
             lambda x: [
                 _p(A["RENT"], "DR", x, "Clear"),
                 _p(A["SUSP"], "CR", x, "Clear")
             ]),
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
# Marking
# ----------------------------

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


def tag_with_question(postings: List[Posting], q_no: int) -> List[Posting]:
    tag = f"Q{q_no}"
    return [Posting(account=p.account, side=p.side, amount=p.amount, narrative=tag) for p in postings]


# ----------------------------
# Streamlit app
# ----------------------------

st.set_page_config(page_title="Double Entry Game", layout="wide")

st.title("Double Entry Game")
st.caption("20 rounds, 10 questions per round. Shows the journal entry and the T accounts after each question.")

with st.sidebar:
    st.header("Round control")
    round_choice = st.selectbox("Choose round", list(range(1, 21)), index=0)
    if st.button("Start new round", type="primary"):
        st.session_state.started = True
        st.session_state.round_no = int(round_choice)
        st.session_state.questions = build_round(st.session_state.round_no, 10)
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.attempts = 0
        st.session_state.ledger = Ledger()
        st.session_state.last_message = ""
        st.session_state.last_journal = ""
        st.session_state.last_correct = None

    if st.button("Reset everything"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]

# Initialise state on first load
if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    st.info("Choose a round in the sidebar, then click Start new round.")
    st.stop()

round_no = st.session_state.round_no
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
    st.markdown(f"**{q.prompt}**")

    st.markdown("Answer format examples")
    st.code("Dr Bank 15000; Cr Capital 15000\nDr Utilities expense 1000; Dr VAT input 200; Cr Bank 1200", language="text")

    entry = st.text_input("Your journal entry", key=f"entry_{round_no}_{q_index}")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        submitted = st.button("Submit entry")
    with col_b:
        show_answer = st.button("Show model answer and post it")

    if submitted:
        try:
            student_postings = parse_entry(entry)
        except Exception as e:
            st.session_state.last_message = f"Not marked. {e}"
            st.session_state.last_correct = False
        else:
            ok, feedback = mark(student_postings, q.expected)
            if ok:
                ledger.post_many(tag_with_question(student_postings, q_index + 1))
                st.session_state.score += 1
                st.session_state.last_correct = True
                st.session_state.last_message = "Correct"
                st.session_state.last_journal = format_postings_lines(student_postings)

                st.session_state.q_index += 1
                st.session_state.attempts = 0
                st.rerun()
            else:
                st.session_state.attempts += 1
                st.session_state.last_correct = False
                st.session_state.last_message = "Not quite"
                st.session_state.last_journal = ""
                st.session_state.last_feedback = feedback

                if st.session_state.attempts >= 2:
                    # Post model answer so learning continues
                    ledger.post_many(tag_with_question(q.expected, q_index + 1))
                    st.session_state.last_message = "Two attempts used. Model answer posted."
                    st.session_state.last_journal = format_postings_lines(q.expected)

                    st.session_state.q_index += 1
                    st.session_state.attempts = 0
                    st.rerun()

    if show_answer:
        ledger.post_many(tag_with_question(q.expected, q_index + 1))
        st.session_state.last_message = "Model answer posted."
        st.session_state.last_journal = format_postings_lines(q.expected)
        st.session_state.last_correct = None

        st.session_state.q_index += 1
        st.session_state.attempts = 0
        st.rerun()

    if st.session_state.last_message:
        if st.session_state.last_correct is True:
            st.success(st.session_state.last_message)
        elif st.session_state.last_correct is False:
            st.warning(st.session_state.last_message)
            if "last_feedback" in st.session_state and st.session_state.last_feedback:
                st.code(st.session_state.last_feedback, language="text")
        else:
            st.info(st.session_state.last_message)

    if st.session_state.last_journal:
        st.markdown("**Double entry posted**")
        st.code(st.session_state.last_journal, language="text")

with right:
    st.subheader("T accounts")
    t_text = ledger.render_all_t_accounts(max_accounts=18)
    st.code(t_text, language="text")

    st.caption("Each posting is labelled Q1, Q2, etc so students can see which question created each entry.")
