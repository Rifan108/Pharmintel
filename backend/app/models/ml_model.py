from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from datetime import datetime
from app.database import Base

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False) # e.g. PHARMINTEL-HYBRIDGNN
    version = Column(String(50), unique=True, nullable=False) # e.g. v1.0.0
    architecture = Column(String(255), nullable=False) # HGT + RGCN + MetaPathAttention
    dataset_name = Column(String(255), nullable=False) # BioSNAP-DDI Benchmark
    dataset_records = Column(Integer, default=0)
    test_accuracy = Column(Float, nullable=False)
    test_precision = Column(Float, nullable=False)
    test_recall = Column(Float, nullable=False)
    test_macro_f1 = Column(Float, nullable=False)
    test_weighted_f1 = Column(Float, nullable=False)
    test_roc_auc = Column(Float, nullable=False)
    test_pr_auc = Column(Float, nullable=False)
    metrics_json = Column(Text, nullable=True) # Full class-wise metrics & confusion matrix
    weights_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    drug_a = Column(String(255), nullable=False, index=True)
    drug_b = Column(String(255), nullable=False, index=True)
    layer_used = Column(String(50), nullable=False) # LAYER_1_RULE, LAYER_2_HYBRIDGNN
    predicted_category = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities_json = Column(Text, nullable=True)
    model_version = Column(String(50), nullable=True)
    evidence_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
