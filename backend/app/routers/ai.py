from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4
import random
import re
import unicodedata
from collections import Counter
from ..database import get_db
from .. import models, schemas


router = APIRouter()


def _norm(s: Optional[str]) -> str:
	return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", (s or "")).strip().lower())


def _classify_spelling_error(correct: str, user: str) -> str:
	c = _norm(correct)
	u = _norm(user)
	if not u:
		return "empty"
	if c == u:
		return "none"

	def strip_diacritics(x: str) -> str:
		return x.replace("ë", "e").replace("ç", "c")

	if strip_diacritics(c) == strip_diacritics(u) and c != u:
		return "diacritics(ë/e, ç/c)"

	if len(u) < len(c) and strip_diacritics(u) in strip_diacritics(c):
		return "missing_letters"
	if len(u) > len(c) and strip_diacritics(c) in strip_diacritics(u):
		return "extra_letters"

	# Double consonant noise (either direction)
	def collapse_double(x: str) -> str:
		return re.sub(r"([a-zëç])\\1+", r"\\1", x)

	if collapse_double(c) == collapse_double(u) and c != u:
		return "double_consonants"

	return "substitution"


@router.post("/ai/coach", response_model=schemas.AICoachResponse)
def ai_coach(request: schemas.AICoachRequest, db: Session = Depends(get_db)):
	"""
	AI Coach: advanced analytics over user attempts to produce:
	- mistake profile (Albanian orthography patterns)
	- micro-lessons (short, actionable explanations)
	- drill plan (what to practice next)
	"""
	q = db.query(models.Attempt).join(models.Exercise, models.Attempt.exercise_id == models.Exercise.id).filter(
		models.Attempt.user_id == request.user_id
	)
	if request.level_id:
		q = q.filter(models.Exercise.level_id == request.level_id)

	attempts = q.order_by(models.Attempt.id.desc()).limit(200).all()
	if not attempts:
		raise HTTPException(status_code=404, detail="No attempts found for AI Coach.")

	incorrect = []
	examples_by_type = {}
	for a in attempts:
		if a.is_correct:
			continue
		ex = db.get(models.Exercise, a.exercise_id)
		if not ex:
			continue
		err_type = _classify_spelling_error(ex.answer, a.response)
		incorrect.append(err_type)
		examples_by_type.setdefault(err_type, [])
		if len(examples_by_type[err_type]) < 5:
			examples_by_type[err_type].append(f"{a.response} → {ex.answer}")

	counts = Counter(incorrect)
	patterns = [
		schemas.AICoachMistakePattern(type=k, count=v, examples=examples_by_type.get(k, []))
		for k, v in counts.most_common()
	]

	micro_lessons: List[str] = []
	drill_plan: List[str] = []

	# Micro-lessons
	if counts.get("diacritics(ë/e, ç/c)"):
		micro_lessons.append("Ë/Ç janë fonema dhe shkronja standarde në shqip. Praktiko dallimin ë↔e dhe ç↔c në fjalët që i ngatërron.")
		drill_plan.append("Bëj 10 ushtrime minimal-pair: ç/c dhe ë/e (fokus te fjalët ku gabon).")
	if counts.get("missing_letters"):
		micro_lessons.append("Kur mungojnë shkronja, zakonisht humbet një rrokje ose një tingull i dobët. Shkruaj ngadalë dhe numëro shkronjat.")
		drill_plan.append("Ushtrim 'Saktësi': numëro shkronjat dhe kontrollo para se ta dërgosh përgjigjen.")
	if counts.get("extra_letters"):
		micro_lessons.append("Shkronjat shtesë shpesh vijnë nga përsëritje automatike ose OCR/typing. Krahaso përgjigjen me fjalën e saktë pa shtuar tinguj.")
		drill_plan.append("Ushtrim 'Redaktim': shkruaj fjalën, pastaj hiq çdo shkronjë që nuk e dëgjon.")
	if counts.get("double_consonants"):
		micro_lessons.append("Bashkëtingëlloret e dyfishta në shqip nuk janë gjithmonë të zakonshme; kontrollo nëse po i dyfishon gabimisht.")
		drill_plan.append("Ushtrim: krahaso variantin me një dhe me dy bashkëtingëllore dhe zgjidh të saktin.")
	if counts.get("substitution"):
		micro_lessons.append("Zëvendësimet e shkronjave kërkojnë vëmendje te pozicioni i gabimit. Fokusohu te shkronja problematike dhe shkruaje fjalën 3 herë saktë.")
		drill_plan.append("Ushtrim: përsëritje e kontrolluar (3 herë) për 5 fjalët me gabimet më të shpeshta.")

	if not micro_lessons:
		micro_lessons.append("Nuk u gjetën modele të qarta gabimesh. Vazhdo me ushtrimet dhe AI Coach do të personalizohet më shumë.")
		drill_plan.append("Vazhdo me 1–2 nivele dhe rikthehu te AI Coach për analizë më të saktë.")

	return schemas.AICoachResponse(
		user_id=request.user_id,
		level_id=request.level_id,
		total_attempts_analyzed=len(attempts),
		incorrect_attempts_analyzed=len(incorrect),
		patterns=patterns,
		micro_lessons=micro_lessons,
		drill_plan=drill_plan,
	)


