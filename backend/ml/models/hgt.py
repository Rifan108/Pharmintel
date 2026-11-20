import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class HeterogeneousGraphTransformerLayer(nn.Module):
    """
    Heterogeneous Graph Transformer (HGT) Layer.
    Implements node-type-aware and relation-aware multi-head self-attention.
    Ref: Hu et al. "Heterogeneous Graph Transformer", WWW 2020.
    """
    def __init__(self, in_dim: int, out_dim: int, num_types: int = 4, num_relations: int = 8, n_heads: int = 4, dropout: float = 0.2):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.num_types = num_types
        self.num_relations = num_relations
        self.n_heads = n_heads
        self.d_k = out_dim // n_heads

        # Type-specific linear projections for Query, Key, Value
        self.k_linears = nn.ModuleList([nn.Linear(in_dim, out_dim) for _ in range(num_types)])
        self.q_linears = nn.ModuleList([nn.Linear(in_dim, out_dim) for _ in range(num_types)])
        self.v_linears = nn.ModuleList([nn.Linear(in_dim, out_dim) for _ in range(num_types)])
        self.a_linears = nn.ModuleList([nn.Linear(out_dim, out_dim) for _ in range(num_types)])

        # Relation-specific transformation matrices for attention and message
        self.relation_att = nn.Parameter(torch.empty(num_relations, n_heads, self.d_k, self.d_k))
        self.relation_msg = nn.Parameter(torch.empty(num_relations, n_heads, self.d_k, self.d_k))

        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(out_dim)
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.relation_att)
        nn.init.xavier_uniform_(self.relation_msg)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_type: torch.Tensor, node_type: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        k = torch.zeros(num_nodes, self.out_dim, device=x.device)
        q = torch.zeros(num_nodes, self.out_dim, device=x.device)
        v = torch.zeros(num_nodes, self.out_dim, device=x.device)

        # Type-specific projections
        for t in range(self.num_types):
            mask = (node_type == t)
            if mask.any():
                k[mask] = self.k_linears[t](x[mask])
                q[mask] = self.q_linears[t](x[mask])
                v[mask] = self.v_linears[t](x[mask])

        # Reshape for multi-head attention: [num_nodes, n_heads, d_k]
        k = k.view(num_nodes, self.n_heads, self.d_k)
        q = q.view(num_nodes, self.n_heads, self.d_k)
        v = v.view(num_nodes, self.n_heads, self.d_k)

        out = torch.zeros(num_nodes, self.n_heads, self.d_k, device=x.device)

        if edge_index.size(1) > 0:
            src, dst = edge_index[0], edge_index[1]

            for r in range(self.num_relations):
                mask = (edge_type == r)
                if not mask.any():
                    continue

                r_src = src[mask]
                r_dst = dst[mask]

                # Key transformed by relation attention matrix: [E, n_heads, d_k]
                k_r = torch.einsum('ehd,hda->eha', k[r_src], self.relation_att[r])
                q_r = q[r_dst]

                # Attention scores
                scores = (k_r * q_r).sum(dim=-1) / math.sqrt(self.d_k)
                # Relation message
                msg_r = torch.einsum('ehd,hda->eha', v[r_src], self.relation_msg[r])

                # Normalized message
                deg = torch.bincount(r_dst, minlength=num_nodes).float()
                norm = 1.0 / torch.clamp(deg[r_dst], min=1.0).unsqueeze(-1).unsqueeze(-1)
                weighted_msg = msg_r * norm

                out.index_add_(0, r_dst, weighted_msg)

        out = out.view(num_nodes, self.out_dim)

        # Target type aggregation
        res = torch.zeros_like(out)
        for t in range(self.num_types):
            mask = (node_type == t)
            if mask.any():
                res[mask] = self.a_linears[t](out[mask])

        # Residual connection + LayerNorm
        h = self.layer_norm(F.gelu(res) + (x if x.size(-1) == self.out_dim else 0))
        return self.dropout(h)

class HGTModule(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, num_types: int = 4, num_relations: int = 8, n_heads: int = 4, dropout: float = 0.2):
        super().__init__()
        self.proj_in = nn.Linear(in_dim, hidden_dim) if in_dim != hidden_dim else nn.Identity()
        self.layer1 = HeterogeneousGraphTransformerLayer(hidden_dim, hidden_dim, num_types, num_relations, n_heads, dropout)
        self.layer2 = HeterogeneousGraphTransformerLayer(hidden_dim, out_dim, num_types, num_relations, n_heads, dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_type: torch.Tensor, node_type: torch.Tensor) -> torch.Tensor:
        h = self.proj_in(x)
        h = self.layer1(h, edge_index, edge_type, node_type)
        h = self.layer2(h, edge_index, edge_type, node_type)
        return h
