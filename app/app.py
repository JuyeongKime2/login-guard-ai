"""LoginGuard AI - Gradio 통합 앱

실행:  python app/app.py
- 코랩/외부 공유: share=True 로 72시간 임시 공개 링크가 생성됨
- 로컬 + ngrok:   SHARE=0 python app/app.py  후  ngrok http 7860
"""
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gradio as gr  # noqa: E402
import numpy as np  # noqa: E402

import config  # noqa: E402
from src.llm_coach.coach import login_alert, password_coach  # noqa: E402
from src.password_risk.predict import diagnose  # noqa: E402
from src.keystroke.capture import events_to_features  # noqa: E402

# ---------------------------------------------------------------
# 브라우저에서 키를 누르고 뗀 시각을 기록하는 JavaScript
# id가 ks_enroll / ks_login 인 입력칸에서만 기록한다.
# ---------------------------------------------------------------
KEY_LISTENER_JS = """
() => {
  if (window.__ksInit) return;
  window.__ksInit = true;
  window.__ks = {ks_enroll: [], ks_login: []};
  const handler = (type) => (e) => {
    const box = e.target && e.target.closest ? e.target.closest('#ks_enroll, #ks_login') : null;
    if (!box) return;
    if (type === 'd' && e.repeat) return;
    const id = box.id;
    if (type === 'd' && e.target.value === '' && e.code !== 'Enter') window.__ks[id] = [];
    window.__ks[id].push({type: type, code: e.code, t: performance.now()});
  };
  document.addEventListener('keydown', handler('d'), true);
  document.addEventListener('keyup', handler('u'), true);
}
"""


def take_events_js(box_id):
    return f"""
(pw, ev) => {{
  const store = window.__ks || {{}};
  const data = JSON.stringify(store['{box_id}'] || []);
  if (window.__ks) window.__ks['{box_id}'] = [];
  return [pw, data];
}}
"""


STATE = {"user_verifier": None, "demo_verifier": None, "demo_samples": None}


def _verifier_cls():
    from src.keystroke.model import Verifier
    return Verifier


def get_demo():
    if STATE["demo_verifier"] is None and config.KS_DEMO_PATH.exists():
        STATE["demo_verifier"] = _verifier_cls().load(config.KS_DEMO_PATH)
        STATE["demo_samples"] = np.load(config.KS_DEMO_SAMPLES)
    return STATE["demo_verifier"]


# ---------------- ① 진단 ----------------
def on_diagnose(pw):
    if not pw:
        return "비밀번호를 입력해주세요.", None
    d = diagnose(pw)
    icon = {"위험": "🔴", "주의": "🟠", "안전": "🟢"}[d["level"]]
    src = "딥러닝(BiLSTM)" if d["used_model"] else "규칙 기반(모델 파일 없음)"
    lines = [f"## {icon} {d['level']}  ·  위험도 {d['risk'] * 100:.0f}%",
             f"<small>판정 엔진: {src}</small>", ""]
    lines += [f"- {r}" for r in d["reasons"]] or ["- 특별한 약점이 발견되지 않았어요."]
    return "\n".join(lines), d["llm_summary"]


# ---------------- ② 코치 ----------------
def on_coach(summary, keywords):
    if not summary:
        return "먼저 ① 진단을 실행해주세요."
    text, provider = password_coach(summary, keywords)
    return f"{text}\n\n---\n<small>🤖 {provider} · 비밀번호 원문은 AI에 전송되지 않았습니다.</small>"


# ---------------- ③ 등록 ----------------
def on_enroll_add(pw, events_json, samples):
    samples = samples or []
    if pw != config.CMU_PASSWORD:
        return "", f"❗ `{config.CMU_PASSWORD}` 를 정확히 입력해주세요.", samples
    try:
        f = events_to_features(json.loads(events_json or "[]"))
    except ValueError as e:
        return "", f"❗ {e}", samples
    samples = samples + [f.tolist()]
    return "", f"✅ {len(samples)}번째 샘플 저장 (최소 10회 권장)", samples


def on_enroll_train(samples, sensitivity):
    if not samples or len(samples) < 5:
        return "❗ 최소 5회 이상 입력해주세요 (10회 이상 권장)."
    X = np.array(samples, dtype=np.float32)
    v = _verifier_cls()().fit(X)
    v.calibrate_from_enrollment(X, multiplier=sensitivity)
    STATE["user_verifier"] = v
    return f"✅ 등록 완료! 샘플 {len(X)}개로 학습했어요. 허용 기준값 = {v.threshold:.3f}"


# ---------------- ③ 로그인 ----------------
def _judge(v, feats, who):
    score = float(v.score(feats)[0])
    ok = score <= v.threshold
    result = {"target": who, "decision": "통과" if ok else "차단",
              "score": round(score, 4), "threshold": round(float(v.threshold), 4)}
    head = (f"## {'✅ 로그인 성공' if ok else '🚫 로그인 차단'}\n"
            f"리듬 차이 점수 **{score:.3f}** / 허용 기준 **{v.threshold:.3f}**")
    alert, provider = login_alert(result)
    return f"{head}\n\n{alert}\n\n<small>🤖 {provider}</small>"


