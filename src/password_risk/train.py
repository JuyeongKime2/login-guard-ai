"""① 비밀번호 위험도 모델 학습.

실행: python -m src.password_risk.train
결과: models/password_risk.pt, reports/password_metrics.json, reports/password_confusion.png
"""
import json

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, TensorDataset

import config
from .generator import build_dataset
from .model import PasswordRiskNet, encode
from .wordlists import BASE_WORDS, SAFE_WORDS, split_words


def to_tensors(data):
    enc = [encode(pw, config.PW_MAX_LEN) for pw, _ in data]
    x = torch.tensor([e[0] for e in enc], dtype=torch.long)
    lengths = torch.tensor([e[1] for e in enc], dtype=torch.long)
    y = torch.tensor([lab for _, lab in data], dtype=torch.float)
    return TensorDataset(x, lengths, y)


def predict_all(model, loader, device):
    model.eval()
    probs, ys = [], []
    with torch.no_grad():
        for x, ln, y in loader:
            probs.append(torch.sigmoid(model(x.to(device), ln)).cpu())
            ys.append(y)
    return torch.cat(probs).numpy(), torch.cat(ys).numpy()


def main(epochs=8, n_train=40000, n_test=8000):
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 평가 단어는 학습 때 안 쓴다 → "처음 보는 단어"에도 일반화되는지 확인
    risky_tr, risky_te = split_words(BASE_WORDS)
    safe_tr, safe_te = split_words(SAFE_WORDS)
    train_ds = to_tensors(build_dataset(n_train, risky_tr, safe_tr, seed=1))
    test_ds = to_tensors(build_dataset(n_test, risky_te, safe_te, seed=2))
    train_dl = DataLoader(train_ds, batch_size=256, shuffle=True)
    test_dl = DataLoader(test_ds, batch_size=512)

    model = PasswordRiskNet(max_len=config.PW_MAX_LEN).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()

    for ep in range(1, epochs + 1):
        model.train()
        total = 0.0
        for x, ln, y in train_dl:
            opt.zero_grad()
            loss = loss_fn(model(x.to(device), ln), y.to(device))
            loss.backward()
            opt.step()
            total += loss.item() * len(y)
        p, yt = predict_all(model, test_dl, device)
        acc = accuracy_score(yt, p > 0.5)
        print(f"[epoch {ep}] train_loss={total / len(train_ds):.4f}  test_acc={acc:.4f}")

    p, yt = predict_all(model, test_dl, device)
    pred = (p > 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(yt, pred)),
        "precision": float(precision_score(yt, pred)),
        "recall": float(recall_score(yt, pred)),
        "f1": float(f1_score(yt, pred)),
        "n_train": n_train, "n_test": n_test,
        "note": "test set uses words never seen in training",
    }
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    (config.REPORT_DIR / "password_metrics.json").write_text(json.dumps(metrics, indent=2))

    cm = confusion_matrix(yt, pred)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.imshow(cm, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=14)
        ax.set_xticks([0, 1], ["safe", "risky"])
        ax.set_yticks([0, 1], ["safe", "risky"])
        ax.set_xlabel("predicted")
        ax.set_ylabel("actual")
        ax.set_title(f"Password risk  F1={metrics['f1']:.3f}")
        fig.tight_layout()
        fig.savefig(config.REPORT_DIR / "password_confusion.png", dpi=150)
    except Exception as e:  # 그림은 선택
        print("confusion plot skipped:", e)

    torch.save({"state_dict": model.cpu().state_dict(), "max_len": config.PW_MAX_LEN},
               config.PW_MODEL_PATH)
    print("saved:", config.PW_MODEL_PATH)


if __name__ == "__main__":
    main()
