import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Any, Optional

from ml.models.rgcn import RGCNModule
from ml.models.hgt import HGTModule
from ml.models.metapath_attn import MetaPathModule

class PharmIntelHybridGNN(nn.Module):
    """
    PHARMINTEL-HYBRIDGNN:
    Heterogeneous Graph Transformer (HGT)
    + Relational Graph Convolutional Network (R-GCN)
    + Meta-Path Attention Network
    + Residual Molecular Physicochemical Projection
    with Symmetric Drug-Pair Bilinear Fusion.
    """
    def __init__(
        self,
        in_dim: int = 137,
        hidden_dim: int = 96,
        out_dim: int = 96,
        num_classes: int = 4,
        num_types: int = 4,
        num_relations: int = 8,
        bio_dim: int = 18,
        mode: str = "full",  # full | rgcn_only | hgt_only | metapath_only | rgcn_hgt | rgcn_metapath | hgt_metapath
        dropout: float = 0.15
    ):
        super().__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        self.num_classes = num_classes
        self.bio_dim = bio_dim
        self.mode = mode

        # Sub-modules
        self.rgcn = RGCNModule(in_dim, hidden_dim, out_dim, num_relations=num_relations, dropout=dropout)
        self.hgt = HGTModule(in_dim, hidden_dim, out_dim, num_types=num_types, num_relations=num_relations, dropout=dropout)
        self.metapath = MetaPathModule(in_dim, out_dim)

        # Direct residual molecular property projection
        self.mol_proj = nn.Sequential(
            nn.Linear(in_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )

        # Cross-module feature fusion gating
        fusion_dim = 0
        if "rgcn" in mode or mode == "full":
            fusion_dim += out_dim
        if "hgt" in mode or mode == "full":
            fusion_dim += out_dim
        if "metapath" in mode or mode == "full":
            fusion_dim += out_dim

        self.drug_compress = nn.Sequential(
            nn.Linear(fusion_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )

        # Symmetric Drug Pair Fusion:
        # Repr = [h_i * h_j, |h_i - h_j|, (h_i + h_j), bio_feat] -> dimension: out_dim * 3 + bio_dim
        pair_dim = out_dim * 3 + bio_dim

        # Multi-layer Classification Head with Skip Connection & LayerNorm
        self.fc1 = nn.Linear(pair_dim, 160)
        self.ln1 = nn.LayerNorm(160)
        self.act1 = nn.GELU()
        self.drop1 = nn.Dropout(dropout)

        self.fc2 = nn.Linear(160, 80)
        self.ln2 = nn.LayerNorm(80)
        self.act2 = nn.GELU()
        self.drop2 = nn.Dropout(dropout)

        self.fc_out = nn.Linear(80, num_classes)
        self.temperature = nn.Parameter(torch.ones(1) * 1.0)

    def extract_drug_representations(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_type: torch.Tensor,
        node_type: torch.Tensor,
        drug_indices: torch.Tensor,
        dpd_adj: torch.Tensor,
        ddis_adj: torch.Tensor,
        dse_adj: torch.Tensor
    ) -> torch.Tensor:
        """
        Computes final multi-relational drug node representations.
        """
        branches = []
        drug_raw_feats = x[drug_indices]

        # Branch 1: R-GCN
        if "rgcn" in self.mode or self.mode == "full":
            h_rgcn_all = self.rgcn(x, edge_index, edge_type)
            h_rgcn_drugs = h_rgcn_all[drug_indices]
            branches.append(h_rgcn_drugs)

        # Branch 2: HGT
        if "hgt" in self.mode or self.mode == "full":
            h_hgt_all = self.hgt(x, edge_index, edge_type, node_type)
            h_hgt_drugs = h_hgt_all[drug_indices]
            branches.append(h_hgt_drugs)

        # Branch 3: Meta-Path Attention Network
        if "metapath" in self.mode or self.mode == "full":
            h_meta, _ = self.metapath(drug_raw_feats, dpd_adj, ddis_adj, dse_adj)
            branches.append(h_meta)

        # Multi-modal fusion
        if len(branches) > 1:
            concat_h = torch.cat(branches, dim=-1)
            h_drugs = self.drug_compress(concat_h)
        else:
            h_drugs = branches[0]

        # Add residual molecular projection
        h_mol = self.mol_proj(drug_raw_feats)
        return h_drugs + h_mol

    def embed_single_drug(self, feat: torch.Tensor) -> torch.Tensor:
        """
        Embeds an arbitrary drug feature vector (shape [137] or [batch, 137])
        using the learned cross-relational projection matrices.
        """
        if feat.dim() == 1:
            feat = feat.unsqueeze(0)

        branches = []
        if "rgcn" in self.mode or self.mode == "full":
            h_rgcn = torch.matmul(feat, self.rgcn.conv1.self_loop_weight)
            branches.append(h_rgcn)

        if "hgt" in self.mode or self.mode == "full":
            h_hgt = self.hgt.layer1.k_linears[0](self.hgt.proj_in(feat))
            branches.append(h_hgt)

        if "metapath" in self.mode or self.mode == "full":
            h_meta = F.relu(self.metapath.proj_dpd(feat))
            branches.append(h_meta)

        if len(branches) > 1:
            concat_h = torch.cat(branches, dim=-1)
            h_d = self.drug_compress(concat_h)
        else:
            h_d = branches[0]

        h_mol = self.mol_proj(feat)
        return h_d + h_mol

    def forward_pairs(
        self,
        h_drugs: torch.Tensor,
        drug_a_idx: torch.Tensor,
        drug_b_idx: torch.Tensor,
        bio_feat: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Symmetric Drug Pair Representation with multi-scale feature fusion:
        Ensures f(drug_a, drug_b) == f(drug_b, drug_a)
        """
        ha = h_drugs[drug_a_idx]
        hb = h_drugs[drug_b_idx]

        elem_prod = ha * hb
        abs_diff = torch.abs(ha - hb)
        elem_sum = ha + hb

        if bio_feat is None:
            bio_feat = torch.zeros(ha.size(0), self.bio_dim, device=ha.device)

        pair_repr = torch.cat([elem_prod, abs_diff, elem_sum, bio_feat], dim=-1)

        z1 = self.drop1(self.act1(self.ln1(self.fc1(pair_repr))))
        z2 = self.drop2(self.act2(self.ln2(self.fc2(z1))))
        logits = self.fc_out(z2)

        calibrated_logits = logits / torch.clamp(self.temperature, min=0.5, max=5.0)
        probs = F.softmax(calibrated_logits, dim=-1)
        return calibrated_logits, probs

    def forward_single_pair(
        self,
        ha: torch.Tensor,
        hb: torch.Tensor,
        bio_feat: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        if ha.dim() == 1:
            ha = ha.unsqueeze(0)
        if hb.dim() == 1:
            hb = hb.unsqueeze(0)

        elem_prod = ha * hb
        abs_diff = torch.abs(ha - hb)
        elem_sum = ha + hb

        if bio_feat is None:
            bio_feat = torch.zeros(ha.size(0), self.bio_dim, device=ha.device)
        elif bio_feat.dim() == 1:
            bio_feat = bio_feat.unsqueeze(0)

        pair_repr = torch.cat([elem_prod, abs_diff, elem_sum, bio_feat], dim=-1)

        z1 = self.drop1(self.act1(self.ln1(self.fc1(pair_repr))))
        z2 = self.drop2(self.act2(self.ln2(self.fc2(z1))))
        logits = self.fc_out(z2)

        calibrated_logits = logits / torch.clamp(self.temperature, min=0.5, max=5.0)
        probs = F.softmax(calibrated_logits, dim=-1)
        return calibrated_logits, probs
