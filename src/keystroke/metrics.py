"""생체인증 평가 지표.

FAR (타인 수락률): 사칭자를 본인으로 잘못 통과시킨 비율
FRR (본인 거부율): 본인을 잘못 차단한 비율
EER (동일오류율): FAR == FRR이 되는 지점의 오류율. 낮을수록 좋음.
점수는 '낮을수록 본인'인 거리 점수라고 가정한다.
"""
import numpy as np


def far_frr(genuine, impostor, threshold):
    genuine, impostor = np.asarray(genuine), np.asarray(impostor)
    far = float(np.mean(impostor <= threshold))
    frr = float(np.mean(genuine > threshold))
    return far, frr


def eer(genuine, impostor):
    thresholds = np.unique(np.concatenate([genuine, impostor]))
    best = (1.0, 0.0, None)
    for t in thresholds:
        far, frr = far_frr(genuine, impostor, t)
        gap = abs(far - frr)
        if gap < best[0]:
            best = (gap, (far + frr) / 2, float(t))
    return best[1], best[2]