@router.get("/ai/recommendations/{user_id}")
def get_ai_recommendations(user_id: str, db: Session = Depends(get_db)):
	"""Get AI-powered exercise recommendations based on user performance"""
	
	# Get user's performance data
	user_attempts = (
		db.query(models.Attempt)
		.filter(models.Attempt.user_id == user_id)
		.all()
	)
	
	if not user_attempts:
		# New user - recommend first course
		first_course = (
			db.query(models.Course)
			.filter(models.Course.order_index == 1)
			.first()
		)
		return {
			"recommendation_type": "new_user",
			"message": "Mirësevini! Fillo me kursin e parë për të mësuar bazat.",
			"recommended_course": first_course.id if first_course else None,
			"difficulty": "beginner"
		}
	
	# Analyze performance patterns
	correct_attempts = [a for a in user_attempts if a.is_correct]
	incorrect_attempts = [a for a in user_attempts if not a.is_correct]
	
	accuracy = len(correct_attempts) / len(user_attempts) if user_attempts else 0
	
	# Get user's current progress
	user_progress = (
		db.query(models.Progress)
		.filter(models.Progress.user_id == user_id)
		.all()
	)
	
	# Find areas for improvement
	weak_categories = []
	for progress in user_progress:
		if progress.errors > progress.points:
			weak_categories.append(progress.category)
	
	# AI recommendation logic
	if accuracy < 0.6:
		recommendation_type = "review_weak_areas"
		message = "Duhet të përmirësosh disa fusha. Fokusohu në ushtrimet e gabuara."
		difficulty = "easier"
	elif accuracy > 0.9:
		recommendation_type = "challenge_yourself"
		message = "Je duke bërë shumë mirë! Provo nivele më të vështira."
		difficulty = "harder"
	else:
		recommendation_type = "steady_progress"
		message = "Po eci mirë! Vazhdo me ritmin tënd."
		difficulty = "current"
	
	# Find next recommended exercise
	recommended_exercise = None
	if weak_categories:
		# Recommend exercise from weak category
		exercise = (
			db.query(models.Exercise)
			.filter(models.Exercise.category.in_(weak_categories))
			.filter(models.Exercise.enabled == True)
			.first()
		)
		if exercise:
			recommended_exercise = exercise.id
	
	return {
		"recommendation_type": recommendation_type,
		"message": message,
		"accuracy": accuracy,
		"weak_categories": [cat.value for cat in weak_categories],
		"difficulty": difficulty,
		"recommended_exercise": recommended_exercise,
		"total_attempts": len(user_attempts),
		"correct_attempts": len(correct_attempts)
	}


