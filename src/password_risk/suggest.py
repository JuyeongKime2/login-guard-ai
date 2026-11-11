"""알고리즘 비밀번호 추천.

입력한 비밀번호/단어로 후보를 만들고 ① 진단 모델(diagnose)로 다시 검사해서
위험도가 낮은 것만 추천한다. 모든 계산은 로컬에서 하며 LLM에는 보내지 않는다.
난수는 secrets(암호학적 난수)를 사용한다.
"""
import re
import secrets
import string

from .predict import diagnose
from .wordlists import SAFE_WORDS

SAFE_THRESHOLD = 0.4   # 이 값 미만이면 '안전'
MAX_TRIES = 12         # 종류별 후보 생성 횟수
SYMBOLS = "!@#$%^&*-_=+?"

# ---------------- 한글 → 두벌식 자판 변환 ----------------
_CHO = ["r", "R", "s", "e", "E", "f", "a", "q", "Q", "t",
        "T", "d", "w", "W", "c", "z", "x", "v", "g"]
_JUNG = ["k", "o", "i", "O", "j", "p", "u", "P", "h", "hk", "ho",
         "hl", "y", "n", "nj", "np", "nl", "b", "m", "ml", "l"]
_JONG = ["", "r", "R", "rt", "s", "sw", "sg", "e", "f", "fr", "fa", "fq",
         "ft", "fx", "fv", "fg", "a", "q", "qt", "t", "T", "d", "w", "c",
         "z", "x", "v", "g"]
# 낱자모 (ㄱ~ㅣ, U+3131~U+3163)
_COMPAT = dict(zip(
    "ㄱㄲㄳㄴㄵㄶㄷㄸㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅃㅄㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ",
    ["r", "R", "rt", "s", "sw", "sg", "e", "E", "f", "fr", "fa", "fq", "ft",
     "fx", "fv", "fg", "a", "q", "Q", "qt", "t", "T", "d", "w", "W", "c",
     "z", "x", "v", "g"] + _JUNG,
))


def hangul_to_keys(text: str) -> str:
    """'제주' → 'wpwn' 처럼 한글을 두벌식 자판 그대로 친 영문으로 바꾼다."""
    out = []
    for ch in text:
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out.append(_CHO[code // 588] + _JUNG[(code % 588) // 28] + _JONG[code % 28])
        else:
            out.append(_COMPAT.get(ch, ch))
    return "".join(out)


# ---------------- 도우미 ----------------
def _pick(seq):
    return secrets.choice(seq)


def _digits(n=2):
    return "".join(_pick(string.digits) for _ in range(n))


def _words(k):
    pool = list(SAFE_WORDS)
    chosen = []
    for _ in range(k):
        w = _pick(pool)
        pool.remove(w)
        chosen.append(w)
    return chosen


def _split_keywords(keywords):
    return [w for w in re.split(r"[,\s/]+", keywords or "") if w]


# ---------------- 후보 생성기 ----------------
def _revive(pw, _kws):
    a, b = _words(2)
    return f"{pw}{_pick('.-_')}{a.capitalize()}{_pick('.-_')}{b.capitalize()}{_digits()}"


def _from_keywords(_pw, kws):
    parts = [hangul_to_keys(w) for w in kws[:3]]
    if len(parts) < 3:  # 단어가 적으면 무관한 단어로 보충
        parts += _words(3 - len(parts))
    sep = _pick("-_.")
    parts = [p.capitalize() for p in parts[:-1]] + [parts[-1]]
    return sep.join(parts) + _digits() + sep


def _passphrase(_pw, _kws):
    ws = _words(4)
    i = secrets.randbelow(4)
    ws[i] = ws[i].capitalize()
    sep = _pick(SYMBOLS)
    return sep.join(ws) + _digits() + _pick(SYMBOLS)


def _random(_pw, _kws, length=16):
    alphabet = string.ascii_letters + string.digits + "!?@#$%&*"
    while True:
        s = "".join(_pick(alphabet) for _ in range(length))
        if (any(c.islower() for c in s) and any(c.isupper() for c in s)
                and any(c.isdigit() for c in s) and any(not c.isalnum() for c in s)):
            return s


def _best(gen, pw, kws):
    """후보를 여러 개 만들어 진단하고, 안전 기준을 넘는 첫 후보(없으면 최저 위험)를 고른다."""
    best = None
    for _ in range(MAX_TRIES):
        cand = gen(pw, kws)
        risk = diagnose(cand)["risk"]
        if best is None or risk < best[1]:
            best = (cand, risk)
        if risk < SAFE_THRESHOLD:
            break
    return best


def suggest(pw: str, keywords: str = "") -> list:
    """추천 목록 반환: [{'title', 'password', 'risk', 'tip'}, ...]"""
    pw = (pw or "").strip()
    kws = _split_keywords(keywords)
    plans = []

    # 흔한 비밀번호(123456 등)는 살릴 가치가 없으므로 '살리기'는 제외
    if pw and not diagnose(pw)["llm_summary"].get("is_common"):
        plans.append(("내 비밀번호 살리기", _revive,
                      "지금 비밀번호 뒤에 무관한 단어 2개와 숫자를 붙였어요."))
    if kws:
        plans.append(("내 단어로 만들기", _from_keywords,
                      "한글 단어를 한글 자판 그대로 영문으로 입력했어요 (예: 제주 → wpwn)."))
    plans.append(("문장형 비밀번호", _passphrase,
                  "서로 관계없는 단어 4개 + 숫자 + 기호. 길어서 강하고 외우기 쉬워요."))
    plans.append(("완전 무작위", _random,
                  "가장 강력해요. 비밀번호 관리 프로그램에 저장해서 쓰세요."))

    items = []
    for title, gen, tip in plans:
        cand, risk = _best(gen, pw, kws)
        items.append({"title": title, "password": cand, "risk": risk, "tip": tip})
    return items
