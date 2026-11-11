"""③ 시연용 '데모 사용자(s002)' 모델 저장 + 백업 시연 샘플 저장.

실행: python -m src.keystroke.train_demo
결과: models/keystroke_demo.pt, models/keystroke_demo_samples.npz
"""
import numpy as np

import config
from .data import load_cmu
from .metrics import eer, far_frr
from .model import Verifier


def main():
    df, cols = load_cmu()
    s = config.DEMO_SUBJECT
    own = df[df.subject == s][cols].to_numpy(np.float32)
    train, valid, demo_genuine = own[:200], own[200:300], own[300:]

    others = df[df.subject != s]
    imp_valid = others.groupby("subject").head(5)[cols].to_numpy(np.float32)
    # 시연용 사칭 샘플은 검증에 안 쓴 뒷부분 세션에서 뽑는다
    imp_demo = others[others.sessionIndex == 8].groupby("subject").head(4)[cols].to_numpy(np.float32)

    v = Verifier().fit(train)
    e, thr = eer(v.score(valid), v.score(imp_valid))
    v.threshold = thr
    far, frr = far_frr(v.score(demo_genuine), v.score(imp_demo), thr)
    print(f"데모 사용자 {s}: 검증 EER={e:.3f}, threshold={thr:.4f}")
    print(f"시연 샘플 기준  본인 거부율(FRR)={frr:.3f}, 타인 통과율(FAR)={far:.3f}")

    v.save(config.KS_DEMO_PATH)
    np.savez(config.KS_DEMO_SAMPLES, genuine=demo_genuine, impostor=imp_demo)
    print("saved:", config.KS_DEMO_PATH, config.KS_DEMO_SAMPLES)
    return v, {"valid_eer": e, "threshold": thr, "demo_far": far, "demo_frr": frr}


if __name__ == "__main__":
    main()
