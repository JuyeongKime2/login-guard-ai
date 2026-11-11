"""③ 51명 전체 성능 평가 (발표용 핵심 수치).

실행: python -m src.keystroke.evaluate
결과: reports/keystroke_eer.csv, reports/keystroke_summary.json, reports/keystroke_eer.png

노트북(notebooks/02_keystroke_analysis.ipynb)에서는 evaluate_all → summarize → plot_eer 순서로 쓴다.
"""
import json

import numpy as np
import pandas as pd

import config
from .data import load_cmu, split_subject
from .metrics import eer
from .model import ScaledManhattan, Verifier


def evaluate_subject(df, cols, subject, epochs=400):
    """한 명에 대해 오토인코더 / Scaled Manhattan의 EER 계산."""
    train, gen_test, imp_test = split_subject(df, cols, subject)
    ae = Verifier().fit(train, epochs=epochs)
    e_ae, _ = eer(ae.score(gen_test), ae.score(imp_test))
    man = ScaledManhattan().fit(train)
    e_man, _ = eer(man.score(gen_test), man.score(imp_test))
    return {"subject": subject, "eer_autoencoder": e_ae, "eer_manhattan": e_man}


def evaluate_all(df, cols, epochs=400, verbose=True):
    rows = []
    subjects = sorted(df.subject.unique())
    for i, s in enumerate(subjects, 1):
        r = evaluate_subject(df, cols, s, epochs)
        rows.append(r)
        if verbose:
            print(f"[{i:2d}/{len(subjects)}] {s}  AE EER={r['eer_autoencoder']:.3f}  "
                  f"Manhattan EER={r['eer_manhattan']:.3f}")
    return pd.DataFrame(rows)


def summarize(res):
    return {
        "autoencoder_eer_mean": float(res.eer_autoencoder.mean()),
        "autoencoder_eer_std": float(res.eer_autoencoder.std()),
        "manhattan_eer_mean": float(res.eer_manhattan.mean()),
        "manhattan_eer_std": float(res.eer_manhattan.std()),
        "paper_best_eer_range": "0.096 ~ 0.102 (Killourhy & Maxion 2009)",
    }


def plot_eer(res, summary):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(res))
    ax.bar(x - 0.2, res.eer_autoencoder, 0.4, label="Autoencoder (DL)")
    ax.bar(x + 0.2, res.eer_manhattan, 0.4, label="Scaled Manhattan (baseline)")
    ax.axhline(summary["autoencoder_eer_mean"], ls="--", lw=1)
    ax.set_xlabel("subject")
    ax.set_ylabel("EER (lower is better)")
    ax.set_title("Keystroke verification EER per subject (CMU benchmark)")
    ax.legend()
    fig.tight_layout()
    return fig


def save_results(res, summary, fig=None):
    res.to_csv(config.REPORT_DIR / "keystroke_eer.csv", index=False)
    (config.REPORT_DIR / "keystroke_summary.json").write_text(json.dumps(summary, indent=2))
    if fig is not None:
        fig.savefig(config.REPORT_DIR / "keystroke_eer.png", dpi=150)


def main(epochs=400):
    df, cols = load_cmu()
    res = evaluate_all(df, cols, epochs)
    summary = summarize(res)
    print(json.dumps(summary, indent=2))
    try:
        fig = plot_eer(res, summary)
    except Exception as e:
        print("plot skipped:", e)
        fig = None
    save_results(res, summary, fig)
    return res, summary


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    main()
