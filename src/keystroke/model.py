"""③ 타이핑 패턴 인증 모델.

- KeystrokeAE: 본인 입력만으로 학습하는 오토인코더 (딥러닝, 이상탐지 방식)
  본인 리듬은 잘 복원하고, 타인 리듬은 복원 오차가 커진다 → 오차 = 이상 점수
- ScaledManhattan: 원 논문의 최상위 기준 모델 (비교용, 딥러닝 아님)
"""
import numpy as np
import torch
import torch.nn as nn


class KeystrokeAE(nn.Module):
    def __init__(self, n=31):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(n, 24), nn.ReLU(), nn.Linear(24, 12), nn.ReLU())
        self.decoder = nn.Sequential(nn.Linear(12, 24), nn.ReLU(), nn.Linear(24, n))

    def forward(self, x):
        return self.decoder(self.encoder(x))


class Verifier:
    """사용자 한 명의 타이핑 패턴 검증기."""

    def __init__(self):
        self.model = KeystrokeAE()
        self.mean = self.std = None
        self.threshold = None

    def _z(self, X):
        return torch.tensor((np.asarray(X, dtype=np.float32) - self.mean) / self.std)

    def fit(self, X, epochs=400, lr=3e-3, noise=0.1, seed=0):
        torch.manual_seed(seed)
        X = np.asarray(X, dtype=np.float32)
        self.mean = X.mean(0)
        self.std = np.maximum(X.std(0), 0.01)  # 샘플이 적을 때 0으로 나누기 방지
        Z = self._z(X)
        if len(Z) < 50:  # 등록 샘플이 적으면 잡음을 섞어 증강
            Z = Z.repeat(max(1, 200 // len(Z)), 1)
            noise = max(noise, 0.3)
        opt = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-4)
        self.model.train()
        for _ in range(epochs):
            opt.zero_grad()
            noisy = Z + noise * torch.randn_like(Z)        # 디노이징 오토인코더
            loss = ((self.model(noisy) - Z) ** 2).mean()
            loss.backward()
            opt.step()
        self.model.eval()
        return self

    def score(self, X):
        X = np.atleast_2d(X)
        with torch.no_grad():
            Z = self._z(X)
            return ((self.model(Z) - Z) ** 2).mean(1).numpy()

    def calibrate_from_enrollment(self, X, percentile=95, multiplier=2.0):
        self.threshold = float(np.percentile(self.score(X), percentile) * multiplier)
        return self.threshold

    def save(self, path):
        torch.save({"state": self.model.state_dict(), "mean": self.mean,
                    "std": self.std, "threshold": self.threshold}, path)

    @classmethod
    def load(cls, path):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        v = cls()
        v.model.load_state_dict(ck["state"])
        v.model.eval()
        v.mean, v.std, v.threshold = ck["mean"], ck["std"], ck["threshold"]
        return v


class ScaledManhattan:
    def fit(self, X):
        X = np.asarray(X)
        self.mean = X.mean(0)
        self.mad = np.maximum(np.abs(X - self.mean).mean(0), 1e-4)
        return self

    def score(self, X):
        return (np.abs(np.atleast_2d(X) - self.mean) / self.mad).sum(1)
