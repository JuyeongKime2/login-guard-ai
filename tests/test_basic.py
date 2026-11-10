"""torch 없이도 돌아가는 기본 테스트. 실행: python -m pytest tests  또는  python tests/test_basic.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import random  # noqa: E402

import numpy as np  # noqa: E402

import config  # noqa: E402
from src.keystroke.capture import events_to_features  # noqa: E402
from src.keystroke.metrics import eer  # noqa: E402
from src.password_risk.generator import build_dataset, risky_password, safe_password  # noqa: E402
from src.password_risk.predict import diagnose  # noqa: E402
from src.password_risk.rules import analyze  # noqa: E402
from src.password_risk.wordlists import BASE_WORDS, SAFE_WORDS  # noqa: E402


def test_rules():
    assert analyze("123456")["flags"]["is_common"]
    assert analyze("qwer1234!")["flags"]["keyboard_pattern"]
    assert analyze("Minsu1998!")["flags"]["date_like"]
    assert analyze("Minsu1998!")["flags"]["contains_common_word"]
    strong = analyze("Orbit-Velvet42-Quartz!")["flags"]
    assert strong["rule_score"] < 0.3, strong


def test_diagnose_has_no_password_in_summary():
    pw = "Sarang2024!"
    d = diagnose(pw)
    assert pw not in str(d["llm_summary"])
    assert d["level"] in ("위험", "주의")


def test_generator_balanced():
    data = build_dataset(1000, BASE_WORDS, SAFE_WORDS, seed=0)
    labels = [y for _, y in data]
    assert sum(labels) == 500
    rng = random.Random(0)
    assert all(len(safe_password(rng, SAFE_WORDS)) >= 12 for _ in range(200))
    assert all(len(risky_password(rng, BASE_WORDS)) > 0 for _ in range(200))


def _fake_events(hold=0.1, gap=0.2):
    ev, t = [], 1000.0
    for code in config.KEY_CODES:
        if code == "KeyR":
            ev.append({"type": "d", "code": "ShiftLeft", "t": t - 30})
        ev.append({"type": "d", "code": code, "t": t})
        ev.append({"type": "u", "code": code, "t": t + hold * 1000})
        if code == "KeyR":
            ev.append({"type": "u", "code": "ShiftLeft", "t": t + hold * 1000 + 10})
        t += gap * 1000
    return ev


def test_capture_features():
    f = events_to_features(_fake_events())
    assert f.shape == (31,)
    assert np.allclose(f[0], 0.1, atol=1e-4)     # H.period
    assert np.allclose(f[1], 0.2, atol=1e-4)     # DD.period.t
    assert np.allclose(f[2], 0.1, atol=1e-4)     # UD.period.t
    assert np.allclose(f[-1], 0.1, atol=1e-4)    # H.Return


def test_capture_rejects_backspace():
    ev = _fake_events() + [{"type": "d", "code": "Backspace", "t": 5000}]
    try:
        events_to_features(ev)
        raise AssertionError("should fail")
    except ValueError:
        pass


def test_eer():
    g = np.random.RandomState(0).normal(1, 0.3, 200)
    i = np.random.RandomState(1).normal(3, 0.3, 250)
    e, thr = eer(g, i)
    assert e < 0.01 and 1 < thr < 3


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
