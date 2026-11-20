import networkx as nx
import torch
import numpy as np
from typing import Dict, List, Tuple, Any
from ml.feature_extraction import extractor
from ml.dataset_loader import BiomedicalDatasetLoader

class HeterogeneousBiomedicalGraph:
    """
    Constructs and manages the heterogeneous knowledge graph:
    Node Types: Drug (0), Protein (1), Disease (2), Side Effect (3)
    Relation Types:
      0: drug-interacts-drug (D-D)
      1: drug-targets-protein (D-P)
      2: protein-targeted-by-drug (P-D)
      3: drug-treats-disease (D-Dis)
      4: disease-treated-by-drug (Dis-D)
      5: drug-causes-side_effect (D-SE)
      6: side_effect-caused-by-drug (SE-D)
      7: protein-interacts-protein (P-P)
    """

    NODE_TYPES = {"drug": 0, "protein": 1, "disease": 2, "side_effect": 3}
    REL_TYPES = {
        "drug_interacts_drug": 0,
        "drug_targets_protein": 1,
        "protein_targeted_by_drug": 2,
        "drug_treats_disease": 3,
        "disease_treated_by_drug": 4,
        "drug_causes_side_effect": 5,
        "side_effect_caused_by_drug": 6,
        "protein_interacts_protein": 7
    }

    def __init__(self):
        self.nx_graph = nx.MultiDiGraph()
        self.node_to_idx = {}
        self.idx_to_node = {}
        self.node_types = []
        self.drug_indices = {} # DrugID -> global node index
        self.drug_features = {} # DrugID -> 137-dim feature vector
        self.node_features = None

    def build_graph(self, exclude_test_pairs: List[Tuple[str, str]] = None):
        """
        Builds the heterogeneous graph.
        Crucial Leakage Prevention: Any drug pair in exclude_test_pairs has its
        direct interaction edge excluded from message passing.
        """
        data = BiomedicalDatasetLoader.load_benchmark_data()
        drugs = data["drugs"]
        interactions = data["interactions"]

        self.nx_graph.clear()
        self.node_to_idx.clear()
        self.idx_to_node.clear()
        self.node_types.clear()
        self.drug_indices.clear()
        self.drug_features.clear()

        # 1. Register Drug nodes
        for d in drugs:
            idx = len(self.node_to_idx)
            self.node_to_idx[d["id"]] = idx
            self.idx_to_node[idx] = d["id"]
            self.node_types.append(self.NODE_TYPES["drug"])
            self.drug_indices[d["id"]] = idx
            
            # Extract molecular features from SMILES
            feats = extractor.extract_full_drug_features(d["smiles"])
            self.drug_features[d["id"]] = feats
            self.nx_graph.add_node(idx, type="drug", id=d["id"], name=d["name"])

        # 2. Register Protein, Disease, and Side Effect nodes
        for d in drugs:
            # Targets
            for p in d.get("targets", []):
                p_key = f"PROT:{p}"
                if p_key not in self.node_to_idx:
                    p_idx = len(self.node_to_idx)
                    self.node_to_idx[p_key] = p_idx
                    self.idx_to_node[p_idx] = p_key
                    self.node_types.append(self.NODE_TYPES["protein"])
                    self.nx_graph.add_node(p_idx, type="protein", name=p)

            # Diseases
            for dis in d.get("diseases", []):
                dis_key = f"DIS:{dis}"
                if dis_key not in self.node_to_idx:
                    dis_idx = len(self.node_to_idx)
                    self.node_to_idx[dis_key] = dis_idx
                    self.idx_to_node[dis_idx] = dis_key
                    self.node_types.append(self.NODE_TYPES["disease"])
                    self.nx_graph.add_node(dis_idx, type="disease", name=dis)

            # Side effects
            for se in d.get("side_effects", []):
                se_key = f"SE:{se}"
                if se_key not in self.node_to_idx:
                    se_idx = len(self.node_to_idx)
                    self.node_to_idx[se_key] = se_idx
                    self.idx_to_node[se_idx] = se_key
                    self.node_types.append(self.NODE_TYPES["side_effect"])
                    self.nx_graph.add_node(se_idx, type="side_effect", name=se)

        # 3. Add Heterogeneous Edges (Drug-Target, Drug-Disease, Drug-Side Effect)
        for d in drugs:
            d_idx = self.drug_indices[d["id"]]
            for p in d.get("targets", []):
                p_idx = self.node_to_idx[f"PROT:{p}"]
                self.nx_graph.add_edge(d_idx, p_idx, rel_type=self.REL_TYPES["drug_targets_protein"])
                self.nx_graph.add_edge(p_idx, d_idx, rel_type=self.REL_TYPES["protein_targeted_by_drug"])

            for dis in d.get("diseases", []):
                dis_idx = self.node_to_idx[f"DIS:{dis}"]
                self.nx_graph.add_edge(d_idx, dis_idx, rel_type=self.REL_TYPES["drug_treats_disease"])
                self.nx_graph.add_edge(dis_idx, d_idx, rel_type=self.REL_TYPES["disease_treated_by_drug"])

            for se in d.get("side_effects", []):
                se_idx = self.node_to_idx[f"SE:{se}"]
                self.nx_graph.add_edge(d_idx, se_idx, rel_type=self.REL_TYPES["drug_causes_side_effect"])
                self.nx_graph.add_edge(se_idx, d_idx, rel_type=self.REL_TYPES["side_effect_caused_by_drug"])

        # 4. Add Known Protein-Protein Interactions (PPI)
        ppi_pairs = [
            ("PTGS1", "PTGS2"), ("CYP3A4", "CYP2C19"), ("CYP2C9", "CYP2C19"),
            ("CACNA1C", "CACNA1D"), ("AGTR1", "PPARG"), ("ATP1A1", "ATP1A2")
        ]
        for p1, p2 in ppi_pairs:
            k1, k2 = f"PROT:{p1}", f"PROT:{p2}"
            if k1 in self.node_to_idx and k2 in self.node_to_idx:
                idx1 = self.node_to_idx[k1]
                idx2 = self.node_to_idx[k2]
                self.nx_graph.add_edge(idx1, idx2, rel_type=self.REL_TYPES["protein_interacts_protein"])
                self.nx_graph.add_edge(idx2, idx1, rel_type=self.REL_TYPES["protein_interacts_protein"])

        # 5. Add Drug-Drug Interaction Edges (EXCLUDING held-out test pairs to prevent graph edge leakage!)
        exclude_set = set()
        if exclude_test_pairs:
            for da, db in exclude_test_pairs:
                exclude_set.add((da, db))
                exclude_set.add((db, da))

        for d1, d2, _, _ in interactions:
            if (d1, d2) not in exclude_set and d1 in self.drug_indices and d2 in self.drug_indices:
                idx1 = self.drug_indices[d1]
                idx2 = self.drug_indices[d2]
                self.nx_graph.add_edge(idx1, idx2, rel_type=self.REL_TYPES["drug_interacts_drug"])
                self.nx_graph.add_edge(idx2, idx1, rel_type=self.REL_TYPES["drug_interacts_drug"])

        # 6. Build Initial Node Feature Matrix (Tensor of shape [num_nodes, in_dim])
        # Drug nodes get 137-dim molecular features; other entity types get one-hot category projection
        total_nodes = len(self.node_to_idx)
        feature_dim = 137
        node_feats = np.zeros((total_nodes, feature_dim), dtype=np.float32)

        for d_id, idx in self.drug_indices.items():
            node_feats[idx] = self.drug_features[d_id]

        # For non-drug nodes, construct biologically grounded embedding based on connected drug averages
        for idx in range(total_nodes):
            if self.node_types[idx] != self.NODE_TYPES["drug"]:
                in_drugs = [u for u, v, _ in self.nx_graph.in_edges(idx, data=True) if self.node_types[u] == self.NODE_TYPES["drug"]]
                if in_drugs:
                    node_feats[idx] = np.mean([node_feats[u] for u in in_drugs], axis=0)
                else:
                    # Deterministic orthogonal type embedding
                    t = self.node_types[idx]
                    node_feats[idx, t % feature_dim] = 1.0

        self.node_features = torch.tensor(node_feats, dtype=torch.float32)
        return self

    def get_pyg_tensors(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns PyTorch tensors for GNN computation:
        (node_features, edge_index, edge_type, node_type)
        """
        edge_list = []
        edge_types = []
        for u, v, data in self.nx_graph.edges(data=True):
            edge_list.append([u, v])
            edge_types.append(data.get("rel_type", 0))

        if edge_list:
            edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
            edge_type = torch.tensor(edge_types, dtype=torch.long)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_type = torch.empty((0,), dtype=torch.long)

        node_type = torch.tensor(self.node_types, dtype=torch.long)
        return self.node_features, edge_index, edge_type, node_type
