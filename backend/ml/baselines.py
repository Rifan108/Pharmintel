import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
from typing import Dict, Any, Tuple

class SimpleGCNLayer(nn.Module):
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        out = self.linear(x)
        if edge_index.size(1) == 0:
            return F.relu(out)

        src, dst = edge_index[0], edge_index[1]
        deg = torch.bincount(dst, minlength=num_nodes).float()
        deg_inv_sqrt = torch.pow(torch.clamp(deg, min=1.0), -0.5)
        norm = deg_inv_sqrt[src] * deg_inv_sqrt[dst]

        msg = out[src] * norm.unsqueeze(-1)
        aggr = torch.zeros_like(out)
        aggr.index_add_(0, dst, msg)
        return F.relu(aggr)

class HomogeneousGCNBaseline(nn.Module):
    def __init__(self, in_dim: int = 137, hidden_dim: int = 64, out_dim: int = 64, num_classes: int = 4):
        super().__init__()
        self.conv1 = SimpleGCNLayer(in_dim, hidden_dim)
        self.conv2 = SimpleGCNLayer(hidden_dim, out_dim)
        self.classifier = nn.Sequential(
            nn.Linear(out_dim * 3, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, drug_indices: torch.Tensor,
                pair_a: torch.Tensor, pair_b: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = self.conv2(h, edge_index)
        drug_h = h[drug_indices]

        ha = drug_h[pair_a]
        hb = drug_h[pair_b]
        pair_repr = torch.cat([ha * hb, torch.abs(ha - hb), ha + hb], dim=-1)
        return self.classifier(pair_repr)

class BaselineModelsManager:
    @staticmethod
    def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
        lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
        lr.fit(X_train, y_train)
        return lr

    @staticmethod
    def train_decision_tree(X_train: np.ndarray, y_train: np.ndarray) -> DecisionTreeClassifier:
        dt = DecisionTreeClassifier(max_depth=10, min_samples_split=4, class_weight="balanced", random_state=42)
        dt.fit(X_train, y_train)
        return dt

    @staticmethod
    def train_svm(X_train: np.ndarray, y_train: np.ndarray) -> SVC:
        svm = SVC(kernel="rbf", C=1.5, probability=True, class_weight="balanced", random_state=42)
        svm.fit(X_train, y_train)
        return svm

    @staticmethod
    def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
        rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=3,
            class_weight="balanced",
            random_state=42
        )
        rf.fit(X_train, y_train)
        return rf

    @staticmethod
    def train_mlp_neural_net(X_train: np.ndarray, y_train: np.ndarray) -> MLPClassifier:
        mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=400, alpha=1e-3, random_state=42)
        mlp.fit(X_train, y_train)
        return mlp

    @staticmethod
    def train_xgboost(X_train: np.ndarray, y_train: np.ndarray) -> xgb.XGBClassifier:
        model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.06,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            random_state=42,
            eval_metric="mlogloss"
        )
        model.fit(X_train, y_train)
        return model
