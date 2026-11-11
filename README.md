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
├── notebooks/               ← 과제 제출용 분석 노트북 (실행 결과 포함, 코랩 실행 가능)
│   ├── 01_password_risk_analysis.ipynb   ① 데이터 생성·EDA·학습·평가·오류 분석
│   └── 02_keystroke_analysis.ipynb       ③ CMU 데이터 EDA·EER 평가·기준 모델 비교
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
