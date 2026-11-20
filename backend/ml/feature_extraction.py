import re
import math
import hashlib
import numpy as np
from typing import Dict, List, Tuple, Any

# Atomic masses for standard elements in organic drugs
ATOMIC_WEIGHTS = {
    'H': 1.008, 'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998,
    'P': 30.974, 'S': 32.065, 'Cl': 35.453, 'Br': 79.904, 'I': 126.904
}

class MolecularFeatureExtractor:
    """
    Extracts authentic molecular fingerprints and physicochemical descriptors from SMILES.
    Implements circular neighborhood hashing (similar to ECFP / Morgan fingerprints)
    and physicochemical property estimators.
    """
    def __init__(self, n_bits: int = 128, radius: int = 2):
        self.n_bits = n_bits
        self.radius = radius

    def parse_smiles_atoms(self, smiles: str) -> List[Dict[str, Any]]:
        """
        Tokenizes SMILES string into atomic nodes with properties.
        """
        # Regex to match bracketed atoms [NH+], two-letter elements (Cl, Br), or single letters (C, N, O, F, P, S, I, c, n, o, s)
        pattern = r"(\[[^\]]+\]|Cl|Br|C|N|O|F|P|S|I|c|n|o|s|B)"
        raw_tokens = re.findall(pattern, smiles)

        atoms = []
        for i, tok in enumerate(raw_tokens):
            clean_elem = re.sub(r"[^A-Za-z]", "", tok)
            is_aromatic = clean_elem.islower()
            elem_upper = clean_elem.capitalize()
            mass = ATOMIC_WEIGHTS.get(elem_upper, 12.011)

            atoms.append({
                "index": i,
                "element": elem_upper,
                "is_aromatic": is_aromatic,
                "mass": mass,
                "raw": tok
            })
        return atoms

    def compute_circular_fingerprint(self, smiles: str) -> np.ndarray:
        """
        Computes circular topological neighborhood hash fingerprint (ECFP-like).
        Deterministic, invariant to SMILES whitespace.
        """
        if not smiles:
            return np.zeros(self.n_bits, dtype=np.float32)

        atoms = self.parse_smiles_atoms(smiles)
        if not atoms:
            return np.zeros(self.n_bits, dtype=np.float32)

        fp = np.zeros(self.n_bits, dtype=np.float32)

        # Radius 0: individual atom properties
        atom_identifiers = []
        for a in atoms:
            h_input = f"{a['element']}_{a['is_aromatic']}".encode("utf-8")
            hash_val = int(hashlib.sha256(h_input).hexdigest(), 16)
            atom_identifiers.append(hash_val)
            fp[hash_val % self.n_bits] = 1.0

        # Radius 1 & 2: local sequence-linear & circular context hashes
        for r in range(1, self.radius + 1):
            new_identifiers = []
            for i in range(len(atoms)):
                # Neighbors in linear SMILES adjacency
                left_id = atom_identifiers[i - 1] if i > 0 else 0
                curr_id = atom_identifiers[i]
                right_id = atom_identifiers[i + 1] if i + 1 < len(atoms) else 0

                context_str = f"r{r}:{left_id}:{curr_id}:{right_id}".encode("utf-8")
                nh_val = int(hashlib.sha256(context_str).hexdigest(), 16)
                new_identifiers.append(nh_val)
                fp[nh_val % self.n_bits] = 1.0
            atom_identifiers = new_identifiers

        return fp

    def compute_physicochemical_descriptors(self, smiles: str) -> np.ndarray:
        """
        Calculates key physicochemical descriptors:
        [Molecular Weight, Carbon Count, Nitrogen Count, Oxygen Count, Halogen Count,
         Estimated H-Bond Donors, Estimated H-Bond Acceptors, Aromatic Ring Atoms, Estimated LogP approximation]
        """
        if not smiles:
            return np.zeros(9, dtype=np.float32)

        atoms = self.parse_smiles_atoms(smiles)
        mw = sum(a['mass'] for a in atoms)
        c_count = sum(1 for a in atoms if a['element'] == 'C')
        n_count = sum(1 for a in atoms if a['element'] == 'N')
        o_count = sum(1 for a in atoms if a['element'] == 'O')
        halogen_count = sum(1 for a in atoms if a['element'] in ['F', 'Cl', 'Br', 'I'])
        aromatic_count = sum(1 for a in atoms if a['is_aromatic'])

        # H-bond acceptors: N and O atoms
        hba = n_count + o_count
        # H-bond donors estimated from NH and OH groups
        hbd = len(re.findall(r"\[NH|\[OH|N[Hh]|O[Hh]", smiles))
        if hbd == 0 and (n_count > 0 or o_count > 0):
            # Conservative estimate
            hbd = min(2, (n_count + o_count) // 2)

        # Simplified Wildman-Crippen-style logP heuristic
        est_logp = (c_count * 0.28) + (halogen_count * 0.5) - (o_count * 0.35) - (n_count * 0.30)

        # Normalize features
        feats = np.array([
            mw / 500.0,
            c_count / 30.0,
            n_count / 10.0,
            o_count / 10.0,
            halogen_count / 5.0,
            hba / 10.0,
            hbd / 5.0,
            aromatic_count / 20.0,
            est_logp / 5.0
        ], dtype=np.float32)

        return feats

    def extract_full_drug_features(self, smiles: str) -> np.ndarray:
        """
        Combines 128-bit circular topological fingerprint + 9-dim physicochemical descriptors = 137-dim vector.
        """
        fp = self.compute_circular_fingerprint(smiles)
        desc = self.compute_physicochemical_descriptors(smiles)
        return np.concatenate([fp, desc]).astype(np.float32)

extractor = MolecularFeatureExtractor(n_bits=128, radius=2)