@router.get("/ai/adaptive-difficulty/{user_id}")
def get_adaptive_difficulty(user_id: str, db: Session = Depends(get_db)):
	"""Get adaptive difficulty settings based on user performance"""
	
	# Get recent performance (last 20 attempts)
	recent_attempts = (
		db.query(models.Attempt)
		.filter(models.Attempt.user_id == user_id)
		.order_by(models.Attempt.id.desc())
		.limit(20)
		.all()
	)
	
	if not recent_attempts:
		return {"difficulty": "normal", "multiplier": 1.0}
	
	recent_accuracy = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
	
	# Adaptive difficulty logic
	if recent_accuracy < 0.4:
		difficulty = "easier"
		multiplier = 0.8  # Reduce difficulty
		message = "Duke u përmirësuar! Po e bëj më të lehtë për ty."
	elif recent_accuracy > 0.8:
		difficulty = "harder"
		multiplier = 1.2  # Increase difficulty
		message = "Je duke bërë shumë mirë! Po e bëj më të vështirë."
	else:
		difficulty = "normal"
		multiplier = 1.0
		message = "Ritmi i duhur! Vazhdo kështu."
	
	return {
		"difficulty": difficulty,
		"multiplier": multiplier,
		"message": message,
		"recent_accuracy": recent_accuracy,
		"attempts_analyzed": len(recent_attempts)
	}


@router.get("/ai/learning-path/{user_id}")
def get_learning_path(user_id: str, db: Session = Depends(get_db)):
	"""Get personalized learning path based on user's learning style and performance"""
	
	# Analyze learning patterns
	user_attempts = (
		db.query(models.Attempt)
		.filter(models.Attempt.user_id == user_id)
		.all()
	)
	
	if not user_attempts:
		return {"path": "standard", "message": "Fillo me rrugën standarde të mësimit."}
	
	# Analyze category preferences
	category_performance = {}
	for attempt in user_attempts:
		exercise = db.get(models.Exercise, attempt.exercise_id)
		if exercise:
			cat = exercise.category.value
			if cat not in category_performance:
				category_performance[cat] = {"correct": 0, "total": 0}
			category_performance[cat]["total"] += 1
			if attempt.is_correct:
				category_performance[cat]["correct"] += 1
	
	# Find strengths and weaknesses
	strengths = []
	weaknesses = []
	
	for cat, perf in category_performance.items():
		accuracy = perf["correct"] / perf["total"]
		if accuracy > 0.8:
			strengths.append(cat)
		elif accuracy < 0.5:
			weaknesses.append(cat)
	
	# Determine learning path
	if len(strengths) > len(weaknesses):
		path = "accelerated"
		message = "Je duke ecur shpejt! Mund të kalosh në nivele më të avancuara."
	elif len(weaknesses) > len(strengths):
		path = "foundational"
		message = "Fokusohu në bazat për të ndërtuar një themel të fortë."
	else:
		path = "balanced"
		message = "Ritmi i balancuar! Vazhdo me të gjitha kategoritë."
	
	return {
		"path": path,
		"message": message,
		"strengths": strengths,
		"weaknesses": weaknesses,
		"category_performance": category_performance
	}


