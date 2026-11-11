"""LoginGuard AI 화면 디자인: 스타일(CSS)과 결과 카드(HTML)를 만드는 함수 모음.

Gradio 버전에 상관없이 적용되도록 CSS는 화면 맨 위 HTML 안에 <style>로 넣는다.
"""
import re
from html import escape

FONT = ('"Pretendard Variable", Pretendard, "Noto Sans KR", -apple-system, "Segoe UI", '
        '"Malgun Gothic", sans-serif')
MONO = '"JetBrains Mono", "D2Coding", Consolas, ui-monospace, monospace'

CSS = """
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600&display=swap");

:root, body, .gradio-container, .dark, .dark .gradio-container {
  --lg-ink: #0b1220;
  --lg-ink-2: #16213a;
  --lg-paper: #f4f5f8;
  --lg-card: #ffffff;
  --lg-line: #e4e7ee;
  --lg-text: #0f172a;
  --lg-muted: #64748b;
  --lg-accent: #4057ff;
  --lg-accent-soft: #eef1ff;
  --lg-ok: #0f9d6b;
  --lg-ok-soft: #e8f7f1;
  --lg-warn: #d98209;
  --lg-warn-soft: #fff5e3;
  --lg-danger: #dc3b45;
  --lg-danger-soft: #fdecee;

  --body-background-fill: var(--lg-paper);
  --background-fill-primary: var(--lg-card);
  --background-fill-secondary: var(--lg-paper);
  --body-text-color: var(--lg-text);
  --body-text-color-subdued: var(--lg-muted);
  --block-background-fill: var(--lg-card);
  --block-border-color: var(--lg-line);
  --block-border-width: 1px;
  --block-radius: 14px;
  --block-shadow: 0 1px 2px rgba(15, 23, 42, .04);
  --block-label-text-color: var(--lg-muted);
  --block-title-text-color: #334155;
  --block-title-text-weight: 600;
  --border-color-primary: var(--lg-line);
  --input-background-fill: #fbfbfd;
  --input-border-color: var(--lg-line);
  --input-border-color-focus: var(--lg-accent);
  --input-shadow-focus: 0 0 0 3px rgba(64, 87, 255, .15);
  --input-radius: 10px;
  --input-text-size: 16px;
  --color-accent: var(--lg-accent);
  --color-accent-soft: var(--lg-accent-soft);
  --slider-color: var(--lg-accent);
  --button-large-radius: 12px;
  --button-small-radius: 10px;
  --button-large-text-weight: 600;
  --button-primary-background-fill: var(--lg-ink);
  --button-primary-background-fill-hover: var(--lg-ink-2);
  --button-primary-text-color: #ffffff;
  --button-primary-border-color: var(--lg-ink);
  --button-primary-border-color-hover: var(--lg-ink-2);
  --button-secondary-background-fill: #ffffff;
  --button-secondary-background-fill-hover: #f1f3f8;
  --button-secondary-text-color: var(--lg-text);
  --button-secondary-border-color: var(--lg-line);
}

body { background: var(--lg-paper) !important; }
.gradio-container {
  max-width: 980px !important; margin: 0 auto !important; padding: 28px 20px 56px !important;
  font-family: __FONT__ !important; color: var(--lg-text);
}
.gradio-container button, .gradio-container input, .gradio-container textarea,
.gradio-container label { font-family: __FONT__ !important; }
footer { display: none !important; }

/* 내가 만든 HTML 블록은 테두리 없이 */
.lg-plain { padding: 0 !important; border: none !important; background: transparent !important;
            box-shadow: none !important; }

/* 내 카드 안의 글자는 부모 색을 따르게 (Gradio 기본 글자색 차단). 아래 규칙들이 이 위에 덮어쓴다 */
.lg-hero *, .lg-sec *, .lg-result *, .lg-sug *, .lg-note *, .lg-foot { color: inherit; }

/* 탭 */
.gradio-container [role="tablist"] { gap: 4px; border-bottom: 1px solid var(--lg-line); }
.gradio-container button[role="tab"] {
  font-size: 15px !important; font-weight: 600 !important; padding: 12px 16px !important;
  color: var(--lg-muted) !important; background: transparent !important;
}
.gradio-container button[role="tab"][aria-selected="true"] { color: var(--lg-ink) !important; }
.gradio-container [role="tabpanel"] {
  border: none !important; background: transparent !important; padding: 22px 0 0 !important;
}

/* 버튼 */
.gradio-container button.primary {
  box-shadow: 0 6px 16px -6px rgba(11, 18, 32, .55); letter-spacing: -.01em;
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.gradio-container button.primary:hover { transform: translateY(-1px); }
.gradio-container button.secondary { transition: background .12s ease; }
.gradio-container button:focus-visible { outline: 3px solid rgba(64, 87, 255, .35); outline-offset: 2px; }
.gradio-container input[type="password"], .gradio-container input[type="text"] {
  letter-spacing: .02em;
}

/* 히어로 */
.lg-hero {
  position: relative; overflow: hidden; border-radius: 22px; padding: 34px 36px 30px;
  color: #e6ebf7; margin-bottom: 6px;
  background:
    radial-gradient(520px 260px at 88% -10%, rgba(64, 87, 255, .55), transparent 70%),
    radial-gradient(420px 240px at 8% 120%, rgba(20, 184, 166, .28), transparent 70%),
    linear-gradient(140deg, #0b1220 0%, #121b33 60%, #0d1528 100%);
  box-shadow: 0 24px 48px -28px rgba(11, 18, 32, .7);
}
.lg-hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .5;
  background-image: linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px);
  background-size: 32px 32px;
  -webkit-mask-image: linear-gradient(180deg, #000, transparent 85%);
          mask-image: linear-gradient(180deg, #000, transparent 85%);
}
.lg-hero > * { position: relative; z-index: 1; }
.lg-brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px;
            letter-spacing: .01em; color: #ffffff; }
.lg-brand svg { width: 26px; height: 26px; }
.lg-tag { margin-left: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;
          color: #c7d2fe; background: rgba(129, 140, 248, .16); border: 1px solid rgba(165, 180, 252, .28); }
.lg-hero h1 {
  margin: 22px 0 10px !important; font-size: 34px !important; line-height: 1.22 !important;
  font-weight: 750 !important; letter-spacing: -.03em !important; color: #ffffff !important;
  text-wrap: balance;
}
.lg-hero p.lg-lead { margin: 0 !important; max-width: 560px; font-size: 15.5px !important;
                     line-height: 1.65 !important; color: #b6c0d8 !important; }
.lg-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 26px; }
.lg-step { padding: 14px 16px; border-radius: 14px; background: rgba(255, 255, 255, .055);
           border: 1px solid rgba(255, 255, 255, .1); backdrop-filter: blur(6px); }
.lg-step b { display: block; font-size: 14.5px; font-weight: 650; color: #ffffff; margin-bottom: 3px; }
.lg-step span { font-size: 13px; color: #a9b4cf; line-height: 1.5; }
.lg-step i { display: inline-grid; place-items: center; width: 22px; height: 22px; margin-right: 8px;
             border-radius: 7px; font-style: normal; font-size: 12px; font-weight: 700;
             color: #0b1220; background: #ffffff; }
.lg-privacy { display: inline-flex; align-items: center; gap: 8px; margin-top: 20px; font-size: 13px;
              color: #9fe8d2; }
.lg-privacy svg { width: 15px; height: 15px; }

/* 섹션 제목 */
.lg-sec { display: flex; align-items: flex-start; gap: 12px; margin: 26px 0 4px; }
.lg-sec:first-child { margin-top: 4px; }
.lg-num { flex: none; display: grid; place-items: center; width: 30px; height: 30px; border-radius: 10px;
          font-size: 14px; font-weight: 700; color: #fff; background: var(--lg-ink); }
.lg-sec h3 { margin: 2px 0 2px !important; font-size: 18px !important; font-weight: 700 !important;
             letter-spacing: -.02em !important; color: var(--lg-text) !important; }
.lg-sec p { margin: 0 !important; font-size: 14px !important; color: var(--lg-muted) !important;
            line-height: 1.55 !important; }
.lg-sec code, .lg-kbd { font-family: __MONO__; font-size: 13px; padding: 2px 7px; border-radius: 6px;
            background: #eef0f6; color: var(--lg-ink); border: 1px solid var(--lg-line); }

/* 결과 카드 */
.lg-result { border-radius: 16px; padding: 22px 24px; background: var(--lg-card);
             border: 1px solid var(--lg-line); box-shadow: 0 10px 30px -22px rgba(15, 23, 42, .35);
             --tone: var(--lg-muted); --tone-soft: #f1f3f8; }
.lg-result.ok { --tone: var(--lg-ok); --tone-soft: var(--lg-ok-soft); }
.lg-result.warn { --tone: var(--lg-warn); --tone-soft: var(--lg-warn-soft); }
.lg-result.danger { --tone: var(--lg-danger); --tone-soft: var(--lg-danger-soft); }
.lg-result { border-top: 3px solid var(--tone); }
.lg-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; }
.lg-eyebrow { font-size: 12.5px; font-weight: 600; letter-spacing: .04em; color: var(--lg-muted); }
.lg-level { display: flex; align-items: center; gap: 10px; margin-top: 4px; font-size: 26px;
            font-weight: 750; letter-spacing: -.03em; color: var(--lg-text); }
.lg-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--tone);
          box-shadow: 0 0 0 5px var(--tone-soft); }
.lg-score { text-align: right; line-height: 1; }
.lg-score b { font-size: 40px; font-weight: 750; letter-spacing: -.04em; color: var(--tone);
              font-variant-numeric: tabular-nums; }
.lg-score small { font-size: 18px; font-weight: 650; color: var(--tone); margin-left: 2px; }
.lg-score span { display: block; margin-top: 6px; font-size: 12.5px; color: var(--lg-muted); }
.lg-gauge { position: relative; height: 10px; margin-top: 18px; border-radius: 999px; background: #edf0f5; }
.lg-gauge > div { height: 100%; border-radius: 999px; background: var(--tone); min-width: 10px;
                  transition: width .5s cubic-bezier(.2, .8, .2, 1); }
.lg-gauge::before, .lg-gauge::after { content: ""; position: absolute; top: -3px; bottom: -3px; width: 2px;
                  background: #fff; border-radius: 2px; }
.lg-gauge::before { left: 40%; } .lg-gauge::after { left: 70%; }
.lg-scale { display: grid; grid-template-columns: 40% 30% 30%; margin-top: 7px; font-size: 12px;
            color: #94a3b8; }
.lg-scale span:nth-child(2) { padding-left: 6px; } .lg-scale span:nth-child(3) { padding-left: 6px; }
.lg-reasons { list-style: none; margin: 18px 0 0 !important; padding: 0 !important; display: grid; gap: 8px; }
.lg-reasons li { display: flex; gap: 10px; align-items: flex-start; margin: 0 !important;
                 padding: 11px 14px; border-radius: 11px; font-size: 14.5px; line-height: 1.55;
                 color: #1e293b; background: var(--tone-soft); }
.lg-reasons li::before { content: ""; flex: none; width: 6px; height: 6px; margin-top: 9px;
                 border-radius: 50%; background: var(--tone); }
.lg-meta { margin-top: 16px; font-size: 12.5px; color: #94a3b8; }

/* 추천 카드 */
.lg-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.lg-sug { padding: 16px 18px; border-radius: 14px; background: var(--lg-card);
          border: 1px solid var(--lg-line); }
.lg-sug-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.lg-sug-top b { font-size: 14.5px; font-weight: 650; color: var(--lg-text); }
.lg-pill { flex: none; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 650;
           color: var(--lg-ok); background: var(--lg-ok-soft); }
.lg-pill.warn { color: var(--lg-warn); background: var(--lg-warn-soft); }
.lg-pill.danger { color: var(--lg-danger); background: var(--lg-danger-soft); }
.lg-pw { margin: 12px 0 10px; padding: 12px 14px; border-radius: 10px; font-family: __MONO__;
         font-size: 15px; font-weight: 600; color: #e8ecff; background: var(--lg-ink);
         overflow-wrap: anywhere; user-select: all; letter-spacing: .01em; }
.lg-sug p { margin: 0 !important; font-size: 13px !important; color: var(--lg-muted) !important;
            line-height: 1.5 !important; }
.lg-foot { margin-top: 12px; font-size: 12.5px; color: #94a3b8; }

/* 알림, 진행률 */
.lg-note { display: flex; gap: 10px; align-items: flex-start; padding: 13px 16px; border-radius: 12px;
           font-size: 14.5px; line-height: 1.55; color: #1e293b; background: #f1f3f8;
           border: 1px solid var(--lg-line); }
.lg-note.ok { background: var(--lg-ok-soft); border-color: #c9ecdf; }
.lg-note.danger { background: var(--lg-danger-soft); border-color: #f8cdd1; }
.lg-note b { font-weight: 650; }
.lg-progress { margin-top: 10px; height: 8px; border-radius: 999px; background: #e6e9f0; overflow: hidden; }
.lg-progress > div { height: 100%; border-radius: 999px; background: var(--lg-ok); transition: width .3s ease; }

/* 타이핑 점수 막대 */
.lg-meter { position: relative; height: 12px; margin: 22px 0 8px; border-radius: 999px;
            background: linear-gradient(90deg, #cfeee2 0 50%, #f9d3d6 50% 100%); }
.lg-meter i { position: absolute; top: 50%; width: 18px; height: 18px; border-radius: 50%;
              background: var(--tone); border: 3px solid #fff; transform: translate(-50%, -50%);
              box-shadow: 0 2px 8px rgba(15, 23, 42, .3); }
.lg-meter::after { content: ""; position: absolute; left: 50%; top: -6px; bottom: -6px; width: 2px;
              background: var(--lg-ink); border-radius: 2px; }
.lg-meter-legend { display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; }
.lg-kv { display: flex; gap: 22px; margin-top: 14px; font-size: 13.5px; color: var(--lg-muted); }
.lg-kv b { color: var(--lg-text); font-variant-numeric: tabular-nums; }

/* LLM 답변 카드 */
.lg-md { padding: 18px 22px !important; border-radius: 14px !important; background: var(--lg-card) !important;
         border: 1px solid var(--lg-line) !important; border-left: 3px solid var(--lg-accent) !important; }
.lg-md, .lg-md p, .lg-md li { font-size: 15px; line-height: 1.7; }

/* 말풍선 */
.lg-bubble {
  position: absolute; z-index: 9999; transform: translate(-50%, -100%); white-space: nowrap;
  padding: 11px 16px; border-radius: 12px; font-family: __FONT__; font-size: 14.5px; font-weight: 650;
  letter-spacing: -.01em; color: #ffffff; background: #0b1220;
  box-shadow: 0 14px 30px -10px rgba(11, 18, 32, .55);
  animation: lg-pop .22s cubic-bezier(.2, .9, .3, 1.3); transition: opacity .3s ease; pointer-events: none;
}
.lg-bubble::after { content: ""; position: absolute; left: 50%; bottom: -6px; width: 12px; height: 12px;
  background: #0b1220; transform: translateX(-50%) rotate(45deg); border-radius: 2px; }
.lg-bubble.lg-out { opacity: 0; }
@keyframes lg-pop { from { opacity: 0; transform: translate(-50%, -85%) scale(.92); }
                    to { opacity: 1; transform: translate(-50%, -100%) scale(1); } }
.lg-pulse { animation: lg-ring 1.1s ease-out 2; }
@keyframes lg-ring { 0% { box-shadow: 0 0 0 0 rgba(64, 87, 255, .55); }
                     100% { box-shadow: 0 0 0 14px rgba(64, 87, 255, 0); } }

@media (max-width: 720px) {
  .lg-hero { padding: 26px 22px; } .lg-hero h1 { font-size: 26px !important; }
  .lg-steps, .lg-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .gradio-container * { transition: none !important; }
  .lg-bubble, .lg-pulse { animation: none !important; }
}
""".replace("__FONT__", FONT).replace("__MONO__", MONO)