def on_login(pw, events_json, target):
    if pw != config.CMU_PASSWORD:
        return "", "## ❌ 비밀번호가 틀렸습니다 (1차 인증 실패)"
    v = STATE["user_verifier"] if target == "내가 등록한 패턴" else get_demo()
    if v is None:
        return "", "❗ 등록된 패턴이 없어요. 먼저 등록하거나 데모 모델을 학습해주세요."
    try:
        f = events_to_features(json.loads(events_json or "[]"))
    except ValueError as e:
        return "", f"❗ {e}"
    return "", "✅ 비밀번호 일치 (1차 인증 통과)\n\n" + _judge(v, f, target)


def on_demo_sample(kind):
    v = get_demo()
    if v is None:
        return "❗ 먼저 `python -m src.keystroke.train_demo` 를 실행해주세요."
    arr = STATE["demo_samples"]["genuine" if kind == "본인" else "impostor"]
    f = arr[random.randrange(len(arr))]
    title = ("👤 데모 사용자 본인의 실제 입력 기록" if kind == "본인"
             else "🕵️ 비밀번호를 훔친 다른 사람의 입력 기록")
    return f"### {title}\n(CMU 데이터 중 학습에 쓰지 않은 샘플)\n\n" + _judge(v, f, f"CMU {kind} 샘플")


# ---------------- UI ----------------
with gr.Blocks(title="LoginGuard AI") as demo:
    gr.Markdown("# 🔐 LoginGuard AI\n"
                "기억하기 쉬운 강한 비밀번호를 만들고(①②), 유출돼도 타이핑 리듬으로 막는다(③)")

    with gr.Tab("① 비밀번호 진단"):
        pw_in = gr.Textbox(label="진단할 비밀번호", type="password")
        btn_diag = gr.Button("진단하기", variant="primary")
        diag_out = gr.Markdown()
        summary_state = gr.State()
        btn_diag.click(on_diagnose, pw_in, [diag_out, summary_state])

        gr.Markdown("### ② AI 보안 코치")
        kw_in = gr.Textbox(label="기억하기 쉬운 단어 2~3개", placeholder="예: 제주, 고양이, 자전거")
        btn_coach = gr.Button("더 안전한 비밀번호 만드는 법 물어보기")
        coach_out = gr.Markdown()
        btn_coach.click(on_coach, [summary_state, kw_in], coach_out)

    with gr.Tab("③-1 타이핑 패턴 등록"):
        gr.Markdown(f"입력칸에 **`{config.CMU_PASSWORD}`** 입력 → **Enter** → [샘플 저장]. "
                    "평소처럼 10회 이상 반복하세요.\n\n"
                    "<small>CMU 공개 데이터와 같은 비밀번호로 모델을 검증했기 때문에 시연도 같은 "
                    "비밀번호를 씁니다. 실제 서비스에서는 사용자 자신의 비밀번호로 등록합니다.</small>")
        en_pw = gr.Textbox(label="비밀번호 입력", type="password", elem_id="ks_enroll")
        en_ev = gr.Textbox(visible=False)
        en_samples = gr.State([])
        btn_add = gr.Button("샘플 저장")
        en_msg = gr.Markdown()
        btn_add.click(on_enroll_add, [en_pw, en_ev, en_samples], [en_pw, en_msg, en_samples],
                      js=take_events_js("ks_enroll"))
        sens = gr.Slider(1.0, 5.0, value=2.0, step=0.5,
                         label="허용 범위 (클수록 관대함, 작을수록 엄격함)")
        btn_train = gr.Button("등록 완료 (내 패턴 학습)", variant="primary")
        train_msg = gr.Markdown()
        btn_train.click(on_enroll_train, [en_samples, sens], train_msg)

    with gr.Tab("③-2 로그인 (2차 인증)"):
        target = gr.Radio(["내가 등록한 패턴", "CMU 데모 사용자(s002)"],
                          value="내가 등록한 패턴", label="누구의 계정으로 로그인할까요?")
        lg_pw = gr.Textbox(label="비밀번호", type="password", elem_id="ks_login")
        lg_ev = gr.Textbox(visible=False)
        btn_login = gr.Button("로그인", variant="primary")
        lg_out = gr.Markdown()
        btn_login.click(on_login, [lg_pw, lg_ev, target], [lg_pw, lg_out],
                        js="""(pw, ev, t) => {
                          const store = window.__ks || {};
                          const data = JSON.stringify(store['ks_login'] || []);
                          if (window.__ks) window.__ks['ks_login'] = [];
                          return [pw, data, t];
                        }""")

    with gr.Tab("③-3 CMU 데이터 시연 (백업)"):
        gr.Markdown("실시간 입력이 안 될 때를 위한 시연입니다. 51명 공개 데이터로 학습한 모델이 "
                    "**같은 비밀번호라도 입력한 사람이 다르면** 구별하는지 보여줍니다.")
        with gr.Row():
            b1 = gr.Button("👤 본인 입력으로 로그인")
            b2 = gr.Button("🕵️ 비밀번호 훔친 타인으로 로그인")
        demo_out = gr.Markdown()
        b1.click(lambda: on_demo_sample("본인"), None, demo_out)
        b2.click(lambda: on_demo_sample("타인"), None, demo_out)

    demo.load(None, None, None, js=KEY_LISTENER_JS)


if __name__ == "__main__":
    share = os.getenv("SHARE", "1") == "1"
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)), share=share)
