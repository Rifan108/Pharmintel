import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, List

class SemanticPathAttention(nn.Module):
    r"""
    Semantic-level attention module to weigh and combine distinct meta-paths:
    $\beta_{\Phi_p} = \frac{\exp(\mathbf{q}^\top \tanh(W \mathbf{z}_{\Phi_p} + \mathbf{b}))}{\sum \exp(\dots)}$
    """
    def __init__(self, in_features: int, hidden_dim: int = 64):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1, bias=False)
        )

    def forward(self, path_embeddings: List[torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        # Stack path embeddings: [num_drugs, num_paths, in_features]
        stacked = torch.stack(path_embeddings, dim=1)
        # Compute attention weights: [num_drugs, num_paths, 1]
        scores = self.proj(stacked)
        weights = F.softmax(scores, dim=1)
        # Weighted combination: [num_drugs, in_features]
        fused = (stacked * weights).sum(dim=1)
        return fused, weights.squeeze(-1)

class MetaPathModule(nn.Module):
    """
    Extracts and aggregates representations across biological meta-paths:
    1. Drug -> Target Protein -> Drug (D-P-D: Shared mechanism/target)
    2. Drug -> Indicated Disease -> Drug (D-Dis-D: Shared indication)
    3. Drug -> Side Effect -> Drug (D-SE-D: Shared toxicity profile)
    """
    def __init__(self, drug_dim: int, out_dim: int):
        super().__init__()
        self.proj_dpd = nn.Linear(drug_dim, out_dim)
        self.proj_ddis = nn.Linear(drug_dim, out_dim)
        self.proj_dse = nn.Linear(drug_dim, out_dim)

        self.semantic_attn = SemanticPathAttention(out_dim)
        self.layer_norm = nn.LayerNorm(out_dim)

    def forward(self, drug_features: torch.Tensor,
                dpd_adj: torch.Tensor,
                ddis_adj: torch.Tensor,
                dse_adj: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        drug_features: [num_drugs, drug_dim]
        adj matrices: [num_drugs, num_drugs] normalized meta-path adjacency
        """
        # Meta-path 1: D-P-D
        h_dpd = torch.matmul(dpd_adj, drug_features)
        h_dpd = F.relu(self.proj_dpd(h_dpd))

        # Meta-path 2: D-Dis-D
        h_ddis = torch.matmul(ddis_adj, drug_features)
        h_ddis = F.relu(self.proj_ddis(h_ddis))

        # Meta-path 3: D-SE-D
        h_dse = torch.matmul(dse_adj, drug_features)
        h_dse = F.relu(self.proj_dse(h_dse))

        # Combine via semantic attention
        fused, attn_weights = self.semantic_attn([h_dpd, h_ddis, h_dse])
        return self.layer_norm(fused), attn_weights