# Gradio 기본 스타일이 글자색을 덮어쓰지 못하도록 모든 글자색에 !important를 붙인다
CSS = re.sub(r"(?<![-\w])color:\s*([^;!}]+);", r"color: \1 !important;", CSS)

_SHIELD = ('<svg viewBox="0 0 24 24" fill="none"><path d="M12 2.5 4 5.6v6.1c0 4.7 3.3 8.3 8 9.8 '
           '4.7-1.5 8-5.1 8-9.8V5.6l-8-3.1Z" fill="#4057ff"/><path d="m8.6 12.2 2.4 2.4 4.6-4.9" '
           'stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
_LOCK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round"><rect x="5" y="11" width="14" height="9" rx="2"/>'
         '<path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>')

_TONE = {"안전": "ok", "주의": "warn", "위험": "danger"}


def hero() -> str:
    return f"""<style>{CSS}</style>
<div class="lg-hero">
  <div class="lg-brand">{_SHIELD} LoginGuard AI <span class="lg-tag">Deep Learning × LLM</span></div>
  <h1>기억하기 쉬운 비밀번호,<br>유출돼도 뚫리지 않는 로그인</h1>
  <p class="lg-lead">비밀번호를 까먹어서 쉬운 걸 쓰고, 여러 곳에 돌려 쓰게 됩니다.
  AI가 약점을 진단하고, 외우기 쉬운 강한 비밀번호를 제안하고, 타이핑 리듬으로 본인만 통과시킵니다.</p>
  <div class="lg-steps">
    <div class="lg-step"><b><i>1</i>위험도 진단</b><span>딥러닝이 추측되기 쉬운 패턴을 찾습니다</span></div>
    <div class="lg-step"><b><i>2</i>AI 보안 코치</b><span>외우기 쉬운 강한 비밀번호를 제안합니다</span></div>
    <div class="lg-step"><b><i>3</i>타이핑 패턴 인증</b><span>비밀번호가 맞아도 리듬이 다르면 차단합니다</span></div>
  </div>
  <div class="lg-privacy">{_LOCK} 비밀번호 원문은 AI(LLM)에 전송되지 않습니다</div>
</div>"""


