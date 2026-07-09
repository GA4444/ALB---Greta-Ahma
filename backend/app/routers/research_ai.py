from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Attempt, Exercise, PedagogicalReview
from ..services.albanian_research_ai import (
    adaptive_next_item,
    augment_sentence,
    correction_metrics,
    deep_learning_sequence_dataset,
    final_experiment_protocol,
    generate_exercise,
    grade_fit_score,
    instruction_pair_from_exercise,
    irt_summary,
    knowledge_tracing_summary,
    pedagogical_feedback,
    rag_ablation_metrics,
    rubric_summary,
    model_training_status,
    training_commands,
)


router = APIRouter()


class AugmentationRequest(BaseModel):
    text: str = Field(..., description="Correct Albanian sentence/text")
    error_rate: float = Field(0.2, ge=0.0, le=1.0)
    error_types: Optional[List[str]] = None


class GeneratedExerciseRequest(BaseModel):
    seed_word: str
    grade: int = Field(3, ge=1, le=8)
    difficulty: str = Field("medium", description="easy | medium | hard")
    exercise_type: str = Field("missing_letter", description="missing_letter | find_error | explain_error")


class FeedbackRequest(BaseModel):
    student_answer: str
    correct_answer: str
    grade: int = Field(3, ge=1, le=8)


class CorrectionEvaluationRequest(BaseModel):
    source: str = Field(..., description="Original incorrect text")
    reference: str = Field(..., description="Gold corrected text")
    hypothesis: str = Field(..., description="System corrected text")


class GradeFitRequest(BaseModel):
    text: str
    grade: int = Field(3, ge=1, le=8)


class TeacherReviewRequest(BaseModel):
    reviewer_user_id: Optional[int] = None
    exercise_id: Optional[int] = None
    item_type: str = "generated_exercise"
    content_snapshot: Dict[str, Any]
    linguistic_accuracy: int = Field(..., ge=1, le=5)
    clarity: int = Field(..., ge=1, le=5)
    age_appropriateness: int = Field(..., ge=1, le=5)
    pedagogical_value: int = Field(..., ge=1, le=5)
    safety: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None
    approved_for_children: bool = False


class RAGAblationRequest(BaseModel):
    with_context: List[Dict[str, Any]]
    without_context: List[Dict[str, Any]]


@router.get("/research-ai/overview")
def research_ai_overview(db: Session = Depends(get_db)):
    """High-level PhD research module status and scientific framing."""
    total_exercises = db.query(Exercise).count()
    total_attempts = db.query(Attempt).count()
    return {
        "module": "AI-assisted Albanian spelling exercise generation and feedback",
        "scientific_focus": [
            "instruction fine-tuning dataset from existing exercises",
            "controlled Albanian orthographic error augmentation",
            "error detection, correction and pedagogical explanation",
            "safety layer: database/rules decide correctness, LLM explains only",
            "IRT-based difficulty calibration and anomaly detection",
            "ERRANT-inspired F0.5 and GLEU-like correction evaluation",
        ],
        "available_data": {
            "existing_exercises": total_exercises,
            "student_attempts": total_attempts,
        },
        "safety_principle": "LLM output is advisory; correctness must come from database answers or deterministic Albanian rules.",
    }


