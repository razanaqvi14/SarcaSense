import torch
import torch.nn as nn


class SarcasmClassifier(nn.Module):
    """Frozen embedding -> BiLSTM -> BiGRU -> additive attention -> linear.

    Same architecture (and parameter names) as `HeadlineSarcasmClassifierAndDetector`
    in the notebook, so `best_model.pt` loads directly.
    """

    def __init__(self, vocab_size: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.embedding.weight.requires_grad = False
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.gru = nn.GRU(hidden_dim * 2, hidden_dim, batch_first=True, bidirectional=True)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.fc = nn.Linear(hidden_dim * 2, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        embeddings = self.embedding(x)
        lstm_output, _ = self.lstm(embeddings)
        gru_output, _ = self.gru(lstm_output)

        attention_scores = self.attention(gru_output).squeeze(-1)
        attention_weights = torch.softmax(attention_scores, dim=1)

        context = torch.bmm(attention_weights.unsqueeze(1), gru_output).squeeze(1)
        logits = self.fc(context).squeeze(1)
        return logits, attention_weights