def section(num, title: str, desc: str = "") -> str:
    """desc에는 내가 쓴 HTML만 넣는다 (사용자 입력 금지)."""
    return (f'<div class="lg-sec"><span class="lg-num">{num}</span>'
            f'<div><h3>{title}</h3><p>{desc}</p></div></div>')


def note(text: str, tone: str = "") -> str:
    """text에는 내가 쓴 HTML만 넣는다."""
    return f'<div class="lg-note {tone}"><div>{text}</div></div>'


def diagnosis_card(d: dict) -> str:
    pct = round(d["risk"] * 100)
    tone = _TONE[d["level"]]
    reasons = d["reasons"] or ["특별한 약점이 발견되지 않았어요."]
    items = "".join(f"<li>{escape(r)}</li>" for r in reasons)
    engine = "딥러닝 BiLSTM + 규칙 분석" if d["used_model"] else "규칙 분석 (학습된 모델 파일 없음)"
    return f"""<div class="lg-result {tone}">
  <div class="lg-head">
    <div><div class="lg-eyebrow">진단 결과</div>
      <div class="lg-level"><span class="lg-dot"></span>{d['level']}</div></div>
    <div class="lg-score"><b>{pct}</b><small>%</small><span>위험도</span></div>
  </div>
  <div class="lg-gauge"><div style="width:{max(pct, 2)}%"></div></div>
  <div class="lg-scale"><span>안전</span><span>주의</span><span>위험</span></div>
  <ul class="lg-reasons">{items}</ul>
  <div class="lg-meta">판정 엔진 · {engine}</div>
</div>"""


