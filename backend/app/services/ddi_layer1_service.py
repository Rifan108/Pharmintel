from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Dict, Any, Optional
from app.models.medicine import Medicine, DrugInteraction
from app.schemas.interaction import InteractionDetail

class DDILayer1Service:
    """
    Safety Layer 1: Authoritative Curated Clinical Drug-Drug Interaction Rules
    Deterministic, verified pharmacology evidence.
    """
    @staticmethod
    def _extract_root_drug(name: str) -> str:
        if not name:
            return ""
        import re
        # Remove strengths e.g. 500mg, 50mg, 5 ml, etc.
        clean = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|tablets?|capsules?)\b", "", name, flags=re.I).strip()
        words = re.findall(r"[a-zA-Z]{4,}", clean)
        return words[0] if words else clean

    @classmethod
    def check_pair(cls, db: Session, drug_a_name: str, drug_b_name: str) -> Optional[InteractionDetail]:
        if not drug_a_name or not drug_b_name:
            return None

        # Clean names
        name_a = drug_a_name.strip()
        name_b = drug_b_name.strip()

        # 1. Exact / Substring query in both symmetric directions
        rule = db.query(DrugInteraction).filter(
            or_(
                and_(DrugInteraction.drug_a_generic.ilike(f"%{name_a}%"), DrugInteraction.drug_b_generic.ilike(f"%{name_b}%")),
                and_(DrugInteraction.drug_a_generic.ilike(f"%{name_b}%"), DrugInteraction.drug_b_generic.ilike(f"%{name_a}%"))
            )
        ).first()

        # 2. If not matched, query using pharmacological root keywords (e.g. "Losartan", "Amlodipine")
        if not rule:
            root_a = cls._extract_root_drug(name_a)
            root_b = cls._extract_root_drug(name_b)
            if root_a and root_b and len(root_a) >= 3 and len(root_b) >= 3:
                rule = db.query(DrugInteraction).filter(
                    or_(
                        and_(DrugInteraction.drug_a_generic.ilike(f"%{root_a}%"), DrugInteraction.drug_b_generic.ilike(f"%{root_b}%")),
                        and_(DrugInteraction.drug_a_generic.ilike(f"%{root_b}%"), DrugInteraction.drug_b_generic.ilike(f"%{root_a}%"))
                    )
                ).first()

        if rule:
            return InteractionDetail(
                drug_a=rule.drug_a_generic,
                drug_b=rule.drug_b_generic,
                severity=rule.severity_category,
                mechanism=rule.mechanism,
                clinical_consequences=rule.clinical_consequences,
                source=rule.evidence_source,
                source_reference=rule.source_reference,
                last_verified_date=rule.last_verified_date,
                layer_detected="LAYER_1_CLINICAL_RULE",
                ml_confidence=None,
                class_probabilities=None
            )
        return None