@router.get("/ai/smart-hints/{exercise_id}/{user_id}")
def get_smart_hints(exercise_id: int, user_id: str, db: Session = Depends(get_db)):
	"""Get smart hints based on user's previous mistakes and learning patterns"""
	
	exercise = db.get(models.Exercise, exercise_id)
	if not exercise:
		raise HTTPException(status_code=404, detail="Exercise not found")
	
	# Get user's previous attempts on similar exercises
	similar_exercises = (
		db.query(models.Exercise)
		.filter(models.Exercise.category == exercise.category)
		.filter(models.Exercise.id != exercise_id)
		.all()
	)
	
	similar_exercise_ids = [ex.id for ex in similar_exercises]
	
	user_attempts_on_similar = (
		db.query(models.Attempt)
		.filter(models.Attempt.user_id == user_id)
		.filter(models.Attempt.exercise_id.in_(similar_exercise_ids))
		.all()
	)
	
	# Analyze common mistakes
	common_mistakes = []
	if user_attempts_on_similar:
		incorrect_attempts = [a for a in user_attempts_on_similar if not a.is_correct]
		if incorrect_attempts:
			# Find patterns in mistakes
			common_mistakes = [
				"Kontrollo drejtshkrimin e fjalëve të gjata",
				"Kujdes me përdorimin e ë/e",
				"Vërejtje me bashkëtingëlloret e dyfishta"
			]
	
	# Generate contextual hints
	contextual_hints = []
	if exercise.category == models.CategoryEnum.SPELLING:
		contextual_hints.append("Kujdes me shkronjat që mungojnë")
	elif exercise.category == models.CategoryEnum.GRAMMAR:
		contextual_hints.append("Kontrollo trajtën e shkurtrave")
	elif exercise.category == models.CategoryEnum.VOCABULARY:
		contextual_hints.append("Mendoni për kuptimin e fjalës")
	
	return {
		"exercise_id": exercise_id,
		"category": exercise.category.value,
		"common_mistakes": common_mistakes,
		"contextual_hints": contextual_hints,
		"similar_exercises_attempted": len(user_attempts_on_similar),
		"accuracy_on_similar": sum(1 for a in user_attempts_on_similar if a.is_correct) / len(user_attempts_on_similar) if user_attempts_on_similar else 0
	}


@router.get("/ai/progress-insights/{user_id}")
def get_progress_insights(user_id: str, db: Session = Depends(get_db)):
	"""Get AI-generated insights about user's learning progress"""
	
	# Get comprehensive user data
	user_progress = (
		db.query(models.Progress)
		.filter(models.Progress.user_id == user_id)
		.all()
	)
	
	user_attempts = (
		db.query(models.Attempt)
		.filter(models.Attempt.user_id == user_id)
		.all()
	)
	
	if not user_attempts:
		return {"insights": ["Je duke filluar udhëtimin tënd!"]}
	
	# Calculate insights
	insights = []
	
	total_attempts = len(user_attempts)
	correct_attempts = sum(1 for a in user_attempts if a.is_correct)
	overall_accuracy = correct_attempts / total_attempts
	
	# Learning streak analysis
	recent_attempts = user_attempts[-10:] if len(user_attempts) >= 10 else user_attempts
	recent_accuracy = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
	
	if recent_accuracy > overall_accuracy:
		insights.append("Je duke përmirësuar! Performanca jote e fundit është më e mirë se mesatarja.")
	elif recent_accuracy < overall_accuracy:
		insights.append("Mund të kesh nevojë për të rishikuar disa koncepte bazë.")
	
	# Category insights
	category_performance = {}
	for attempt in user_attempts:
		exercise = db.get(models.Exercise, attempt.exercise_id)
		if exercise:
			cat = exercise.category.value
			if cat not in category_performance:
				category_performance[cat] = {"correct": 0, "total": 0}
			category_performance[cat]["total"] += 1
			if attempt.is_correct:
				category_performance[cat]["correct"] += 1
	
	best_category = None
	worst_category = None
	best_accuracy = 0
	worst_accuracy = 1
	
	for cat, perf in category_performance.items():
		accuracy = perf["correct"] / perf["total"]
		if accuracy > best_accuracy:
			best_accuracy = accuracy
			best_category = cat
		if accuracy < worst_accuracy:
			worst_accuracy = accuracy
			worst_category = cat
	
	if best_category and best_accuracy > 0.8:
		insights.append(f"Je shumë i fortë në {best_category}! Mund të ndihmosh të tjerët.")
	
	if worst_category and worst_accuracy < 0.6:
		insights.append(f"Fokusohu më shumë në {worst_category} për të përmirësuar rezultatet.")
	
	# Time-based insights
	if total_attempts > 50:
		insights.append("Ke bërë shumë progres! Vazhdo kështu.")
	elif total_attempts > 20:
		insights.append("Je duke ndërtuar një themel të fortë. Vazhdo me ushtrimet.")
	else:
		insights.append("Çdo ushtrim të afron më afër qëllimit. Vazhdo!")
	
	return {
		"insights": insights,
		"overall_accuracy": overall_accuracy,
		"total_attempts": total_attempts,
		"best_category": best_category,
		"worst_category": worst_category,
		"learning_streak": "positive" if recent_accuracy > overall_accuracy else "needs_improvement"
	}


