import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class SMARTInput:
    alternatives: List[str]
    criteria: List[str]
    performance: np.ndarray
    weights_raw: np.ndarray
    types: List[str]
    weight_method: str = "direct"


class SMARTEngine:
    @staticmethod
    def compute_weights(weights_raw: np.ndarray, method: str = "direct") -> np.ndarray:
        w_raw = np.atleast_1d(np.asarray(weights_raw, dtype=float))
        n = len(w_raw)
        if n == 0:
            raise ValueError("Minimal harus ada satu kriteria.")

        if method == "equal":
            return np.full(n, 1.0 / n)

        if method == "roc":
            roc_standard = np.zeros(n)
            for k in range(1, n + 1):
                roc_standard[k - 1] = (1 / n) * sum(1 / j for j in range(k, n + 1))
            weights = np.zeros(n)
            for i, rank in enumerate(w_raw):
                rank_index = int(rank) - 1
                weights[i] = roc_standard[rank_index] if 0 <= rank_index < n else 1.0 / n
            return weights / weights.sum() if weights.sum() > 0 else np.full(n, 1.0 / n)

        total = w_raw.sum()
        if total <= 0:
            return np.full(n, 1.0 / n)
        return w_raw / total

    @staticmethod
    def compute_utility(performance: np.ndarray, types: List[str]) -> np.ndarray:
        X = np.atleast_2d(np.asarray(performance, dtype=float))
        if X.shape[1] != len(types):
            raise ValueError("Jumlah tipe kriteria tidak sesuai dengan jumlah kolom matriks.")

        U = np.zeros_like(X, dtype=float)
        for j, ctype in enumerate(types):
            col = X[:, j]
            x_min, x_max = float(col.min()), float(col.max())
            if np.isclose(x_max, x_min):
                U[:, j] = 1.0
                continue
            if ctype.lower() == "benefit":
                U[:, j] = (col - x_min) / (x_max - x_min)
            elif ctype.lower() == "cost":
                U[:, j] = (x_max - col) / (x_max - x_min)
            else:
                raise ValueError(f"Tipe kriteria tidak dikenal: {ctype}")
        return U

    def calculate(self, data: SMARTInput) -> Dict[str, Any]:
        if len(data.alternatives) < 2:
            raise ValueError("Minimal diperlukan dua alternatif.")
        if len(data.criteria) < 2:
            raise ValueError("Minimal diperlukan dua kriteria.")

        weights = self.compute_weights(data.weights_raw, data.weight_method)
        U = self.compute_utility(data.performance, data.types)
        aggregation_matrix = U * weights
        scores = np.atleast_1d(U @ weights)
        ranking = np.argsort(scores)[::-1].tolist()

        return {
            "normalized_weights": weights.tolist(),
            "utility_matrix": U.tolist(),
            "aggregation_matrix": aggregation_matrix.tolist(),
            "final_scores": scores.tolist(),
            "ranking_indices": ranking,
            "ranked_alternatives": [data.alternatives[i] for i in ranking],
        }

    def run_oat_sensitivity(self, data: SMARTInput, target_idx: int = 0, steps: int = 25):
        w_base = self.compute_weights(data.weights_raw, data.weight_method)
        if target_idx < 0 or target_idx >= len(w_base):
            target_idx = 0

        weight_vals = np.linspace(0.0, 1.0, steps)
        scores_history = []
        U = self.compute_utility(data.performance, data.types)

        for target_weight in weight_vals:
            w_new = w_base.copy()
            others_total = 1.0 - float(w_base[target_idx])
            if others_total > 1e-9:
                for j in range(len(w_base)):
                    if j != target_idx:
                        w_new[j] = float(w_base[j]) * (1.0 - target_weight) / others_total
            else:
                n_other = len(w_base) - 1
                if n_other > 0:
                    for j in range(len(w_base)):
                        if j != target_idx:
                            w_new[j] = (1.0 - target_weight) / n_other
            w_new[target_idx] = target_weight
            scores_history.append(np.atleast_1d(U @ w_new).tolist())

        return weight_vals.tolist(), scores_history
