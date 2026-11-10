"""브라우저에서 기록한 키 이벤트 → CMU와 같은 31개 특징으로 변환.

events 예: [{"type": "d", "code": "Period", "t": 1203.5}, {"type": "u", ...}, ...]
  type: d=keydown, u=keyup / t: 밀리초 (performance.now())
Shift 키는 CMU처럼 무시하고 R 키 자체의 시간만 쓴다.
"""
import numpy as np

import config


def events_to_features(events, codes=config.KEY_CODES):
    ev = sorted(events or [], key=lambda e: e["t"])
    if any(e["code"] == "Backspace" for e in ev):
        raise ValueError("오타 수정(Backspace)이 있어요. 입력칸을 비우고 처음부터 다시 입력해주세요.")

    times, start = [], 0
    for code in codes:
        d = next((i for i in range(start, len(ev))
                  if ev[i]["type"] == "d" and ev[i]["code"] == code), None)
        if d is None:
            raise ValueError(f"'{code}' 키 입력을 찾지 못했어요. "
                             f"{config.CMU_PASSWORD} 입력 후 Enter까지 눌러주세요.")
        u = next((i for i in range(d + 1, len(ev))
                  if ev[i]["type"] == "u" and ev[i]["code"] == code), None)
        if u is None:
            raise ValueError(f"'{code}' 키를 뗀 기록이 없어요. 다시 입력해주세요.")
        times.append((ev[d]["t"] / 1000.0, ev[u]["t"] / 1000.0))
        start = d + 1

    feats = []
    for i, (down, up) in enumerate(times):
        feats.append(up - down)                      # H
        if i < len(times) - 1:
            next_down = times[i + 1][0]
            feats += [next_down - down, next_down - up]  # DD, UD
    return np.array(feats, dtype=np.float32)
