"""CMU Keystroke Dynamics Benchmark 다운로드/로드.

51명이 '.tie5Roanl'을 400번씩 입력한 데이터 (Killourhy & Maxion, DSN 2009).
컬럼: subject, sessionIndex, rep, 그리고 31개 시간 특징(초 단위)
  H.x      : x 키를 누르고 있던 시간 (Hold)
  DD.x.y   : x 누른 순간 → y 누른 순간 (Down-Down)
  UD.x.y   : x 뗀 순간 → y 누른 순간 (Up-Down, 음수 가능)

실행: python -m src.keystroke.data   (다운로드만)
"""
import urllib.request

import pandas as pd

import config


def download_cmu():
    if not config.CMU_CSV.exists():
        print("CMU 데이터 다운로드 중...", config.CMU_URL)
        urllib.request.urlretrieve(config.CMU_URL, config.CMU_CSV)
    print("데이터 위치:", config.CMU_CSV)


def load_cmu():
    if not config.CMU_CSV.exists():
        download_cmu()
    df = pd.read_csv(config.CMU_CSV)
    feat_cols = [c for c in df.columns if c.split(".")[0] in ("H", "DD", "UD")]
    assert len(feat_cols) == 31, f"특징 개수가 31이 아님: {len(feat_cols)}"
    return df, feat_cols


def split_subject(df, feat_cols, subject):
    """Killourhy 표준 평가 방식.
    - 본인 학습: 처음 200회
    - 본인 테스트: 나머지 200회
    - 타인(사칭자) 테스트: 다른 50명의 처음 5회씩 = 250회
    """
    own = df[df.subject == subject][feat_cols].to_numpy()
    others = df[df.subject != subject].groupby("subject").head(5)[feat_cols].to_numpy()
    return own[:200], own[200:], others


if __name__ == "__main__":
    download_cmu()
    d, cols = load_cmu()
    print(d.shape, "명수:", d.subject.nunique())
    print(cols)
