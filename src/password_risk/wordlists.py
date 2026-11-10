"""학습 데이터 생성용 단어 목록.

실제 유출 비밀번호 DB는 개인정보이므로 사용하지 않는다.
대신 각종 보안 보고서에 반복적으로 등장하는 '흔한 비밀번호 유형'과
흔한 단어를 직접 정리해서, 변형 규칙으로 위험 비밀번호를 합성한다.
"""

# 그대로 쓰면 매우 위험한 대표 비밀번호
COMMON_PASSWORDS = [
    "123456", "123456789", "12345678", "1234567", "12345", "1234567890",
    "password", "password1", "qwerty", "qwerty123", "111111", "000000",
    "123123", "abc123", "iloveyou", "admin", "admin123", "welcome",
    "letmein", "monkey", "dragon", "sunshine", "princess", "football",
    "baseball", "master", "shadow", "superman", "1q2w3e4r", "1q2w3e4r5t",
    "qwer1234", "asdf1234", "1qaz2wsx", "zxcvbnm", "asdfgh", "qazwsx",
    "654321", "666666", "888888", "121212", "aaaaaa", "passw0rd",
    "p@ssw0rd", "test1234", "guest", "login", "korea123", "sarang123",
]

# 변형해서 위험 비밀번호를 만들 기본 단어 (train / test로 나눠 일반화 평가)
BASE_WORDS = [
    "love", "sarang", "saranghae", "korea", "seoul", "busan", "happy",
    "angel", "dragon", "tiger", "monkey", "puppy", "kitty", "cookie",
    "summer", "winter", "spring", "flower", "star", "moon", "sun",
    "music", "game", "soccer", "baseball", "school", "family", "mother",
    "father", "baby", "honey", "sweet", "candy", "apple", "banana",
    "orange", "coffee", "pizza", "chicken", "samsung", "naver", "kakao",
    "google", "hello", "admin", "user", "test", "pass", "secret", "lucky",
    "minjun", "seoyeon", "jiwoo", "hayoon", "doyun", "seojun", "jimin",
    "minsu", "younghee", "chulsoo", "jihoon", "sujin", "hyunwoo", "yuna",
    "princess", "prince", "king", "queen", "hero", "power", "magic",
    "jesus", "michael", "jennifer", "thomas", "charlie", "daniel",
]

# 안전한 문장형 비밀번호(패스프레이즈) 합성용 단어
SAFE_WORDS = [
    "maple", "orbit", "tundra", "violet", "canyon", "harbor", "pepper",
    "lantern", "glacier", "meadow", "copper", "falcon", "velvet", "summit",
    "thistle", "ember", "quartz", "willow", "pebble", "cobalt", "saffron",
    "juniper", "marble", "nimbus", "otter", "prairie", "raven", "sequoia",
    "timber", "umber", "walrus", "yarrow", "zephyr", "basil", "cedar",
    "dune", "fjord", "garnet", "heron", "indigo", "jasper", "kelp",
    "lagoon", "mosaic", "nectar", "obsidian", "pylon", "quill", "ripple",
    "sorrel", "trellis", "upland", "vortex", "wren", "yodel", "zircon",
]

KEYBOARD_WALKS = [
    "qwerty", "qwer", "asdf", "asdfgh", "zxcv", "zxcvbn", "1q2w3e4r",
    "1qaz2wsx", "qazwsx", "!@#$", "!@#$%^", "1234qwer", "qwer1234",
    "asdf1234", "poiuy", "lkjhg", "mnbvc", "qweasd", "wasd",
]


def split_words(words, test_ratio=0.25):
    """앞쪽은 학습용, 뒤쪽은 평가용. 평가 단어는 학습 때 한 번도 안 나옴."""
    k = int(len(words) * (1 - test_ratio))
    return words[:k], words[k:]
