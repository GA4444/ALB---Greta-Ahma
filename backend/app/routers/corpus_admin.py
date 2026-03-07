"""
Admin endpoints for the Albanian Spelling Corpus (Korpusi i Drejtshkrimit).

PhD-level corpus management: CRUD, aggregation, linguistic analysis,
classification, validation, duplicate detection, per-class statistics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib
import json
import re
import math
from collections import Counter

router = APIRouter()


def verify_admin(user_id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CorpusDocumentCreate(BaseModel):
    title: str
    content: str
    author: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    dialect: Optional[str] = None
    source: Optional[str] = None
    fuse_class_code: Optional[str] = None
    class_id: Optional[int] = None

class CorpusDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    dialect: Optional[str] = None
    source: Optional[str] = None
    fuse_class_code: Optional[str] = None
    class_id: Optional[int] = None
    processing_status: Optional[str] = None
    is_validated: Optional[bool] = None
    validation_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# NLP Helpers
# ---------------------------------------------------------------------------

_ALBANIAN_WORD = re.compile(r"[a-zA-ZëËçÇ]+", re.UNICODE)
_SENTENCE_END = re.compile(r"[.!?]+")

def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _tokenize(text: str) -> list[str]:
    return _ALBANIAN_WORD.findall(text.lower())

def _count_sentences(text: str) -> int:
    parts = _SENTENCE_END.split(text.strip())
    return max(1, len([p for p in parts if p.strip()]))

def _process_document(doc: models.CorpusDocument) -> None:
    tokens = _tokenize(doc.content)
    doc.token_count = len(tokens)
    doc.sentence_count = _count_sentences(doc.content)
    freq = Counter(tokens)
    doc.lemma_count = len(freq)
    doc.type_token_ratio = round(len(freq) / max(len(tokens), 1), 4)
    doc.avg_word_length = round(sum(len(t) for t in tokens) / max(len(tokens), 1), 2)
    doc.word_frequencies = json.dumps(dict(freq.most_common(500)), ensure_ascii=False)
    doc.content_hash = _compute_hash(doc.content)
    doc.processing_status = models.CorpusProcessingStatus.TOKENIZED

def _doc_to_dict(doc: models.CorpusDocument) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "content": doc.content[:500] + ("…" if len(doc.content) > 500 else ""),
        "full_content": doc.content,
        "author": doc.author,
        "year": doc.year,
        "class_id": doc.class_id,
        "class_name": doc.linked_class.name if doc.linked_class else None,
        "genre": doc.genre.value if doc.genre else None,
        "dialect": doc.dialect.value if doc.dialect else None,
        "source": doc.source.value if doc.source else None,
        "fuse_class_code": doc.fuse_class_code,
        "token_count": doc.token_count,
        "lemma_count": doc.lemma_count,
        "sentence_count": doc.sentence_count,
        "avg_word_length": doc.avg_word_length,
        "type_token_ratio": doc.type_token_ratio,
        "processing_status": doc.processing_status.value if doc.processing_status else "pending",
        "is_validated": doc.is_validated,
        "validation_notes": doc.validation_notes,
        "content_hash": doc.content_hash,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.get("/corpus/documents")
def list_documents(
    user_id: int,
    genre: Optional[str] = None,
    dialect: Optional[str] = None,
    source: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fuse_class_code: Optional[str] = None,
    class_id: Optional[int] = None,
    processing_status: Optional[str] = None,
    is_validated: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    verify_admin(user_id, db)
    q = db.query(models.CorpusDocument)
    if genre:
        q = q.filter(models.CorpusDocument.genre == genre)
    if dialect:
        q = q.filter(models.CorpusDocument.dialect == dialect)
    if source:
        q = q.filter(models.CorpusDocument.source == source)
    if year_from:
        q = q.filter(models.CorpusDocument.year >= year_from)
    if year_to:
        q = q.filter(models.CorpusDocument.year <= year_to)
    if fuse_class_code:
        q = q.filter(models.CorpusDocument.fuse_class_code == fuse_class_code)
    if class_id is not None:
        q = q.filter(models.CorpusDocument.class_id == class_id)
    if processing_status:
        q = q.filter(models.CorpusDocument.processing_status == processing_status)
    if is_validated is not None:
        q = q.filter(models.CorpusDocument.is_validated == is_validated)
    if search:
        q = q.filter(models.CorpusDocument.title.ilike(f"%{search}%"))
    total = q.count()
    docs = q.order_by(models.CorpusDocument.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "documents": [_doc_to_dict(d) for d in docs]}


@router.get("/corpus/documents/{doc_id}")
def get_document(doc_id: int, user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    doc = db.query(models.CorpusDocument).filter(models.CorpusDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    result = _doc_to_dict(doc)
    result["content"] = doc.content
    try:
        result["word_frequencies"] = json.loads(doc.word_frequencies) if doc.word_frequencies else {}
    except (json.JSONDecodeError, TypeError):
        result["word_frequencies"] = {}
    return result


@router.post("/corpus/documents")
def create_document(body: CorpusDocumentCreate, user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    doc = models.CorpusDocument(
        title=body.title, content=body.content,
        author=body.author, year=body.year,
        fuse_class_code=body.fuse_class_code, class_id=body.class_id,
    )
    if body.genre:
        doc.genre = models.CorpusGenre(body.genre)
    if body.dialect:
        doc.dialect = models.CorpusDialect(body.dialect)
    if body.source:
        doc.source = models.CorpusSource(body.source)
    _process_document(doc)
    dup = db.query(models.CorpusDocument).filter(
        models.CorpusDocument.content_hash == doc.content_hash,
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail=f"Duplikatë — përputhet me dokumentin id={dup.id} \"{dup.title}\"")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _doc_to_dict(doc)


@router.put("/corpus/documents/{doc_id}")
def update_document(doc_id: int, body: CorpusDocumentUpdate, user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    doc = db.query(models.CorpusDocument).filter(models.CorpusDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if body.title is not None:
        doc.title = body.title
    if body.content is not None:
        doc.content = body.content
        _process_document(doc)
    if body.author is not None:
        doc.author = body.author
    if body.year is not None:
        doc.year = body.year
    if body.class_id is not None:
        doc.class_id = body.class_id if body.class_id != 0 else None
    if body.genre is not None:
        doc.genre = models.CorpusGenre(body.genre) if body.genre else None
    if body.dialect is not None:
        doc.dialect = models.CorpusDialect(body.dialect) if body.dialect else None
    if body.source is not None:
        doc.source = models.CorpusSource(body.source) if body.source else None
    if body.fuse_class_code is not None:
        doc.fuse_class_code = body.fuse_class_code
    if body.processing_status is not None:
        doc.processing_status = models.CorpusProcessingStatus(body.processing_status)
    if body.is_validated is not None:
        doc.is_validated = body.is_validated
    if body.validation_notes is not None:
        doc.validation_notes = body.validation_notes
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return _doc_to_dict(doc)


@router.delete("/corpus/documents/{doc_id}")
def delete_document(doc_id: int, user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    doc = db.query(models.CorpusDocument).filter(models.CorpusDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": f"Dokumenti {doc_id} u fshi"}


# ---------------------------------------------------------------------------
# Aggregation / Stats
# ---------------------------------------------------------------------------

@router.get("/corpus/stats")
def corpus_stats(user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    CD = models.CorpusDocument

    total_docs = db.query(func.count(CD.id)).scalar() or 0
    total_tokens = db.query(func.sum(CD.token_count)).scalar() or 0
    total_lemmas = db.query(func.sum(CD.lemma_count)).scalar() or 0
    total_sentences = db.query(func.sum(CD.sentence_count)).scalar() or 0
    validated_count = db.query(func.count(CD.id)).filter(CD.is_validated == True).scalar() or 0
    avg_ttr = db.query(func.avg(CD.type_token_ratio)).scalar() or 0
    avg_wl = db.query(func.avg(CD.avg_word_length)).scalar() or 0
    avg_doc_tokens = round(total_tokens / max(total_docs, 1), 1)
    avg_sentences_per_doc = round(total_sentences / max(total_docs, 1), 1)

    def _agg(col):
        rows = db.query(col, func.count(CD.id)).group_by(col).all()
        return {(v.value if hasattr(v, "value") else str(v) if v else "pa_klasifikim"): c for v, c in rows}

    def _tok_agg(col):
        rows = db.query(col, func.sum(CD.token_count)).group_by(col).all()
        return {(v.value if hasattr(v, "value") else str(v) if v else "pa_klasifikim"): c or 0 for v, c in rows}

    by_year = {str(y): c for y, c in db.query(CD.year, func.count(CD.id)).filter(CD.year.isnot(None)).group_by(CD.year).order_by(CD.year).all()}
    top_authors = {a: c for a, c in db.query(CD.author, func.count(CD.id)).filter(CD.author.isnot(None)).group_by(CD.author).order_by(func.count(CD.id).desc()).limit(20).all()}

    # Per-class breakdown
    class_rows = (
        db.query(
            models.Course.id, models.Course.name,
            func.count(CD.id), func.sum(CD.token_count),
            func.sum(CD.lemma_count), func.avg(CD.type_token_ratio),
        )
        .outerjoin(CD, CD.class_id == models.Course.id)
        .filter(models.Course.parent_class_id.is_(None))
        .group_by(models.Course.id)
        .order_by(models.Course.order_index)
        .all()
    )
    by_class = [
        {"class_id": cid, "class_name": cname, "documents": cnt or 0,
         "tokens": tok or 0, "lemmas": lem or 0, "avg_ttr": round(ttr or 0, 4)}
        for cid, cname, cnt, tok, lem, ttr in class_rows
    ]

    unlinked = db.query(func.count(CD.id)).filter(CD.class_id.is_(None)).scalar() or 0

    return {
        "total_documents": total_docs,
        "total_tokens": total_tokens,
        "total_lemmas": total_lemmas,
        "total_sentences": total_sentences,
        "validated_count": validated_count,
        "unvalidated_count": total_docs - validated_count,
        "avg_type_token_ratio": round(avg_ttr, 4),
        "avg_word_length": round(avg_wl, 2),
        "avg_doc_tokens": avg_doc_tokens,
        "avg_sentences_per_doc": avg_sentences_per_doc,
        "by_genre": _agg(CD.genre),
        "by_dialect": _agg(CD.dialect),
        "by_source": _agg(CD.source),
        "by_status": _agg(CD.processing_status),
        "by_year": by_year,
        "top_authors": top_authors,
        "tokens_by_genre": _tok_agg(CD.genre),
        "tokens_by_dialect": _tok_agg(CD.dialect),
        "by_class": by_class,
        "unlinked_documents": unlinked,
    }


# ---------------------------------------------------------------------------
# Linguistic Analysis
# ---------------------------------------------------------------------------

@router.get("/corpus/linguistic-metrics")
def linguistic_metrics(
    user_id: int,
    class_id: Optional[int] = None,
    genre: Optional[str] = None,
    dialect: Optional[str] = None,
    db: Session = Depends(get_db),
):
    verify_admin(user_id, db)
    CD = models.CorpusDocument
    q = db.query(CD)
    if class_id is not None:
        q = q.filter(CD.class_id == class_id)
    if genre:
        q = q.filter(CD.genre == genre)
    if dialect:
        q = q.filter(CD.dialect == dialect)

    docs = q.all()
    if not docs:
        return {"error": "Nuk ka dokumente për këto filtra"}

    all_tokens: list[str] = []
    total_chars = 0
    sentence_lengths: list[int] = []
    for d in docs:
        tokens = _tokenize(d.content)
        all_tokens.extend(tokens)
        total_chars += sum(len(t) for t in tokens)
        sents = _SENTENCE_END.split(d.content.strip())
        for s in sents:
            wc = len(_ALBANIAN_WORD.findall(s))
            if wc > 0:
                sentence_lengths.append(wc)

    freq = Counter(all_tokens)
    total_tok = len(all_tokens)
    unique_tok = len(freq)
    ttr = round(unique_tok / max(total_tok, 1), 4)
    avg_wl = round(total_chars / max(total_tok, 1), 2)
    avg_sent_len = round(sum(sentence_lengths) / max(len(sentence_lengths), 1), 2)

    hapax = sum(1 for w, c in freq.items() if c == 1)
    dis = sum(1 for w, c in freq.items() if c == 2)

    # Yule's K (lexical richness)
    freq_of_freq = Counter(freq.values())
    m1 = total_tok
    m2 = sum(i * i * vi for i, vi in freq_of_freq.items())
    yules_k = round(10000 * (m2 - m1) / max(m1 * m1, 1), 4) if m1 > 0 else 0

    # Top 10 per length category
    short_words = [w for w in freq if len(w) <= 3]
    long_words = [w for w in freq if len(w) >= 8]
    top_short = sorted(short_words, key=lambda w: freq[w], reverse=True)[:10]
    top_long = sorted(long_words, key=lambda w: freq[w], reverse=True)[:10]

    # Word length distribution
    wl_dist: dict[int, int] = {}
    for t in all_tokens:
        l = len(t)
        wl_dist[l] = wl_dist.get(l, 0) + 1
    wl_chart = [{"length": k, "count": v} for k, v in sorted(wl_dist.items())]

    return {
        "document_count": len(docs),
        "total_tokens": total_tok,
        "unique_tokens": unique_tok,
        "type_token_ratio": ttr,
        "avg_word_length": avg_wl,
        "avg_sentence_length": avg_sent_len,
        "hapax_legomena": hapax,
        "dis_legomena": dis,
        "yules_k": yules_k,
        "top_short_words": [{"word": w, "count": freq[w]} for w in top_short],
        "top_long_words": [{"word": w, "count": freq[w]} for w in top_long],
        "word_length_distribution": wl_chart,
        "sentence_length_stats": {
            "min": min(sentence_lengths) if sentence_lengths else 0,
            "max": max(sentence_lengths) if sentence_lengths else 0,
            "avg": avg_sent_len,
            "median": sorted(sentence_lengths)[len(sentence_lengths) // 2] if sentence_lengths else 0,
        },
    }


# ---------------------------------------------------------------------------
# Word Frequency
# ---------------------------------------------------------------------------

@router.get("/corpus/word-frequencies")
def word_frequencies(
    user_id: int,
    top_n: int = Query(default=100, le=500),
    genre: Optional[str] = None,
    dialect: Optional[str] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    verify_admin(user_id, db)
    q = db.query(models.CorpusDocument.word_frequencies).filter(
        models.CorpusDocument.word_frequencies.isnot(None)
    )
    if genre:
        q = q.filter(models.CorpusDocument.genre == genre)
    if dialect:
        q = q.filter(models.CorpusDocument.dialect == dialect)
    if class_id is not None:
        q = q.filter(models.CorpusDocument.class_id == class_id)

    merged: Counter = Counter()
    for (wf_json,) in q.all():
        try:
            merged.update(json.loads(wf_json))
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "total_unique_words": len(merged),
        "top_words": [{"word": w, "count": c} for w, c in merged.most_common(top_n)],
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@router.post("/corpus/validate/{doc_id}")
def validate_document(doc_id: int, user_id: int, notes: Optional[str] = None, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    doc = db.query(models.CorpusDocument).filter(models.CorpusDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    issues: list[str] = []
    if doc.token_count == 0:
        issues.append("Dokumenti nuk ka token — teksti mund të jetë bosh.")
    if not doc.genre:
        issues.append("Zhanri nuk është klasifikuar.")
    if not doc.dialect:
        issues.append("Dialekti nuk është caktuar.")
    if not doc.source:
        issues.append("Burimi nuk është caktuar.")
    if not doc.author:
        issues.append("Autori mungon.")
    if not doc.year:
        issues.append("Viti mungon.")
    if doc.token_count < 50:
        issues.append(f"Teksti është shumë i shkurtër ({doc.token_count} token).")
    if doc.class_id is None:
        issues.append("Dokumenti nuk është lidhur me asnjë klasë.")
    if not issues:
        doc.is_validated = True
        doc.processing_status = models.CorpusProcessingStatus.VALIDATED
        doc.validation_notes = notes or "Validuar me sukses."
    else:
        doc.is_validated = False
        doc.validation_notes = "; ".join(issues)
    db.commit()
    db.refresh(doc)
    return {"is_valid": len(issues) == 0, "issues": issues, "document": _doc_to_dict(doc)}


@router.post("/corpus/validate-all")
def validate_all(user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    docs = db.query(models.CorpusDocument).all()
    results: dict = {"valid": 0, "invalid": 0, "issues_summary": Counter()}
    for doc in docs:
        issues: list[str] = []
        if doc.token_count == 0:
            issues.append("bosh")
        if not doc.genre:
            issues.append("pa_zhanër")
        if not doc.dialect:
            issues.append("pa_dialekt")
        if not doc.source:
            issues.append("pa_burim")
        if not doc.author:
            issues.append("pa_autor")
        if not doc.year:
            issues.append("pa_vit")
        if doc.class_id is None:
            issues.append("pa_klasë")
        if doc.token_count < 50:
            issues.append("tekst_i_shkurtër")
        if not issues:
            doc.is_validated = True
            doc.processing_status = models.CorpusProcessingStatus.VALIDATED
            doc.validation_notes = "Validuar automatikisht."
            results["valid"] += 1
        else:
            doc.is_validated = False
            doc.validation_notes = "; ".join(issues)
            results["invalid"] += 1
            for iss in issues:
                results["issues_summary"][iss] += 1
    db.commit()
    return {"total": len(docs), "valid": results["valid"], "invalid": results["invalid"], "issues_summary": dict(results["issues_summary"])}


# ---------------------------------------------------------------------------
# Duplicates
# ---------------------------------------------------------------------------

@router.get("/corpus/duplicates")
def find_duplicates(user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    dup_hashes = (
        db.query(models.CorpusDocument.content_hash)
        .filter(models.CorpusDocument.content_hash.isnot(None))
        .group_by(models.CorpusDocument.content_hash)
        .having(func.count(models.CorpusDocument.id) > 1)
        .all()
    )
    groups = []
    for (h,) in dup_hashes:
        docs = db.query(models.CorpusDocument).filter(models.CorpusDocument.content_hash == h).all()
        groups.append({
            "hash": h, "count": len(docs),
            "documents": [{"id": d.id, "title": d.title, "author": d.author, "year": d.year, "class_id": d.class_id} for d in docs],
        })
    return {"total_duplicate_groups": len(groups), "groups": groups}


# ---------------------------------------------------------------------------
# Fuse Codes
# ---------------------------------------------------------------------------

@router.get("/corpus/fuse-codes")
def list_fuse_codes(user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    rows = (
        db.query(models.CorpusDocument.fuse_class_code, func.count(models.CorpusDocument.id), func.sum(models.CorpusDocument.token_count))
        .filter(models.CorpusDocument.fuse_class_code.isnot(None))
        .group_by(models.CorpusDocument.fuse_class_code)
        .order_by(models.CorpusDocument.fuse_class_code)
        .all()
    )
    return {"codes": [{"code": code, "document_count": cnt, "total_tokens": tok or 0} for code, cnt, tok in rows]}


# ---------------------------------------------------------------------------
# Reprocess
# ---------------------------------------------------------------------------

@router.post("/corpus/reprocess-all")
def reprocess_all(user_id: int, db: Session = Depends(get_db)):
    verify_admin(user_id, db)
    docs = db.query(models.CorpusDocument).all()
    for doc in docs:
        _process_document(doc)
    db.commit()
    return {"reprocessed": len(docs)}


# ---------------------------------------------------------------------------
# Auto-populate corpus from exercises/courses
# ---------------------------------------------------------------------------

@router.post("/corpus/auto-populate")
def auto_populate_from_exercises(user_id: int, db: Session = Depends(get_db)):
    """
    Automatically create corpus documents from existing exercises/courses.
    Groups exercises by course (parent class) and creates one document per course.
    """
    verify_admin(user_id, db)

    top_level_classes = db.query(models.Course).filter(
        models.Course.parent_class_id == None
    ).all()

    created = 0
    skipped = 0

    for cls in top_level_classes:
        sub_courses = db.query(models.Course).filter(
            models.Course.parent_class_id == cls.id
        ).all()

        for course in sub_courses:
            exercises = db.query(models.Exercise).filter(
                models.Exercise.course_id == course.id,
                models.Exercise.enabled == True,
            ).all()

            if not exercises:
                continue

            content_parts = []
            for ex in exercises:
                line = f"{ex.prompt or ''}"
                if ex.answer:
                    line += f" — {ex.answer}"
                content_parts.append(line)

            content = "\n".join(content_parts)
            content_hash = _compute_hash(content)

            existing = db.query(models.CorpusDocument).filter(
                models.CorpusDocument.content_hash == content_hash
            ).first()
            if existing:
                skipped += 1
                continue

            category_name = exercises[0].category.value if exercises[0].category else "general"
            doc = models.CorpusDocument(
                title=f"{course.name} ({category_name})",
                content=content,
                author="AlbLingo Platform",
                year=datetime.now().year,
                class_id=cls.id,
                source=models.CorpusSource.PLATFORMA,
                genre=models.CorpusGenre.DIDAKTIK,
                dialect=models.CorpusDialect.STANDARDE,
                is_validated=True,
            )
            _process_document(doc)
            db.add(doc)
            created += 1

    db.commit()
    return {"created": created, "skipped_duplicates": skipped}


# ---------------------------------------------------------------------------
# User-facing: browse validated corpus documents (no admin required)
# ---------------------------------------------------------------------------

@router.get("/corpus/browse")
def browse_corpus(
    class_id: Optional[int] = None,
    genre: Optional[str] = None,
    dialect: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Public endpoint for users to browse validated corpus documents."""
    q = db.query(models.CorpusDocument).filter(models.CorpusDocument.is_validated == True)
    if class_id is not None:
        q = q.filter(models.CorpusDocument.class_id == class_id)
    if genre:
        q = q.filter(models.CorpusDocument.genre == genre)
    if dialect:
        q = q.filter(models.CorpusDocument.dialect == dialect)
    if search:
        q = q.filter(models.CorpusDocument.title.ilike(f"%{search}%"))
    total = q.count()
    docs = q.order_by(models.CorpusDocument.id.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "documents": [{
            "id": d.id, "title": d.title,
            "content": d.content[:300] + ("…" if len(d.content) > 300 else ""),
            "author": d.author, "year": d.year,
            "genre": d.genre.value if d.genre else None,
            "dialect": d.dialect.value if d.dialect else None,
            "source": d.source.value if d.source else None,
            "token_count": d.token_count, "class_id": d.class_id,
            "class_name": d.linked_class.name if d.linked_class else None,
        } for d in docs],
    }


@router.get("/corpus/browse/{doc_id}")
def browse_document(doc_id: int, db: Session = Depends(get_db)):
    """Public endpoint to read a single validated document."""
    doc = db.query(models.CorpusDocument).filter(
        models.CorpusDocument.id == doc_id,
        models.CorpusDocument.is_validated == True,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id, "title": doc.title, "content": doc.content,
        "author": doc.author, "year": doc.year,
        "genre": doc.genre.value if doc.genre else None,
        "dialect": doc.dialect.value if doc.dialect else None,
        "source": doc.source.value if doc.source else None,
        "token_count": doc.token_count, "sentence_count": doc.sentence_count,
        "class_id": doc.class_id,
        "class_name": doc.linked_class.name if doc.linked_class else None,
    }
