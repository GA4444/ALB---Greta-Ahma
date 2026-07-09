from __future__ import annotations

import json
import math
import os
import random
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ALBANIAN_VOWELS = set("aeiouyë")
ALBANIAN_DIGRAPHS = ("sh", "xh", "zh", "gj", "ll", "rr", "nj", "dh", "th")
MODEL_ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "model_artifacts"))
ALBANIAN_CASE_ENDINGS = ("ëve", "ave", "esh", "ish", "in", "it", "ve", "at", "ën", "ës", "ë", "e", "i", "a")
ALBANIAN_CASE_REPLACEMENTS = {
    "ë": ("e", "a", ""),
    "e": ("ë", "a"),
    "i": ("in", "it", "ë"),
    "in": ("i", "it"),
    "it": ("i", "in"),
    "a": ("at", "ës", "ë"),
    "at": ("a", "ave"),
    "ës": ("ë", "a"),
    "ën": ("ë", "e"),
    "ve": ("ëve", "ave"),
    "ëve": ("ve", "ave"),
    "ave": ("ve", "ëve"),
}


def normalize_sq(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "").strip().lower()


def tokenize_sq(text: str) -> List[str]:
    return re.findall(r"[a-zA-ZëËçÇ]+", normalize_sq(text))


def lexical_metrics(text: str) -> Dict[str, float]:
    tokens = tokenize_sq(text)
    if not tokens:
        return {
            "token_count": 0,
            "type_count": 0,
            "type_token_ratio": 0.0,
            "avg_word_length": 0.0,
            "yules_k": 0.0,
        }

    counts = Counter(tokens)
    freq_of_freq = Counter(counts.values())
    n = len(tokens)
    yules_k = 10000 * ((sum((freq ** 2) * value for freq, value in freq_of_freq.items()) - n) / (n ** 2))
    return {
        "token_count": n,
        "type_count": len(counts),
        "type_token_ratio": round(len(counts) / n, 4),
        "avg_word_length": round(sum(len(t) for t in tokens) / n, 2),
        "yules_k": round(yules_k, 2),
    }


def expected_metric_profile(grade: int) -> Dict[str, Tuple[float, float]]:
    """Conservative grade bands used as a safety check for generated items."""
    grade = max(1, min(8, int(grade or 1)))
    return {
        "avg_word_length": (3.2 + grade * 0.25, 5.4 + grade * 0.45),
        "type_token_ratio": (0.25, min(0.95, 0.55 + grade * 0.06)),
        "yules_k": (25.0, max(80.0, 180.0 - grade * 8.0)),
    }


def grade_fit_score(text: str, grade: int) -> Dict[str, Any]:
    metrics = lexical_metrics(text)
    bands = expected_metric_profile(grade)
    checks: Dict[str, bool] = {}
    distances = []
    for key, (low, high) in bands.items():
        value = float(metrics.get(key, 0.0))
        ok = low <= value <= high
        checks[key] = ok
        if value < low:
            distances.append((low - value) / max(low, 1.0))
        elif value > high:
            distances.append((value - high) / max(high, 1.0))
        else:
            distances.append(0.0)
    score = max(0.0, 1.0 - sum(distances) / max(len(distances), 1))
    return {
        "grade": grade,
        "fit_score": round(score, 3),
        "checks": checks,
        "metrics": metrics,
        "expected_profile": bands,
    }


def classify_error(correct: str, observed: str) -> Dict[str, Any]:
    correct_n = normalize_sq(correct)
    observed_n = normalize_sq(observed)
    if correct_n == observed_n:
        return {"type": "correct", "label": "Pa gabim", "severity": "none"}

    if correct_n.replace("ë", "e").replace("ç", "c") == observed_n:
        missing = []
        if "ë" in correct_n and "ë" not in observed_n:
            missing.append("ë")
        if "ç" in correct_n and "ç" not in observed_n:
            missing.append("ç")
        return {
            "type": "missing_diacritic",
            "label": "Mungesë e shenjave ë/ç",
            "severity": "medium",
            "details": missing,
        }

    for digraph in ALBANIAN_DIGRAPHS:
        reduced = digraph[0]
        if digraph in correct_n and correct_n.replace(digraph, reduced) == observed_n:
            return {
                "type": "digraph_reduction",
                "label": f"Reduktim i digrafit {digraph}",
                "severity": "high",
                "details": [digraph],
            }

    cq_confusion = _detect_c_q_confusion(correct_n, observed_n)
    if cq_confusion:
        return {
            "type": "c_q_confusion",
            "label": "Ngatërrim i shkronjave ç/q/c",
            "severity": "high",
            "details": cq_confusion,
        }

    case_error = _detect_case_ending_error(correct_n, observed_n)
    if case_error:
        return {
            "type": "case_ending_error",
            "label": "Gabim në rasë ose mbaresë",
            "severity": "high",
            "details": case_error,
        }

    if _is_adjacent_transposition(correct_n, observed_n):
        return {"type": "letter_transposition", "label": "Ndërrim i rendit të shkronjave", "severity": "medium"}
    if _one_deletion_from(correct_n, observed_n):
        return {"type": "missing_letter", "label": "Shkronjë e munguar", "severity": "medium"}
    if _one_deletion_from(observed_n, correct_n):
        return {"type": "extra_letter", "label": "Shkronjë e tepërt", "severity": "medium"}
    if len(correct_n) == len(observed_n) and sum(a != b for a, b in zip(correct_n, observed_n)) == 1:
        return {"type": "wrong_letter", "label": "Shkronjë e gabuar", "severity": "medium"}
    return {"type": "unknown_orthographic", "label": "Gabim drejtshkrimor i përgjithshëm", "severity": "review"}


def _detect_c_q_confusion(correct: str, observed: str) -> Optional[Dict[str, Any]]:
    if len(correct) != len(observed):
        return None
    diffs = [
        (idx, c_char, o_char)
        for idx, (c_char, o_char) in enumerate(zip(correct, observed))
        if c_char != o_char
    ]
    if len(diffs) != 1:
        return None
    idx, c_char, o_char = diffs[0]
    if {c_char, o_char}.issubset({"ç", "q", "c"}) and "q" in {c_char, o_char}:
        return {"position": idx, "expected": c_char, "observed": o_char}
    return None


