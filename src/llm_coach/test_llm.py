"""API 키가 잘 작동하는지 확인. 실행: python -m src.llm_coach.test_llm"""
from .coach import password_coach

if __name__ == "__main__":
    demo = {"length": 8, "n_classes": 2, "is_common": False, "contains_common_word": True,
            "keyboard_pattern": False, "sequential": False, "repeated": False,
            "date_like": True, "risk_score": 0.91, "level": "위험"}
    text, provider = password_coach(demo, "제주, 고양이, 자전거")
    print("사용한 LLM:", provider)
    print(text)
