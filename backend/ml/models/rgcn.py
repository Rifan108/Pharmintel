import torch
import torch.nn as nn
import torch.nn.functional as F

class RelationalGraphConv(nn.Module):
    r"""
    R-GCN (Relational Graph Convolutional Network) Layer
    h_i^{(l+1)} = \sigma \left( \sum_{r \in \mathcal{R}} \sum_{j \in \mathcal{N}_i^r} \frac{1}{c_{i,r}} W_r^{(l)} h_j^{(l)} + W_0^{(l)} h_i^{(l)} \right)
    Uses basis-decomposition or full relation matrices for multi-relational knowledge graphs.
    """
    def __init__(self, in_features: int, out_features: int, num_relations: int):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.num_relations = num_relations

        # Relation-specific weight matrices
        self.weight = nn.Parameter(torch.empty(num_relations, in_features, out_features))
        self.self_loop_weight = nn.Parameter(torch.empty(in_features, out_features))
        self.bias = nn.Parameter(torch.zeros(out_features))

        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.weight)
        nn.init.xavier_uniform_(self.self_loop_weight)
        nn.init.zeros_(self.bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_type: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        out = torch.matmul(x, self.self_loop_weight)

        if edge_index.size(1) == 0:
            return out + self.bias

        src, dst = edge_index[0], edge_index[1]

        for r in range(self.num_relations):
            mask = (edge_type == r)
            if not mask.any():
                continue

            r_src = src[mask]
            r_dst = dst[mask]

            # Transform source node features with relation matrix W_r
            r_msg = torch.matmul(x[r_src], self.weight[r])

            # In-degree normalization per relation
            deg = torch.bincount(r_dst, minlength=num_nodes).float()
            norm = 1.0 / torch.clamp(deg[r_dst], min=1.0).unsqueeze(-1)
            r_msg = r_msg * norm

            out.index_add_(0, r_dst, r_msg)

        out = out + self.bias
        return F.relu(out)

class RGCNModule(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, num_relations: int = 8, dropout: float = 0.2):
        super().__init__()
        self.conv1 = RelationalGraphConv(in_dim, hidden_dim, num_relations)
        self.conv2 = RelationalGraphConv(hidden_dim, out_dim, num_relations)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(out_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_type: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index, edge_type)
        h = self.dropout(h)
        h = self.conv2(h, edge_index, edge_type)
        return self.layer_norm(h)
