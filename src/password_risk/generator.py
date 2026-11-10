"""위험(1) / 안전(0) 비밀번호 합성 데이터 생성기."""
import random
import string

from .wordlists import COMMON_PASSWORDS, KEYBOARD_WALKS

LEET = {"a": "@", "o": "0", "e": "3", "i": "1", "s": "$", "l": "1"}
SYMBOLS = "!@#$%^&*-_=+?"


def _year(rng):
    return str(rng.randint(1970, 2026))


def _mmdd(rng):
    return f"{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}"


def _mutate(word, rng):
    """사람들이 흔히 쓰는 '살짝 바꾸기' 규칙."""
    w = word
    if rng.random() < 0.5:
        w = w.capitalize()
    if rng.random() < 0.3:
        w = "".join(LEET.get(c, c) if rng.random() < 0.6 else c for c in w)
    r = rng.random()
    if r < 0.25:
        w += _year(rng)
    elif r < 0.45:
        w += rng.choice(["1", "12", "123", "1234", "0", "00", "7", "77"])
    elif r < 0.6:
        w += _mmdd(rng)
    elif r < 0.7:
        w = _year(rng)[2:] + w
    if rng.random() < 0.35:
        w += rng.choice(["!", "!!", "@", "#", "!@#", "*"])
    return w


def risky_password(rng, words):
    kind = rng.random()
    if kind < 0.12:
        return rng.choice(COMMON_PASSWORDS)
    if kind < 0.55:
        return _mutate(rng.choice(words), rng)
    if kind < 0.65:
        return _mutate(rng.choice(words) + rng.choice(words), rng)
    if kind < 0.75:
        w = rng.choice(KEYBOARD_WALKS)
        return w + rng.choice(["", "!", "1", "123", _year(rng)[2:]])
    if kind < 0.83:  # 숫자열 / 생년월일
        return rng.choice([
            _year(rng) + _mmdd(rng), _year(rng)[2:] + _mmdd(rng),
            str(rng.randint(0, 9)) * rng.randint(4, 8),
            "".join(str(i % 10) for i in range(rng.randint(0, 5), rng.randint(9, 13))),
        ])
    if kind < 0.92:  # 짧은 랜덤 문자열
        n = rng.randint(4, 7)
        return "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(n))
    # 반복 패턴
    c = rng.choice(string.ascii_lowercase)
    return c * rng.randint(3, 5) + str(rng.randint(0, 9)) * rng.randint(3, 4)


def safe_password(rng, words):
    if rng.random() < 0.5:  # 무작위 강한 문자열
        n = rng.randint(12, 20)
        pools = [string.ascii_lowercase, string.ascii_uppercase, string.digits, SYMBOLS]
        chars = [rng.choice(p) for p in pools]
        allc = "".join(pools)
        chars += [rng.choice(allc) for _ in range(n - len(chars))]
        rng.shuffle(chars)
        return "".join(chars)
    # 문장형(패스프레이즈): 서로 무관한 단어 3~4개 + 구분기호 + 숫자
    k = rng.randint(3, 4)
    ws = rng.sample(words, k)
    ws = [w.capitalize() if rng.random() < 0.5 else w for w in ws]
    sep = rng.choice(list(SYMBOLS) + ["", "."])
    pw = sep.join(ws)
    pos = rng.randint(0, len(pw))
    pw = pw[:pos] + str(rng.randint(10, 999)) + pw[pos:]
    if rng.random() < 0.5:
        pw += rng.choice(SYMBOLS)
    return pw


def build_dataset(n, risky_words, safe_words, seed=42):
    """n개의 (비밀번호, 라벨) 생성. 라벨 1=위험, 0=안전. 클래스 균형."""
    rng = random.Random(seed)
    data = []
    for i in range(n):
        if i % 2 == 0:
            data.append((risky_password(rng, risky_words), 1))
        else:
            data.append((safe_password(rng, safe_words), 0))
    rng.shuffle(data)
    return data
