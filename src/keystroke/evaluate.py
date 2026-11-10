"""③ 51명 전체 성능 평가 (발표용 핵심 수치).

실행: python -m src.keystroke.evaluate
결과: reports/keystroke_eer.csv, reports/keystroke_summary.json, reports/keystroke_eer.png
"""
import json

import numpy as np
import pandas as pd

import config
from .data import load_cmu, split_subject
from .metrics import eer
from .model import ScaledManhattan, Verifier


def main(epochs=400):
    df, cols = load_cmu()
    rows = []
    for i, s in enumerate(sorted(df.subject.unique()), 1):
        train, gen_test, imp_test = split_subject(df, cols, s)
        ae = Verifier().fit(train, epochs=epochs)
        e_ae, _ = eer(ae.score(gen_test), ae.score(imp_test))
        man = ScaledManhattan().fit(train)
        e_man, _ = eer(man.score(gen_test), man.score(imp_test))
        rows.append({"subject": s, "eer_autoencoder": e_ae, "eer_manhattan": e_man})
        print(f"[{i:2d}/51] {s}  AE EER={e_ae:.3f}  Manhattan EER={e_man:.3f}")

    res = pd.DataFrame(rows)
    res.to_csv(config.REPORT_DIR / "keystroke_eer.csv", index=False)
    summary = {
        "autoencoder_eer_mean": float(res.eer_autoencoder.mean()),
        "autoencoder_eer_std": float(res.eer_autoencoder.std()),
        "manhattan_eer_mean": float(res.eer_manhattan.mean()),
        "manhattan_eer_std": float(res.eer_manhattan.std()),
        "paper_best_eer_range": "0.096 ~ 0.102 (Killourhy & Maxion 2009)",
    }
    (config.REPORT_DIR / "keystroke_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
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
        fig.savefig(config.REPORT_DIR / "keystroke_eer.png", dpi=150)
    except Exception as e:
        print("plot skipped:", e)


if __name__ == "__main__":
    main()
