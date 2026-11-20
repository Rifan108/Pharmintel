import os
import sys
import json
import pytest
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
RESULTS_DIR = os.path.join(BASE_DIR, "ml", "results")
WEIGHTS_PATH = os.path.join(BASE_DIR, "ml", "saved_models", "pharmintel_hybridgnn_weights.pt")
SUMMARY_PATH = os.path.join(RESULTS_DIR, "evaluation_summary.json")

EXPECTED_GRAPHS = [
    "ablation_study_comparison.png",
    "class_distribution.png",
    "confusion_matrix_heatmap.png",
    "model_performance_comparison.png",
    "precision_recall_curve.png",
    "roc_curve.png",
    "training_vs_validation_accuracy.png",
    "training_vs_validation_loss.png"
]

def test_evaluation_summary_exists():
    assert os.path.exists(SUMMARY_PATH), "evaluation_summary.json must exist in ml/results"
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert "performance_summary" in summary
    assert "model_comparison" in summary
    assert "ablation_study" in summary

def test_model_performance_exceeds_thresholds():
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    perf = summary["performance_summary"]

    assert perf["accuracy"] >= 0.90, f"Independent test accuracy {perf['accuracy']} must be >= 0.90"
    assert perf["macro_f1"] >= 0.90, f"Macro F1 {perf['macro_f1']} must be >= 0.90"
    assert perf["contraindicated_sensitivity"] >= 0.95, f"Contraindicated sensitivity {perf['contraindicated_sensitivity']} must be >= 0.95"
    assert perf["roc_auc"] >= 0.95, f"ROC-AUC {perf['roc_auc']} must be >= 0.95"

def test_all_eight_graphs_exist_and_meet_dpi():
    for graph_name in EXPECTED_GRAPHS:
        graph_path = os.path.join(RESULTS_DIR, graph_name)
        assert os.path.exists(graph_path), f"Required graph {graph_name} does not exist"
        assert os.path.getsize(graph_path) > 10000, f"Graph {graph_name} has invalid file size"

        with Image.open(graph_path) as img:
            dpi = img.info.get("dpi", (0, 0))
            assert dpi[0] >= 295, f"Graph {graph_name} DPI {dpi[0]} is below 300 DPI publication requirement"

def test_baselines_comparison_integrity():
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    comp = summary["model_comparison"]

    expected_models = [
        "Logistic Regression",
        "Decision Tree",
        "Support Vector Machine",
        "Random Forest",
        "MLP Neural Network",
        "Homogeneous GCN",
        "PHARMINTEL-HYBRIDGNN (Proposed)"
    ]

    for model_name in expected_models:
        assert model_name in comp, f"Model {model_name} missing from model_comparison"
        assert "accuracy" in comp[model_name]
        assert "macro_f1" in comp[model_name]

    # Proposed model must strictly outperform all classical and homogeneous baselines
    proposed_acc = comp["PHARMINTEL-HYBRIDGNN (Proposed)"]["accuracy"]
    for base_model in ["Logistic Regression", "Decision Tree", "Support Vector Machine", "Random Forest", "Homogeneous GCN"]:
        assert proposed_acc > comp[base_model]["accuracy"], f"Proposed model ({proposed_acc}) must outperform {base_model} ({comp[base_model]['accuracy']})"

def test_ablation_study_integrity():
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    abl = summary["ablation_study"]

    assert len(abl) >= 5, "Ablation study must evaluate at least 5 configurations"
    assert "Full Proposed (PHARMINTEL-HYBRIDGNN)" in abl
    assert "Baseline (Homogeneous GCN)" in abl

    full_f1 = abl["Full Proposed (PHARMINTEL-HYBRIDGNN)"]["f1"]
    base_f1 = abl["Baseline (Homogeneous GCN)"]["f1"]
    assert full_f1 > base_f1, f"Full model F1 ({full_f1}) must exceed baseline GCN F1 ({base_f1})"

def test_ddi_layer2_service_integration():
    from app.services.ddi_layer2_service import DDILayer2Service
    DDILayer2Service.initialize_model()
    assert DDILayer2Service._model is not None, "DDILayer2Service model must initialize properly"

    res = DDILayer2Service.predict_pair_ml("CC(=O)Oc1ccccc1C(=O)O", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    assert "predicted_category" in res
    assert "confidence" in res
    assert "probabilities" in res
    assert res["predicted_category"] in ["Contraindicated", "Major", "Moderate", "Minor"]
