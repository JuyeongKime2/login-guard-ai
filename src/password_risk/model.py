"""문자 단위 BiLSTM 비밀번호 위험도 분류기."""
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence

PAD, UNK = 0, 96
VOCAB_SIZE = 97  # 0=패딩, 1~95=출력 가능한 ASCII, 96=그 외(한글 등)


def encode(pw: str, max_len: int):
    ids = []
    for c in pw[:max_len]:
        o = ord(c)
        ids.append(o - 31 if 32 <= o <= 126 else UNK)
    length = len(ids)
    ids += [PAD] * (max_len - length)
    return ids, length


class PasswordRiskNet(nn.Module):
    def __init__(self, vocab=VOCAB_SIZE, emb=32, hidden=64, max_len=32):
        super().__init__()
        self.max_len = max_len
        self.emb = nn.Embedding(vocab, emb, padding_idx=PAD)
        self.lstm = nn.LSTM(emb, hidden, batch_first=True, bidirectional=True)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2 + 1, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1)
        )

    def forward(self, x, lengths):
        e = self.emb(x)
        packed = pack_padded_sequence(e, lengths.cpu().clamp(min=1), batch_first=True,
                                      enforce_sorted=False)
        _, (h, _) = self.lstm(packed)
        h = torch.cat([h[-2], h[-1]], dim=1)          # 정방향 + 역방향 마지막 은닉 상태
        length_feat = (lengths.float() / self.max_len).unsqueeze(1)
        return self.head(torch.cat([h, length_feat], dim=1)).squeeze(1)  # logit
