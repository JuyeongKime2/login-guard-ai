"""① 진단 함수: 딥러닝 점수 + 규칙 근거를 합친다."""
import config
from .rules import analyze

_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None and config.PW_MODEL_PATH.exists():
        import torch
        from .model import PasswordRiskNet
        ckpt = torch.load(config.PW_MODEL_PATH, map_location="cpu")
        m = PasswordRiskNet(max_len=ckpt["max_len"])
        m.load_state_dict(ckpt["state_dict"])
        m.eval()
        _MODEL = m
    return _MODEL


def model_prob(pw: str):
    model = _load_model()
    if model is None:
        return None
    import torch
    from .model import encode
    ids, ln = encode(pw, model.max_len)
    with torch.no_grad():
        return float(torch.sigmoid(model(torch.tensor([ids]), torch.tensor([ln])))[0])


def diagnose(pw: str) -> dict:
    """반환값의 'llm_summary'에는 비밀번호 원문이 들어가지 않는다."""
    rule = analyze(pw)
    flags = rule["flags"]
    prob = model_prob(pw)
    used_model = prob is not None
    risk = 0.5 * prob + 0.5 * flags["rule_score"] if used_model else flags["rule_score"]
    if flags["is_common"]:
        risk = max(risk, 0.99)
    if flags["length"] < 8:
        risk = max(risk, 0.85)

    level = "위험" if risk >= 0.7 else ("주의" if risk >= 0.4 else "안전")
    llm_summary = {k: v for k, v in flags.items()}  # 원문 없음
    llm_summary.update({"risk_score": round(risk, 3), "level": level})
    return {"risk": risk, "level": level, "reasons": rule["reasons"],
            "used_model": used_model, "llm_summary": llm_summary}