def _detect_case_ending_error(correct: str, observed: str) -> Optional[Dict[str, Any]]:
    if correct == observed or len(correct) < 4 or len(observed) < 3:
        return None
    for correct_ending in ALBANIAN_CASE_ENDINGS:
        if not correct.endswith(correct_ending):
            continue
        stem = correct[: -len(correct_ending)] if correct_ending else correct
        if len(stem) < 3 or not observed.startswith(stem):
            continue
        observed_ending = observed[len(stem):]
        if observed_ending == correct_ending:
            continue
        if observed_ending in ALBANIAN_CASE_ENDINGS or observed_ending == "":
            return {
                "stem": stem,
                "expected_ending": correct_ending,
                "observed_ending": observed_ending or "∅",
            }
    return None


def _one_deletion_from(longer: str, shorter: str) -> bool:
    if len(longer) != len(shorter) + 1:
        return False
    for i in range(len(longer)):
        if longer[:i] + longer[i + 1 :] == shorter:
            return True
    return False


def _is_adjacent_transposition(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diffs = [idx for idx, (x, y) in enumerate(zip(a, b)) if x != y]
    return len(diffs) == 2 and diffs[1] == diffs[0] + 1 and a[diffs[0]] == b[diffs[1]] and a[diffs[1]] == b[diffs[0]]


def corrupt_word(word: str, error_type: Optional[str] = None) -> Tuple[str, str]:
    original = normalize_sq(word)
    if not original:
        return word, "none"

    candidates = []
    if "ë" in original:
        candidates.append(("missing_diacritic", original.replace("ë", "e", 1)))
    if "ç" in original:
        candidates.append(("missing_diacritic", original.replace("ç", "c", 1)))
        candidates.append(("c_q_confusion", original.replace("ç", "q", 1)))
    if "q" in original:
        candidates.append(("c_q_confusion", original.replace("q", "ç", 1)))
        candidates.append(("c_q_confusion", original.replace("q", "c", 1)))
    for digraph in ALBANIAN_DIGRAPHS:
        if digraph in original:
            candidates.append(("digraph_reduction", original.replace(digraph, digraph[0], 1)))
    if len(original) > 4:
        mid = len(original) // 2
        candidates.append(("missing_letter", original[:mid] + original[mid + 1 :]))
    if len(original) > 3:
        idx = min(2, len(original) - 1)
        candidates.append(("extra_letter", original[:idx] + original[idx] + original[idx:]))
    if len(original) > 4:
        idx = 1
        candidates.append(("letter_transposition", original[:idx] + original[idx + 1] + original[idx] + original[idx + 2 :]))
    if original.endswith("ë") and len(original) > 4:
        candidates.append(("drop_final_vowel", original[:-1]))
    case_variant = _corrupt_case_ending(original)
    if case_variant and case_variant != original:
        candidates.append(("case_ending_error", case_variant))

    if error_type:
        candidates = [c for c in candidates if c[0] == error_type]
    if not candidates:
        return original, "none"
    selected_type, corrupted = random.choice(candidates)
    return corrupted, selected_type


def _corrupt_case_ending(word: str) -> Optional[str]:
    for ending in ALBANIAN_CASE_ENDINGS:
        if not word.endswith(ending):
            continue
        stem = word[: -len(ending)] if ending else word
        if len(stem) < 3:
            continue
        replacements = ALBANIAN_CASE_REPLACEMENTS.get(ending)
        if not replacements:
            continue
        replacement = random.choice(list(replacements))
        return stem + replacement
    return None


def augment_sentence(sentence: str, error_rate: float = 0.2, error_types: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    tokens = sentence.split()
    if not tokens:
        return {"original": sentence, "corrupted": sentence, "errors": []}
    max_errors = max(1, round(len(tokens) * max(0.0, min(error_rate, 1.0))))
    candidate_indices = [i for i, token in enumerate(tokens) if re.search(r"[a-zA-ZëËçÇ]", token)]
    random.shuffle(candidate_indices)
    errors = []
    for idx in candidate_indices[:max_errors]:
        clean = re.sub(r"(^\W+|\W+$)", "", tokens[idx])
        corrupted, e_type = clean, "none"
        if error_types:
            preferred_types = list(error_types)
            random.shuffle(preferred_types)
            for preferred_type in preferred_types:
                corrupted, e_type = corrupt_word(clean, preferred_type)
                if e_type != "none" and corrupted != clean:
                    break
        else:
            corrupted, e_type = corrupt_word(clean)
        if e_type == "none" or corrupted == clean:
            continue
        tokens[idx] = tokens[idx].replace(clean, corrupted, 1)
        errors.append({
            "index": idx,
            "correct": clean,
            "corrupted": corrupted,
            "error_type": e_type,
            "classification": classify_error(clean, corrupted),
        })
    return {"original": sentence, "corrupted": " ".join(tokens), "errors": errors}


def generate_exercise(seed_word: str, grade: int, difficulty: str = "medium", exercise_type: str = "missing_letter") -> Dict[str, Any]:
    word = normalize_sq(seed_word)
    if not word:
        raise ValueError("seed_word is required")
    if exercise_type == "find_error":
        corrupted, e_type = corrupt_word(word)
        prompt = f"Gjej gabimin dhe shkruaj fjalën saktë: {corrupted}"
        data = {"incorrect": corrupted, "error_type": e_type}
        answer = word
    elif exercise_type == "explain_error":
        corrupted, e_type = corrupt_word(word)
        prompt = f"Shpjego pse fjala '{corrupted}' duhet shkruar '{word}'."
        data = {"incorrect": corrupted, "correct": word, "error_type": e_type}
        answer = word
    else:
        hidden = _hide_letter(word, difficulty)
        prompt = f"Plotëso shkronjën që mungon: {hidden}"
        data = {"word": word, "hidden": hidden, "exercise_type": "missing_letter"}
        answer = word
    fit = grade_fit_score(f"{prompt} {answer}", grade)
    result = {
        "instruction": f"Gjenero një ushtrim '{exercise_type}' për klasën {grade}, vështirësi {difficulty}.",
        "prompt": prompt,
        "answer": answer,
        "data": data,
        "grade": grade,
        "difficulty": difficulty,
        "safety": {
            "correctness_source": "database_or_rule_based_answer",
            "llm_role": "explanation_only",
            "requires_teacher_review": fit["fit_score"] < 0.65,
        },
        "grade_fit": fit,
    }
    lora_candidate = generate_lora_exercise_candidate(
        seed_word=word,
        grade=grade,
        difficulty=difficulty,
        exercise_type=exercise_type,
    )
    result["model_runtime"] = {
        "lora_loaded": bool(lora_candidate.get("loaded")),
        "lora_used": bool(lora_candidate.get("used")),
        "method": lora_candidate.get("method", "rule_based_fallback"),
        "note": "LoRA proposes content; rules/database keep the authoritative answer.",
    }
    if lora_candidate.get("candidate"):
        result["ai_candidate"] = lora_candidate["candidate"]
    if lora_candidate.get("warning"):
        result["model_runtime"]["warning"] = lora_candidate["warning"]
    return result


def generate_lora_exercise_candidate(seed_word: str, grade: int, difficulty: str, exercise_type: str) -> Dict[str, Any]:
    runtime = _load_lora_runtime()
    if not runtime.get("loaded"):
        return runtime
    prompt = (
        "### Instruksion:\n"
        f"Gjenero një ushtrim të sigurt për drejtshkrimin shqip. Kategoria: {exercise_type}. "
        f"Klasa: {grade}. Vështirësia: {difficulty}. Fjala bazë: {seed_word}.\n\n"
        "### Input:\n"
        + json.dumps({
            "seed_word": seed_word,
            "grade": grade,
            "difficulty": difficulty,
            "exercise_type": exercise_type,
            "safety": "Kthe vetëm propozim; përgjigjja finale kontrollohet nga rregullat.",
        }, ensure_ascii=False)
        + "\n\n### Përgjigje:\n"
    )
    try:
        torch = runtime["torch"]
        tokenizer = runtime["tokenizer"]
        model = runtime["model"]
        inputs = tokenizer(prompt, return_tensors="pt")
        device = runtime.get("device", "cpu")
        if device != "cpu":
            inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=140,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        decoded = tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
        return {
            "loaded": True,
            "used": True,
            "method": "LoRA_adapter_runtime",
            "candidate": {
                "raw_text": decoded[:1200],
                "validated_for_child": False,
                "requires_rule_or_teacher_review": True,
            },
        }
    except Exception as exc:
        return {
            "loaded": True,
            "used": False,
            "method": "rule_based_fallback",
            "warning": f"LoRA runtime failed; used safe rule output instead: {type(exc).__name__}: {exc}",
        }


def _hide_letter(word: str, difficulty: str) -> str:
    if len(word) <= 2:
        return "_" + word[1:]
    if difficulty == "easy":
        idx = len(word) - 1 if word.endswith("ë") else 1
    elif difficulty == "hard":
        idx = max(1, len(word) // 2)
    else:
        idx = max(1, min(len(word) - 2, len(word) // 2))
    return word[:idx] + "_" + word[idx + 1 :]


def pedagogical_feedback(student_answer: str, correct_answer: str, grade: int = 3) -> Dict[str, Any]:
    classification = classify_error(correct_answer, student_answer)
    correct = normalize_sq(correct_answer)
    observed = normalize_sq(student_answer)
    label = classification["type"]
    rule_map = {
        "missing_diacritic": "Në shqip, ë dhe ç janë shkronja të veçanta dhe ndryshojnë kuptimin e fjalës.",
        "digraph_reduction": "Disa tinguj shqip shkruhen me dy shkronja bashkë, si sh, dh, th, gj, nj, ll dhe rr.",
        "c_q_confusion": "Në shqip, ç dhe q janë shkronja të ndryshme dhe nuk zëvendësojnë njëra-tjetrën.",
        "case_ending_error": "Mbaresa e fjalës ndryshon sipas rasës dhe rolit që fjala ka në fjali.",
        "letter_transposition": f"Radha e shkronjave në '{correct}' është {'-'.join(correct)}.",
        "missing_letter": "Kontrollo çdo shkronjë me radhë që fjala të jetë e plotë.",
        "extra_letter": "Fjala ka një shkronjë më tepër; lexoje ngadalë dhe krahasoje me formën e saktë.",
        "wrong_letter": "Një shkronjë është zëvendësuar me një tjetër; krahaso fjalën shkronjë për shkronjë.",
    }
    why_map = {
        "missing_diacritic": "Shenja mbi shkronjë nuk është zbukurim; ajo është pjesë e drejtshkrimit.",
        "digraph_reduction": "Kur hiqet një pjesë e digrafit, fjala mund të tingëllojë ose të kuptohet ndryshe.",
        "c_q_confusion": "Kur ndërrohet ç me q, tingulli dhe forma standarde e fjalës ndryshojnë.",
        "case_ending_error": "Në këtë fjali fjala ka nevojë për mbaresën e saktë që të lidhet mirë me fjalët e tjera.",
        "letter_transposition": "Shkronjat janë të sakta, por janë vendosur në rend të gabuar.",
    }
    easier = _hide_letter(correct, "easy")
    return {
        "what_student_wrote": observed,
        "correct_form": correct,
        "error_type": label,
        "error_label": classification["label"],
        "simple_rule": rule_map.get(label, "Krahaso fjalën tënde me formën e saktë dhe shiko ku ndryshojnë."),
        "why": why_map.get(label, "Ky ndryshim e bën fjalën të pasaktë në drejtshkrimin standard shqip."),
        "tone": "supportive_non_punitive",
        "next_practice": {
            "prompt": f"Provo përsëri: plotëso fjalën {easier}",
            "answer": correct,
            "difficulty": "easy",
        },
        "safety": {
            "correctness_source": "database_or_rule_based_answer",
            "llm_allowed": "explanation_only_after_rule_classification",
        },
    }


def correction_metrics(source: str, reference: str, hypothesis: str) -> Dict[str, Any]:
    src_tokens = tokenize_sq(source)
    ref_tokens = tokenize_sq(reference)
    hyp_tokens = tokenize_sq(hypothesis)
    src_to_ref = _token_edit_count(src_tokens, ref_tokens)
    hyp_to_ref = _token_edit_count(hyp_tokens, ref_tokens)
    src_to_hyp = _token_edit_count(src_tokens, hyp_tokens)
    proposed = max(src_to_hyp, 1)
    gold = max(src_to_ref, 1)
    correct_edits = max(0, proposed + gold - hyp_to_ref) / 2
    precision = correct_edits / proposed
    recall = correct_edits / gold
    beta2 = 0.5 ** 2
    f05 = ((1 + beta2) * precision * recall / (beta2 * precision + recall)) if (precision + recall) else 0.0
    return {
        "errant_like_f0_5": round(f05, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "gleu_like": round(_gleu_like(src_tokens, ref_tokens, hyp_tokens), 4),
        "edit_distance_to_reference": hyp_to_ref,
        "notes": "ERRANT-like uses token edit overlap approximation; for publication, report this as lightweight ERRANT-inspired F0.5 unless official ERRANT is added.",
    }


def _token_edit_count(a: Sequence[str], b: Sequence[str]) -> int:
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        dp[i][0] = i
    for j in range(len(b) + 1):
        dp[0][j] = j
    for i, x in enumerate(a, 1):
        for j, y in enumerate(b, 1):
            cost = 0 if x == y else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[-1][-1]


def _ngrams(tokens: Sequence[str], n: int) -> Counter:
    return Counter(tuple(tokens[i : i + n]) for i in range(max(0, len(tokens) - n + 1)))


def _gleu_like(source: Sequence[str], reference: Sequence[str], hypothesis: Sequence[str]) -> float:
    if not hypothesis:
        return 0.0
    scores = []
    for n in (1, 2, 3, 4):
        hyp = _ngrams(hypothesis, n)
        ref = _ngrams(reference, n)
        if not hyp:
            continue
        overlap = sum((hyp & ref).values())
        scores.append(overlap / max(sum(hyp.values()), 1))
    precision = sum(scores) / max(len(scores), 1)
    brevity = min(1.0, len(hypothesis) / max(len(reference), 1))
    penalty = 0.0
    if source:
        unchanged_errors = max(0, _token_edit_count(source, reference) - _token_edit_count(hypothesis, reference))
        penalty = 0.05 if unchanged_errors == 0 and source != reference else 0.0
    return max(0.0, precision * brevity - penalty)


def irt_summary(attempt_rows: Iterable[Any]) -> Dict[str, Any]:
    by_item: Dict[int, List[bool]] = defaultdict(list)
    by_user: Dict[str, List[bool]] = defaultdict(list)
    for row in attempt_rows:
        by_item[int(row.exercise_id)].append(bool(row.is_correct))
        by_user[str(row.user_id)].append(bool(row.is_correct))

    items = []
    for exercise_id, values in by_item.items():
        p = _clip_probability(sum(values) / len(values))
        beta = -_logit(p)
        items.append({
            "exercise_id": exercise_id,
            "attempts": len(values),
            "accuracy": round(p, 3),
            "beta_difficulty": round(beta, 3),
            "flag": "possible_anomaly" if len(values) >= 5 and (p < 0.15 or p > 0.95) else "ok",
        })

    users = []
    for user_id, values in by_user.items():
        p = _clip_probability(sum(values) / len(values))
        users.append({
            "user_id": user_id,
            "attempts": len(values),
            "accuracy": round(p, 3),
            "theta_ability": round(_logit(p), 3),
        })

    return {
        "model": "Rasch 1PL approximation P=1/(1+exp(-(theta-beta)))",
        "items": sorted(items, key=lambda x: x["beta_difficulty"], reverse=True),
        "users": sorted(users, key=lambda x: x["theta_ability"], reverse=True),
    }


def knowledge_tracing_summary(attempt_rows: Iterable[Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Lightweight Bayesian Knowledge Tracing approximation.

    This is intentionally interpretable for thesis/prototype use: it estimates
    mastery per exercise category from the sequence of attempts. Deep-IRT/DKT
    can later replace this while keeping the same API contract.
    """
    rows = list(attempt_rows)
    if user_id is not None:
        rows = [row for row in rows if str(row.user_id) == str(user_id)]

    mastery_by_skill: Dict[str, float] = defaultdict(lambda: 0.25)
    evidence_by_skill: Dict[str, Dict[str, int]] = defaultdict(lambda: {"attempts": 0, "correct": 0})

    for row in sorted(rows, key=lambda r: getattr(r, "id", 0)):
        exercise = getattr(row, "exercise", None)
        skill = getattr(getattr(exercise, "category", None), "value", None) or "unknown"
        prior = mastery_by_skill[skill]
        is_correct = bool(row.is_correct)
        # Interpretable BKT-like update with slip/guess assumptions.
        guess = 0.20
        slip = 0.10
        learn = 0.12
        if is_correct:
            posterior = (prior * (1 - slip)) / max(prior * (1 - slip) + (1 - prior) * guess, 1e-6)
        else:
            posterior = (prior * slip) / max(prior * slip + (1 - prior) * (1 - guess), 1e-6)
        mastery_by_skill[skill] = min(0.99, posterior + (1 - posterior) * learn)
        evidence_by_skill[skill]["attempts"] += 1
        evidence_by_skill[skill]["correct"] += 1 if is_correct else 0

    skills = []
    for skill, mastery in mastery_by_skill.items():
        ev = evidence_by_skill[skill]
        skills.append({
            "skill": skill,
            "mastery_probability": round(mastery, 3),
            "attempts": ev["attempts"],
            "accuracy": round(ev["correct"] / max(ev["attempts"], 1), 3),
            "recommendation": _mastery_recommendation(mastery),
        })

    neural = neural_knowledge_tracing_summary(rows, user_id=user_id)
    result = {
        "model": "Interpretable BKT-style Knowledge Tracing",
        "user_id": user_id,
        "skills": sorted(skills, key=lambda item: item["mastery_probability"]),
        "safety_note": "Used for recommendation only; grading remains rule/database-based.",
    }
    if neural.get("loaded"):
        result["neural_dkt"] = neural
        result["model"] = "Interpretable BKT + active neural DKT artifact"
    else:
        result["neural_dkt"] = neural
    return result


def _mastery_recommendation(mastery: float) -> str:
    if mastery < 0.45:
        return "practice_foundational_items"
    if mastery < 0.75:
        return "practice_targeted_medium_items"
    return "advance_or_spiral_review"


def adaptive_next_item(attempt_rows: Iterable[Any], exercise_rows: Iterable[Any], user_id: str) -> Dict[str, Any]:
    """Select the next exercise closest to the learner's estimated ability."""
    attempt_list = list(attempt_rows)
    exercise_list = list(exercise_rows)
    irt = irt_summary(attempt_list)
    kt = knowledge_tracing_summary(attempt_list, user_id=user_id)
    user = next((u for u in irt["users"] if str(u["user_id"]) == str(user_id)), None)
    theta = user["theta_ability"] if user else 0.0
    weak_skills = [s["skill"] for s in kt["skills"] if s["mastery_probability"] < 0.75]

    item_difficulty = {item["exercise_id"]: item["beta_difficulty"] for item in irt["items"]}
    neural_scores = neural_adaptive_item_scores(attempt_list, exercise_list, user_id=user_id)
    candidates = []
    for exercise in exercise_list:
        skill = getattr(getattr(exercise, "category", None), "value", "unknown")
        beta = item_difficulty.get(exercise.id, 0.0)
        distance = abs(theta - beta)
        skill_bonus = -0.25 if skill in weak_skills else 0.0
        info = _item_information(theta, beta)
        neural = neural_scores.get("scores", {}).get(int(exercise.id), {})
        neural_bonus = -0.20 * float(neural.get("combined_success_probability", 0.0))
        candidates.append({
            "exercise_id": exercise.id,
            "prompt": exercise.prompt,
            "skill": skill,
            "beta_difficulty": round(beta, 3),
            "theta_ability": round(theta, 3),
            "information": round(info, 4),
            "neural_deep_irt_probability": neural.get("deep_irt_success_probability"),
            "neural_dkt_probability": neural.get("dkt_success_probability"),
            "selection_score": round(distance - info + skill_bonus + neural_bonus, 4),
            "reason": (
                "neural_irt_dkt_plus_weak_skill"
                if neural_scores.get("loaded") and skill in weak_skills
                else "neural_irt_dkt_plus_irt"
                if neural_scores.get("loaded")
                else "closest_to_ability_and_targets_weak_skill"
                if skill in weak_skills
                else "closest_to_ability"
            ),
        })

    candidates.sort(key=lambda item: item["selection_score"])
    return {
        "user_id": user_id,
        "strategy": "IRT + Knowledge Tracing + optimal-information heuristic",
        "recommended": candidates[0] if candidates else None,
        "top_candidates": candidates[:5],
        "model_runtime": neural_scores.get("runtime", neural_scores),
        "zone_of_proximal_development": "avoids very easy and very hard items by matching beta to theta",
    }


def _item_information(theta: float, beta: float) -> float:
    p = 1 / (1 + math.exp(-(theta - beta)))
    return p * (1 - p)


@lru_cache(maxsize=1)
def _load_lora_runtime() -> Dict[str, Any]:
    adapter_dir = os.path.join(MODEL_ARTIFACT_DIR, "lora_qlora", "adapter")
    manifest_path = os.path.join(adapter_dir, "training_manifest.json")
    if not os.path.exists(manifest_path):
        return {"loaded": False, "used": False, "method": "rule_based_fallback", "warning": "LoRA adapter manifest missing"}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        base_model = manifest.get("base_model", "Qwen/Qwen2.5-0.5B-Instruct")
        tokenizer = AutoTokenizer.from_pretrained(adapter_dir, use_fast=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        device = "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu"
        model = AutoModelForCausalLM.from_pretrained(base_model)
        model = PeftModel.from_pretrained(model, adapter_dir)
        model.eval()
        if device != "cpu":
            model.to(device)
        return {
            "loaded": True,
            "used": False,
            "method": "LoRA_adapter_runtime",
            "manifest": manifest,
            "torch": torch,
            "tokenizer": tokenizer,
            "model": model,
            "device": device,
        }
    except Exception as exc:
        return {
            "loaded": False,
            "used": False,
            "method": "rule_based_fallback",
            "warning": f"LoRA runtime unavailable: {type(exc).__name__}: {exc}",
        }


@lru_cache(maxsize=1)
def _load_neural_irt_dkt_runtime() -> Dict[str, Any]:
    artifact_dir = os.path.join(MODEL_ARTIFACT_DIR, "deep_irt_dkt")
    manifest_path = os.path.join(artifact_dir, "training_manifest.json")
    dkt_path = os.path.join(artifact_dir, "dkt_model.pt")
    irt_path = os.path.join(artifact_dir, "deep_irt_model.pt")
    if not all(os.path.exists(path) for path in (manifest_path, dkt_path, irt_path)):
        return {"loaded": False, "warning": "Deep-IRT/DKT artifact files are missing"}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        import torch
        from torch import nn

        skills = manifest.get("skills", {})
        users = manifest.get("users", {})
        exercises = manifest.get("exercises", {})
        n_skills = len(skills) + 1
        dkt_state = torch.load(dkt_path, map_location="cpu")
        irt_state = torch.load(irt_path, map_location="cpu")
        hidden = int(dkt_state["rnn.weight_ih_l0"].shape[0] // 3)

        class DKT(nn.Module):
            def __init__(self, n_skills: int, hidden: int):
                super().__init__()
                self.embed = nn.Embedding(n_skills * 2, hidden)
                self.rnn = nn.GRU(hidden, hidden, batch_first=True)
                self.out = nn.Linear(hidden, n_skills)

            def forward(self, x):
                emb = self.embed(x)
                h, _ = self.rnn(emb)
                return self.out(h)

        class NeuralIRT(nn.Module):
            def __init__(self, n_users: int, n_items: int, n_skills: int, hidden: int):
                super().__init__()
                emb = int(irt_state["user_emb.weight"].shape[1])
                self.user_emb = nn.Embedding(max(n_users, 1), emb)
                self.item_emb = nn.Embedding(max(n_items, 1), emb)
                self.skill_emb = nn.Embedding(n_skills, emb)
                self.net = nn.Sequential(
                    nn.Linear(emb * 3, hidden),
                    nn.ReLU(),
                    nn.Linear(hidden, 1),
                )

            def forward(self, user_ids, item_ids, skill_ids):
                x = torch.cat(
                    [
                        self.user_emb(user_ids),
                        self.item_emb(item_ids),
                        self.skill_emb(skill_ids),
                    ],
                    dim=-1,
                )
                return self.net(x).squeeze(-1)

        dkt = DKT(n_skills=n_skills, hidden=hidden)
        dkt.load_state_dict(dkt_state)
        deep_irt = NeuralIRT(
            n_users=len(users),
            n_items=len(exercises),
            n_skills=n_skills,
            hidden=hidden,
        )
        deep_irt.load_state_dict(irt_state)
        dkt.eval()
        deep_irt.eval()
        return {
            "loaded": True,
            "torch": torch,
            "dkt": dkt,
            "deep_irt": deep_irt,
            "manifest": manifest,
            "skills": skills,
            "users": users,
            "exercises": exercises,
        }
    except Exception as exc:
        return {"loaded": False, "warning": f"Deep-IRT/DKT runtime unavailable: {type(exc).__name__}: {exc}"}


def neural_knowledge_tracing_summary(attempt_rows: Iterable[Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    runtime = _load_neural_irt_dkt_runtime()
    if not runtime.get("loaded"):
        return {"loaded": False, "used": False, "warning": runtime.get("warning")}
    rows = sorted(list(attempt_rows), key=lambda r: getattr(r, "id", 0))
    if user_id is not None:
        rows = [row for row in rows if str(row.user_id) == str(user_id)]
    if not rows:
        return {"loaded": True, "used": False, "warning": "No attempts available for this user"}

    skills = runtime["skills"]
    n_skills = len(skills) + 1
    x = []
    for row in rows:
        exercise = getattr(row, "exercise", None)
        skill = getattr(getattr(exercise, "category", None), "value", "unknown") if exercise else "unknown"
        skill_id = int(skills.get(skill, 0))
        x.append(skill_id + (n_skills if bool(row.is_correct) else 0))
    if not x:
        return {"loaded": True, "used": False, "warning": "No valid attempt sequence"}

    torch = runtime["torch"]
    with torch.no_grad():
        logits = runtime["dkt"](torch.tensor([x], dtype=torch.long))[0, -1]
        probs = torch.sigmoid(logits).tolist()
    skill_predictions = [
        {
            "skill": skill,
            "next_success_probability": round(float(probs[int(skill_id)]), 4),
        }
        for skill, skill_id in skills.items()
        if int(skill_id) < len(probs)
    ]
    return {
        "loaded": True,
        "used": True,
        "model": "Active GRU-DKT artifact",
        "sequence_length": len(x),
        "skill_predictions": sorted(skill_predictions, key=lambda item: item["next_success_probability"]),
    }


def neural_adaptive_item_scores(attempt_rows: Iterable[Any], exercise_rows: Iterable[Any], user_id: str) -> Dict[str, Any]:
    runtime = _load_neural_irt_dkt_runtime()
    if not runtime.get("loaded"):
        return {"loaded": False, "runtime": {"loaded": False, "warning": runtime.get("warning")}, "scores": {}}
    users = runtime["users"]
    exercises = runtime["exercises"]
    skills = runtime["skills"]
    user_idx = users.get(str(user_id))
    if user_idx is None:
        return {"loaded": False, "runtime": {"loaded": True, "used": False, "warning": "User not present in trained Deep-IRT manifest"}, "scores": {}}

    dkt_summary = neural_knowledge_tracing_summary(attempt_rows, user_id=user_id)
    dkt_by_skill = {
        item["skill"]: item["next_success_probability"]
        for item in dkt_summary.get("skill_predictions", [])
    }
    torch = runtime["torch"]
    scores: Dict[int, Dict[str, float]] = {}
    with torch.no_grad():
        for exercise in exercise_rows:
            exercise_idx = exercises.get(str(int(exercise.id)))
            skill = getattr(getattr(exercise, "category", None), "value", "unknown")
            skill_id = skills.get(skill)
            if exercise_idx is None or skill_id is None:
                continue
            logit = runtime["deep_irt"](
                torch.tensor([int(user_idx)], dtype=torch.long),
                torch.tensor([int(exercise_idx)], dtype=torch.long),
                torch.tensor([int(skill_id)], dtype=torch.long),
            )
            deep_irt_prob = float(torch.sigmoid(logit)[0].item())
            dkt_prob = float(dkt_by_skill.get(skill, deep_irt_prob))
            scores[int(exercise.id)] = {
                "deep_irt_success_probability": round(deep_irt_prob, 4),
                "dkt_success_probability": round(dkt_prob, 4),
                "combined_success_probability": round((deep_irt_prob + dkt_prob) / 2, 4),
            }
    return {
        "loaded": True,
        "runtime": {
            "loaded": True,
            "used": True,
            "method": "Active Deep-IRT + DKT artifacts",
            "scored_items": len(scores),
        },
        "scores": scores,
    }


def rag_ablation_metrics(with_context: Sequence[Dict[str, Any]], without_context: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare correction/explanation error rates with and without retrieval context."""
    def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        total = max(len(rows), 1)
        incorrect = sum(1 for row in rows if not bool(row.get("is_correct", False)))
        unsafe = sum(1 for row in rows if bool(row.get("unsafe", False)))
        return {
            "n": len(rows),
            "error_rate": incorrect / total,
            "unsafe_rate": unsafe / total,
        }

    rag = summarize(with_context)
    base = summarize(without_context)
    reduction = (base["error_rate"] - rag["error_rate"]) / max(base["error_rate"], 1e-6)
    return {
        "with_rag": {k: round(v, 4) if isinstance(v, float) else v for k, v in rag.items()},
        "without_rag": {k: round(v, 4) if isinstance(v, float) else v for k, v in base.items()},
        "relative_error_reduction": round(reduction, 4),
        "interpretation": "Positive value means retrieval/context reduced errors compared with no-context generation.",
    }


def rubric_summary(review_rows: Iterable[Any]) -> Dict[str, Any]:
    rows = list(review_rows)
    if not rows:
        return {
            "count": 0,
            "averages": {},
            "approved_rate": 0.0,
            "rubric": {
                "linguistic_accuracy": "A është shqipja e saktë?",
                "clarity": "A është shpjegimi i qartë për fëmijën?",
                "age_appropriateness": "A i përshtatet moshës/klasës?",
                "pedagogical_value": "A mëson diçka konkrete?",
                "safety": "A shmang shpjegime të gabuara apo ndëshkuese?",
            },
        }
    fields = ["linguistic_accuracy", "clarity", "age_appropriateness", "pedagogical_value", "safety"]
    averages = {
        field: round(sum(int(getattr(row, field, 0)) for row in rows) / len(rows), 2)
        for field in fields
    }
    return {
        "count": len(rows),
        "averages": averages,
        "approved_rate": round(sum(1 for row in rows if row.approved_for_children) / len(rows), 3),
    }


def final_experiment_protocol(stats: Dict[str, int]) -> Dict[str, Any]:
    """Protocol checklist for turning the platform prototype into publishable PhD experiments."""
    exercise_count = int(stats.get("exercise_count", 0))
    attempt_count = int(stats.get("attempt_count", 0))
    review_count = int(stats.get("review_count", 0))
    model_status = model_training_status()
    return {
        "child_facing_name": "AI Mësimore",
        "scientific_name": "AI-assisted Albanian spelling exercise generation and pedagogical feedback",
        "readiness": {
            "lora_qlora_dataset": {
                "status": "lora_trained_and_runtime_active" if model_status["models"]["lora_qlora"]["trained"] else "ready_for_export" if exercise_count > 0 else "needs_exercises",
                "available_pairs": exercise_count,
                "implemented": [
                    "763 existing exercises are exportable as instruction-output pairs.",
                    "LoRA adapter is loaded at runtime for automatic exercise proposals.",
                    "QLoRA command path is defined for CUDA/NVIDIA GPU training.",
                ],
                "required_next_step": "Use QLoRA only on CUDA/NVIDIA GPU; current local artifact is LoRA because macOS bitsandbytes has no GPU quantization.",
            },
            "official_errant_gleu": {
                "status": "benchmark_artifact_ready" if model_status["models"]["errant_gleu_benchmark"]["trained"] else "protocol_defined",
                "implemented": [
                    "GLEU package and ERRANT package are installed in the training environment.",
                    "Benchmark runner stores reproducible JSON artifacts.",
                    "Fallback metrics are explicitly labeled ERRANT-inspired/GLEU-like.",
                ],
                "required_next_step": "For publication, validate Albanian tokenization/annotation and use a teacher-approved gold correction set.",
            },
            "deep_irt_knowledge_tracing": {
                "status": "trained_and_runtime_active" if model_status["models"]["deep_irt_dkt"]["trained"] else "data_ready" if attempt_count >= 100 else "needs_more_student_attempts",
                "available_attempts": attempt_count,
                "implemented": [
                    "IRT estimates theta/beta and flags anomalous items.",
                    "DKT artifact predicts next skill success over time.",
                    "Deep-IRT artifact scores candidate exercises in adaptive selection.",
                ],
                "required_next_step": "Collect more student attempts before claiming final generalizable model performance.",
            },
            "teacher_linguist_evaluation": {
                "status": "rubric_active" if review_count > 0 else "rubric_ready_needs_reviews",
                "available_reviews": review_count,
                "implemented": [
                    "Rubric fields are implemented: linguistic accuracy, clarity, age appropriateness, pedagogical value, safety.",
                    "Admin UI can submit and summarize reviews.",
                    "Generated items remain unapproved for children until reviewed.",
                ],
                "required_next_step": "Collect real ratings from Albanian teachers/linguists; demo reviews must not be reported as human evaluation.",
            },
        },
        "recommended_study_design": [
            "Split data into train/validation/test at exercise and student-attempt level.",
            "Compare generated exercises with database-authored exercises using grade-fit metrics.",
            "Evaluate correction with official ERRANT F0.5 and GLEU on a teacher-validated gold set.",
            "Evaluate explanations with teacher rubric: linguistic accuracy, clarity, age fit, pedagogical value, safety.",
            "Compare RAG/context generation against no-context generation and report relative error reduction.",
            "Use IRT/KT estimates only for recommendations, never as correctness authority.",
        ],
        "safety_policy": [
            "Children see supportive labels such as AI Mësimore, Ndihmë, Provo përsëri.",
            "The database and deterministic rules decide correctness.",
            "LLM output is limited to explanations and must pass rule/teacher review before child-facing reuse.",
            "Closed categories such as numbers, antonyms, synonyms and fixed answers never rely on LLM correctness.",
        ],
    }


def deep_learning_sequence_dataset(attempt_rows: Iterable[Any]) -> Dict[str, Any]:
    """Export chronological attempt sequences suitable for Deep-IRT/DKT training."""
    by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in sorted(list(attempt_rows), key=lambda r: getattr(r, "id", 0)):
        exercise = getattr(row, "exercise", None)
        by_user[str(row.user_id)].append({
            "exercise_id": int(row.exercise_id),
            "skill": getattr(getattr(exercise, "category", None), "value", "unknown") if exercise else "unknown",
            "correct": 1 if row.is_correct else 0,
            "score_delta": int(getattr(row, "score_delta", 0) or 0),
        })
    sequences = [
        {"user_id": user_id, "sequence_length": len(seq), "attempts": seq}
        for user_id, seq in by_user.items()
    ]
    return {
        "format": "deep_irt_dkt_sequence_json",
        "sequence_count": len(sequences),
        "total_attempts": sum(item["sequence_length"] for item in sequences),
        "minimum_recommendation": "For neural Deep-IRT/DKT, collect substantially more chronological attempts before claiming final model performance.",
        "sequences": sequences,
    }


def model_training_status(base_dir: Optional[str] = None) -> Dict[str, Any]:
    base_dir = base_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "model_artifacts"))
    checks = {
        "lora_qlora": {
            "artifact_dir": os.path.join(base_dir, "lora_qlora", "adapter"),
            "required_files": ["training_manifest.json"],
            "child_facing_use": "Gjeneron ushtrime të reja si AI Mësimore pas trajnimit.",
        },
        "deep_irt_dkt": {
            "artifact_dir": os.path.join(base_dir, "deep_irt_dkt"),
            "required_files": ["training_manifest.json", "dkt_model.pt", "deep_irt_model.pt"],
            "child_facing_use": "Ndihmon në zgjedhjen e ushtrimit të radhës në nivel të përshtatshëm.",
        },
        "errant_gleu_benchmark": {
            "artifact_dir": os.path.join(base_dir, "benchmarks"),
            "required_files": ["errant_gleu_results.json"],
            "manifest_file": "errant_gleu_results.json",
            "child_facing_use": "Nuk shfaqet te fëmijët; përdoret vetëm për vlerësim shkencor.",
        },
    }
    status = {}
    for name, cfg in checks.items():
        artifact_dir = cfg["artifact_dir"]
        required = [os.path.join(artifact_dir, file_name) for file_name in cfg["required_files"]]
        trained = all(os.path.exists(path) for path in required)
        manifest = None
        manifest_path = os.path.join(artifact_dir, cfg.get("manifest_file", "training_manifest.json"))
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                manifest = {"warning": "manifest exists but could not be read"}
        status[name] = {
            "trained": trained,
            "artifact_dir": artifact_dir,
            "missing_files": [path for path in required if not os.path.exists(path)],
            "manifest": manifest,
            "child_facing_use": cfg["child_facing_use"],
        }
        if name == "lora_qlora":
            status[name]["scientific_status"] = {
                "lora": "trained_and_runtime_loaded_when_dependencies_are_available" if trained else "not_trained",
                "qlora": "cuda_gpu_required_for_real_4bit_training",
                "runtime_policy": "LLM proposes content; database/rules remain authoritative.",
            }
        elif name == "deep_irt_dkt":
            status[name]["scientific_status"] = {
                "deep_irt": "active_in_adaptive_next_item" if trained else "not_available",
                "dkt": "active_in_knowledge_tracing" if trained else "not_available",
                "runtime_policy": "Used for recommendation/scoring only, never grading correctness.",
            }
        elif name == "errant_gleu_benchmark":
            status[name]["scientific_status"] = {
                "errant": "package_available_but_albanian_requires_validated_preprocessing",
                "gleu": "benchmark_artifact_available" if trained else "not_available",
                "publication_policy": "Use teacher-validated Albanian gold set; otherwise label as ERRANT-inspired.",
            }
    return {
        "base_dir": base_dir,
        "models": status,
        "deployment_rule": "Render/Vercel load artifacts only; training should run on GPU/Colab and artifacts are then copied into backend/model_artifacts.",
    }


def training_commands() -> Dict[str, Any]:
    return {
        "install_training_dependencies": "pip install -r backend/requirements-training.txt",
        "lora_qlora": [
            "cd backend",
            "python scripts/export_lora_dataset.py",
            "python scripts/train_lora_qlora.py --model Qwen/Qwen2.5-0.5B-Instruct --qlora",
        ],
        "deep_irt_dkt": [
            "cd backend",
            "python scripts/train_deep_irt_dkt.py --epochs 30",
        ],
        "errant_gleu": [
            "cd backend",
            "python scripts/run_errant_gleu_benchmark.py --input model_artifacts/benchmarks/test_corrections.jsonl",
        ],
        "important": "Run these on a GPU/Colab/training machine. Do not run full training on Render free tier.",
    }


def _clip_probability(value: float) -> float:
    return min(0.99, max(0.01, float(value)))


def _logit(p: float) -> float:
    p = _clip_probability(p)
    return math.log(p / (1 - p))


def instruction_pair_from_exercise(exercise: Any) -> Dict[str, Any]:
    level = getattr(exercise, "level", None)
    course = getattr(exercise, "course", None)
    grade = None
    try:
        if course and getattr(course, "parent_class", None):
            grade = getattr(course.parent_class, "order_index", None)
    except Exception:
        grade = None
    answer = getattr(exercise, "answer", "")
    data = {}
    if getattr(exercise, "data", None):
        try:
            data = json.loads(exercise.data)
        except Exception:
            data = {"raw": exercise.data}
    return {
        "instruction": f"Gjenero një ushtrim të kategorisë '{exercise.category.value}' për klasën {grade or 'N/A'} me vështirësi të përshtatur.",
        "input": {
            "category": exercise.category.value,
            "prompt_style": getattr(exercise, "prompt", ""),
            "grade": grade,
            "level": getattr(level, "order_index", None),
            "rule": getattr(exercise, "rule", None),
        },
        "output": {
            "prompt": getattr(exercise, "prompt", ""),
            "answer": answer,
            "data": data,
            "points": getattr(exercise, "points", 1),
        },
    }