def suggestion_cards(items: list) -> str:
    cards = []
    for it in items:
        pct = round(it["risk"] * 100)
        tone, label = ("", "안전") if it["risk"] < 0.4 else (("warn", "주의") if it["risk"] < 0.7
                                                            else ("danger", "위험"))
        cards.append(f"""<div class="lg-sug">
  <div class="lg-sug-top"><b>{escape(it['title'])}</b><span class="lg-pill {tone}">{label} · 위험도 {pct}%</span></div>
  <div class="lg-pw">{escape(it['password'])}</div>
  <p>{escape(it['tip'])}</p>
</div>""")
    return (f'<div class="lg-grid">{"".join(cards)}</div>'
            '<div class="lg-foot">이 기기 안에서 만들고 진단 모델로 다시 검사했습니다. AI(LLM)에는 전송되지 않습니다. '
            '버튼을 다시 누르면 새로운 추천이 나옵니다.</div>')


def enroll_progress(count: int, goal: int = 10) -> str:
    pct = min(100, round(count / goal * 100))
    msg = (f"<b>{count}번째 샘플 저장</b> · {goal}회 이상 권장" if count < goal
           else f"<b>{count}개 저장 완료</b> · 이제 [등록 완료]를 눌러주세요")
    return (f'<div class="lg-note ok"><div style="flex:1">{msg}'
            f'<div class="lg-progress"><div style="width:{pct}%"></div></div></div></div>')


