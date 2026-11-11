"""② 무료 LLM 연결: Gemini → (실패 시) Groq → (둘 다 실패 시) 오프라인 안내문.

API 키는 환경변수로만 받는다. 코드나 GitHub에 키를 적지 말 것.
  GEMINI_API_KEY : https://aistudio.google.com 에서 무료 발급
  GROQ_API_KEY   : https://console.groq.com/keys 에서 무료 발급
모델명은 무료 목록이 자주 바뀌므로 환경변수로 바꿀 수 있게 했다.
"""
import os

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _gemini(prompt, system):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    res = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system,
                                           temperature=0.7, max_output_tokens=900),
    )
    return res.text


def _groq(prompt, system):
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    res = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=900,
    )
    return res.choices[0].message.content


def generate(prompt: str, system: str, fallback: str):
    """(답변, 사용한 제공자) 반환. 발표 중 API가 막혀도 앱이 멈추지 않게 한다."""
    errors = []
    if os.getenv("GEMINI_API_KEY"):
        try:
            text = _gemini(prompt, system)
            if text:
                return text, f"Gemini ({GEMINI_MODEL})"
        except Exception as e:
            errors.append(f"Gemini: {type(e).__name__}")
    if os.getenv("GROQ_API_KEY"):
        try:
            text = _groq(prompt, system)
            if text:
                return text, f"Groq ({GROQ_MODEL})"
        except Exception as e:
            errors.append(f"Groq: {type(e).__name__}")
    note = " / ".join(errors) if errors else "API 키 없음"
    return fallback, f"오프라인 안내문 ({note})"
