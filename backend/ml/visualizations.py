import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless rendering for backend / CI
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Dict, List, Any

# =========================================================================
# IEEE Publication Styling & Healthcare Color Palette
# =========================================================================
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#334155'
plt.rcParams['axes.linewidth'] = 1.0

NAVY_BLUE = "#1e3a8a"    # Primary / Proposed model
EMERALD = "#059669"      # Minor / Safe
AMBER_WARN = "#d97706"   # Moderate
CRIMSON = "#dc2626"      # Contraindicated / High Alert
INDIGO = "#4f46e5"       # Major
SLATE_GRAY = "#64748b"   # Baselines / Muted
ACCENT_CYAN = "#0891b2"
GRID_COLOR = "#e2e8f0"

CLASS_COLORS = {
    "Contraindicated": CRIMSON,
    "Major": INDIGO,
    "Moderate": AMBER_WARN,
    "Minor": EMERALD
}

class VisualizationsGenerator:
    """
    Generates IEEE-format research-grade evaluation figures from actual measured experimental results.
    Strictly adheres to 300+ DPI minimum, professional typography, and publication layouts.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_accuracy_curve(self, history: Dict[str, List[float]]) -> str:
        """
        7. training_vs_validation_accuracy.png
        Regenerates training-versus-validation accuracy from genuine epoch logs.
        """
        fig, ax = plt.subplots(figsize=(8, 5.2), dpi=300)
        epochs = np.arange(1, len(history["train_acc"]) + 1)

        ax.plot(epochs, history["train_acc"], color=NAVY_BLUE, label="Training Accuracy", linewidth=2.4)
        ax.plot(epochs, history["val_acc"], color=ACCENT_CYAN, linestyle="--", label="Validation Accuracy", linewidth=2.4)

        # Highlight best validation epoch
        best_idx = int(np.argmax(history["val_acc"]))
        best_ep = epochs[best_idx]
        best_val = history["val_acc"][best_idx]
        ax.scatter([best_ep], [best_val], color=CRIMSON, s=70, zorder=5)
        ax.annotate(
            f"Peak Val: {best_val*100:.1f}% (Ep {best_ep})",
            xy=(best_ep, best_val),
            xytext=(best_ep - 25, best_val - 0.10 if best_val > 0.85 else best_val + 0.06),
            arrowprops=dict(facecolor=CRIMSON, shrink=0.08, width=1.2, headwidth=6),
            fontsize=9.5, fontweight="bold", color=CRIMSON,
            bbox=dict(boxstyle="round,pad=0.3", fc="#fef2f2", ec="#fca5a5", lw=1)
        )

        ax.set_title("Training vs. Validation Accuracy (PHARMINTEL-HYBRIDGNN)", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
        ax.set_xlabel("Training Epoch", fontsize=11, fontweight="medium", labelpad=8)
        ax.set_ylabel("Classification Accuracy", fontsize=11, fontweight="medium", labelpad=8)
        ax.set_ylim([0.40, 1.03])
        ax.set_xlim([1, len(epochs)])
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.9)
        ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=10, loc="lower right", shadow=True)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "training_vs_validation_accuracy.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_loss_curve(self, history: Dict[str, List[float]]) -> str:
        """
        8. training_vs_validation_loss.png
        Regenerates training-versus-validation loss curve from genuine epoch logs.
        """
        fig, ax = plt.subplots(figsize=(8, 5.2), dpi=300)
        epochs = np.arange(1, len(history["train_loss"]) + 1)

        ax.plot(epochs, history["train_loss"], color=CRIMSON, label="Training Loss (Weighted Cross-Entropy)", linewidth=2.4)
        ax.plot(epochs, history["val_loss"], color=AMBER_WARN, linestyle="--", label="Validation Loss", linewidth=2.4)

        ax.set_title("Training vs. Validation Loss Convergence Curve", fontsize=13, fontweight="bold", pad=14, color="#0f172a")
        ax.set_xlabel("Training Epoch", fontsize=11, fontweight="medium", labelpad=8)
        ax.set_ylabel("Loss Value", fontsize=11, fontweight="medium", labelpad=8)
        ax.set_xlim([1, len(epochs)])
        ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.9)
        ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=10, loc="upper right", shadow=True)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "training_vs_validation_loss.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_confusion_matrix(self, cm: np.ndarray, class_names: List[str]) -> str:
        """
        3. confusion_matrix_heatmap.png
        Generates independent test confusion matrix with raw counts and normalized percentages.
        """
        fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=300)
        cm_norm = cm.astype('float') / np.maximum(cm.sum(axis=1, keepdims=True), 1)

        im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.set_ylabel("Interaction Pair Count", rotation=-90, va="bottom", fontsize=10)

        ax.set(
            xticks=np.arange(cm.shape[1]),
            yticks=np.arange(cm.shape[0]),
            xticklabels=class_names,
            yticklabels=class_names,
            title="Confusion Matrix Heatmap (Independent Held-Out Test Set)",
            ylabel="Actual Ground-Truth Severity",
            xlabel="Predicted Interaction Severity"
        )
        ax.set_title("Confusion Matrix Heatmap (Independent Held-Out Test Set)", fontsize=12, fontweight="bold", pad=14)
        plt.setp(ax.get_xticklabels(), rotation=25, ha="right", rotation_mode="anchor", fontsize=10)
        plt.setp(ax.get_yticklabels(), fontsize=10)

        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                count = cm[i, j]
                pct = cm_norm[i, j] * 100
                txt = f"{count}\n({pct:.1f}%)" if cm[i].sum() > 0 else f"{count}"
                text_color = "white" if count > thresh else "#0f172a"
                ax.text(j, i, txt, ha="center", va="center", color=text_color,
                        fontweight="bold", fontsize=9.5)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "confusion_matrix_heatmap.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_class_distribution(
        self,
        full_counts: Dict[str, int],
        train_counts: Dict[str, int],
        val_counts: Dict[str, int],
        test_counts: Dict[str, int]
    ) -> str:
        """
        2. class_distribution.png
        Shows: Original, Training, Validation, and Testing class distributions side-by-side
        with exact counts and percentages to demonstrate balanced stratified sampling.
        """
        fig, axes = plt.subplots(1, 4, figsize=(16, 4.8), dpi=300, sharey=False)
        categories = ["Contraindicated", "Major", "Moderate", "Minor"]
        splits = [
            ("Original Dataset (100%)", full_counts, axes[0]),
            ("Training Split (70%)", train_counts, axes[1]),
            ("Validation Split (15%)", val_counts, axes[2]),
            ("Testing Split (15%)", test_counts, axes[3]),
        ]

        colors = [CRIMSON, INDIGO, AMBER_WARN, EMERALD]

        for title, counts_dict, ax in splits:
            total = sum(counts_dict.values())
            counts = [counts_dict.get(c, 0) for c in categories]
            bars = ax.bar(categories, counts, color=colors, width=0.6, edgecolor="#334155", linewidth=0.8)

            ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
            ax.set_ylabel("Pair Count" if ax == axes[0] else "", fontsize=9.5)
            ax.grid(True, linestyle=":", color=GRID_COLOR, axis='y', alpha=0.8)
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)

            max_y = max(counts) if counts else 10
            ax.set_ylim([0, max_y * 1.25])

            for bar in bars:
                h = bar.get_height()
                pct = (h / total * 100) if total > 0 else 0
                ax.text(
                    bar.get_x() + bar.get_width() / 2, h + (max_y * 0.03),
                    f"{h}\n({pct:.1f}%)", ha="center", va="bottom",
                    fontweight="bold", fontsize=8.5, color="#0f172a"
                )

        fig.suptitle("PHARMINTEL Interaction Class Distribution & Stratified Split Integrity", fontsize=13, fontweight="bold", y=1.03)
        plt.tight_layout()
        path = os.path.join(self.output_dir, "class_distribution.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_model_performance_comparison(self, comparison_data: Dict[str, Dict[str, float]]) -> str:
        """
        4. model_performance_comparison.png
        Compares all benchmarked models (Logistic Regression, Decision Tree, SVM,
        Random Forest, MLP, Homogeneous GCN, Proposed PHARMINTEL-HYBRIDGNN).
        Evaluates: Accuracy, Precision, Recall, F1-Score.
        """
        fig, ax = plt.subplots(figsize=(12, 6.2), dpi=300)
        models = list(comparison_data.keys())
        metrics = ["accuracy", "precision", "recall", "macro_f1"]
        metric_labels = ["Accuracy", "Precision", "Recall", "Macro F1"]

        x = np.arange(len(models))
        width = 0.20
        palette = [NAVY_BLUE, ACCENT_CYAN, AMBER_WARN, CRIMSON]

        for i, (m_key, m_lbl) in enumerate(zip(metrics, metric_labels)):
            vals = [comparison_data[m].get(m_key, 0.0) for m in models]
            offset = (i - 1.5) * width
            bars = ax.bar(x + offset, vals, width, label=m_lbl, color=palette[i], alpha=0.92, edgecolor="#1e293b", linewidth=0.5)

            # Add value labels on top of proposed model
            for j, bar in enumerate(bars):
                if "PHARMINTEL" in models[j] or "Proposed" in models[j]:
                    h = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.012, f"{h*100:.1f}%",
                            ha="center", va="bottom", fontsize=7.5, fontweight="bold", color="#0f172a")

        ax.set_title("Benchmarked Model Performance Comparison (Independent Test Set)", fontsize=13, fontweight="bold", pad=14)
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=22, ha="right", fontsize=9.5, fontweight="medium")
        ax.set_ylabel("Score (0.00 – 1.00)", fontsize=11, fontweight="medium")
        ax.set_ylim([0.0, 1.12])
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.8, axis='y')
        ax.axhline(0.90, color=EMERALD, linestyle="--", linewidth=1.2, alpha=0.7, label="90% Benchmark Threshold")
        ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=9.5, loc="upper left", ncol=3)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "model_performance_comparison.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_ablation_comparison(self, ablation_data: Dict[str, Dict[str, float]]) -> str:
        """
        1. ablation_study_comparison.png
        Ablation study comparing Accuracy, Precision, Recall, and F1 across components.
        """
        fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
        variants = list(ablation_data.keys())
        metrics = ["accuracy", "precision", "recall", "f1"]
        metric_labels = ["Accuracy", "Precision", "Recall", "Macro F1"]

        y = np.arange(len(variants))
        height = 0.20
        palette = [NAVY_BLUE, ACCENT_CYAN, AMBER_WARN, EMERALD]

        for i, (m_key, m_lbl) in enumerate(zip(metrics, metric_labels)):
            vals = [ablation_data[v].get(m_key, 0.0) for v in variants]
            offset = (i - 1.5) * height
            ax.barh(y + offset, vals, height, label=m_lbl, color=palette[i], alpha=0.92, edgecolor="#1e293b", linewidth=0.5)

        ax.set_title("Ablation Study: Component Contributions to Clinical DDI Detection", fontsize=13, fontweight="bold", pad=14)
        ax.set_yticks(y)
        ax.set_yticklabels(variants, fontsize=9.5, fontweight="medium")
        ax.set_xlabel("Score (0.00 – 1.00)", fontsize=11, fontweight="medium")
        ax.set_xlim([0.50, 1.05])
        ax.xaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.8, axis='x')
        ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=9.5, loc="lower right")

        plt.tight_layout()
        path = os.path.join(self.output_dir, "ablation_study_comparison.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_roc_curve(self, roc_data: Dict[str, Any]) -> str:
        """
        6. roc_curve.png
        Multi-class One-vs-Rest ROC curves with AUC values and reference random line.
        """
        fig, ax = plt.subplots(figsize=(7.5, 5.8), dpi=300)
        colors = [CRIMSON, INDIGO, AMBER_WARN, EMERALD]

        for idx, (cls_name, curve) in enumerate(roc_data.items()):
            color = colors[idx % len(colors)]
            ax.plot(
                curve["fpr"], curve["tpr"], color=color,
                label=f"{cls_name} (AUC = {curve['auc']:.3f})",
                linewidth=2.2
            )

        ax.plot([0, 1], [0, 1], 'k--', alpha=0.45, linewidth=1.5, label="Random Chance (AUC = 0.500)")
        ax.set_title("Multi-Class Receiver Operating Characteristic (ROC) Curves", fontsize=12, fontweight="bold", pad=14)
        ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=10.5, fontweight="medium")
        ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=10.5, fontweight="medium")
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([-0.02, 1.04])
        ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.8)
        ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=9.5, loc="lower right", shadow=True)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "roc_curve.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_pr_curve(self, pr_data: Dict[str, Any]) -> str:
        """
        5. precision_recall_curve.png
        Precision-Recall curves with Average Precision (AP) for each interaction class.
        """
        fig, ax = plt.subplots(figsize=(7.5, 5.8), dpi=300)
        colors = [CRIMSON, INDIGO, AMBER_WARN, EMERALD]

        for idx, (cls_name, curve) in enumerate(pr_data.items()):
            color = colors[idx % len(colors)]
            ax.plot(
                curve["recall"], curve["precision"], color=color,
                label=f"{cls_name} (AP = {curve['auc']:.3f})",
                linewidth=2.2
            )

        ax.set_title("Multi-Class Precision-Recall (PR) Curves", fontsize=12, fontweight="bold", pad=14)
        ax.set_xlabel("Recall (Sensitivity)", fontsize=10.5, fontweight="medium")
        ax.set_ylabel("Precision (Positive Predictive Value)", fontsize=10.5, fontweight="medium")
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([-0.02, 1.04])
        ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.8)
        ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=9.5, loc="lower left", shadow=True)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "precision_recall_curve.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return path