@router.post("/ai/personalized-practice", response_model=schemas.PersonalizedPracticeResponse)
def personalized_practice(request: schemas.PersonalizedPracticeRequest, db: Session = Depends(get_db)):
	"""
	Generate advanced, personalized practice exercises for a specific level using local heuristics.

	Design goals:
	- Not just "write the word" repeatedly.
	- Each returned exercise should have a different pedagogical focus (context, discrimination, precision).
	- Personalized based on the user's real mistakes for this level when available.
	"""

	level = db.get(models.Level, request.level_id)
	if not level:
		raise HTTPException(status_code=404, detail="Level not found")

	course = db.get(models.Course, level.course_id)
	parent_class = None
	if course and course.parent_class_id:
		parent_class = db.get(models.Course, course.parent_class_id)

	attempts = (
		db.query(models.Attempt)
		.join(models.Exercise, models.Attempt.exercise_id == models.Exercise.id)
		.filter(
			models.Attempt.user_id == request.user_id,
			models.Exercise.level_id == request.level_id
		)
		.order_by(models.Attempt.id.desc())
		.all()
	)

	problem_terms = []
	mistake_lookup = {}
	for attempt in attempts:
		exercise = db.get(models.Exercise, attempt.exercise_id)
		if exercise and not attempt.is_correct:
			problem_terms.append(exercise.answer)
			mistake_lookup.setdefault(exercise.answer, []).append(attempt.response)

	problem_terms = list(dict.fromkeys(problem_terms))

	level_exercises = (
		db.query(models.Exercise)
		.filter(
			models.Exercise.level_id == request.level_id,
			models.Exercise.enabled == True
		)
		.order_by(models.Exercise.order_index.asc())
		.all()
	)

	fallback_terms = [ex.answer for ex in level_exercises if ex.answer]
	for term in fallback_terms:
		if len(problem_terms) >= 3:
			break
		if term not in problem_terms:
			problem_terms.append(term)

	if not problem_terms:
		raise HTTPException(status_code=400, detail="Nuk u gjetën të dhëna për ushtrime AI")

	random.shuffle(problem_terms)
	slices = problem_terms[:3]

	base_exercise_by_term = {}
	for ex in level_exercises:
		if ex.answer and ex.answer not in base_exercise_by_term:
			base_exercise_by_term[ex.answer] = ex

	exercises: List[schemas.PersonalizedPracticeExerciseOut] = []
	used_kinds = set()
	for idx, term in enumerate(slices):
		base_ex = base_exercise_by_term.get(term)
		mistake_examples = mistake_lookup.get(term, [])
		mistake_response = mistake_examples[0] if mistake_examples else None
		analysis = _analyze_mistake(term, mistake_response)

		kind = _pick_exercise_kind(analysis["type"], used_kinds)
		used_kinds.add(kind)

		prompt, expected_answer, hint = _build_personalized_exercise(
			term=term,
			kind=kind,
			level=level,
			parent_class=parent_class,
			base_exercise=base_ex,
			mistake_response=mistake_response,
			mistake_hint=analysis.get("hint"),
		)

		exercises.append(
			schemas.PersonalizedPracticeExerciseOut(
				id=str(uuid4()),
				prompt=prompt,
				answer=expected_answer,
				category=(base_ex.category.value if base_ex else models.CategoryEnum.SPELLING.value),
				hint=hint,
				order_index=idx + 1,
			)
		)

	message = (
		"Ushtrimet shtesë janë të personalizuara për këtë nivel: "
		"një ushtrim për kontekst (diktim në fjali), një për dallim gabimesh (variantet), "
		"dhe një për saktësi (kontroll shkronjash)."
	)

	return schemas.PersonalizedPracticeResponse(
		exercises=exercises,
		message=message
	)


def _letters_count(term: str) -> int:
	# Count alphabetic characters only (handles Albanian letters in Unicode)
	return sum(1 for ch in term if ch.isalpha())


