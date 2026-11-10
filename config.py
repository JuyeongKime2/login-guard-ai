"""프로젝트 전역 설정 (경로, 상수)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
for _d in (DATA_DIR, MODEL_DIR, REPORT_DIR):
    _d.mkdir(exist_ok=True)

# ---------- ① 비밀번호 위험도 진단 ----------
PW_MAX_LEN = 32
PW_MODEL_PATH = MODEL_DIR / "password_risk.pt"

# ---------- ③ 타이핑 패턴 (CMU Keystroke Benchmark) ----------
CMU_URL = "https://www.cs.cmu.edu/~keystroke/DSL-StrongPasswordData.csv"
CMU_CSV = DATA_DIR / "DSL-StrongPasswordData.csv"
CMU_PASSWORD = ".tie5Roanl"
# 브라우저 KeyboardEvent.code 기준. CMU 컬럼 순서와 같음 (마지막은 Enter = Return)
KEY_CODES = ["Period", "KeyT", "KeyI", "KeyE", "Digit5", "KeyR",
             "KeyO", "KeyA", "KeyN", "KeyL", "Enter"]
DEMO_SUBJECT = "s002"
KS_DEMO_PATH = MODEL_DIR / "keystroke_demo.pt"
KS_DEMO_SAMPLES = MODEL_DIR / "keystroke_demo_samples.npz"
