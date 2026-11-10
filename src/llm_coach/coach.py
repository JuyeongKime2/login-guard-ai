"""② LLM 보안 코치: 프롬프트 설계.

개인정보 보호 원칙
- 비밀번호 원문은 절대 보내지 않는다. 진단 결과(참/거짓, 길이, 점수)만 보낸다.
- 타이핑 인증도 점수와 판정 결과만 보낸다.
"""
import json

from .client import generate

SYSTEM = (
    "당신은 일반인을 돕는 친절한 계정 보안 코치입니다. "
    "주어진 진단 결과만 근거로 설명하고 과장하지 마세요. "
    "한국어로, 짧고 쉬운 문장으로 답하세요. 마크다운 사용 가능."
)

FLAG_KO = {
    "length": "길이", "n_classes": "문자 종류 수", "is_common": "흔한 비밀번호 목록 포함",
    "contains_common_word": "흔한 단어/이름 포함", "keyboard_pattern": "키보드 패턴",
    "sequential": "연속 문자", "repeated": "반복 문자", "date_like": "날짜/연도 형태",
    "risk_score": "AI 위험도(0~1)", "level": "판정",
}


def password_coach(llm_summary: dict, keywords: str) -> tuple:
    facts = {FLAG_KO[k]: v for k, v in llm_summary.items() if k in FLAG_KO}
    prompt = f"""[비밀번호 진단 결과 - 원문은 보안상 제공되지 않음]
{json.dumps(facts, ensure_ascii=False, indent=1)}

[사용자가 기억하기 쉬운 단어] {keywords or "(없음)"}

다음 순서로 답하세요.
1. 이 비밀번호가 왜 위험(또는 안전)한지 2~3줄
2. 기억하기 쉬우면서 강한 '문장형 비밀번호' 만드는 방법 (사용자 단어 활용, 서로 관련 없는 단어 3개 이상 + 숫자/기호 섞기)
3. 방법을 보여주는 예시 2개 (예시는 그대로 쓰지 말고 자기만의 방식으로 바꾸라고 안내)
4. 사이트마다 다른 비밀번호를 쓰는 간단한 요령 1가지
전체 12줄 이내."""
    fallback = (
        "**AI 코치 연결이 안 되어 기본 안내를 보여드려요.**\n\n"
        "- 서로 관련 없는 단어 3~4개를 이어 붙이면 길고 기억하기 쉬운 비밀번호가 됩니다.\n"
        "- 단어 사이에 기호를, 중간에 숫자를 넣으세요. 예: `구름.자전거7.라면` 방식을 영문으로\n"
        "- 생일, 이름, 전화번호, qwer·1234 같은 패턴은 빼세요.\n"
        "- 사이트마다 끝에 사이트별 규칙(예: 사이트 이름 첫 글자 2개)을 붙여 재사용을 피하세요."
    )
    return generate(prompt, SYSTEM, fallback)


def login_alert(result: dict) -> tuple:
    prompt = f"""[로그인 2차 인증(타이핑 패턴) 결과]
{json.dumps(result, ensure_ascii=False, indent=1)}

score는 평소 타이핑 리듬과의 차이(클수록 다름), threshold는 허용 기준입니다.
사용자에게 보낼 보안 알림을 4~6줄로 작성하세요.
- 통과면: 정상 로그인 확인 + 짧은 보안 팁
- 차단이면: 비밀번호는 맞았지만 입력 리듬이 평소와 달라 차단했다는 설명,
  본인이면 할 일(다시 시도, 추가 인증), 본인이 아니면 할 일(비밀번호 변경, 다른 사이트 비밀번호도 확인)"""
    if result.get("decision") == "통과":
        fallback = "✅ **정상 로그인입니다.** 평소 타이핑 리듬과 일치합니다."
    else:
        fallback = (
            "🚫 **로그인이 차단되었습니다.** 비밀번호는 맞았지만 입력 리듬이 평소와 달랐어요.\n\n"
            "- 본인이라면: 평소처럼 편하게 다시 입력하거나 추가 인증을 진행하세요.\n"
            "- 본인이 아니라면: 비밀번호가 유출됐을 수 있습니다. 즉시 변경하고, "
            "같은 비밀번호를 쓰는 다른 사이트도 바꾸세요."
        )
    return generate(prompt, SYSTEM, fallback)