def _generate_sentence_frame(term: str) -> str:
	"""
	Generate a short, level-safe sentence containing the term.
	We keep it generic to avoid semantic errors and grammar issues.
	
	IMPORTANT: Uses grammatically correct Albanian sentences.
	Avoids case inflection issues by using nominative contexts.
	"""
	term_cap = term[:1].upper() + term[1:] if term else term
	frames = [
		f"{term_cap} është këtu në klasë.",
		f"Sot po mësojmë fjalën: {term}.",
		f"Shkruaje saktë fjalën {term} me kujdes.",
		f"Fjala e sotme është: {term}.",
		f"Përsërite fjalën: {term}.",
		f"Në fletore shkruaj: {term}.",
		f"Kjo është fjala {term}.",
	]
	return random.choice(frames)


def _generate_distractors(term: str, mistake_response: Optional[str]) -> List[str]:
	"""
	Generate plausible distractors (near-misses) for spelling discrimination.
	"""
	term_clean = term.strip()
	distractors = []

	if mistake_response:
		mr = mistake_response.strip()
		if mr and mr.lower() != term_clean.lower():
			distractors.append(mr)

	# Common Albanian confusions + generic perturbations
	def swap_chars(s: str, a: str, b: str) -> str:
		return s.replace(a, b) if a in s else s

	candidates = [
		swap_chars(term_clean, "ë", "e"),
		swap_chars(term_clean, "e", "ë"),
		swap_chars(term_clean, "ç", "c"),
		swap_chars(term_clean, "c", "ç"),
		term_clean[:-1] if len(term_clean) > 3 else term_clean,
		(term_clean + term_clean[-1]) if term_clean else term_clean,
	]

	for c in candidates:
		if c and c.lower() != term_clean.lower() and c not in distractors:
			distractors.append(c)

	# Ensure we return 3 choices including the correct one
	choices = [term_clean] + distractors
	# remove duplicates by lower
	unique = []
	seen = set()
	for c in choices:
		key = c.lower()
		if key not in seen and c:
			seen.add(key)
			unique.append(c)
	if len(unique) < 3:
		unique += [term_clean] * (3 - len(unique))
	return unique[:3]


def _analyze_mistake(term: str, attempt_response: Optional[str]) -> dict:
	"""
	Classify the user's mistake to tailor the exercise.
	"""
	if not attempt_response:
		return {"type": "none", "hint": None}

	t = term.strip().lower()
	r = attempt_response.strip().lower()
	if not r:
		return {"type": "none", "hint": None}

	def normalize_diacritics(s: str) -> str:
		return s.replace("ë", "e").replace("ç", "c")

	if normalize_diacritics(t) == normalize_diacritics(r) and t != r:
		return {
			"type": "diacritics",
			"hint": f"Fokusi: dallimi i shkronjave të veçanta (p.sh. ë/e, ç/c). Ke shkruar \"{attempt_response}\"."
		}

	if len(r) < len(t) and normalize_diacritics(r) in normalize_diacritics(t):
		return {"type": "missing", "hint": f"Fokusi: mungesë shkronjash. Ke shkruar \"{attempt_response}\"."}
	if len(r) > len(t) and normalize_diacritics(t) in normalize_diacritics(r):
		return {"type": "extra", "hint": f"Fokusi: shkronja shtesë. Ke shkruar \"{attempt_response}\"."}

	return {"type": "substitution", "hint": _describe_mistake(term, attempt_response)}


def _pick_exercise_kind(mistake_type: str, used_kinds: set) -> str:
	"""
	Pick a pedagogically distinct exercise kind, avoiding duplicates when possible.
	"""
	preferred = {
		"diacritics": ["discrimination", "context", "precision"],
		"missing": ["precision", "discrimination", "context"],
		"extra": ["precision", "discrimination", "context"],
		"substitution": ["discrimination", "precision", "context"],
		"none": ["context", "precision", "discrimination"],
	}.get(mistake_type, ["context", "precision", "discrimination"])

	for k in preferred:
		if k not in used_kinds:
			return k
	return preferred[0]


