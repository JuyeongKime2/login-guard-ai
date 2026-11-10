"""규칙 기반 분석: 딥러닝 점수의 '근거'를 사람이 읽을 수 있게 만든다.

중요: LLM에는 이 모듈이 만든 flags(참/거짓, 길이 등)만 보낸다.
비밀번호 원문이나 그 일부(예: 포함된 단어)는 절대 외부로 보내지 않는다.
"""
import re

from .wordlists import BASE_WORDS, COMMON_PASSWORDS, KEYBOARD_WALKS

_UNLEET = str.maketrans({"@": "a", "0": "o", "3": "e", "1": "i", "$": "s", "!": "i"})
_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890"]
_COMMON_WORDS = sorted({w for w in BASE_WORDS + COMMON_PASSWORDS if len(w) >= 4 and w.isalpha()})


def _has_run(s, alphabet, k=4):
    """alphabet에서 연속된 k글자(정방향/역방향)가 들어있는지."""
    for i in range(len(alphabet) - k + 1):
        seg = alphabet[i:i + k]
        if seg in s or seg[::-1] in s:
            return True
    return False


def analyze(pw: str) -> dict:
    low = pw.lower()
    plain = low.translate(_UNLEET)
    flags = {
        "length": len(pw),
        "has_lower": any(c.islower() for c in pw),
        "has_upper": any(c.isupper() for c in pw),
        "has_digit": any(c.isdigit() for c in pw),
        "has_symbol": any(not c.isalnum() for c in pw),
        "is_common": low in COMMON_PASSWORDS,
        "contains_common_word": any(w in plain for w in _COMMON_WORDS),
        "keyboard_pattern": any(w in low for w in KEYBOARD_WALKS if len(w) >= 4)
        or any(_has_run(low, row) for row in _ROWS[:3]),
        "sequential": _has_run(low, "abcdefghijklmnopqrstuvwxyz") or _has_run(low, "0123456789"),
        "repeated": bool(re.search(r"(.)\1\1", pw)),
        "date_like": bool(re.search(r"(19[5-9]\d|20[0-2]\d)", pw))
        or bool(re.search(r"\d{6,8}", pw)),
        "non_ascii": any(ord(c) > 126 for c in pw),
    }
    flags["n_classes"] = sum([flags["has_lower"], flags["has_upper"],
                              flags["has_digit"], flags["has_symbol"]])

    reasons = []
    if flags["is_common"]:
        reasons.append("가장 흔한 비밀번호 목록에 있습니다. 해킹 프로그램이 제일 먼저 시도합니다.")
    if flags["length"] < 8:
        reasons.append(f"길이가 {flags['length']}자로 너무 짧습니다 (최소 12자 권장).")
    elif flags["length"] < 12:
        reasons.append(f"길이가 {flags['length']}자입니다. 12자 이상이면 훨씬 안전해집니다.")
    if flags["contains_common_word"]:
        reasons.append("사전에 있는 흔한 단어나 이름이 들어 있습니다 (@→a 같은 치환도 쉽게 풀립니다).")
    if flags["keyboard_pattern"]:
        reasons.append("키보드 배열 패턴(qwer, asdf 등)이 있습니다.")
    if flags["sequential"]:
        reasons.append("1234, abcd 같은 연속 문자가 있습니다.")
    if flags["repeated"]:
        reasons.append("같은 문자가 3번 이상 반복됩니다.")
    if flags["date_like"]:
        reasons.append("연도나 생년월일로 보이는 숫자가 있습니다. 개인정보로 추측되기 쉽습니다.")
    if flags["n_classes"] < 3 and flags["length"] < 16:
        reasons.append("영문 대·소문자, 숫자, 특수문자 중 3종류 이상을 섞으면 좋습니다.")
    if flags["non_ascii"]:
        reasons.append("한글 등은 많은 사이트에서 비밀번호로 허용되지 않습니다.")

    # 규칙 점수 (모델이 없을 때 대체용, 모델 점수의 하한선으로도 사용)
    score = 0.0
    score += 0.9 if flags["is_common"] else 0
    score += max(0, (12 - flags["length"])) * 0.06
    score += 0.25 * flags["contains_common_word"] + 0.2 * flags["keyboard_pattern"]
    score += 0.15 * flags["sequential"] + 0.1 * flags["repeated"] + 0.15 * flags["date_like"]
    score += 0.08 * max(0, 3 - flags["n_classes"])
    flags["rule_score"] = round(min(score, 1.0), 3)
    return {"flags": flags, "reasons": reasons}