def login_card(ok: bool, score: float, threshold: float, title: str = "", sub: str = "") -> str:
    tone = "ok" if ok else "danger"
    pos = max(3.0, min(97.0, score / (threshold * 2) * 100)) if threshold > 0 else 50
    head = title or ("로그인 성공" if ok else "로그인 차단")
    sub_html = f'<div class="lg-meta" style="margin-top:6px">{escape(sub)}</div>' if sub else ""
    return f"""<div class="lg-result {tone}">
  <div class="lg-head">
    <div><div class="lg-eyebrow">2차 인증 · 타이핑 패턴</div>
      <div class="lg-level"><span class="lg-dot"></span>{escape(head)}</div>{sub_html}</div>
    <div class="lg-score"><b>{score:.2f}</b><span>리듬 차이 점수</span></div>
  </div>
  <div class="lg-meter"><i style="left:{pos:.1f}%"></i></div>
  <div class="lg-meter-legend"><span>평소와 같음</span><span>허용 기준</span><span>평소와 다름</span></div>
  <div class="lg-kv"><span>이번 입력 <b>{score:.3f}</b></span><span>허용 기준 <b>{threshold:.3f}</b></span>
    <span>판정 <b>{'본인으로 확인' if ok else '본인이 아닐 가능성'}</b></span></div>
</div>"""