def _build_personalized_exercise(
	term: str,
	kind: str,
	level: models.Level,
	parent_class: Optional[models.Course],
	base_exercise: Optional[models.Exercise],
	mistake_response: Optional[str],
	mistake_hint: Optional[str],
) -> tuple[str, str, Optional[str]]:
	"""
	Return (prompt, expected_answer, hint) for one advanced exercise.
	"""
	class_name = parent_class.name if parent_class else f"Klasa {level.course_id}"
	level_name = f"Niveli {level.order_index}"

	# A small, safe "why this matters" hint – keeps exercises meaningful.
	def goal(text: str) -> str:
		return f"Qëllimi: {text} ({class_name}, {level_name})."

	if kind == "discrimination":
		a, b, c = _generate_distractors(term, mistake_response)
		prompt = (
			f"[Dallim gabimesh] Zgjidh variantin e saktë dhe shkruaje saktë si përgjigje.\n"
			f"A) {a}\nB) {b}\nC) {c}"
		)
		hint = goal("të dallosh gabimin tipik dhe të fiksosh drejtshkrimin") + (f" {mistake_hint}" if mistake_hint else "")
		return prompt, term, hint

	if kind == "precision":
		n = _letters_count(term)
		prompt = (
			f"[Saktësi] Shkruaje fjalën saktë. Kontrollo që të ketë saktësisht {n} shkronja.\n"
			f"Fjala: {term}"
		)
		hint = goal("të shmangësh heqjen/shtimin e shkronjave") + (f" {mistake_hint}" if mistake_hint else "")
		return prompt, term, hint

	# kind == "context" (default)
	sentence = _generate_sentence_frame(term)
	prompt = (
		f"[Kontekst / diktim] Shkruaj vetëm fjalën e nënvizuar nga fjalia.\n"
		f"Fjalia: \"{sentence}\""
	)
	hint = goal("ta përdorësh fjalën saktë në fjali dhe të përforcosh kujtesën ortografike")
	# If we have the original base prompt, add a subtle reference to keep it level-aligned
	if base_exercise and base_exercise.prompt:
		hint += f" (Referencë e nivelit: \"{base_exercise.prompt[:60]}\".)"
	return prompt, term, hint

def _build_ai_prompt(term: str, level: models.Level, parent_class: Optional[models.Course], mistake_hint: Optional[str]) -> str:
	"""Build AI-generated prompt text for personalized practice exercises"""
	class_name = parent_class.name if parent_class else f"Klasa {level.course_id}"
	templates = [
		"Dëgjo fjalën \"{term}\" nga Niveli {level} të {class_name} dhe shkruaje me drejtshkrim të saktë.",
		"Shkruaj fjalën që dëgjon: \"{term}\". Ky ushtrim është pjesë e Niveli {level} të {class_name}.",
		"Përmbledhje e fjalës \"{term}\": përpiqu ta shkruash saktë dhe përqendrohu te tingujt që po të përkeqësojnë gabimet në {class_name}.",
		"Shkruaj njëherë pa gabime fjalën \"{term}\". Fjala është për Niveli {level} të {class_name}."
	]

	hint_phrase = f" {mistake_hint}" if mistake_hint else ""
	template = random.choice(templates)
	return template.format(term=term, level=level.order_index, class_name=class_name) + hint_phrase


def _describe_mistake(term: str, attempt_response: Optional[str]) -> Optional[str]:
	if not attempt_response:
		return None
	term_clean = term.strip().lower()
	response_clean = attempt_response.strip().lower()
	for idx, (t_char, r_char) in enumerate(zip(term_clean, response_clean)):
		if t_char != r_char:
			return (
				f"Ke shkruar \"{attempt_response}\" në vend të \"{term}\" (qëndro te shkronja #{idx + 1}: '{t_char}'). "
				"Shiko kujdesin me ë/e apo ç/çh për të mos përsëritur gabimin."
			)
	if len(response_clean) != len(term_clean):
		return f"Shkruaj pa shtuar ose hequr shkronja; për shembull ke shkruar \"{attempt_response}\" me gjatësinë e gabuar."
	return None
