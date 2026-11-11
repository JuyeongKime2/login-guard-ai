"""LoginGuard AI - Gradio 통합 앱

실행:  python app/app.py
- 코랩/외부 공유: share=True 로 72시간 임시 공개 링크가 생성됨
- 로컬 + ngrok:   SHARE=0 python app/app.py  후  ngrok http 7860
"""
import inspect
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
from src.password_risk.suggest import suggest  # noqa: E402
from src.keystroke.capture import events_to_features  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui  # noqa: E402

# ---------------------------------------------------------------
# 브라우저에서 키를 누르고 뗀 시각을 기록하는 JavaScript
# id가 ks_enroll / ks_login 인 입력칸에서만 기록한다.
# ---------------------------------------------------------------
KEY_LISTENER_JS = """
() => {
  // 화면을 밝은 테마로 고정 (디자인이 밝은 테마 기준)
  const url = new URL(window.location);
  if (url.searchParams.get('__theme') !== 'light') {
    url.searchParams.set('__theme', 'light');
    window.location.replace(url.href);
    return;
  }
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

  // 진단 전에 [AI 코치에게 물어보기]를 누르면 버튼 위에 말풍선을 띄운다
  const bubble = (anchor, text) => {
    document.querySelectorAll('.lg-bubble').forEach((b) => b.remove());
    const r = anchor.getBoundingClientRect();
    const b = document.createElement('div');
    b.className = 'lg-bubble';
    b.setAttribute('role', 'alert');
    b.textContent = text;
    const x = Math.min(Math.max(r.left + r.width / 2, 150), window.innerWidth - 150);
    b.style.left = (x + window.scrollX) + 'px';
    b.style.top = (r.top + window.scrollY - 12) + 'px';
    document.body.appendChild(b);
    setTimeout(() => b.classList.add('lg-out'), 2600);
    setTimeout(() => b.remove(), 3000);
  };
  document.addEventListener('click', (e) => {
    const btn = e.target && e.target.closest ? e.target.closest('#btn_coach') : null;
    if (!btn) return;
    if (document.querySelector('#diag_out .lg-result')) return;
    bubble(btn, '먼저 위에서 진단을 받아주세요');
    const d = document.querySelector('#btn_diag');
    if (d) { d.classList.remove('lg-pulse'); void d.offsetWidth; d.classList.add('lg-pulse'); }
  }, true);
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
        return ui.note("비밀번호를 입력해주세요."), None
    d = diagnose(pw)
    return ui.diagnosis_card(d), d["llm_summary"]


def on_suggest(pw, keywords):
    return ui.suggestion_cards(suggest(pw, keywords))


# ---------------- ② 코치 ----------------
def on_coach(summary, keywords):
    if not summary:  # 안내는 화면의 말풍선이 한다
        return gr.update(visible=False)
    text, provider = password_coach(summary, keywords)
    return gr.update(value=f"{text}\n\n---\n<small>🤖 {provider} · 비밀번호 원문은 AI에 "
                           "전송되지 않았습니다.</small>", visible=True)


# ---------------- ③ 등록 ----------------
def on_enroll_add(pw, events_json, samples):
    samples = samples or []
    if pw != config.CMU_PASSWORD:
        return "", ui.note(f"<b>다시 입력해주세요.</b> <code>{config.CMU_PASSWORD}</code> 를 "
                           "정확히 입력해야 합니다.", "danger"), samples
    try:
        f = events_to_features(json.loads(events_json or "[]"))
    except ValueError as e:
        return "", ui.note(f"<b>다시 입력해주세요.</b> {e}", "danger"), samples
    samples = samples + [f.tolist()]
    return "", ui.enroll_progress(len(samples)), samples


def on_enroll_train(samples, sensitivity):
    if not samples or len(samples) < 5:
        return ui.note("<b>샘플이 부족해요.</b> 최소 5회, 가능하면 10회 이상 입력해주세요.", "danger")
    X = np.array(samples, dtype=np.float32)
    v = _verifier_cls()().fit(X)
    v.calibrate_from_enrollment(X, multiplier=sensitivity)
    STATE["user_verifier"] = v
    return ui.note(f"<b>등록 완료.</b> 샘플 {len(X)}개로 내 타이핑 패턴을 학습했어요. "
                   f"허용 기준값 {v.threshold:.3f} · 이제 로그인 탭에서 확인해보세요.", "ok")


# ---------------- ③ 로그인 ----------------
def _judge(v, feats, who, sub=""):
    """(결과 카드 HTML, LLM 알림 업데이트)"""
    score = float(v.score(feats)[0])
    ok = score <= v.threshold
    result = {"target": who, "decision": "통과" if ok else "차단",
              "score": round(score, 4), "threshold": round(float(v.threshold), 4)}
    alert, provider = login_alert(result)
    card = ui.login_card(ok, score, float(v.threshold), sub=sub)
    return card, gr.update(value=f"{alert}\n\n<small>🤖 {provider}</small>", visible=True)


def on_login(pw, events_json, target):
    hide = gr.update(visible=False)
    if pw != config.CMU_PASSWORD:
        return "", ui.note("<b>비밀번호가 틀렸습니다.</b> 1차 인증에서 차단되었습니다.", "danger"), hide
    v = STATE["user_verifier"] if target == "내가 등록한 패턴" else get_demo()
    if v is None:
        return "", ui.note("<b>등록된 패턴이 없어요.</b> 먼저 패턴 등록 탭에서 등록해주세요."), hide
    try:
        f = events_to_features(json.loads(events_json or "[]"))
    except ValueError as e:
        return "", ui.note(f"<b>다시 입력해주세요.</b> {e}", "danger"), hide
    card, alert = _judge(v, f, target, sub="비밀번호 일치 · 1차 인증 통과")
    return "", card, alert


def on_demo_sample(kind):
    v = get_demo()
    if v is None:
        return ui.note("<b>시연 모델이 없어요.</b> 터미널에서 "
                       "<code>python -m src.keystroke.train_demo</code> 를 먼저 실행해주세요."), \
            gr.update(visible=False)
    arr = STATE["demo_samples"]["genuine" if kind == "본인" else "impostor"]
    f = arr[random.randrange(len(arr))]
    sub = ("계정 주인의 실제 입력 기록 (학습에 쓰지 않은 샘플)" if kind == "본인"
           else "비밀번호를 알아낸 다른 사람의 입력 기록")
    return _judge(v, f, f"CMU {kind} 샘플", sub=sub)


# ---------------- UI ----------------
def _supported(fn, opts):
    params = inspect.signature(fn).parameters
    return {k: v for k, v in opts.items() if k in params}


try:
    STYLE = {"theme": gr.themes.Base(primary_hue="indigo", neutral_hue="slate", radius_size="lg")}
except Exception:
    STYLE = {}


def html(value="", **kw):
    return gr.HTML(value, elem_classes="lg-plain", **kw)


with gr.Blocks(title="LoginGuard AI", **_supported(gr.Blocks.__init__, STYLE)) as demo:
    html(ui.hero())

    with gr.Tab("비밀번호 진단 · 코치"):
        html(ui.section(1, "비밀번호 위험도 진단",
                        "비밀번호를 입력하면 딥러닝 모델이 얼마나 쉽게 추측되는지 알려줍니다."))
        with gr.Row(equal_height=True):
            pw_in = gr.Textbox(label="진단할 비밀번호", type="password", scale=5,
                               placeholder="비밀번호를 입력하세요")
            btn_show = gr.Button("👁 보기", scale=1, min_width=96)
        pw_visible = gr.State(False)

        def toggle_pw(visible):
            visible = not visible
            return (visible,
                    gr.update(type="text" if visible else "password"),
                    gr.update(value="🙈 숨기기" if visible else "👁 보기"))

        btn_show.click(toggle_pw, pw_visible, [pw_visible, pw_in, btn_show])
        btn_diag = gr.Button("진단하기", variant="primary", size="lg", elem_id="btn_diag")
        diag_out = html(elem_id="diag_out")
        summary_state = gr.State()
        btn_diag.click(on_diagnose, pw_in, [diag_out, summary_state])
        pw_in.submit(on_diagnose, pw_in, [diag_out, summary_state])

        html(ui.section(2, "더 안전한 비밀번호 만들기",
                        "기억하기 쉬운 단어를 넣으면 알고리즘이 후보를 만들고, AI 코치가 방법을 설명합니다."))
        kw_in = gr.Textbox(label="기억하기 쉬운 단어 2~3개", placeholder="예: 제주, 고양이, 자전거")
        with gr.Row():
            btn_suggest = gr.Button("추천 비밀번호 받기", variant="primary")
            btn_coach = gr.Button("AI 코치에게 물어보기", elem_id="btn_coach")
        suggest_out = html()
        coach_out = gr.Markdown(visible=False, elem_classes="lg-md")
        btn_suggest.click(on_suggest, [pw_in, kw_in], suggest_out)
        btn_coach.click(on_coach, [summary_state, kw_in], coach_out)

    with gr.Tab("타이핑 패턴 등록"):
        html(ui.section(3, "내 타이핑 리듬 등록",
                        f"입력칸에 <code>{config.CMU_PASSWORD}</code> 입력 → "
                        '<span class="lg-kbd">Enter</span> → [샘플 저장]. 평소처럼 10회 이상 반복하세요.'))
        en_pw = gr.Textbox(label="비밀번호 입력", type="password", elem_id="ks_enroll")
        en_ev = gr.Textbox(visible=False)
        en_samples = gr.State([])
        btn_add = gr.Button("샘플 저장", variant="primary")
        en_msg = html()
        btn_add.click(on_enroll_add, [en_pw, en_ev, en_samples], [en_pw, en_msg, en_samples],
                      js=take_events_js("ks_enroll"))
        sens = gr.Slider(1.0, 5.0, value=2.0, step=0.5,
                         label="허용 범위 (클수록 관대함, 작을수록 엄격함)")
        btn_train = gr.Button("등록 완료 · 내 패턴 학습")
        train_msg = html()
        btn_train.click(on_enroll_train, [en_samples, sens], train_msg)
        html(ui.note("공개 데이터(CMU, 51명)와 같은 비밀번호로 모델을 검증했기 때문에 시연도 같은 비밀번호를 "
                     "씁니다. 실제 서비스에서는 사용자 자신의 비밀번호로 등록합니다."))

    with gr.Tab("로그인"):
        html(ui.section(3, "타이핑 패턴 2차 인증",
                        "비밀번호가 맞아도 입력 리듬이 등록된 패턴과 다르면 차단합니다. "
                        '입력 후 <span class="lg-kbd">Enter</span> 를 누르고 [로그인]을 눌러주세요.'))
        target = gr.Radio(["내가 등록한 패턴", "CMU 데모 사용자(s002)"],
                          value="내가 등록한 패턴", label="로그인할 계정")
        lg_pw = gr.Textbox(label="비밀번호", type="password", elem_id="ks_login")
        lg_ev = gr.Textbox(visible=False)
        btn_login = gr.Button("로그인", variant="primary", size="lg")
        lg_out = html()
        lg_alert = gr.Markdown(visible=False, elem_classes="lg-md")
        btn_login.click(on_login, [lg_pw, lg_ev, target], [lg_pw, lg_out, lg_alert],
                        js="""(pw, ev, t) => {
                          const store = window.__ks || {};
                          const data = JSON.stringify(store['ks_login'] || []);
                          if (window.__ks) window.__ks['ks_login'] = [];
                          return [pw, data, t];
                        }""")

    with gr.Tab("공개 데이터 시연"):
        html(ui.section(3, "같은 비밀번호, 다른 사람",
                        "51명이 같은 비밀번호를 입력한 공개 데이터로 학습한 모델이, "
                        "비밀번호를 알아낸 다른 사람을 구별하는지 보여줍니다."))
        with gr.Row():
            b1 = gr.Button("계정 주인이 로그인", variant="primary")
            b2 = gr.Button("비밀번호를 훔친 사람이 로그인")
        demo_out = html()
        demo_alert = gr.Markdown(visible=False, elem_classes="lg-md")
        b1.click(lambda: on_demo_sample("본인"), None, [demo_out, demo_alert])
        b2.click(lambda: on_demo_sample("타인"), None, [demo_out, demo_alert])

    demo.load(None, None, None, js=KEY_LISTENER_JS)


if __name__ == "__main__":
    share = os.getenv("SHARE", "1") == "1"
    extra = {k: v for k, v in _supported(demo.launch, STYLE).items()}
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)), share=share,
                **extra)