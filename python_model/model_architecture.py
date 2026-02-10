import torch
import torch.nn as nn
import math

# ================= MODEL CLASSES =================

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=2048):
        super().__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1), :]

class DNARepairAutoencoder(nn.Module):
    def __init__(self, vocab_size=5, embedding_dim=128, max_len=1024):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=4)
        self.pos_encoder = PositionalEncoding(embedding_dim, max_len)

        self.encoder_cnn = nn.Sequential(
            nn.Conv1d(embedding_dim, 128, 7, padding=3),
            nn.BatchNorm1d(128),
            nn.ReLU(),

            nn.Conv1d(128, 128, 5, padding=2),
            nn.BatchNorm1d(128),
            nn.ReLU()
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=128,
            nhead=8,
            dim_feedforward=512,
            batch_first=True,
            dropout=0.1
        )

        self.transformer_block = nn.TransformerEncoder(encoder_layer, num_layers=4)
        self.output_layer = nn.Linear(128, vocab_size)

    def forward(self, x):
        x = self.embedding(x).permute(0,2,1)
        x = self.encoder_cnn(x)
        x = x.permute(0,2,1)
        x = self.pos_encoder(x)
        x = self.transformer_block(x)
        return self.output_layer(x)