@router.get("/research-ai/instruction-dataset")
def export_instruction_dataset(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Convert existing exercises into instruction -> answer pairs for LoRA/QLoRA datasets."""
    exercises = (
        db.query(Exercise)
        .options(joinedload(Exercise.level), joinedload(Exercise.course))
        .filter(Exercise.enabled == True)
        .order_by(Exercise.id.asc())
        .limit(limit)
        .all()
    )
    pairs = [instruction_pair_from_exercise(ex) for ex in exercises]
    return {
        "count": len(pairs),
        "format": "instruction_tuning_jsonl_ready",
        "pairs": pairs,
    }


@router.post("/research-ai/augment")
def create_augmented_error_pair(body: AugmentationRequest):
    """Create corrupted -> correct examples with controlled Albanian error types."""
    return augment_sentence(body.text, error_rate=body.error_rate, error_types=body.error_types)


@router.post("/research-ai/generate-exercise")
def create_research_exercise(body: GeneratedExerciseRequest):
    """Generate a safe structured exercise candidate from a seed word and grade."""
    return generate_exercise(
        seed_word=body.seed_word,
        grade=body.grade,
        difficulty=body.difficulty,
        exercise_type=body.exercise_type,
    )


@router.post("/research-ai/feedback")
def explain_error_for_child(body: FeedbackRequest):
    """Generate short, supportive and rule-grounded pedagogical feedback."""
    return pedagogical_feedback(body.student_answer, body.correct_answer, grade=body.grade)


@router.post("/research-ai/evaluate-correction")
def evaluate_correction(body: CorrectionEvaluationRequest):
    """Return lightweight ERRANT-inspired F0.5 and GLEU-like correction metrics."""
    return correction_metrics(body.source, body.reference, body.hypothesis)


@router.post("/research-ai/grade-fit")
def evaluate_grade_fit(body: GradeFitRequest):
    """Check whether text metrics are plausible for a target grade."""
    return grade_fit_score(body.text, body.grade)


@router.get("/research-ai/irt-summary")
def get_irt_summary(
    min_attempts: int = Query(1, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Calibrate approximate user ability and exercise difficulty from attempts."""
    attempts = db.query(Attempt).all()
    summary = irt_summary(attempts)
    summary["items"] = [item for item in summary["items"] if item["attempts"] >= min_attempts]
    summary["users"] = [user for user in summary["users"] if user["attempts"] >= min_attempts]
    summary["interpretation"] = {
        "theta_ability": "higher means stronger estimated learner ability",
        "beta_difficulty": "higher means harder estimated exercise",
        "possible_anomaly": "very high/low accuracy items should be reviewed by a teacher or linguist",
    }
    return summary


@router.get("/research-ai/knowledge-tracing")
def get_knowledge_tracing(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    attempts = db.query(Attempt).options(joinedload(Attempt.exercise)).all()
    return knowledge_tracing_summary(attempts, user_id=user_id)


@router.get("/research-ai/adaptive-next-item")
def get_adaptive_next_item(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    attempts = db.query(Attempt).options(joinedload(Attempt.exercise)).all()
    exercises = db.query(Exercise).filter(Exercise.enabled == True).all()
    return adaptive_next_item(attempts, exercises, user_id=user_id)


@router.post("/research-ai/rag-ablation")
def compare_rag_vs_no_context(body: RAGAblationRequest):
    return rag_ablation_metrics(body.with_context, body.without_context)


@router.post("/research-ai/teacher-review")
def create_teacher_review(body: TeacherReviewRequest, db: Session = Depends(get_db)):
    review = PedagogicalReview(
        reviewer_user_id=body.reviewer_user_id,
        exercise_id=body.exercise_id,
        item_type=body.item_type,
        content_snapshot=json_dumps(body.content_snapshot),
        linguistic_accuracy=body.linguistic_accuracy,
        clarity=body.clarity,
        age_appropriateness=body.age_appropriateness,
        pedagogical_value=body.pedagogical_value,
        safety=body.safety,
        notes=body.notes,
        approved_for_children=body.approved_for_children,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "id": review.id,
        "approved_for_children": review.approved_for_children,
        "summary": rubric_summary([review]),
    }


@router.get("/research-ai/teacher-review-summary")
def get_teacher_review_summary(db: Session = Depends(get_db)):
    reviews = db.query(PedagogicalReview).all()
    return rubric_summary(reviews)


@router.get("/research-ai/final-experiment-protocol")
def get_final_experiment_protocol(db: Session = Depends(get_db)):
    return final_experiment_protocol({
        "exercise_count": db.query(Exercise).count(),
        "attempt_count": db.query(Attempt).count(),
        "review_count": db.query(PedagogicalReview).count(),
    })


@router.get("/research-ai/deep-learning-dataset")
def get_deep_learning_dataset(db: Session = Depends(get_db)):
    attempts = db.query(Attempt).options(joinedload(Attempt.exercise)).all()
    return deep_learning_sequence_dataset(attempts)


@router.get("/research-ai/model-training-status")
def get_model_training_status():
    return model_training_status()


@router.get("/research-ai/training-commands")
def get_training_commands():
    return training_commands()


def json_dumps(value: Dict[str, Any]) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)
