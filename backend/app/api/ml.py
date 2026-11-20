import os
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ml.dataset_loader import BiomedicalDatasetLoader
from app.services.ddi_layer2_service import DDILayer2Service

router = APIRouter(prefix="/ml", tags=["ML Research & Explainability"])

class MLPredictRequest(BaseModel):
    drug_a_smiles: str
    drug_b_smiles: str

@router.get("/metrics")
def get_ml_metrics():
    """
    Returns authentic measured benchmark metrics, model comparison,
    and ablation results from the experimental pipeline.
    """
    results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "results")
    summary_path = os.path.join(results_dir, "evaluation_summary.json")

    if not os.path.exists(summary_path):
        raise HTTPException(
            status_code=503,
            detail="Evaluation summary is currently pending. Please run the training pipeline."
        )

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@router.get("/graphs/{graph_name}")
def get_evaluation_graph(graph_name: str):
    """
    Serves the 8 authentic evaluation graphs generated from experimental data.
    """
    results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "results")
    allowed_graphs = {
        "accuracy": "training_vs_validation_accuracy.png",
        "loss": "training_vs_validation_loss.png",
        "confusion_matrix": "confusion_matrix_heatmap.png",
        "roc": "roc_curve.png",
        "pr_curve": "precision_recall_curve.png",
        "comparison": "model_performance_comparison.png",
        "class_distribution": "class_distribution.png",
        "ablation": "ablation_study_comparison.png"
    }

    if graph_name not in allowed_graphs:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_name}' not recognized. Allowed: {list(allowed_graphs.keys())}")

    filename = allowed_graphs[graph_name]
    file_path = os.path.join(results_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Graph image '{filename}' not found.")

    return FileResponse(file_path, media_type="image/png")

@router.post("/predict")
def predict_pair(req: MLPredictRequest):
    """
    Executes symmetric inference with PHARMINTEL-HYBRIDGNN.
    """
    try:
        return DDILayer2Service.predict_pair_ml(req.drug_a_smiles, req.drug_b_smiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
