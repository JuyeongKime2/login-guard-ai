# 🔐 LoginGuard AI

**"비밀번호를 까먹는 사람들을 위한 AI 로그인 보안 서비스"**

사람들은 비밀번호를 까먹기 때문에 쉬운 비밀번호를 쓰고, 여러 사이트에 재사용합니다.
그래서 한 곳만 유출돼도 다른 계정까지 연쇄로 털립니다.
LoginGuard AI는 이 문제를 3단계로 해결합니다.

| 단계 | 기능 | 기술 | 해결하는 문제 |
|---|---|---|---|
| ① | 비밀번호 위험도 진단 | **딥러닝** 문자 단위 BiLSTM | 쉬운 비밀번호 |
| ② | AI 보안 코치 | **LLM** Gemini (실패 시 Groq) | 기억하기 쉬우면서 강한 비밀번호 만들기 |
| ③ | 타이핑 패턴 2차 인증 | **딥러닝** 디노이징 오토인코더 | 비밀번호가 유출돼도 타인 로그인 차단 |

**개인정보 보호 설계**: 비밀번호 원문은 LLM에 절대 보내지 않습니다. 진단 결과(길이, 패턴 여부, 점수)만 보냅니다.

---

## 📁 폴더 구조

```
login-guard-ai/
├── README.md                ← 지금 이 파일 (전체 순서)
├── run_colab.ipynb          ← 코랩에서 위에서부터 차례대로 실행하면 끝
├── requirements.txt
├── config.py                ← 경로, 상수 설정
│
├── src/
│   ├── password_risk/       ← ① 비밀번호 위험도 진단 (딥러닝)
│   │   ├── wordlists.py         흔한 비밀번호·단어 목록
│   │   ├── generator.py         위험/안전 비밀번호 학습 데이터 생성
│   │   ├── rules.py             규칙 분석 (진단 근거 + LLM에 보낼 요약)
│   │   ├── model.py             BiLSTM 모델
│   │   ├── train.py             학습 + 평가 (정확도, F1, 혼동행렬)
│   │   └── predict.py           진단 함수
│   │
│   ├── llm_coach/           ← ② LLM 보안 코치
│   │   ├── client.py            Gemini → Groq → 오프라인 안내문 순서로 자동 전환
│   │   ├── coach.py             프롬프트 (비밀번호 코칭, 로그인 알림)
│   │   └── test_llm.py          API 키 확인용
│   │
│   └── keystroke/           ← ③ 타이핑 패턴 2차 인증 (딥러닝)
│       ├── data.py              CMU 공개 데이터 다운로드/분할
│       ├── capture.py           브라우저 키 입력 → 31개 특징 변환
│       ├── model.py             오토인코더 + 비교용 기준 모델
│       ├── metrics.py           FAR, FRR, EER
│       ├── evaluate.py          51명 전체 성능 평가 (발표 핵심 수치)
│       └── train_demo.py        시연용 모델 저장
│
├── app/app.py               ← Gradio 통합 앱 (탭 4개)
├── data/                    ← CMU 데이터가 여기에 다운로드됨
├── models/                  ← 학습된 모델 저장
├── reports/                 ← 성능 지표, 그래프 (발표 자료에 그대로 사용)
├── tests/test_basic.py      ← 기본 동작 테스트
└── docs/발표_구성.md         ← 발표/PDF 목차와 각 슬라이드 내용
```

---

## 🗓 진행 순서 (월 ~ 금)

### 0. 준비 (주말, 10분)
1. Gemini API 키 발급: https://aistudio.google.com → Get API key
2. Groq API 키 발급(백업): https://console.groq.com/keys
3. 코랩 왼쪽 🔑(Secrets)에 `GEMINI_API_KEY`, `GROQ_API_KEY` 등록 → "노트북 액세스" 켜기

### 1. 월요일: ① 진단 + ② 코치
1. 코랩에 `login-guard-ai.zip` 업로드 → `run_colab.ipynb`의 1~3번 셀 실행 (압축 해제, 설치, 키 설정)
2. **4번 셀**: `python -m src.password_risk.train`
   - 결과: `reports/password_metrics.json`(정확도, F1), `reports/password_confusion.png`
   - 평가 데이터는 학습 때 **한 번도 안 본 단어**로 만든 것 → "처음 보는 비밀번호에도 일반화" 라고 발표
3. **5번 셀**: `python -m src.llm_coach.test_llm` → "사용한 LLM: Gemini ..." 가 나오면 성공
4. 💡 막히면: 모델 없이도 규칙 기반으로 앱은 돌아갑니다

### 2. 화요일: ③ 타이핑 패턴 모델
1. **6번 셀**: `python -m src.keystroke.data` (CMU 데이터 다운로드)
2. **7번 셀**: `python -m src.keystroke.evaluate` (51명 평가, CPU로 몇 분)
   - 결과: `reports/keystroke_summary.json`의 **평균 EER**
   - 비교 기준: 원 논문 최고 성능 EER 9.6~10.2%, 같은 조건의 Manhattan 기준모델도 함께 계산됨
3. **8번 셀**: `python -m src.keystroke.train_demo` (시연용 모델 저장)

### 3. 수요일: 앱 통합 + 배포
1. **9번 셀**: `python app/app.py` → `https://xxxx.gradio.live` 링크 생성 (72시간 유효)
2. 탭별 확인
   - ① 진단: `123456`, `Minsu1998!`, `Orbit-Velvet42-Quartz!` 비교
   - ② 코치: 단어 "제주, 고양이, 자전거" 입력
   - ③-1 등록: `.tie5Roanl` 입력 → Enter → [샘플 저장] × 10회 → [등록 완료]
   - ③-2 로그인: 내가 입력하면 통과 / 친구가 입력하면 차단되는지
   - ③-3 백업: 버튼 두 개로 본인/타인 판별
3. 본인이 자꾸 차단되면 "허용 범위" 슬라이더를 올리고 다시 등록

### 4. 목요일: 발표 준비
1. **시연 영상 녹화** (링크가 끊길 때 대비, 필수)
2. `reports/` 그래프와 수치를 PDF에 넣기 → `docs/발표_구성.md` 참고
3. 리허설 1회. **새 기능 추가 금지**

### 5. 금요일: 발표 🎤

---

## 🌐 배포 방법 3가지 (과제 공지 기준)

| 방법 | 명령 | 비고 |
|---|---|---|
| Gradio 공유 (추천) | `python app/app.py` | 코드에 `share=True, server_name="0.0.0.0"` 적용됨 |
| ngrok | `SHARE=0 python app/app.py` 후 `ngrok http 7860` | 로컬 PC에서 실행할 때 |
| Streamlit Cloud | - | 이 프로젝트는 Gradio 기반이라 사용 안 함 |

## ⚠️ 한계 (발표에서 솔직하게 말하면 좋은 점)
- ① 학습 데이터는 실제 유출 DB 대신 **합성 데이터**를 썼다 (개인정보 보호). 실제 서비스는 더 큰 데이터 필요
- ③ CMU 데이터가 `.tie5Roanl` 한 가지 비밀번호라 시연도 같은 비밀번호를 사용. 실제 서비스는 사용자 비밀번호로 등록
- 무료 LLM은 사용량 제한이 있어 오류 시 Groq → 오프라인 안내문으로 자동 전환되게 설계
