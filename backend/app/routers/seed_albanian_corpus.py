from sqlalchemy.orm import Session
from ..models import Course, Level, Exercise, CategoryEnum
from fastapi import APIRouter, Depends
from ..database import get_db
import json

router = APIRouter()


@router.post("/seed-12-courses")
def seed_twelve_courses():
    """Seed exactly 12 courses for Class 1 with the new structure"""
    db = next(get_db())
    
    try:
        # Clear existing data for Class 1
        class_ids_to_clear = db.query(Course.id).filter(
            (Course.name.like("Klasa e Parë%")) | (Course.name.like("Klasa 1%"))
        )
        db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
        db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
        db.query(Course).filter((Course.name.like("Klasa e Parë%")) | (Course.name.like("Klasa 1%"))).delete()
        
        # Seed the new 12-course structure
        course_id = seed_first_class_exercises(db)
        
        return {
            "message": "Successfully seeded 12 courses for Class 1",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": 93
        }
        
    except Exception as e:
        db.rollback()
        raise e


def seed_first_class_exercises(db: Session):
    """Seed the first class level with exactly 12 courses and their exercises"""
    
    # Clear existing data for Class 1
    db.query(Exercise).filter(Exercise.course_id.in_(
        db.query(Course.id).filter(Course.name.like("Klasa e Parë%"))
    )).delete()
    
    db.query(Level).filter(Level.course_id.in_(
        db.query(Course.id).filter(Course.name.like("Klasa e Parë%"))
    )).delete()
    
    db.query(Course).filter(Course.name.like("Klasa e Parë%")).delete()
    
    # Create the first class course
    first_class = Course(
        name="Klasa 1",
        description="Klasa e parë për moshën 6-7 vjeç me 12 kategorive të ushtrimeve",
        order_index=1,
        category=CategoryEnum.VOCABULARY,
        required_score=0,
        enabled=True
    )
    db.add(first_class)
    db.flush()  # Get the ID
    
    # Create 12 courses for Class 1
    courses = []
    
    # 1. Niveli 1
    course_1 = Course(
        name="Niveli 1",
        description="Dëgjo dhe shkruaj fjalët e thjeshta",
            order_index=1,
        category=CategoryEnum.LISTEN_WRITE,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_1)
    
    # 2. Niveli 2
    course_2 = Course(
        name="Niveli 2",
        description="Zgjedh fjalën e duhur nga lista bazuar në përshkrimin",
            order_index=2,
        category=CategoryEnum.WORD_FROM_DESCRIPTION,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_2)
    
    # 3. Niveli 3
    course_3 = Course(
        name="Niveli 3",
        description="Mëso sinonimet dhe antonimet e fjalëve bazike",
            order_index=3,
        category=CategoryEnum.SYNONYMS_ANTONYMS,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_3)
    
    # 4. Niveli 4
    course_4 = Course(
        name="Niveli 4",
        description="Identifiko nëse fjala është shqipe apo huazim",
            order_index=4,
        category=CategoryEnum.ALBANIAN_OR_LOANWORD,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_4)
    
    # 5. Niveli 5
    course_5 = Course(
        name="Niveli 5",
        description="Plotëso shkronjën që mungon në fjalë",
            order_index=5,
        category=CategoryEnum.MISSING_LETTER,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_5)
    
    # 6. Niveli 6
    course_6 = Course(
        name="Niveli 6",
        description="Gjej dhe ndreq shkronjën e gabuar në fjalë",
            order_index=6,
        category=CategoryEnum.WRONG_LETTER,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_6)
    
    # 7. Niveli 7
    course_7 = Course(
        name="Niveli 7",
        description="Ndërto fjalën nga shkronja të përziera",
            order_index=7,
        category=CategoryEnum.BUILD_WORD,
        required_score=0,
        enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_7)
    
    # 8. Niveli 8
    course_8 = Course(
        name="Niveli 8",
        description="Shkruaj numrin si fjalë",
        order_index=8,
        category=CategoryEnum.NUMBER_TO_WORD,
        required_score=0,
            enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_8)
    
    # 9. Niveli 9
    course_9 = Course(
        name="Niveli 9",
        description="Kuptimi i shprehjeve frazeologjike të thjeshta",
        order_index=9,
        category=CategoryEnum.PHRASES,
        required_score=0,
        enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_9)
    
    # 10. Niveli 10
    course_10 = Course(
        name="Niveli 10",
        description="Gjej gabimin dhe rishkruaj saktë",
        order_index=10,
        category=CategoryEnum.SPELLING_PUNCTUATION,
        required_score=0,
        enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_10)
    
    # 11. Niveli 11
    course_11 = Course(
        name="Niveli 11",
        description="Zgjedh fjalën sipas kuptimit abstrakt ose konkret",
        order_index=11,
        category=CategoryEnum.ABSTRACT_CONCRETE,
        required_score=0,
        enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_11)
    
    # 12. Niveli 12
    course_12 = Course(
        name="Niveli 12",
        description="Ndërto fjali të thjeshta nga fjalët e dhëna",
        order_index=12,
        category=CategoryEnum.BUILD_SENTENCE,
        required_score=0,
        enabled=True,
        parent_class_id=first_class.id
    )
    courses.append(course_12)
    
    # Add all courses to database
    for course in courses:
        db.add(course)
    db.flush()
    
    # Create a level for each course (like in Class 2 and 3)
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime bazike për fillestarët",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()
    
    # Create exercises for each course
    exercises = []
    
    # 1. Niveli 1 - 5 exercises
    dictation_exercises = [
        ("Zogu", "zogu"),
        ("Topi", "topi"),
        ("Dritë", "dritë"),
        ("Këngë", "këngë"),
        ("Shkollë", "shkollë")
    ]
    
    for i, (prompt, answer) in enumerate(dictation_exercises):
        exercise = Exercise(
            category=CategoryEnum.LISTEN_WRITE,
                course_id=course_1.id,
            level_id=level_by_course[course_1.id].id,
            # Do not include the target word in the prompt; audio will carry the word
            prompt="Shkruaj fjalën që dëgjon.",
            data=json.dumps({"audio_word": prompt, "type": "dictation"}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 2. Niveli 2 - 5 exercises
    description_exercises = [
        ("Ata që kujdesen gjithmonë për ne.", "prindërit", ["prindërit", "e kuqe", "çadra", "karrige", "mësuesi"]),
        ("Personi që na mëson në shkollë.", "mësuesi", ["prindërit", "e kuqe", "çadra", "karrige", "mësuesi"]),
        ("Ngjyra e gjakut.", "e kuqe", ["prindërit", "e kuqe", "çadra", "karrige", "mësuesi"]),
        ("Na mbron nga shiu.", "çadra", ["prindërit", "e kuqe", "çadra", "karrige", "mësuesi"]),
        ("Ku ulemi kur jemi të lodhur.", "karrige", ["prindërit", "e kuqe", "çadra", "karrige", "mësuesi"])
    ]
    
    for i, (prompt, answer, choices) in enumerate(description_exercises):
        exercise = Exercise(
            category=CategoryEnum.WORD_FROM_DESCRIPTION,
            course_id=course_2.id,
            level_id=level_by_course[course_2.id].id,
            prompt=prompt,
            data=json.dumps({"choices": choices, "type": "multiple_choice"}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 3. Niveli 3 - 10 exercises
    synonym_antonym_exercises = [
        # Antonime
        ("i mirë → _______", "i keq", ["i keq", "i lumtur", "i bukur"], "antonym"),
        ("i gjatë → _______", "i shkurtër", ["i shkurtër", "i i ri", "i vjetër"], "antonym"),
        ("i lumtur → _______", "i trishtuar", ["i trishtuar", "i gëzuar", "i bukur"], "antonym"),
        ("i ftohtë → _______", "i nxehtë", ["i nxehtë", "i ngrohtë", "i butë"], "antonym"),
        ("i shpejtë → _______", "i ngadaltë", ["i ngadaltë", "i i ri", "i vjetër"], "antonym"),
        # Sinonime
        ("i lumtur → _______", "i gëzuar", ["i gëzuar", "i bukur", "i mirë"], "synonym"),
        ("i bukur → _______", "i hijshëm", ["i hijshëm", "i mirë", "i lumtur"], "synonym"),
        ("i mençur → _______", "i zgjuar", ["i zgjuar", "i mirë", "i lumtur"], "synonym"),
        ("i qetë → _______", "i heshtur", ["i heshtur", "i mirë", "i lumtur"], "synonym"),
        ("i guximshëm → _______", "trim", ["trim", "i mirë", "i lumtur"], "synonym")
    ]
    
    for i, (prompt, answer, choices, exercise_type) in enumerate(synonym_antonym_exercises):
        exercise = Exercise(
            category=CategoryEnum.SYNONYMS_ANTONYMS,
            course_id=course_3.id,
            level_id=level_by_course[course_3.id].id,
            prompt=prompt,
            data=json.dumps({"choices": choices, "type": exercise_type}),
                answer=answer,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 4. Niveli 4 - 10 exercises
    albanian_loanword_exercises = [
        ("shmang", "Shqip", ["Shqip", "Huazim"]),
        ("evitoj", "Huazim", ["Shqip", "Huazim"]),
        ("libër", "Shqip", ["Shqip", "Huazim"]),
        ("kompjuter", "Huazim", ["Shqip", "Huazim"]),
        ("telefon", "Huazim", ["Shqip", "Huazim"]),
        ("ushqim", "Shqip", ["Shqip", "Huazim"]),
        ("celular", "Huazim", ["Shqip", "Huazim"]),
        ("shtëpi", "Shqip", ["Shqip", "Huazim"]),
        ("lojë", "Shqip", ["Shqip", "Huazim"]),
        ("internet", "Huazim", ["Shqip", "Huazim"])
    ]
    
    for i, (word, answer, choices) in enumerate(albanian_loanword_exercises):
        exercise = Exercise(
            category=CategoryEnum.ALBANIAN_OR_LOANWORD,
            course_id=course_4.id,
            level_id=level_by_course[course_4.id].id,
            prompt=f"'{word}' është:",
            data=json.dumps({"choices": choices, "type": "albanian_loanword"}),
            answer=answer,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 5. Niveli 5 - 8 exercises
    missing_letter_exercises = [
        ("g_ysh", "gjysh"),
        ("fs_at", "fshat"),
        ("z_g", "zog"),
        ("l_ps", "laps"),
        ("b_ba", "baba"),
        ("_ënë", "nënë"),
        ("t_p", "top"),
        ("m_l", "mal")
    ]
    
    for i, (word_with_gap, answer) in enumerate(missing_letter_exercises):
        exercise = Exercise(
            category=CategoryEnum.MISSING_LETTER,
            course_id=course_5.id,
            level_id=level_by_course[course_5.id].id,
            prompt=f"Shkruaj fjalën: {word_with_gap}",
            data=json.dumps({"word_with_gap": word_with_gap, "type": "missing_letter"}),
            answer=answer,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 6. Niveli 6 - 10 exercises
    wrong_letter_exercises = [
        ("Shoku im është i mrië.", "mirë"),
        ("Babi bleu një makin.", "makinë"),
        ("Rina ka një lapsi.", "laps"),
        ("Qeni është kafshe.", "kafshë"),
        ("Lumi është i madsh.", "madh"),
        ("Ola ka një librr.", "libër"),
        ("Hëna ndriçon natn.", "natën"),
        ("Dielli ndriçon dotën.", "ditën"),
        ("Yjet janë në qaell.", "qiell"),
        ("Flutura fluturon lert.", "lart")
    ]
    
    for i, (sentence, correct_word) in enumerate(wrong_letter_exercises):
        exercise = Exercise(
            category=CategoryEnum.WRONG_LETTER,
            course_id=course_6.id,
            level_id=level_by_course[course_6.id].id,
            prompt=f"{sentence}\nFjala e saktë: __________",
            data=json.dumps({"sentence": sentence, "type": "wrong_letter"}),
            answer=correct_word,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 7. Niveli 7 - 10 exercises
    build_word_exercises = [
        ("ëmep", "pemë"),
        ("lleid", "diell"),
        ("lëmu", "lumë"),
        ("zgo", "zog"),
        ("klaë", "kalë"),
        ("Pot", "top"),
        ("sapl", "laps"),
        ("edër", "derë"),
        ("bbaa", "baba"),
        ("nëën", "nënë")
    ]
    
    for i, (scrambled_word, correct_word) in enumerate(build_word_exercises):
        exercise = Exercise(
            category=CategoryEnum.BUILD_WORD,
            course_id=course_7.id,
            level_id=level_by_course[course_7.id].id,
            prompt=f"{scrambled_word} → __________",
            data=json.dumps({"scrambled_word": scrambled_word, "type": "build_word"}),
            answer=correct_word,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 8. Niveli 8 - 11 exercises (0-10)
    number_to_word_exercises = [
        ("0", "zero"),
            ("1", "një"),
            ("2", "dy"),
            ("3", "tre"),
            ("4", "katër"),
            ("5", "pesë"),
            ("6", "gjashtë"),
            ("7", "shtatë"),
            ("8", "tetë"),
            ("9", "nëntë"),
        ("10", "dhjetë")
    ]
    
    for i, (number, word) in enumerate(number_to_word_exercises):
        exercise = Exercise(
            category=CategoryEnum.NUMBER_TO_WORD,
            course_id=course_8.id,
            level_id=level_by_course[course_8.id].id,
            prompt=f"{number} → _____",
            data=json.dumps({"number": number, "type": "number_to_word"}),
                answer=word,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 9. Niveli 9 - 4 exercises
    phrase_exercises = [
        ("Një njeri që jep mësim në një shkollë.", "Mësuesi"),
        ("Kafshë që jeton në ujë.", "Peshku"),
        ("Rritet në tokë, ka degë e gjethe.", "Pema"),
        ("Shkëlqen në qiell ditën.", "Dielli")
    ]
    
    for i, (description, word) in enumerate(phrase_exercises):
        exercise = Exercise(
            category=CategoryEnum.PHRASES,
            course_id=course_9.id,
            level_id=level_by_course[course_9.id].id,
            prompt=f"Përshkrimi: {description}\nFjala:",
            data=json.dumps({"description": description, "type": "phrase"}),
            answer=word,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 10. Niveli 10 - 5 exercises
    spelling_punctuation_exercises = [
        ("babi bleu një top të kuq", "Babi bleu një top të kuq."),
        ("shiu bie në kopsht", "Shiu bie në kopsht."),
        ("hëna ndriçon natën", "Hëna ndriçon natën."),
        ("unë dua të shkoj në shkollë", "Unë dua të shkoj në shkollë."),
        ("gjyshi lexon përralla", "Gjyshi lexon përralla.")
    ]
    
    for i, (incorrect, correct) in enumerate(spelling_punctuation_exercises):
        exercise = Exercise(
            category=CategoryEnum.SPELLING_PUNCTUATION,
            course_id=course_10.id,
            level_id=level_by_course[course_10.id].id,
            prompt=f"{incorrect}\nSaktë:",
            data=json.dumps({"incorrect": incorrect, "type": "spelling_punctuation"}),
            answer=correct,
                points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 11. Niveli 11 - 10 exercises
    abstract_concrete_exercises = [
        # Konkrete
        ("trishtim / libër / baba → libër (konkret)", "libër", ["trishtim", "libër", "baba"], "concrete"),
        ("gëzim / lumturi / kopsht → kopsht (konkret)", "kopsht", ["gëzim", "lumturi", "kopsht"], "concrete"),
        ("mendim / guxim / top → top (konkret)", "top", ["mendim", "guxim", "top"], "concrete"),
        ("dashuri / frikë / fletore → fletore (konkret)", "fletore", ["dashuri", "frikë", "fletore"], "concrete"),
        ("frikë / laps / dritare → laps (konkret)", "laps", ["frikë", "laps", "dritare"], "concrete"),
        # Abstrakte
        ("lumturi / top / laps → lumturi (abstrakte)", "lumturi", ["lumturi", "top", "laps"], "abstract"),
        ("trishtim / libër / karrige → trishtim (abstrakte)", "trishtim", ["trishtim", "libër", "karrige"], "abstract"),
        ("dashuri / shishe / derë → dashuri (abstrakte)", "dashuri", ["dashuri", "shishe", "derë"], "abstract"),
        ("frikë / libër / pemë → frikë (abstrakte)", "frikë", ["frikë", "libër", "pemë"], "abstract"),
        ("mendim / top / dritare → mendim (abstrakte)", "mendim", ["mendim", "top", "dritare"], "abstract")
    ]
    
    for i, (prompt, answer, choices, exercise_type) in enumerate(abstract_concrete_exercises):
        # Remove explicit correct-answer hint from prompt text
        clean_prompt = prompt.split("→")[0].strip()
        exercise = Exercise(
            category=CategoryEnum.ABSTRACT_CONCRETE,
            course_id=course_11.id,
            level_id=level_by_course[course_11.id].id,
            prompt=clean_prompt,
            data=json.dumps({"choices": choices, "type": exercise_type}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 12. Niveli 12 - 5 exercises
    build_sentence_exercises = [
        (["laps", "Rina", "një", "ka"], "Rina ka një laps."),
        (["kafshë", "Qeni", "është"], "Qeni është kafshë."),
        (["natën", "ndriçon", "Hëna"], "Hëna ndriçon natën."),
        (["top", "Macja", "me", "luan"], "Macja luan me top."),
        (["Gjyshi", "tregon", "përralla"], "Gjyshi tregon përralla.")
    ]
    
    for i, (words, correct_sentence) in enumerate(build_sentence_exercises):
        exercise = Exercise(
            category=CategoryEnum.BUILD_SENTENCE,
            course_id=course_12.id,
            level_id=level_by_course[course_12.id].id,
            prompt=f"Fjalë: {words}\nFjalia: ____________________________",
            data=json.dumps({"words": words, "type": "build_sentence"}),
            answer=correct_sentence,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # Add all exercises to the database
    for exercise in exercises:
        db.add(exercise)
    
    db.commit()
    print(f"Successfully seeded {len(courses)} courses and {len(exercises)} exercises for first class level")
    return first_class.id


@router.post("/seed-class-2")
def seed_class_2():
    """Seed Class 2 with advanced exercises following Class 1 structure"""
    db = next(get_db())
    
    try:
        # Clear existing data for Class 2
        class_ids_to_clear = db.query(Course.id).filter(
            Course.name.like("Klasa 2%")
        )
        db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
        db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
        db.query(Course).filter(Course.name.like("Klasa 2%")).delete()
        
        # Seed Class 2
        course_id = seed_second_class_exercises(db)
        
        return {
            "message": "Successfully seeded 12 courses for Class 2",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": 93
        }
        
    except Exception as e:
        db.rollback()
        raise e


def seed_second_class_exercises(db: Session):
    """Seed the second class level with exactly 12 courses and their advanced exercises"""
    
    # Create the second class course
    second_class = Course(
        name="Klasa 2",
        description="Klasa e dytë për moshën 7-8 vjeç me 12 kategorive të ushtrimeve të avancuara",
        order_index=2,
        category=CategoryEnum.VOCABULARY,
        required_score=80,  # Requires completion of Class 1
        enabled=True
    )
    db.add(second_class)
    db.flush()
    
    # Create 12 courses for Class 2 (same structure as Class 1)
    courses = []
    
    # 1. Niveli 1
    course_1 = Course(
        name="Niveli 1",
        description="Dëgjo dhe shkruaj fjalët e avancuara",
        order_index=1,
        category=CategoryEnum.LISTEN_WRITE,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_1)
    
    # 2. Niveli 2
    course_2 = Course(
        name="Niveli 2",
        description="Zgjedh fjalën e duhur nga lista bazuar në përshkrimin e avancuar",
        order_index=2,
        category=CategoryEnum.WORD_FROM_DESCRIPTION,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_2)
    
    # 3. Niveli 3
    course_3 = Course(
        name="Niveli 3",
        description="Mëso sinonimet dhe antonimet e fjalëve të avancuara",
        order_index=3,
        category=CategoryEnum.SYNONYMS_ANTONYMS,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_3)
    
    # 4. Niveli 4
    course_4 = Course(
        name="Niveli 4",
        description="Identifiko nëse fjala është shqipe apo huazim (avancuar)",
        order_index=4,
        category=CategoryEnum.ALBANIAN_OR_LOANWORD,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_4)
    
    # 5. Niveli 5
    course_5 = Course(
        name="Niveli 5",
        description="Plotëso shkronjën që mungon në fjalë të avancuara",
        order_index=5,
        category=CategoryEnum.MISSING_LETTER,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_5)
    
    # 6. Niveli 6
    course_6 = Course(
        name="Niveli 6",
        description="Gjej dhe ndreq shkronjën e gabuar në fjali të avancuara",
        order_index=6,
        category=CategoryEnum.WRONG_LETTER,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_6)
    
    # 7. Niveli 7
    course_7 = Course(
        name="Niveli 7",
        description="Ndërto fjalën e avancuar nga shkronja të përziera",
        order_index=7,
        category=CategoryEnum.BUILD_WORD,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_7)
    
    # 8. Niveli 8
    course_8 = Course(
        name="Niveli 8",
        description="Shkruaj numrin si fjalë (11-20)",
        order_index=8,
        category=CategoryEnum.NUMBER_TO_WORD,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_8)
    
    # 9. Niveli 9
    course_9 = Course(
        name="Niveli 9",
        description="Kuptimi i shprehjeve frazeologjike të avancuara",
        order_index=9,
        category=CategoryEnum.PHRASES,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_9)
    
    # 10. Niveli 10
    course_10 = Course(
        name="Niveli 10",
        description="Gjej gabimin dhe rishkruaj saktë (avancuar)",
        order_index=10,
        category=CategoryEnum.SPELLING_PUNCTUATION,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_10)
    
    # 11. Niveli 11
    course_11 = Course(
        name="Niveli 11",
        description="Zgjedh fjalën sipas kuptimit abstrakt ose konkret (avancuar)",
        order_index=11,
        category=CategoryEnum.ABSTRACT_CONCRETE,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_11)
    
    # 12. Niveli 12
    course_12 = Course(
        name="Niveli 12",
        description="Ndërto fjali të avancuara nga fjalët e dhëna",
        order_index=12,
        category=CategoryEnum.BUILD_SENTENCE,
        required_score=0,
        enabled=True,
        parent_class_id=second_class.id
    )
    courses.append(course_12)
    
    # Add all courses to database
    for course in courses:
        db.add(course)
    db.flush()
    
    # Create a level for each course (like in Class 3)
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime të avancuara për klasën e dytë",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()
    
    # Create exercises for each course (ADVANCED versions)
    exercises = []
    
    # 1. Niveli 1 - 5 exercises (Longer words with more complex sounds)
    dictation_exercises = [
        ("Lojtar", "lojtar"),
        ("Fëmijë", "fëmijë"),
        ("Shkollë", "shkollë"),
        ("Rrugë", "rrugë"),
        ("Përshëndetje", "përshëndetje")
    ]
    
    for i, (prompt, answer) in enumerate(dictation_exercises):
        exercise = Exercise(
            category=CategoryEnum.LISTEN_WRITE,
            course_id=course_1.id,
            level_id=level_by_course[course_1.id].id,
            prompt="Shkruaj fjalën që dëgjon.",
            data=json.dumps({"audio_word": prompt, "type": "dictation"}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 2. Niveli 2 - 5 exercises (More complex descriptions)
    description_exercises = [
        ("Personi që na mëson në shkollë dhe na ndihmon të mësojmë.", "mësuesi", ["mësuesi", "mjeku", "inxhinieri", "bibliotekari", "zyrtari"]),
        ("Vendi ku lexojmë libra dhe studiojmë.", "biblioteka", ["biblioteka", "shtëpia", "kopshti", "shkolla", "salla"]),
        ("Njëri që shëron njerëzit kur janë të sëmurë.", "mjeku", ["mjeku", "mësuesi", "inxhinieri", "zyrtari", "bibliotekari"]),
        ("Vendi ku rriten pemë dhe lulet.", "kopshti", ["kopshti", "biblioteka", "shtëpia", "shkolla", "rruga"]),
        ("Personi që projektë dhe ndërton ndërtesa.", "inxhinieri", ["inxhinieri", "mjeku", "mësuesi", "zyrtari", "bibliotekari"])
    ]
    
    for i, (prompt, answer, choices) in enumerate(description_exercises):
        exercise = Exercise(
            category=CategoryEnum.WORD_FROM_DESCRIPTION,
            course_id=course_2.id,
            level_id=level_by_course[course_2.id].id,
            prompt=prompt,
            data=json.dumps({"choices": choices, "type": "multiple_choice"}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 3. Niveli 3 - 10 exercises (More advanced synonyms/antonyms)
    synonym_antonym_exercises = [
        # Antonime
        ("i guximshëm → _______", "i frikësuar", ["i frikësuar", "i trim", "i zgjuar"], "antonym"),
        ("i pasur → _______", "i varfër", ["i varfër", "i lumtur", "i mirë"], "antonym"),
        ("i vjetër → _______", "i ri", ["i ri", "i vjetër", "i mirë"], "antonym"),
        ("i ngadaltë → _______", "i shpejtë", ["i shpejtë", "i ngadaltë", "i mirë"], "antonym"),
        ("i lumtur → _______", "i trishtuar", ["i trishtuar", "i gëzuar", "i mirë"], "antonym"),
        # Sinonime
        ("i zgjuar → _______", "i mençur", ["i mençur", "i mirë", "i lumtur"], "synonym"),
        ("i trim → _______", "i guximshëm", ["i guximshëm", "i mirë", "i lumtur"], "synonym"),
        ("i bukur → _______", "i hijshëm", ["i hijshëm", "i mirë", "i lumtur"], "synonym"),
        ("i gëzuar → _______", "i lumtur", ["i lumtur", "i mirë", "i bukur"], "synonym"),
        ("i qetë → _______", "i heshtur", ["i heshtur", "i mirë", "i lumtur"], "synonym")
    ]
    
    for i, (prompt, answer, choices, exercise_type) in enumerate(synonym_antonym_exercises):
        exercise = Exercise(
            category=CategoryEnum.SYNONYMS_ANTONYMS,
            course_id=course_3.id,
            level_id=level_by_course[course_3.id].id,
            prompt=prompt,
            data=json.dumps({"choices": choices, "type": exercise_type}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 4. Niveli 4 - 10 exercises (More loanwords)
    albanian_loanword_exercises = [
        ("printer", "Huazim", ["Shqip", "Huazim"]),
        ("skaner", "Huazim", ["Shqip", "Huazim"]),
        ("email", "Huazim", ["Shqip", "Huazim"]),
        ("familje", "Shqip", ["Shqip", "Huazim"]),
        ("mësuese", "Shqip", ["Shqip", "Huazim"]),
        ("tablet", "Huazim", ["Shqip", "Huazim"]),
        ("bibliotekë", "Shqip", ["Shqip", "Huazim"]),
        ("download", "Huazim", ["Shqip", "Huazim"]),
        ("shkollë", "Shqip", ["Shqip", "Huazim"]),
        ("software", "Huazim", ["Shqip", "Huazim"])
    ]
    
    for i, (word, answer, choices) in enumerate(albanian_loanword_exercises):
        exercise = Exercise(
            category=CategoryEnum.ALBANIAN_OR_LOANWORD,
            course_id=course_4.id,
            level_id=level_by_course[course_4.id].id,
            prompt=f"'{word}' është:",
            data=json.dumps({"choices": choices, "type": "albanian_loanword"}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 5. Niveli 5 - 8 exercises (More complex missing letters)
    missing_letter_exercises = [
        ("fëm_jë", "fëmijë"),
        ("shk_llë", "shkollë"),
        ("drit_re", "dritare"),
        ("libr_ri", "librari"),
        ("kafsh_re", "kafshë"),
        ("mësu_se", "mësuese"),
        ("famil_e", "familje"),
        ("rrug_", "rrugë")
    ]
    
    for i, (word_with_gap, answer) in enumerate(missing_letter_exercises):
        exercise = Exercise(
            category=CategoryEnum.MISSING_LETTER,
            course_id=course_5.id,
            level_id=level_by_course[course_5.id].id,
            prompt=f"Shkruaj fjalën: {word_with_gap}",
            data=json.dumps({"word_with_gap": word_with_gap, "type": "missing_letter"}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 6. Niveli 6 - 10 exercises (More complex sentences)
    wrong_letter_exercises = [
        ("Mësuesi na mëson në shkolle.", "shkollë"),
        ("Fëmijët luajnë në oborrin e shkollës.", "fëmijët"),
        ("Biblioteka është vendi ku lexojmë libra.", "biblioteka"),
        ("Rina shkruan me laps në fletore.", "fletore"),
        ("Dielli ndriçon ditën dhe na ngroh.", "ditën"),
        ("Familja ime është e madhe dhe e lumtur.", "familja"),
        ("Ne shkojmë në shkollë çdo ditë.", "shkojmë"),
        ("Mësuesja na tregon përralla të bukura.", "përralla"),
        ("Fëmijët lexojnë libra në bibliotekë.", "lexojnë"),
        ("Kopshti është plot me lule të bukura.", "kopshti")
    ]
    
    for i, (sentence, correct_word) in enumerate(wrong_letter_exercises):
        exercise = Exercise(
            category=CategoryEnum.WRONG_LETTER,
            course_id=course_6.id,
            level_id=level_by_course[course_6.id].id,
            prompt=f"{sentence}\nFjala e saktë: __________",
            data=json.dumps({"sentence": sentence, "type": "wrong_letter"}),
            answer=correct_word,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 7. Niveli 7 - 10 exercises (Longer scrambled words)
    build_word_exercises = [
        ("mijëfë", "fëmijë"),
        ("llëshko", "shkollë"),
        ("taredri", "dritare"),
        ("rralibi", "librari"),
        ("ëshkaf", "kafshë"),
        ("esuëm", "mësuese"),
        ("ejlifam", "familje"),
        ("gurë", "rrugë"),
        ("tëpërshëndetje", "përshëndetje"),
        ("tëjlo", "lojtar")
    ]
    
    for i, (scrambled_word, correct_word) in enumerate(build_word_exercises):
        exercise = Exercise(
            category=CategoryEnum.BUILD_WORD,
            course_id=course_7.id,
            level_id=level_by_course[course_7.id].id,
            prompt=f"{scrambled_word} → __________",
            data=json.dumps({"scrambled_word": scrambled_word, "type": "build_word"}),
            answer=correct_word,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 8. Niveli 8 - 10 exercises (11-20)
    number_to_word_exercises = [
        ("11", "njëmbëdhjetë"),
        ("12", "dymbëdhjetë"),
        ("13", "trembëdhjetë"),
        ("14", "katërmbëdhjetë"),
        ("15", "pesëmbëdhjetë"),
        ("16", "gjashtëmbëdhjetë"),
        ("17", "shtatëmbëdhjetë"),
        ("18", "tetëmbëdhjetë"),
        ("19", "nëntëmbëdhjetë"),
        ("20", "njëzet")
    ]
    
    for i, (number, word) in enumerate(number_to_word_exercises):
        exercise = Exercise(
            category=CategoryEnum.NUMBER_TO_WORD,
            course_id=course_8.id,
            level_id=level_by_course[course_8.id].id,
            prompt=f"{number} → _____",
            data=json.dumps({"number": number, "type": "number_to_word"}),
            answer=word,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 9. Niveli 9 - 5 exercises (More complex phrases)
    phrase_exercises = [
        ("Vendi ku lexojmë libra dhe studiojmë.", "Biblioteka"),
        ("Personi që shëron njerëzit kur janë të sëmurë.", "Mjeku"),
        ("Vendi ku rriten pemë dhe lulet.", "Kopshti"),
        ("Personi që projektë dhe ndërton ndërtesa.", "Inxhinieri"),
        ("Njëri që punon në zyrë dhe zgjidh dokumente.", "Zyrtari")
    ]
    
    for i, (description, word) in enumerate(phrase_exercises):
        exercise = Exercise(
            category=CategoryEnum.PHRASES,
            course_id=course_9.id,
            level_id=level_by_course[course_9.id].id,
            prompt=f"Përshkrimi: {description}\nFjala:",
            data=json.dumps({"description": description, "type": "phrase"}),
            answer=word,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 10. Niveli 10 - 5 exercises (More complex sentences)
    spelling_punctuation_exercises = [
        ("mësuesi na mëson në shkollë çdo ditë", "Mësuesi na mëson në shkollë çdo ditë."),
        ("fëmijët luajnë në oborrin e shkollës", "Fëmijët luajnë në oborrin e shkollës."),
        ("biblioteka është vendi ku lexojmë libra", "Biblioteka është vendi ku lexojmë libra."),
        ("familja ime është e madhe dhe e lumtur", "Familja ime është e madhe dhe e lumtur."),
        ("ne shkojmë në shkollë me shokët tanë", "Ne shkojmë në shkollë me shokët tanë.")
    ]
    
    for i, (incorrect, correct) in enumerate(spelling_punctuation_exercises):
        exercise = Exercise(
            category=CategoryEnum.SPELLING_PUNCTUATION,
            course_id=course_10.id,
            level_id=level_by_course[course_10.id].id,
            prompt=f"{incorrect}\nSaktë:",
            data=json.dumps({"incorrect": incorrect, "type": "spelling_punctuation"}),
            answer=correct,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 11. Niveli 11 - 10 exercises (More abstract concepts)
    abstract_concrete_exercises = [
        # Konkrete
        ("mendim / libër / bibliotekë → bibliotekë (konkret)", "bibliotekë", ["mendim", "libër", "bibliotekë"], "concrete"),
        ("gëzim / lumturi / kopsht → kopsht (konkret)", "kopsht", ["gëzim", "lumturi", "kopsht"], "concrete"),
        ("mendim / guxim / shkollë → shkollë (konkret)", "shkollë", ["mendim", "guxim", "shkollë"], "concrete"),
        ("dashuri / frikë / fletore → fletore (konkret)", "fletore", ["dashuri", "frikë", "fletore"], "concrete"),
        ("frikë / laps / dritare → dritare (konkret)", "dritare", ["frikë", "laps", "dritare"], "concrete"),
        # Abstrakte
        ("lumturi / shkollë / laps → lumturi (abstrakte)", "lumturi", ["lumturi", "shkollë", "laps"], "abstract"),
        ("trishtim / libër / karrige → trishtim (abstrakte)", "trishtim", ["trishtim", "libër", "karrige"], "abstract"),
        ("dashuri / shishe / derë → dashuri (abstrakte)", "dashuri", ["dashuri", "shishe", "derë"], "abstract"),
        ("frikë / libër / pemë → frikë (abstrakte)", "frikë", ["frikë", "libër", "pemë"], "abstract"),
        ("mendim / shkollë / dritare → mendim (abstrakte)", "mendim", ["mendim", "shkollë", "dritare"], "abstract")
    ]
    
    for i, (prompt, answer, choices, exercise_type) in enumerate(abstract_concrete_exercises):
        clean_prompt = prompt.split("→")[0].strip()
        exercise = Exercise(
            category=CategoryEnum.ABSTRACT_CONCRETE,
            course_id=course_11.id,
            level_id=level_by_course[course_11.id].id,
            prompt=clean_prompt,
            data=json.dumps({"choices": choices, "type": exercise_type}),
            answer=answer,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # 12. Niveli 12 - 5 exercises (Longer sentences)
    build_sentence_exercises = [
        (["mësuesi", "na", "mëson", "në", "shkollë"], "Mësuesi na mëson në shkollë."),
        (["fëmijët", "luajnë", "në", "oborrin", "e", "shkollës"], "Fëmijët luajnë në oborrin e shkollës."),
        (["biblioteka", "është", "vendi", "ku", "lexojmë", "libra"], "Biblioteka është vendi ku lexojmë libra."),
        (["familja", "ime", "është", "e", "madhe"], "Familja ime është e madhe."),
        (["ne", "shkojmë", "në", "shkollë", "me", "shokët", "tanë"], "Ne shkojmë në shkollë me shokët tanë.")
    ]
    
    for i, (words, correct_sentence) in enumerate(build_sentence_exercises):
        exercise = Exercise(
            category=CategoryEnum.BUILD_SENTENCE,
            course_id=course_12.id,
            level_id=level_by_course[course_12.id].id,
            prompt=f"Fjalë: {words}\nFjalia: ____________________________",
            data=json.dumps({"words": words, "type": "build_sentence"}),
            answer=correct_sentence,
            points=1,
            order_index=i + 1
        )
        exercises.append(exercise)
    
    # Add all exercises to the database
    for exercise in exercises:
        db.add(exercise)
    
    db.commit()
    print(f"Successfully seeded {len(courses)} courses and {len(exercises)} exercises for second class level")
    return second_class.id


def seed_third_class_exercises(db: Session):
    """Seed the third class with the same 12-category structure, advanced content"""

    # Clear existing data for Class 3
    class_ids_to_clear = db.query(Course.id).filter(Course.name.like("Klasa 3%"))
    db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
    db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
    db.query(Course).filter(Course.name.like("Klasa 3%")).delete()

    # Create Class 3
    third_class = Course(
        name="Klasa 3",
        description="Klasa e tretë (8-9 vjeç) me 12 kategori ushtrimesh më të avancuara",
        order_index=3,
        category=CategoryEnum.VOCABULARY,
        required_score=80,
        enabled=True,
    )
    db.add(third_class)
    db.flush()

    # Create levels 1..12
    level_1 = Level(
        course_id=third_class.id,
        name="Niveli 1",
        description="Ushtrime të avancuara për klasën e tretë",
        order_index=1,
        required_score=0,
        enabled=True,
    )
    db.add(level_1)
    db.flush()

    extra_levels = []
    for idx in range(2, 13):
        extra_levels.append(
            Level(
                course_id=third_class.id,
                name=f"Niveli {idx}",
                description=f"Niveli {idx} për Klasa 3",
                order_index=idx,
                required_score=80 if idx > 1 else 0,
                enabled=True,
            )
        )
    for lvl in extra_levels:
        db.add(lvl)
    db.flush()

    # Create 12 courses (categories) under Class 3
    courses = []
    course_defs = [
        ("Niveli 1", CategoryEnum.LISTEN_WRITE),
        ("Niveli 2", CategoryEnum.WORD_FROM_DESCRIPTION),
        ("Niveli 3", CategoryEnum.SYNONYMS_ANTONYMS),
        ("Niveli 4", CategoryEnum.ALBANIAN_OR_LOANWORD),
        ("Niveli 5", CategoryEnum.MISSING_LETTER),
        ("Niveli 6", CategoryEnum.WRONG_LETTER),
        ("Niveli 7", CategoryEnum.BUILD_WORD),
        ("Niveli 8", CategoryEnum.NUMBER_TO_WORD),
        ("Niveli 9", CategoryEnum.PHRASES),
        ("Niveli 10", CategoryEnum.SPELLING_PUNCTUATION),
        ("Niveli 11", CategoryEnum.ABSTRACT_CONCRETE),
        ("Niveli 12", CategoryEnum.BUILD_SENTENCE),
    ]
    for idx, (name, cat) in enumerate(course_defs, start=1):
        c = Course(
            name=name,
            description=name,
            order_index=idx,
            category=cat,
            required_score=0,
            enabled=True,
            parent_class_id=third_class.id,
        )
        db.add(c)
        courses.append(c)
    db.flush()

    # Map level 1 to all courses (si në Klasa 1/2)
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime të avancuara",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()

    # Short helper
    def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
        ex = Exercise(
            category=cat,
            course_id=course.id,
            level_id=level.id,
            prompt=prompt,
            data=json.dumps(data_obj),
            answer=answer,
            points=1,
            order_index=idx,
        )
        db.add(ex)

    # Unpack courses and levels
    (
        c1,
        c2,
        c3,
        c4,
        c5,
        c6,
        c7,
        c8,
        c9,
        c10,
        c11,
        c12,
    ) = courses
    l1 = level_by_course[c1.id]
    l2 = level_by_course[c2.id]
    l3 = level_by_course[c3.id]
    l4 = level_by_course[c4.id]
    l5 = level_by_course[c5.id]
    l6 = level_by_course[c6.id]
    l7 = level_by_course[c7.id]
    l8 = level_by_course[c8.id]
    l9 = level_by_course[c9.id]
    l10 = level_by_course[c10.id]
    l11 = level_by_course[c11.id]
    l12 = level_by_course[c12.id]

    # 1) LISTEN_WRITE (shprehje 2-3 fjalëshe)
    dictation_exercises = [
        ("shtëpi e madhe", "shtëpi e madhe"),
        ("ditë me diell", "ditë me diell"),
        ("libër i ri", "libër i ri"),
        ("oborr i shkollës", "oborr i shkollës"),
        ("përshëndetje e ngrohtë", "përshëndetje e ngrohtë"),
    ]
    for i, (p, a) in enumerate(dictation_exercises, start=1):
        add_exercise(
            CategoryEnum.LISTEN_WRITE,
            c1,
            l1,
            "Shkruaj fjalinë që dëgjon.",
            {"audio_word": p, "type": "dictation"},
            a,
            i,
        )

    # 2) WORD_FROM_DESCRIPTION (më abstrakte)
    desc_exercises = [
        (
            "Ndjenjë kur dikush të ndihmon dhe të kupton.",
            "miqësi",
            ["miqësi", "frikë", "gëzim", "familje", "libër"],
        ),
        (
            "Detyrimi për të bërë diçka siç duhet.",
            "përgjegjësi",
            ["përgjegjësi", "lojë", "pushim", "gëzim", "frikë"],
        ),
        (
            "Rregullat që mbajnë qetësinë dhe radhën.",
            "rregulli",
            ["rregulli", "loja", "koha", "shkolla", "fjeta"],
        ),
        (
            "Ndihmë që i jepet dikujt që ka nevojë.",
            "ndihmë",
            ["ndihmë", "shije", "hobby", "pikturë", "muzikë"],
        ),
        (
            "Ndjenjë e mirë kur arrin një sukses.",
            "krenari",
            ["krenari", "frikë", "mërzi", "gjumë", "faj"],
        ),
    ]
    for i, (p, a, choices) in enumerate(desc_exercises, start=1):
        add_exercise(
            CategoryEnum.WORD_FROM_DESCRIPTION,
            c2,
            l2,
            p,
            {"choices": choices, "type": "multiple_choice"},
            a,
            i,
        )

    # 3) SYNONYMS_ANTONYMS (nuanca më të pasura)
    syn_ant_exercises = [
        # Antonime
        ("i drejtë → _______", "i padrejtë", ["i padrejtë", "i qetë", "i mirë"], "antonym"),
        ("i sinqertë → _______", "hipokrit", ["hipokrit", "i qeshur", "i ngadaltë"], "antonym"),
        ("i rëndësishëm → _______", "i parëndësishëm", ["i parëndësishëm", "i vjetër", "i ri"], "antonym"),
        ("i hareshëm → _______", "i dëshpëruar", ["i dëshpëruar", "i lumtur", "i vjetër"], "antonym"),
        ("i drejtë → _______", "i gabuar", ["i gabuar", "i qetë", "i bukur"], "antonym"),
        # Sinonime
        ("i zgjuar → _______", "i aftë", ["i aftë", "i gjatë", "i ndrojtur"], "synonym"),
        ("i guximshëm → _______", "trim", ["trim", "i butë", "i qetë"], "synonym"),
        ("i qetë → _______", "i paqtë", ["i paqtë", "i nxituar", "i ngadaltë"], "synonym"),
        ("i gëzuar → _______", "i lumtur", ["i lumtur", "i trishtuar", "i qetë"], "synonym"),
        ("i sjellshëm → _______", "i edukuar", ["i edukuar", "i zhurmshëm", "i pagdhendur"], "synonym"),
    ]
    for i, (p, a, choices, t) in enumerate(syn_ant_exercises, start=1):
        add_exercise(
            CategoryEnum.SYNONYMS_ANTONYMS,
            c3,
            l3,
            p,
            {"choices": choices, "type": t},
            a,
            i,
        )

    # 4) ALBANIAN_OR_LOANWORD (më shumë teknologji/terminologji)
    albanian_loanword_exercises = [
        ("laptop", "Huazim", ["Shqip", "Huazim"]),
        ("aplikacion", "Huazim", ["Shqip", "Huazim"]),
        ("kanal", "Huazim", ["Shqip", "Huazim"]),
        ("album", "Huazim", ["Shqip", "Huazim"]),
        ("serial", "Huazim", ["Shqip", "Huazim"]),
        ("kujtesë", "Shqip", ["Shqip", "Huazim"]),
        ("muzikë", "Shqip", ["Shqip", "Huazim"]),
        ("dritare", "Shqip", ["Shqip", "Huazim"]),
        ("arkitekturë", "Huazim", ["Shqip", "Huazim"]),
        ("stadium", "Huazim", ["Shqip", "Huazim"]),
    ]
    for i, (w, a, choices) in enumerate(albanian_loanword_exercises, start=1):
        add_exercise(
            CategoryEnum.ALBANIAN_OR_LOANWORD,
            c4,
            l4,
            f"'{w}' është:",
            {"choices": choices, "type": "albanian_loanword"},
            a,
            i,
        )

    # 5) MISSING_LETTER (fjalë më të gjata)
    missing_letter_exercises = [
        ("shq_ptar", "shqiptar"),
        ("dem_kraci", "demokraci"),
        ("shkr_mtar", "shkrimtar"),
        ("përgj_gje", "përgjigje"),
        ("eksper_ment", "eksperiment"),
        ("gje_graphi", "gjeografi"),
        ("hist_ri", "histori"),
        ("gram_tikë", "gramatikë"),
    ]
    for i, (w, a) in enumerate(missing_letter_exercises, start=1):
        add_exercise(
            CategoryEnum.MISSING_LETTER,
            c5,
            l5,
            f"Shkruaj fjalën: {w}",
            {"word_with_gap": w, "type": "missing_letter"},
            a,
            i,
        )

    # 6) WRONG_LETTER (fjali më të gjata)
    wrong_letter_exercises = [
        ("Nxënësit lexojn libra në bibliotekë çdo ditë.", "lexojnë"),
        ("Miqësia është e rëndësishme për të gjithë neve.", "rëndësishme"),
        ("Ne duhet të tregojm respekt ndaj të tjerëve.", "tregojmë"),
        ("Klasa jonë përgatit një projekt për natyrën.", "përgatit"),
        ("Mësuesja shpjegon me kujdes mësimin e sotëm.", "shpjegon"),
        ("Eksperimenti kërkon vëmendje dhe kujdes.", "vëmendje"),
        ("Shkencëtarët studiojn yjet dhe planetet.", "studiojnë"),
        ("Biblioteka ka shumë libra shkencor.", "shkencorë"),
        ("Grupi ynë punon së bashku për projektin.", "bashku"),
        ("Në muze pamë artefakte historike.", "artefakte"),
    ]
    for i, (s, a) in enumerate(wrong_letter_exercises, start=1):
        add_exercise(
            CategoryEnum.WRONG_LETTER,
            c6,
            l6,
            f"{s}\nFjala e saktë: __________",
            {"sentence": s, "type": "wrong_letter"},
            a,
            i,
        )

    # 7) BUILD_WORD (scrambled words më të gjata)
    build_word_exercises = [
        ("imtshqar", "shqiptar"),
        ("cimokread", "demokraci"),
        ("tmrahskr", "shkrimtar"),
        ("gjëpërgij", "përgjigje"),
        ("menteksper", "eksperiment"),
        ("gofreagji", "gjeografi"),
        ("ristohi", "histori"),
        ("kimratgë", "gramatikë"),
        ("ejskëm", "mësejk?"),  # skip problematic; replace
        ("nrepsh", "shpresë"),
    ]
    # Fix the problematic one: remove "ejskëm", keep 9 items
    build_word_exercises = [
        ("imtshqar", "shqiptar"),
        ("cimokread", "demokraci"),
        ("tmrahskr", "shkrimtar"),
        ("gjëpërgij", "përgjigje"),
        ("menteksper", "eksperiment"),
        ("gofreagji", "gjeografi"),
        ("ristohi", "histori"),
        ("kimratgë", "gramatikë"),
        ("rgoalem", "moralge?"),  # replace again
        ("nrepsh", "shpresë"),
    ]
    # Correct the two placeholders:
    build_word_exercises[-2] = ("rgoalem", "gromale?")  # still odd; use another word
    build_word_exercises[-2] = ("tiferks", "fistik")  # coherent word

    for i, (w, a) in enumerate(build_word_exercises, start=1):
        add_exercise(
            CategoryEnum.BUILD_WORD,
            c7,
            l7,
            f"{w} → __________",
            {"scrambled_word": w, "type": "build_word"},
            a,
            i,
        )

    # 8) NUMBER_TO_WORD (21-30)
    number_to_word_exercises = [
        ("21", "njëzet e një"),
        ("22", "njëzet e dy"),
        ("23", "njëzet e tre"),
        ("24", "njëzet e katër"),
        ("25", "njëzet e pesë"),
        ("26", "njëzet e gjashtë"),
        ("27", "njëzet e shtatë"),
        ("28", "njëzet e tetë"),
        ("29", "njëzet e nëntë"),
        ("30", "tridhjetë"),
    ]
    for i, (n, w) in enumerate(number_to_word_exercises, start=1):
        add_exercise(
            CategoryEnum.NUMBER_TO_WORD,
            c8,
            l8,
            f"{n} → _____",
            {"number": n, "type": "number_to_word"},
            w,
            i,
        )

    # 9) PHRASES (përshkrime më të gjata)
    phrase_exercises = [
        ("Vend ku mblidhen nxënësit për veprimtari shkollore.", "salla e madhe"),
        ("Ambient ku bëhen eksperimente shkencore.", "laboratori"),
        ("Vendi ku ruhen libra të shumtë.", "biblioteka"),
        ("Ambient për sport dhe aktivitete fizike.", "palestra"),
        ("Njerëz që punojnë së bashku në një projekt.", "ekipi"),
    ]
    for i, (d, w) in enumerate(phrase_exercises, start=1):
        add_exercise(
            CategoryEnum.PHRASES,
            c9,
            l9,
            f"Përshkrimi: {d}\nFjala:",
            {"description": d, "type": "phrase"},
            w,
            i,
        )

    # 10) SPELLING_PUNCTUATION (tekste më të gjata)
    spelling_punctuation_exercises = [
        ("nxënësit lexojnë libra në bibliotekë çdo ditë", "Nxënësit lexojnë libra në bibliotekë çdo ditë."),
        ("miqësia dhe respekti na ndihmojnë të punojmë së bashku", "Miqësia dhe respekti na ndihmojnë të punojmë së bashku."),
        ("projekti ynë për natyrën kërkon vëmendje dhe përkushtim", "Projekti ynë për natyrën kërkon vëmendje dhe përkushtim."),
        ("mësuesja shpjegon me kujdes mësimin e sotëm në klasë", "Mësuesja shpjegon me kujdes mësimin e sotëm në klasë."),
        ("grupi ynë përgatit një prezantim për historinë e qytetit", "Grupi ynë përgatit një prezantim për historinë e qytetit."),
    ]
    for i, (inc, corr) in enumerate(spelling_punctuation_exercises, start=1):
        add_exercise(
            CategoryEnum.SPELLING_PUNCTUATION,
            c10,
            l10,
            f"{inc}\nSaktë:",
            {"incorrect": inc, "type": "spelling_punctuation"},
            corr,
            i,
        )

    # 11) ABSTRACT_CONCRETE (më shumë abstrakte)
    abstract_concrete_exercises = [
        ("drejtësi / librari / fletore → drejtësi (abstrakte)", "drejtësi", ["drejtësi", "librari", "fletore"], "abstract"),
        ("barazi / laps / tryezë → barazi (abstrakte)", "barazi", ["barazi", "laps", "tryezë"], "abstract"),
        ("solidaritet / dritare / qytet → solidaritet (abstrakte)", "solidaritet", ["solidaritet", "dritare", "qytet"], "abstract"),
        ("liri / shkollë / kopsht → liri (abstrakte)", "liri", ["liri", "shkollë", "kopsht"], "abstract"),
        ("motivim / libër / tavolinë → motivim (abstrakte)", "motivim", ["motivim", "libër", "tavolinë"], "abstract"),
        ("bibliotekë / drejtësi / libër → bibliotekë (konkret)", "bibliotekë", ["drejtësi", "bibliotekë", "libër"], "concrete"),
        ("laborator / solidaritet / mikroskop → laborator (konkret)", "laborator", ["solidaritet", "laborator", "mikroskop"], "concrete"),
        ("fletore / barazi / laps → fletore (konkret)", "fletore", ["barazi", "fletore", "laps"], "concrete"),
        ("palestra / motivim / top → palestra (konkret)", "palestra", ["motivim", "palestra", "top"], "concrete"),
        ("qytet / liri / rrugë → qytet (konkret)", "qytet", ["liri", "qytet", "rrugë"], "concrete"),
    ]
    for i, (p, a, choices, t) in enumerate(abstract_concrete_exercises, start=1):
        clean_prompt = p.split("→")[0].strip()
        add_exercise(
            CategoryEnum.ABSTRACT_CONCRETE,
            c11,
            l11,
            clean_prompt,
            {"choices": choices, "type": t},
            a,
            i,
        )

    # 12) BUILD_SENTENCE (fjali më të gjata me lidhëza)
    build_sentence_exercises = [
        (["Nxënësit", "lexojnë", "libra", "në", "bibliotekë", "sepse", "duan", "të", "mësojnë"], "Nxënësit lexojnë libra në bibliotekë sepse duan të mësojnë."),
        (["Mësuesi", "na", "ndihmon", "të", "kuptojmë", "mësimin", "dhe", "të", "punojmë", "bashkë"], "Mësuesi na ndihmon të kuptojmë mësimin dhe të punojmë bashkë."),
        (["Grupi", "ynë", "përgatit", "një", "projekt", "për", "natyrën", "dhe", "mjedisin"], "Grupi ynë përgatit një projekt për natyrën dhe mjedisin."),
        (["Ne", "shkojmë", "në", "palestrë", "për", "të", "ushtruar", "dhe", "të", "qëndruar", "të", "shëndetshëm"], "Ne shkojmë në palestër për të ushtruar dhe të qëndruar të shëndetshëm."),
        (["Për", "historinë", "e", "qytetit", "mësuam", "shumë", "në", "muze", "dhe", "në", "bibliotekë"], "Për historinë e qytetit mësuam shumë në muze dhe në bibliotekë."),
    ]
    for i, (words, sentence) in enumerate(build_sentence_exercises, start=1):
        add_exercise(
            CategoryEnum.BUILD_SENTENCE,
            c12,
            l12,
            f"Fjalë: {words}\nFjalia: ____________________________",
            {"words": words, "type": "build_sentence"},
            sentence,
            i,
        )

    db.commit()
    # Count exercises created
    exercise_count = db.query(Exercise).filter(Exercise.course_id.in_([c.id for c in courses])).count()
    print(f"Successfully seeded {len(courses)} courses and {exercise_count} exercises for third class level")
    return third_class.id


def seed_fourth_class_exercises(db: Session):
    """Seed the fourth class with the same 12-category structure, even more advanced content"""

    # Clear existing data for Class 4
    class_ids_to_clear = db.query(Course.id).filter(Course.name.like("Klasa 4%"))
    db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
    db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
    db.query(Course).filter(Course.name.like("Klasa 4%")).delete()

    # Create Class 4
    fourth_class = Course(
        name="Klasa 4",
        description="Klasa e katërt (9-10 vjeç) me 12 kategori ushtrimesh edhe më të avancuara",
        order_index=4,
        category=CategoryEnum.VOCABULARY,
        required_score=80,
        enabled=True,
    )
    db.add(fourth_class)
    db.flush()

    # Create levels 1..12
    level_1 = Level(
        course_id=fourth_class.id,
        name="Niveli 1",
        description="Ushtrime të avancuara për klasën e katërt",
        order_index=1,
        required_score=0,
        enabled=True,
    )
    db.add(level_1)
    db.flush()

    extra_levels = []
    for idx in range(2, 13):
        extra_levels.append(
            Level(
                course_id=fourth_class.id,
                name=f"Niveli {idx}",
                description=f"Niveli {idx} për Klasa 4",
                order_index=idx,
                required_score=80 if idx > 1 else 0,
                enabled=True,
            )
        )
    for lvl in extra_levels:
        db.add(lvl)
    db.flush()

    # Create 12 courses (categories) under Class 4
    courses = []
    course_defs = [
        ("Niveli 1", CategoryEnum.LISTEN_WRITE),
        ("Niveli 2", CategoryEnum.WORD_FROM_DESCRIPTION),
        ("Niveli 3", CategoryEnum.SYNONYMS_ANTONYMS),
        ("Niveli 4", CategoryEnum.ALBANIAN_OR_LOANWORD),
        ("Niveli 5", CategoryEnum.MISSING_LETTER),
        ("Niveli 6", CategoryEnum.WRONG_LETTER),
        ("Niveli 7", CategoryEnum.BUILD_WORD),
        ("Niveli 8", CategoryEnum.NUMBER_TO_WORD),
        ("Niveli 9", CategoryEnum.PHRASES),
        ("Niveli 10", CategoryEnum.SPELLING_PUNCTUATION),
        ("Niveli 11", CategoryEnum.ABSTRACT_CONCRETE),
        ("Niveli 12", CategoryEnum.BUILD_SENTENCE),
    ]
    for idx, (name, cat) in enumerate(course_defs, start=1):
        c = Course(
            name=name,
            description=name,
            order_index=idx,
            category=cat,
            required_score=0,
            enabled=True,
            parent_class_id=fourth_class.id,
        )
        db.add(c)
        courses.append(c)
    db.flush()

    # Map level 1 to all courses
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime të avancuara",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()

    def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
        ex = Exercise(
            category=cat,
            course_id=course.id,
            level_id=level.id,
            prompt=prompt,
            data=json.dumps(data_obj),
            answer=answer,
            points=1,
            order_index=idx,
        )
        db.add(ex)

    (
        c1,
        c2,
        c3,
        c4,
        c5,
        c6,
        c7,
        c8,
        c9,
        c10,
        c11,
        c12,
    ) = courses
    l1 = level_by_course[c1.id]
    l2 = level_by_course[c2.id]
    l3 = level_by_course[c3.id]
    l4 = level_by_course[c4.id]
    l5 = level_by_course[c5.id]
    l6 = level_by_course[c6.id]
    l7 = level_by_course[c7.id]
    l8 = level_by_course[c8.id]
    l9 = level_by_course[c9.id]
    l10 = level_by_course[c10.id]
    l11 = level_by_course[c11.id]
    l12 = level_by_course[c12.id]

    # 1) LISTEN_WRITE – fjali të plota (diktim)
    dictation_exercises = [
        (
            "Sot ne shkojmë në bibliotekën e qytetit për të lexuar libra.",
            "Sot ne shkojmë në bibliotekën e qytetit për të lexuar libra.",
        ),
        (
            "Familja jonë udhëton shpesh për të vizituar vende të reja.",
            "Familja jonë udhëton shpesh për të vizituar vende të reja.",
        ),
        (
            "Mësuesja na shpjegon me kujdes mësimin e ri të historisë.",
            "Mësuesja na shpjegon me kujdes mësimin e ri të historisë.",
        ),
        (
            "Në laborator bëjmë eksperimente interesante për shkencën.",
            "Në laborator bëjmë eksperimente interesante për shkencën.",
        ),
        (
            "Ne duhet të respektojmë rregullat e klasës dhe të shkollës.",
            "Ne duhet të respektojmë rregullat e klasës dhe të shkollës.",
        ),
    ]
    for i, (p, a) in enumerate(dictation_exercises, start=1):
        add_exercise(
            CategoryEnum.LISTEN_WRITE,
            c1,
            l1,
            "Shkruaj fjalinë që dëgjon.",
            {"audio_word": p, "type": "dictation"},
            a,
            i,
        )

    # 2) WORD_FROM_DESCRIPTION – përshkrime më të gjata
    desc_exercises = [
        (
            "Shkrim i shkurtër ku tregon një ngjarje që të ka ndodhur.",
            "përshkrim",
            ["përshkrim", "projekt", "eksperiment", "udhëtim", "fjalor"],
        ),
        (
            "Vështrim i shkurtër i një libri përpara se ta lexosh.",
            "përmbledhje",
            ["përmbledhje", "kapitull", "libër", "autor", "faqe"],
        ),
        (
            "Dokument ku shkruhen rregullat kryesore të një klase.",
            "rregullore",
            ["rregullore", "ditar", "fletore", "raport", "projekt"],
        ),
        (
            "Vizatim ose figurë që tregon diçka me pamje, jo vetëm me fjalë.",
            "ilustrim",
            ["ilustrim", "paragraf", "fjalor", "projekt", "ese"],
        ),
        (
            "Punë e gjatë me shkrim ku shpjegon një temë të caktuar.",
            "ese",
            ["ese", "përshkrim", "dokument", "pyetje", "dialog"],
        ),
    ]
    for i, (p, a, choices) in enumerate(desc_exercises, start=1):
        add_exercise(
            CategoryEnum.WORD_FROM_DESCRIPTION,
            c2,
            l2,
            p,
            {"choices": choices, "type": "multiple_choice"},
            a,
            i,
        )

    # 3) SYNONYMS_ANTONYMS – fjalë më abstrakte
    syn_ant_exercises = [
        ("i përgjegjshëm → _______", "i pakujdesshëm", ["i pakujdesshëm", "i qetë", "i qeshur"], "antonym"),
        ("i drejtë → _______", "i padrejtë", ["i padrejtë", "i sjellshëm", "i sinqertë"], "antonym"),
        ("i qetë → _______", "i trazuar", ["i trazuar", "i qetë", "i ngadalshëm"], "antonym"),
        ("i sinqertë → _______", "i gënjeshtërt", ["i gënjeshtërt", "i guximshëm", "i qeshur"], "antonym"),
        ("i duruar → _______", "i paduruar", ["i paduruar", "i zgjuar", "i bukur"], "antonym"),
        ("i rëndësishëm → _______", "thelbësor", ["thelbësor", "i dobët", "i zhurmshëm"], "synonym"),
        ("i sinqertë → _______", "i ndershëm", ["i ndershëm", "i trishtuar", "i lodhur"], "synonym"),
        ("i sjellshëm → _______", "i edukuar", ["i edukuar", "i varfër", "i mërzitur"], "synonym"),
        ("i vendosur → _______", "i qëndrueshëm", ["i qëndrueshëm", "i dobët", "i trishtuar"], "synonym"),
        ("i gëzuar → _______", "i lumtur", ["i lumtur", "i nxehtë", "i fortë"], "synonym"),
    ]
    for i, (p, a, choices, t) in enumerate(syn_ant_exercises, start=1):
        add_exercise(
            CategoryEnum.SYNONYMS_ANTONYMS,
            c3,
            l3,
            p,
            {"choices": choices, "type": t},
            a,
            i,
        )

    # 4) ALBANIAN_OR_LOANWORD – teknologji & media
    albanian_loanword_exercises = [
        ("televizor", "Huazim", ["Shqip", "Huazim"]),
        ("mikrofon", "Huazim", ["Shqip", "Huazim"]),
        ("gazetar", "Huazim", ["Shqip", "Huazim"]),
        ("lajm", "Shqip", ["Shqip", "Huazim"]),
        ("kamerë", "Huazim", ["Shqip", "Huazim"]),
        ("shkrimtar", "Shqip", ["Shqip", "Huazim"]),
        ("revistë", "Huazim", ["Shqip", "Huazim"]),
        ("fletore", "Shqip", ["Shqip", "Huazim"]),
        ("internet", "Huazim", ["Shqip", "Huazim"]),
        ("faqe", "Shqip", ["Shqip", "Huazim"]),
    ]
    for i, (w, a, choices) in enumerate(albanian_loanword_exercises, start=1):
        add_exercise(
            CategoryEnum.ALBANIAN_OR_LOANWORD,
            c4,
            l4,
            f"'{w}' është:",
            {"choices": choices, "type": "albanian_loanword"},
            a,
            i,
        )

    # 5) MISSING_LETTER – fjalë nga lëndët
    missing_letter_exercises = [
        ("gje_grafi", "gjeografi"),
        ("hist_ri", "histori"),
        ("eksper_ment", "eksperiment"),
        ("mate_matike", "matematike"),
        ("shkenc_tar", "shkencëtar"),
        ("pro_ekt", "projekt"),
        ("dem_kraci", "demokraci"),
        ("libra_ri", "librari"),
    ]
    for i, (w, a) in enumerate(missing_letter_exercises, start=1):
        add_exercise(
            CategoryEnum.MISSING_LETTER,
            c5,
            l5,
            f"Shkruaj fjalën: {w}",
            {"word_with_gap": w, "type": "missing_letter"},
            a,
            i,
        )

    # 6) WRONG_LETTER – paragraf i shkurtër, një fjalë gabim
    wrong_letter_exercises = [
        (
            "Nxënësit përgatisin një proekt të rëndësishëm për mjedisin.",
            "projekt",
        ),
        (
            "Mësuesja na kërkon të shkruajm një përshkrim të shkurtër për veten.",
            "shkruajmë",
        ),
        (
            "Në historí mësojmë për ngjarje të vjetrta dhe të rëndësishme.",
            "vjetra",
        ),
        (
            "Gjatë orës së gjeografis mësojmë për kontinentet dhe oqeanet.",
            "gjeografisë",
        ),
        (
            "Në bibliotekë ne gjejmë libra shkencore dhe artistike.",
            "shkencorë",
        ),
    ]
    for i, (s, a) in enumerate(wrong_letter_exercises, start=1):
        add_exercise(
            CategoryEnum.WRONG_LETTER,
            c6,
            l6,
            f"{s}\nFjala e saktë: __________",
            {"sentence": s, "type": "wrong_letter"},
            a,
            i,
        )

    # 7) BUILD_WORD – fjalë nga shkolla dhe tekstet
    build_word_exercises = [
        ("gorajgefi", "gjeografi"),
        ("tsirohi", "histori"),
        ("ktemesiprer", "eksperiment"),
        ("timaktamee", "matematike"),
        ("rtarkëncshë", "shkencëtar"),
        ("trojekp", "projekt"),
        ("cimarkode", "demokraci"),
        ("rralibib", "bibliar?"),  # do ta zëvendësojmë
        ("roikur`,", "kurorí?"),   # zëvendësim
        ("revilats", "librat?"),   # zëvendësim
    ]
    # Përdorim fjalë më të sakta:
    build_word_exercises = [
        ("gorajgefi", "gjeografi"),
        ("tsirohi", "histori"),
        ("ktemesiprer", "eksperiment"),
        ("timaktamee", "matematike"),
        ("rtarkëncshë", "shkencëtar"),
        ("trojekp", "projekt"),
        ("cimarkode", "demokraci"),
        ("ralibib", "librari"),
        ("epmap", "pamje"),
        ("tseret", "treset?"),  # zëvendësim
    ]
    build_word_exercises[-1] = ("tseret", "treste?")  # që të shmangim anomalitë
    build_word_exercises[-1] = ("ktilra", "artikl?")  # sërish
    build_word_exercises[-1] = ("kartil", "artikl")  # fjalë e huazuar por e njohur

    for i, (w, a) in enumerate(build_word_exercises, start=1):
        add_exercise(
            CategoryEnum.BUILD_WORD,
            c7,
            l7,
            f"{w} → __________",
            {"scrambled_word": w, "type": "build_word"},
            a,
            i,
        )

    # 8) NUMBER_TO_WORD – 31-40
    number_to_word_exercises = [
        ("31", "tridhjetë e një"),
        ("32", "tridhjetë e dy"),
        ("33", "tridhjetë e tre"),
        ("34", "tridhjetë e katër"),
        ("35", "tridhjetë e pesë"),
        ("36", "tridhjetë e gjashtë"),
        ("37", "tridhjetë e shtatë"),
        ("38", "tridhjetë e tetë"),
        ("39", "tridhjetë e nëntë"),
        ("40", "dyzet"),
    ]
    for i, (n, w) in enumerate(number_to_word_exercises, start=1):
        add_exercise(
            CategoryEnum.NUMBER_TO_WORD,
            c8,
            l8,
            f"{n} → _____",
            {"number": n, "type": "number_to_word"},
            w,
            i,
        )

    # 9) PHRASES – situata shkollore e shoqërore
    phrase_exercises = [
        ("Takim ku diskutojmë ide dhe probleme të klasës.", "mbledhje"),
        ("Pushim i shkurtër mes dy orëve mësimore.", "pushim"),
        ("Vend ku nxënësit hanë ushqim në shkollë.", "mensë"),
        ("Akt ku tregon një histori në skenë.", "drama"),
        ("Shfaqje me këngë dhe valle në fund vitit.", "koncert"),
    ]
    for i, (d, w) in enumerate(phrase_exercises, start=1):
        add_exercise(
            CategoryEnum.PHRASES,
            c9,
            l9,
            f"Përshkrimi: {d}\nFjala:",
            {"description": d, "type": "phrase"},
            w,
            i,
        )

    # 10) SPELLING_PUNCTUATION – paragraf me 2 fjali
    spelling_punctuation_exercises = [
        (
            "nxënësit përgatitin një projekt për natyrën dhe mjedisin ne duhet të kujdesemi për tokën tonë",
            "Nxënësit përgatitin një projekt për natyrën dhe mjedisin. Ne duhet të kujdesemi për tokën tonë.",
        ),
        (
            "mësuesja na shpjegon si të shkruajmë një përshkrim të bukur ne e lexojmë me zë të lartë në klasë",
            "Mësuesja na shpjegon si të shkruajmë një përshkrim të bukur. Ne e lexojmë me zë të lartë në klasë.",
        ),
        (
            "familja ime viziton muzeun e qytetit atje mësojmë shumë për historinë",
            "Familja ime viziton muzeun e qytetit. Atje mësojmë shumë për historinë.",
        ),
        (
            "në bibliotekë kërkojmë libra për detyrën e shtëpisë pastaj shkruajmë një përmbledhje të shkurtër",
            "Në bibliotekë kërkojmë libra për detyrën e shtëpisë. Pastaj shkruajmë një përmbledhje të shkurtër.",
        ),
        (
            "pas mësimit ne luajmë në oborrin e shkollës kjo na ndihmon të pushojmë dhe të argëtohemi",
            "Pas mësimit ne luajmë në oborrin e shkollës. Kjo na ndihmon të pushojmë dhe të argëtohemi.",
        ),
    ]
    for i, (inc, corr) in enumerate(spelling_punctuation_exercises, start=1):
        add_exercise(
            CategoryEnum.SPELLING_PUNCTUATION,
            c10,
            l10,
            f"{inc}\nSaktë:",
            {"incorrect": inc, "type": "spelling_punctuation"},
            corr,
            i,
        )

    # 11) ABSTRACT_CONCRETE – më të pasura
    abstract_concrete_exercises = [
        ("drejtësi / palë / fletore → drejtësi (abstrakte)", "drejtësi", ["drejtësi", "palë", "fletore"], "abstract"),
        ("mirënjohje / libër / tavolinë → mirënjohje (abstrakte)", "mirënjohje", ["mirënjohje", "libër", "tavolinë"], "abstract"),
        ("bashkëpunim / klasë / dritare → bashkëpunim (abstrakte)", "bashkëpunim", ["bashkëpunim", "klasë", "dritare"], "abstract"),
        ("respekt / pemë / top → respekt (abstrakte)", "respekt", ["respekt", "pemë", "top"], "abstract"),
        ("besim / rrugë / fletore → besim (abstrakte)", "besim", ["besim", "rrugë", "fletore"], "abstract"),
        ("libër / solidaritet / laps → libër (konkret)", "libër", ["libër", "solidaritet", "laps"], "concrete"),
        ("karrige / barazi / tavolinë → karrige (konkret)", "karrige", ["karrige", "barazi", "tavolinë"], "concrete"),
        ("palestra / liri / top → palestra (konkret)", "palestra", ["palestra", "liri", "top"], "concrete"),
        ("muze / drejtësi / derë → muze (konkret)", "muze", ["muze", "drejtësi", "derë"], "concrete"),
        ("qytet / motivim / rrugë → qytet (konkret)", "qytet", ["qytet", "motivim", "rrugë"], "concrete"),
    ]
    for i, (p, a, choices, t) in enumerate(abstract_concrete_exercises, start=1):
        clean_prompt = p.split("→")[0].strip()
        add_exercise(
            CategoryEnum.ABSTRACT_CONCRETE,
            c11,
            l11,
            clean_prompt,
            {"choices": choices, "type": t},
            a,
            i,
        )

    # 12) BUILD_SENTENCE – dy fjali të lidhura
    build_sentence_exercises = [
        (
            ["Sot", "ne", "vizitojmë", "muzeun", "dhe", "mësojmë", "për", "historinë", "e", "qytetit"],
            "Sot ne vizitojmë muzeun dhe mësojmë për historinë e qytetit.",
        ),
        (
            ["Pas", "shkollës", "ne", "shkojmë", "në", "bibliotekë", "për", "të", "lexuar", "libra"],
            "Pas shkollës ne shkojmë në bibliotekë për të lexuar libra.",
        ),
        (
            ["Gjatë", "orës", "së", "gjeografisë", "mësuesja", "na", "tregon", "për", "kontinentet", "dhe", "oqeanet"],
            "Gjatë orës së gjeografisë mësuesja na tregon për kontinentet dhe oqeanet.",
        ),
        (
            ["Ne", "përgatisim", "një", "projekt", "për", "mjedisin", "dhe", "e", "prezantojmë", "para", "klasës"],
            "Ne përgatisim një projekt për mjedisin dhe e prezantojmë para klasës.",
        ),
        (
            ["Në", "fund", "të", "vitit", "shkollor", "ne", "organizojmë", "një", "koncert", "dhe", "shfaqje"],
            "Në fund të vitit shkollor ne organizojmë një koncert dhe shfaqje.",
        ),
    ]
    for i, (words, sentence) in enumerate(build_sentence_exercises, start=1):
        add_exercise(
            CategoryEnum.BUILD_SENTENCE,
            c12,
            l12,
            f"Fjalë: {words}\nFjalia: ____________________________",
            {"words": words, "type": "build_sentence"},
            sentence,
            i,
        )

    db.commit()
    exercise_count = db.query(Exercise).filter(Exercise.course_id.in_([c.id for c in courses])).count()
    print(f"Successfully seeded {len(courses)} courses and {exercise_count} exercises for fourth class level")
    return fourth_class.id


def seed_fifth_class_exercises(db: Session):
    """Seed the fifth class with the same 12-category structure, very advanced content"""

    # Clear existing data for Class 5
    class_ids_to_clear = db.query(Course.id).filter(Course.name.like("Klasa 5%"))
    db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
    db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
    db.query(Course).filter(Course.name.like("Klasa 5%")).delete()

    # Create Class 5
    fifth_class = Course(
        name="Klasa 5",
        description="Klasa e pestë (10-11 vjeç) me 12 kategori ushtrimesh shumë të avancuara",
        order_index=5,
        category=CategoryEnum.VOCABULARY,
        required_score=80,
        enabled=True,
    )
    db.add(fifth_class)
    db.flush()

    # Create levels 1..12
    level_1 = Level(
        course_id=fifth_class.id,
        name="Niveli 1",
        description="Ushtrime shumë të avancuara për klasën e pestë",
        order_index=1,
        required_score=0,
        enabled=True,
    )
    db.add(level_1)
    db.flush()

    extra_levels = []
    for idx in range(2, 13):
        extra_levels.append(
            Level(
                course_id=fifth_class.id,
                name=f"Niveli {idx}",
                description=f"Niveli {idx} për Klasa 5",
                order_index=idx,
                required_score=80 if idx > 1 else 0,
                enabled=True,
            )
        )
    for lvl in extra_levels:
        db.add(lvl)
    db.flush()

    # Create 12 courses (categories) under Class 5
    courses = []
    course_defs = [
        ("Niveli 1", CategoryEnum.LISTEN_WRITE),
        ("Niveli 2", CategoryEnum.WORD_FROM_DESCRIPTION),
        ("Niveli 3", CategoryEnum.SYNONYMS_ANTONYMS),
        ("Niveli 4", CategoryEnum.ALBANIAN_OR_LOANWORD),
        ("Niveli 5", CategoryEnum.MISSING_LETTER),
        ("Niveli 6", CategoryEnum.WRONG_LETTER),
        ("Niveli 7", CategoryEnum.BUILD_WORD),
        ("Niveli 8", CategoryEnum.NUMBER_TO_WORD),
        ("Niveli 9", CategoryEnum.PHRASES),
        ("Niveli 10", CategoryEnum.SPELLING_PUNCTUATION),
        ("Niveli 11", CategoryEnum.ABSTRACT_CONCRETE),
        ("Niveli 12", CategoryEnum.BUILD_SENTENCE),
    ]
    for idx, (name, cat) in enumerate(course_defs, start=1):
        c = Course(
            name=name,
            description=name,
            order_index=idx,
            category=cat,
            required_score=0,
            enabled=True,
            parent_class_id=fifth_class.id,
        )
        db.add(c)
        courses.append(c)
    db.flush()

    # Map level 1 to all courses
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime shumë të avancuara",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()

    def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
        ex = Exercise(
            category=cat,
            course_id=course.id,
            level_id=level.id,
            prompt=prompt,
            data=json.dumps(data_obj),
            answer=answer,
            points=1,
            order_index=idx,
        )
        db.add(ex)

    (
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12
    ) = courses
    l1 = level_by_course[c1.id]
    l2 = level_by_course[c2.id]
    l3 = level_by_course[c3.id]
    l4 = level_by_course[c4.id]
    l5 = level_by_course[c5.id]
    l6 = level_by_course[c6.id]
    l7 = level_by_course[c7.id]
    l8 = level_by_course[c8.id]
    l9 = level_by_course[c9.id]
    l10 = level_by_course[c10.id]
    l11 = level_by_course[c11.id]
    l12 = level_by_course[c12.id]

    # 1) LISTEN_WRITE – fjali komplekse
    dictation_exercises = [
        ("Shkencëtarët studiojnë natyrën për të kuptuar ligjet e saj.", "Shkencëtarët studiojnë natyrën për të kuptuar ligjet e saj."),
        ("Demokracia kërkon pjesëmarrje aktive nga të gjithë qytetarët.", "Demokracia kërkon pjesëmarrje aktive nga të gjithë qytetarët."),
        ("Kultura jonë pasqyron traditat dhe vlerat e popullit tonë.", "Kultura jonë pasqyron traditat dhe vlerat e popullit tonë."),
        ("Teknologjia moderne transformon mënyrën se si komunikojmë.", "Teknologjia moderne transformon mënyrën se si komunikojmë."),
        ("Edukimi është themeli i zhvillimit personal dhe shoqëror.", "Edukimi është themeli i zhvillimit personal dhe shoqëror."),
    ]
    for i, (p, a) in enumerate(dictation_exercises, start=1):
        add_exercise(CategoryEnum.LISTEN_WRITE, c1, l1, "Shkruaj fjalinë që dëgjon.", {"audio_word": p, "type": "dictation"}, a, i)

    # 2) WORD_FROM_DESCRIPTION – koncepte komplekse
    desc_exercises = [
        ("Sistemi që organizon dhe kontrollon një shtet.", "qeveria", ["qeveria", "shkolla", "familja", "biblioteka", "spitali"]),
        ("Ndjenjë e thellë respekti dhe admirimi për dikë.", "nderim", ["nderim", "gëzim", "frikë", "lumturi", "trishtim"]),
        ("Procesi i mësimit dhe zhvillimit të njohurive.", "edukim", ["edukim", "lojë", "pushim", "udhëtim", "vizitë"]),
        ("Ligjet dhe rregullat që rregullojnë një shoqëri.", "legjislacion", ["legjislacion", "libër", "letër", "fletore", "revistë"]),
        ("Ndjenjë e përbashkët e identitetit dhe përkatësisë.", "solidaritet", ["solidaritet", "lojë", "kohë", "vend", "shtëpi"]),
    ]
    for i, (desc, word, choices) in enumerate(desc_exercises, start=1):
        add_exercise(CategoryEnum.WORD_FROM_DESCRIPTION, c2, l2, desc, {"choices": choices, "type": "multiple_choice"}, word, i)

    # 3) SYNONYMS_ANTONYMS – fjalë komplekse
    syn_ant_exercises = [
        ("i zgjuar → _______", "i mençur", "synonym"),
        ("i guximshëm → _______", "i frikacak", "antonym"),
        ("i përgjegjshëm → _______", "i përgjegjshëm", "synonym"),
        ("i përpiktë → _______", "i pasaktë", "antonym"),
        ("i qëndrueshëm → _______", "i paqëndrueshëm", "antonym"),
        ("i besueshëm → _______", "i pabesueshëm", "antonym"),
        ("i dinak → _______", "i ndershëm", "antonym"),
        ("i përmbajtur → _______", "i shfrenuar", "antonym"),
    ]
    for i, (p, a, t) in enumerate(syn_ant_exercises, start=1):
        add_exercise(CategoryEnum.SYNONYMS_ANTONYMS, c3, l3, p, {"choices": [], "type": t}, a, i)

    # 4) ALBANIAN_OR_LOANWORD – fjalë komplekse
    al_lo_exercises = [
        ("demokraci", "Huazim"), ("kulturë", "Shqip"), ("teknologji", "Huazim"),
        ("traditë", "Shqip"), ("komunikim", "Shqip"), ("sistem", "Huazim"),
        ("edukim", "Shqip"), ("organizim", "Huazim"), ("transformim", "Huazim"),
        ("identitet", "Huazim"),
    ]
    for i, (w, a) in enumerate(al_lo_exercises, start=1):
        add_exercise(CategoryEnum.ALBANIAN_OR_LOANWORD, c4, l4, f"'{w}' është:", {"choices": ["Shqip", "Huazim"], "type": "albanian_loanword"}, a, i)

    # 5) MISSING_LETTER – fjalë komplekse
    miss_exercises = [
        ("demokr_ci", "demokraci"), ("kult_rë", "kulturë"), ("teknol_gji", "teknologji"),
        ("trad_të", "traditë"), ("komun_kim", "komunikim"), ("s_stem", "sistem"),
        ("eduk_m", "edukim"), ("organ_zim", "organizim"),
    ]
    for i, (w, a) in enumerate(miss_exercises, start=1):
        add_exercise(CategoryEnum.MISSING_LETTER, c5, l5, f"Shkruaj fjalën: {w}", {"word_with_gap": w, "type": "missing_letter"}, a, i)

    # 6) WRONG_LETTER – fjali komplekse
    wrong_exercises = [
        ("Demokracia kërkon pjesmarrje aktive.", "pjesëmarrje"),
        ("Edukimi është themeli i zhvillimit.", "zhvillimit"),
        ("Kultura pasqyron traditat tona.", "traditat"),
        ("Teknologjia transformon komunikimin.", "komunikimin"),
    ]
    for i, (s, a) in enumerate(wrong_exercises, start=1):
        add_exercise(CategoryEnum.WRONG_LETTER, c6, l6, f"{s}\nFjala e saktë: __________", {"sentence": s, "type": "wrong_letter"}, a, i)

    # 7) BUILD_WORD – fjalë komplekse
    buildw_exercises = [
        ("demokraci", "demokraci"), ("kulturë", "kulturë"), ("teknologji", "teknologji"),
        ("traditë", "traditë"), ("komunikim", "komunikim"), ("sistem", "sistem"),
        ("edukim", "edukim"), ("organizim", "organizim"),
    ]
    for i, (w, a) in enumerate(buildw_exercises, start=1):
        scrambled = ''.join(sorted(w, key=lambda x: hash(x) % 10))
        add_exercise(CategoryEnum.BUILD_WORD, c7, l7, f"{scrambled} → __________", {"scrambled_word": scrambled, "type": "build_word"}, a, i)

    # 8) NUMBER_TO_WORD – numra më të mëdhenj
    numw_exercises = [
        ("11", "njëmbëdhjetë"), ("12", "dymbëdhjetë"), ("15", "pesëmbëdhjetë"),
        ("20", "njëzet"), ("25", "njëzet e pesë"), ("30", "tridhjetë"),
        ("50", "pesëdhjetë"), ("100", "njëqind"),
    ]
    for i, (n, w) in enumerate(numw_exercises, start=1):
        add_exercise(CategoryEnum.NUMBER_TO_WORD, c8, l8, f"{n} → _____", {"number": n, "type": "number_to_word"}, w, i)

    # 9) PHRASES – koncepte komplekse
    phrase_exercises = [
        ("Sistemi që organizon dhe kontrollon një shtet.", "qeveria"),
        ("Ndjenjë e thellë respekti dhe admirimi.", "nderim"),
        ("Procesi i mësimit dhe zhvillimit të njohurive.", "edukim"),
        ("Ligjet që rregullojnë një shoqëri.", "legjislacion"),
    ]
    for i, (desc, word) in enumerate(phrase_exercises, start=1):
        add_exercise(CategoryEnum.PHRASES, c9, l9, f"Përshkrimi: {desc}\nFjala:", {"description": desc, "type": "phrase"}, word, i)

    # 10) SPELLING_PUNCTUATION – fjali komplekse
    spellp_exercises = [
        ("demokracia kërkon pjesëmarrje aktive", "Demokracia kërkon pjesëmarrje aktive."),
        ("edukimi është themeli i zhvillimit", "Edukimi është themeli i zhvillimit."),
        ("kultura pasqyron traditat tona", "Kultura pasqyron traditat tona."),
        ("teknologjia transformon komunikimin", "Teknologjia transformon komunikimin."),
    ]
    for i, (inc, corr) in enumerate(spellp_exercises, start=1):
        add_exercise(CategoryEnum.SPELLING_PUNCTUATION, c10, l10, f"{inc}\nSaktë:", {"incorrect": inc, "type": "spelling_punctuation"}, corr, i)

    # 11) ABSTRACT_CONCRETE – koncepte komplekse
    abscon_exercises = [
        ("demokraci / qeveri / parlament → parlament (konkret)", "parlament", "concrete"),
        ("kulturë / traditë / muze → muze (konkret)", "muze", "concrete"),
        ("edukim / shkollë / universitet → universitet (konkret)", "universitet", "concrete"),
        ("demokraci / qeveri / ligj → demokraci (abstrakte)", "demokraci", "abstract"),
        ("kulturë / traditë / vlerë → vlerë (abstrakte)", "vlerë", "abstract"),
    ]
    for i, (p, a, t) in enumerate(abscon_exercises, start=1):
        base = p.split("→")[0].strip()
        add_exercise(CategoryEnum.ABSTRACT_CONCRETE, c11, l11, f"Zgjidh fjalën e duhur: {base}", {"choices": [], "type": t}, a, i)

    # 12) BUILD_SENTENCE – fjali komplekse
    builds_exercises = [
        (["Demokracia", "kërkon", "pjesëmarrje", "aktive", "nga", "qytetarët"], "Demokracia kërkon pjesëmarrje aktive nga qytetarët."),
        (["Edukimi", "është", "themeli", "i", "zhvillimit", "personal"], "Edukimi është themeli i zhvillimit personal."),
        (["Kultura", "pasqyron", "traditat", "dhe", "vlerat", "e", "popullit"], "Kultura pasqyron traditat dhe vlerat e popullit."),
    ]
    for i, (words, sentence) in enumerate(builds_exercises, start=1):
        add_exercise(CategoryEnum.BUILD_SENTENCE, c12, l12, f"Fjalë: {words}\nFjalia: ____________________________", {"words": words, "type": "build_sentence"}, sentence, i)

    db.commit()
    exercise_count = db.query(Exercise).filter(Exercise.course_id.in_([c.id for c in courses])).count()
    print(f"Successfully seeded {len(courses)} courses and {exercise_count} exercises for fifth class level")
    return fifth_class.id


def seed_sixth_class_exercises(db: Session):
    """Seed the sixth class with the same 12-category structure, extremely advanced content"""

    # Clear existing data for Class 6
    class_ids_to_clear = db.query(Course.id).filter(Course.name.like("Klasa 6%"))
    db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
    db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
    db.query(Course).filter(Course.name.like("Klasa 6%")).delete()

    # Create Class 6
    sixth_class = Course(
        name="Klasa 6",
        description="Klasa e gjashtë (11-12 vjeç) me 12 kategori ushtrimesh ekstremisht të avancuara",
        order_index=6,
        category=CategoryEnum.VOCABULARY,
        required_score=80,
        enabled=True,
    )
    db.add(sixth_class)
    db.flush()

    # Create levels 1..12
    level_1 = Level(
        course_id=sixth_class.id,
        name="Niveli 1",
        description="Ushtrime ekstremisht të avancuara për klasën e gjashtë",
        order_index=1,
        required_score=0,
        enabled=True,
    )
    db.add(level_1)
    db.flush()

    extra_levels = []
    for idx in range(2, 13):
        extra_levels.append(
            Level(
                course_id=sixth_class.id,
                name=f"Niveli {idx}",
                description=f"Niveli {idx} për Klasa 6",
                order_index=idx,
                required_score=80 if idx > 1 else 0,
                enabled=True,
            )
        )
    for lvl in extra_levels:
        db.add(lvl)
    db.flush()

    # Create 12 courses (categories) under Class 6
    courses = []
    course_defs = [
        ("Niveli 1", CategoryEnum.LISTEN_WRITE),
        ("Niveli 2", CategoryEnum.WORD_FROM_DESCRIPTION),
        ("Niveli 3", CategoryEnum.SYNONYMS_ANTONYMS),
        ("Niveli 4", CategoryEnum.ALBANIAN_OR_LOANWORD),
        ("Niveli 5", CategoryEnum.MISSING_LETTER),
        ("Niveli 6", CategoryEnum.WRONG_LETTER),
        ("Niveli 7", CategoryEnum.BUILD_WORD),
        ("Niveli 8", CategoryEnum.NUMBER_TO_WORD),
        ("Niveli 9", CategoryEnum.PHRASES),
        ("Niveli 10", CategoryEnum.SPELLING_PUNCTUATION),
        ("Niveli 11", CategoryEnum.ABSTRACT_CONCRETE),
        ("Niveli 12", CategoryEnum.BUILD_SENTENCE),
    ]
    for idx, (name, cat) in enumerate(course_defs, start=1):
        c = Course(
            name=name,
            description=name,
            order_index=idx,
            category=cat,
            required_score=0,
            enabled=True,
            parent_class_id=sixth_class.id,
        )
        db.add(c)
        courses.append(c)
    db.flush()

    # Map level 1 to all courses
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime ekstremisht të avancuara",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()

    def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
        ex = Exercise(
            category=cat,
            course_id=course.id,
            level_id=level.id,
            prompt=prompt,
            data=json.dumps(data_obj),
            answer=answer,
            points=1,
            order_index=idx,
        )
        db.add(ex)

    (
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12
    ) = courses
    l1 = level_by_course[c1.id]
    l2 = level_by_course[c2.id]
    l3 = level_by_course[c3.id]
    l4 = level_by_course[c4.id]
    l5 = level_by_course[c5.id]
    l6 = level_by_course[c6.id]
    l7 = level_by_course[c7.id]
    l8 = level_by_course[c8.id]
    l9 = level_by_course[c9.id]
    l10 = level_by_course[c10.id]
    l11 = level_by_course[c11.id]
    l12 = level_by_course[c12.id]

    # 1) LISTEN_WRITE – paragrafë kompleks
    dictation_exercises = [
        ("Shkencëtarët studiojnë natyrën për të kuptuar ligjet e saj dhe për të zbuluar sekrete të reja.", "Shkencëtarët studiojnë natyrën për të kuptuar ligjet e saj dhe për të zbuluar sekrete të reja."),
        ("Demokracia moderne kërkon pjesëmarrje aktive nga të gjithë qytetarët në proceset vendimmarrëse.", "Demokracia moderne kërkon pjesëmarrje aktive nga të gjithë qytetarët në proceset vendimmarrëse."),
        ("Kultura jonë kombëtare pasqyron traditat e lashta dhe vlerat e popullit tonë që kanë kaluar brez pas brezi.", "Kultura jonë kombëtare pasqyron traditat e lashta dhe vlerat e popullit tonë që kanë kaluar brez pas brezi."),
        ("Teknologjia moderne transformon mënyrën se si komunikojmë, punojmë dhe jetojmë në shoqërinë e sotme.", "Teknologjia moderne transformon mënyrën se si komunikojmë, punojmë dhe jetojmë në shoqërinë e sotme."),
        ("Edukimi cilësor është themeli i zhvillimit personal, profesional dhe shoqëror për të gjithë brezat.", "Edukimi cilësor është themeli i zhvillimit personal, profesional dhe shoqëror për të gjithë brezat."),
    ]
    for i, (p, a) in enumerate(dictation_exercises, start=1):
        add_exercise(CategoryEnum.LISTEN_WRITE, c1, l1, "Shkruaj fjalinë që dëgjon.", {"audio_word": p, "type": "dictation"}, a, i)

    # 2) WORD_FROM_DESCRIPTION – koncepte shkencore dhe filozofike
    desc_exercises = [
        ("Sistemi kompleks që organizon, kontrollon dhe administron një shtet ose organizatë.", "qeveria", ["qeveria", "shkolla", "familja", "biblioteka", "spitali"]),
        ("Ndjenjë e thellë respekti, admirimi dhe vlerësimi për dikë ose diçka.", "nderim", ["nderim", "gëzim", "frikë", "lumturi", "trishtim"]),
        ("Procesi i vazhdueshëm i mësimit, zhvillimit dhe përmirësimit të njohurive dhe aftësive.", "edukim", ["edukim", "lojë", "pushim", "udhëtim", "vizitë"]),
        ("Tërësia e ligjeve, rregullave dhe normave që rregullojnë dhe organizojnë një shoqëri.", "legjislacion", ["legjislacion", "libër", "letër", "fletore", "revistë"]),
        ("Ndjenjë e përbashkët e identitetit, përkatësisë dhe mbështetjes reciproke në një grup.", "solidaritet", ["solidaritet", "lojë", "kohë", "vend", "shtëpi"]),
    ]
    for i, (desc, word, choices) in enumerate(desc_exercises, start=1):
        add_exercise(CategoryEnum.WORD_FROM_DESCRIPTION, c2, l2, desc, {"choices": choices, "type": "multiple_choice"}, word, i)

    # 3) SYNONYMS_ANTONYMS – fjalë shkencore
    syn_ant_exercises = [
        ("i analitik → _______", "i logjik", "synonym"),
        ("i inovativ → _______", "i konvencional", "antonym"),
        ("i kritik → _______", "i pranueshëm", "antonym"),
        ("i objektiv → _______", "i subjektiv", "antonym"),
        ("i racional → _______", "i emocional", "antonym"),
        ("i sistematik → _______", "i çrregullt", "antonym"),
        ("i teoretik → _______", "i praktik", "antonym"),
        ("i universal → _______", "i lokal", "antonym"),
    ]
    for i, (p, a, t) in enumerate(syn_ant_exercises, start=1):
        add_exercise(CategoryEnum.SYNONYMS_ANTONYMS, c3, l3, p, {"choices": [], "type": t}, a, i)

    # 4) ALBANIAN_OR_LOANWORD – fjalë shkencore dhe teknike
    al_lo_exercises = [
        ("demokraci", "Huazim"), ("kulturë", "Shqip"), ("teknologji", "Huazim"),
        ("traditë", "Shqip"), ("komunikim", "Shqip"), ("sistem", "Huazim"),
        ("edukim", "Shqip"), ("organizim", "Huazim"), ("transformim", "Huazim"),
        ("identitet", "Huazim"), ("legjislacion", "Huazim"), ("solidaritet", "Huazim"),
    ]
    for i, (w, a) in enumerate(al_lo_exercises, start=1):
        add_exercise(CategoryEnum.ALBANIAN_OR_LOANWORD, c4, l4, f"'{w}' është:", {"choices": ["Shqip", "Huazim"], "type": "albanian_loanword"}, a, i)

    # 5) MISSING_LETTER – fjalë komplekse
    miss_exercises = [
        ("demokr_ci", "demokraci"), ("kult_rë", "kulturë"), ("teknol_gji", "teknologji"),
        ("trad_të", "traditë"), ("komun_kim", "komunikim"), ("s_stem", "sistem"),
        ("eduk_m", "edukim"), ("organ_zim", "organizim"), ("transform_m", "transformim"),
    ]
    for i, (w, a) in enumerate(miss_exercises, start=1):
        add_exercise(CategoryEnum.MISSING_LETTER, c5, l5, f"Shkruaj fjalën: {w}", {"word_with_gap": w, "type": "missing_letter"}, a, i)

    # 6) WRONG_LETTER – fjali komplekse
    wrong_exercises = [
        ("Demokracia moderne kërkon pjesmarrje aktive nga qytetarët.", "pjesëmarrje"),
        ("Edukimi cilësor është themeli i zhvillimit shoqëror.", "zhvillimit"),
        ("Kultura kombëtare pasqyron traditat dhe vlerat tona.", "traditat"),
        ("Teknologjia transformon mënyrën e komunikimit modern.", "komunikimit"),
    ]
    for i, (s, a) in enumerate(wrong_exercises, start=1):
        add_exercise(CategoryEnum.WRONG_LETTER, c6, l6, f"{s}\nFjala e saktë: __________", {"sentence": s, "type": "wrong_letter"}, a, i)

    # 7) BUILD_WORD – fjalë komplekse
    buildw_exercises = [
        ("demokraci", "demokraci"), ("kulturë", "kulturë"), ("teknologji", "teknologji"),
        ("traditë", "traditë"), ("komunikim", "komunikim"), ("sistem", "sistem"),
        ("edukim", "edukim"), ("organizim", "organizim"), ("transformim", "transformim"),
    ]
    for i, (w, a) in enumerate(buildw_exercises, start=1):
        scrambled = ''.join(sorted(w, key=lambda x: hash(x) % 10))
        add_exercise(CategoryEnum.BUILD_WORD, c7, l7, f"{scrambled} → __________", {"scrambled_word": scrambled, "type": "build_word"}, a, i)

    # 8) NUMBER_TO_WORD – numra kompleks
    numw_exercises = [
        ("21", "njëzet e një"), ("35", "tridhjetë e pesë"), ("47", "dyzet e shtatë"),
        ("58", "pesëdhjetë e tetë"), ("69", "gjashtëdhjetë e nëntë"), ("73", "shtatëdhjetë e tre"),
        ("84", "tetëdhjetë e katër"), ("96", "nëntëdhjetë e gjashtë"), ("100", "njëqind"),
    ]
    for i, (n, w) in enumerate(numw_exercises, start=1):
        add_exercise(CategoryEnum.NUMBER_TO_WORD, c8, l8, f"{n} → _____", {"number": n, "type": "number_to_word"}, w, i)

    # 9) PHRASES – koncepte shkencore
    phrase_exercises = [
        ("Sistemi kompleks që organizon dhe kontrollon një shtet.", "qeveria"),
        ("Ndjenjë e thellë respekti dhe admirimi për dikë.", "nderim"),
        ("Procesi i vazhdueshëm i mësimit dhe zhvillimit.", "edukim"),
        ("Tërësia e ligjeve që rregullojnë një shoqëri.", "legjislacion"),
    ]
    for i, (desc, word) in enumerate(phrase_exercises, start=1):
        add_exercise(CategoryEnum.PHRASES, c9, l9, f"Përshkrimi: {desc}\nFjala:", {"description": desc, "type": "phrase"}, word, i)

    # 10) SPELLING_PUNCTUATION – fjali komplekse
    spellp_exercises = [
        ("demokracia moderne kërkon pjesëmarrje aktive", "Demokracia moderne kërkon pjesëmarrje aktive."),
        ("edukimi cilësor është themeli i zhvillimit", "Edukimi cilësor është themeli i zhvillimit."),
        ("kultura kombëtare pasqyron traditat tona", "Kultura kombëtare pasqyron traditat tona."),
        ("teknologjia transformon komunikimin modern", "Teknologjia transformon komunikimin modern."),
    ]
    for i, (inc, corr) in enumerate(spellp_exercises, start=1):
        add_exercise(CategoryEnum.SPELLING_PUNCTUATION, c10, l10, f"{inc}\nSaktë:", {"incorrect": inc, "type": "spelling_punctuation"}, corr, i)

    # 11) ABSTRACT_CONCRETE – koncepte komplekse
    abscon_exercises = [
        ("demokraci / qeveri / parlament → parlament (konkret)", "parlament", "concrete"),
        ("kulturë / traditë / muze → muze (konkret)", "muze", "concrete"),
        ("edukim / shkollë / universitet → universitet (konkret)", "universitet", "concrete"),
        ("demokraci / qeveri / ligj → demokraci (abstrakte)", "demokraci", "abstract"),
        ("kulturë / traditë / vlerë → vlerë (abstrakte)", "vlerë", "abstract"),
        ("edukim / shkollë / njohuri → njohuri (abstrakte)", "njohuri", "abstract"),
    ]
    for i, (p, a, t) in enumerate(abscon_exercises, start=1):
        base = p.split("→")[0].strip()
        add_exercise(CategoryEnum.ABSTRACT_CONCRETE, c11, l11, f"Zgjidh fjalën e duhur: {base}", {"choices": [], "type": t}, a, i)

    # 12) BUILD_SENTENCE – fjali komplekse me lidhëza
    builds_exercises = [
        (["Demokracia", "moderne", "kërkon", "pjesëmarrje", "aktive", "nga", "qytetarët", "në", "proceset", "vendimmarrëse"], "Demokracia moderne kërkon pjesëmarrje aktive nga qytetarët në proceset vendimmarrëse."),
        (["Edukimi", "cilësor", "është", "themeli", "i", "zhvillimit", "personal", "dhe", "shoqëror"], "Edukimi cilësor është themeli i zhvillimit personal dhe shoqëror."),
        (["Kultura", "kombëtare", "pasqyron", "traditat", "e", "lashta", "dhe", "vlerat", "e", "popullit"], "Kultura kombëtare pasqyron traditat e lashta dhe vlerat e popullit."),
    ]
    for i, (words, sentence) in enumerate(builds_exercises, start=1):
        add_exercise(CategoryEnum.BUILD_SENTENCE, c12, l12, f"Fjalë: {words}\nFjalia: ____________________________", {"words": words, "type": "build_sentence"}, sentence, i)

    db.commit()
    exercise_count = db.query(Exercise).filter(Exercise.course_id.in_([c.id for c in courses])).count()
    print(f"Successfully seeded {len(courses)} courses and {exercise_count} exercises for sixth class level")
    return sixth_class.id


def seed_seventh_class_exercises(db: Session):
    """Seed the seventh class with the same 12-category structure, highly advanced content"""

    # Clear existing data for Class 7
    class_ids_to_clear = db.query(Course.id).filter(Course.name.like("Klasa 7%"))
    db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
    db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
    db.query(Course).filter(Course.name.like("Klasa 7%")).delete()

    # Create Class 7
    seventh_class = Course(
        name="Klasa 7",
        description="Klasa e shtatë (12-13 vjeç) me 12 kategori ushtrimesh shumë të avancuara dhe komplekse",
        order_index=7,
        category=CategoryEnum.VOCABULARY,
        required_score=80,
        enabled=True,
    )
    db.add(seventh_class)
    db.flush()

    # Create levels 1..12
    level_1 = Level(
        course_id=seventh_class.id,
        name="Niveli 1",
        description="Ushtrime shumë të avancuara për klasën e shtatë",
        order_index=1,
        required_score=0,
        enabled=True,
    )
    db.add(level_1)
    db.flush()

    extra_levels = []
    for idx in range(2, 13):
        extra_levels.append(
            Level(
                course_id=seventh_class.id,
                name=f"Niveli {idx}",
                description=f"Niveli {idx} për Klasa 7",
                order_index=idx,
                required_score=80 if idx > 1 else 0,
                enabled=True,
            )
        )
    for lvl in extra_levels:
        db.add(lvl)
    db.flush()

    # Create 12 courses (categories) under Class 7
    courses = []
    course_defs = [
        ("Niveli 1", CategoryEnum.LISTEN_WRITE),
        ("Niveli 2", CategoryEnum.WORD_FROM_DESCRIPTION),
        ("Niveli 3", CategoryEnum.SYNONYMS_ANTONYMS),
        ("Niveli 4", CategoryEnum.ALBANIAN_OR_LOANWORD),
        ("Niveli 5", CategoryEnum.MISSING_LETTER),
        ("Niveli 6", CategoryEnum.WRONG_LETTER),
        ("Niveli 7", CategoryEnum.BUILD_WORD),
        ("Niveli 8", CategoryEnum.NUMBER_TO_WORD),
        ("Niveli 9", CategoryEnum.PHRASES),
        ("Niveli 10", CategoryEnum.SPELLING_PUNCTUATION),
        ("Niveli 11", CategoryEnum.ABSTRACT_CONCRETE),
        ("Niveli 12", CategoryEnum.BUILD_SENTENCE),
    ]
    for idx, (name, cat) in enumerate(course_defs, start=1):
        c = Course(
            name=name,
            description=name,
            order_index=idx,
            category=cat,
            required_score=0,
            enabled=True,
            parent_class_id=seventh_class.id,
        )
        db.add(c)
        courses.append(c)
    db.flush()

    # Map level 1 to all courses
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime shumë të avancuara",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()

    def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
        ex = Exercise(
            category=cat,
            course_id=course.id,
            level_id=level.id,
            prompt=prompt,
            data=json.dumps(data_obj),
            answer=answer,
            points=1,
            order_index=idx,
        )
        db.add(ex)

    (
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12
    ) = courses
    l1 = level_by_course[c1.id]
    l2 = level_by_course[c2.id]
    l3 = level_by_course[c3.id]
    l4 = level_by_course[c4.id]
    l5 = level_by_course[c5.id]
    l6 = level_by_course[c6.id]
    l7 = level_by_course[c7.id]
    l8 = level_by_course[c8.id]
    l9 = level_by_course[c9.id]
    l10 = level_by_course[c10.id]
    l11 = level_by_course[c11.id]
    l12 = level_by_course[c12.id]

    # 1) LISTEN_WRITE – paragrafë kompleks dhe argumentative
    dictation_exercises = [
        ("Shkencëtarët modernë studiojnë natyrën në thellësi për të kuptuar ligjet e saj themelore dhe për të zbuluar sekrete të reja që mund të transformojnë botën tonë.", "Shkencëtarët modernë studiojnë natyrën në thellësi për të kuptuar ligjet e saj themelore dhe për të zbuluar sekrete të reja që mund të transformojnë botën tonë."),
        ("Demokracia moderne kërkon pjesëmarrje aktive dhe të informuar nga të gjithë qytetarët në proceset vendimmarrëse që ndikojnë në të ardhmen e shoqërisë.", "Demokracia moderne kërkon pjesëmarrje aktive dhe të informuar nga të gjithë qytetarët në proceset vendimmarrëse që ndikojnë në të ardhmen e shoqërisë."),
        ("Kultura jonë kombëtare pasqyron traditat e lashta, vlerat e popullit tonë dhe identitetin tonë unik që kanë kaluar brez pas brezi dhe që na bëjnë të dallueshëm.", "Kultura jonë kombëtare pasqyron traditat e lashta, vlerat e popullit tonë dhe identitetin tonë unik që kanë kaluar brez pas brezi dhe që na bëjnë të dallueshëm."),
        ("Teknologjia moderne transformon mënyrën se si komunikojmë, punojmë, mësojmë dhe jetojmë në shoqërinë e sotme, duke krijuar mundësi të reja dhe sfida të reja.", "Teknologjia moderne transformon mënyrën se si komunikojmë, punojmë, mësojmë dhe jetojmë në shoqërinë e sotme, duke krijuar mundësi të reja dhe sfida të reja."),
        ("Edukimi cilësor është themeli i zhvillimit personal, profesional dhe shoqëror për të gjithë brezat, duke siguruar një të ardhme më të mirë për të gjithë.", "Edukimi cilësor është themeli i zhvillimit personal, profesional dhe shoqëror për të gjithë brezat, duke siguruar një të ardhme më të mirë për të gjithë."),
    ]
    for i, (p, a) in enumerate(dictation_exercises, start=1):
        add_exercise(CategoryEnum.LISTEN_WRITE, c1, l1, "Shkruaj fjalinë që dëgjon.", {"audio_word": p, "type": "dictation"}, a, i)

    # 2) WORD_FROM_DESCRIPTION – koncepte akademike dhe filozofike
    desc_exercises = [
        ("Sistemi kompleks dhe i organizuar që administron, kontrollon dhe drejton një shtet ose organizatë më të madhe.", "qeveria", ["qeveria", "shkolla", "familja", "biblioteka", "spitali"]),
        ("Ndjenjë e thellë dhe e sinqertë respekti, admirimi dhe vlerësimi për dikë ose diçka që konsiderohet e rëndësishme.", "nderim", ["nderim", "gëzim", "frikë", "lumturi", "trishtim"]),
        ("Procesi i vazhdueshëm dhe i planifikuar i mësimit, zhvillimit dhe përmirësimit të njohurive, aftësive dhe kompetencave.", "edukim", ["edukim", "lojë", "pushim", "udhëtim", "vizitë"]),
        ("Tërësia e ligjeve, rregullave, normave dhe procedurave që rregullojnë, organizojnë dhe kontrollojnë një shoqëri ose sistem.", "legjislacion", ["legjislacion", "libër", "letër", "fletore", "revistë"]),
        ("Ndjenjë e përbashkët e thellë e identitetit, përkatësisë dhe mbështetjes reciproke në një grup, komunitet ose shoqëri.", "solidaritet", ["solidaritet", "lojë", "kohë", "vend", "shtëpi"]),
    ]
    for i, (desc, word, choices) in enumerate(desc_exercises, start=1):
        add_exercise(CategoryEnum.WORD_FROM_DESCRIPTION, c2, l2, desc, {"choices": choices, "type": "multiple_choice"}, word, i)

    # 3) SYNONYMS_ANTONYMS – fjalë akademike
    syn_ant_exercises = [
        ("i analitik → _______", "i logjik", "synonym"),
        ("i inovativ → _______", "i konvencional", "antonym"),
        ("i kritik → _______", "i pranueshëm", "antonym"),
        ("i objektiv → _______", "i subjektiv", "antonym"),
        ("i racional → _______", "i emocional", "antonym"),
        ("i sistematik → _______", "i çrregullt", "antonym"),
        ("i teoretik → _______", "i praktik", "antonym"),
        ("i universal → _______", "i lokal", "antonym"),
        ("i sofistikuar → _______", "i thjeshtë", "antonym"),
    ]
    for i, (p, a, t) in enumerate(syn_ant_exercises, start=1):
        add_exercise(CategoryEnum.SYNONYMS_ANTONYMS, c3, l3, p, {"choices": [], "type": t}, a, i)

    # 4) ALBANIAN_OR_LOANWORD – fjalë akademike dhe teknike
    al_lo_exercises = [
        ("demokraci", "Huazim"), ("kulturë", "Shqip"), ("teknologji", "Huazim"),
        ("traditë", "Shqip"), ("komunikim", "Shqip"), ("sistem", "Huazim"),
        ("edukim", "Shqip"), ("organizim", "Huazim"), ("transformim", "Huazim"),
        ("identitet", "Huazim"), ("legjislacion", "Huazim"), ("solidaritet", "Huazim"),
    ]
    for i, (w, a) in enumerate(al_lo_exercises, start=1):
        add_exercise(CategoryEnum.ALBANIAN_OR_LOANWORD, c4, l4, f"'{w}' është:", {"choices": ["Shqip", "Huazim"], "type": "albanian_loanword"}, a, i)

    # 5) MISSING_LETTER – fjalë komplekse akademike
    miss_exercises = [
        ("demokr_ci", "demokraci"), ("kult_rë", "kulturë"), ("teknol_gji", "teknologji"),
        ("trad_të", "traditë"), ("komun_kim", "komunikim"), ("s_stem", "sistem"),
        ("eduk_m", "edukim"), ("organ_zim", "organizim"), ("transform_m", "transformim"),
    ]
    for i, (w, a) in enumerate(miss_exercises, start=1):
        add_exercise(CategoryEnum.MISSING_LETTER, c5, l5, f"Shkruaj fjalën: {w}", {"word_with_gap": w, "type": "missing_letter"}, a, i)

    # 6) WRONG_LETTER – fjali komplekse akademike
    wrong_exercises = [
        ("Demokracia moderne kërkon pjesmarrje aktive nga qytetarët.", "pjesëmarrje"),
        ("Edukimi cilësor është themeli i zhvillimit shoqëror.", "zhvillimit"),
        ("Kultura kombëtare pasqyron traditat dhe vlerat tona.", "traditat"),
        ("Teknologjia transformon mënyrën e komunikimit modern.", "komunikimit"),
    ]
    for i, (s, a) in enumerate(wrong_exercises, start=1):
        add_exercise(CategoryEnum.WRONG_LETTER, c6, l6, f"{s}\nFjala e saktë: __________", {"sentence": s, "type": "wrong_letter"}, a, i)

    # 7) BUILD_WORD – fjalë komplekse akademike
    buildw_exercises = [
        ("demokraci", "demokraci"), ("kulturë", "kulturë"), ("teknologji", "teknologji"),
        ("traditë", "traditë"), ("komunikim", "komunikim"), ("sistem", "sistem"),
        ("edukim", "edukim"), ("organizim", "organizim"), ("transformim", "transformim"),
    ]
    for i, (w, a) in enumerate(buildw_exercises, start=1):
        scrambled = ''.join(sorted(w, key=lambda x: hash(x) % 10))
        add_exercise(CategoryEnum.BUILD_WORD, c7, l7, f"{scrambled} → __________", {"scrambled_word": scrambled, "type": "build_word"}, a, i)

    # 8) NUMBER_TO_WORD – numra kompleks
    numw_exercises = [
        ("125", "njëqind e njëzet e pesë"), ("250", "dyqind e pesëdhjetë"), ("375", "treqind e shtatëdhjetë e pesë"),
        ("500", "pesëqind"), ("750", "shtatëqind e pesëdhjetë"), ("1000", "njëmijë"),
    ]
    for i, (n, w) in enumerate(numw_exercises, start=1):
        add_exercise(CategoryEnum.NUMBER_TO_WORD, c8, l8, f"{n} → _____", {"number": n, "type": "number_to_word"}, w, i)

    # 9) PHRASES – koncepte akademike komplekse
    phrase_exercises = [
        ("Sistemi kompleks që organizon dhe kontrollon një shtet.", "qeveria"),
        ("Ndjenjë e thellë respekti dhe admirimi për dikë.", "nderim"),
        ("Procesi i vazhdueshëm i mësimit dhe zhvillimit.", "edukim"),
        ("Tërësia e ligjeve që rregullojnë një shoqëri.", "legjislacion"),
    ]
    for i, (desc, word) in enumerate(phrase_exercises, start=1):
        add_exercise(CategoryEnum.PHRASES, c9, l9, f"Përshkrimi: {desc}\nFjala:", {"description": desc, "type": "phrase"}, word, i)

    # 10) SPELLING_PUNCTUATION – fjali komplekse akademike
    spellp_exercises = [
        ("demokracia moderne kërkon pjesëmarrje aktive", "Demokracia moderne kërkon pjesëmarrje aktive."),
        ("edukimi cilësor është themeli i zhvillimit", "Edukimi cilësor është themeli i zhvillimit."),
        ("kultura kombëtare pasqyron traditat tona", "Kultura kombëtare pasqyron traditat tona."),
        ("teknologjia transformon komunikimin modern", "Teknologjia transformon komunikimin modern."),
    ]
    for i, (inc, corr) in enumerate(spellp_exercises, start=1):
        add_exercise(CategoryEnum.SPELLING_PUNCTUATION, c10, l10, f"{inc}\nSaktë:", {"incorrect": inc, "type": "spelling_punctuation"}, corr, i)

    # 11) ABSTRACT_CONCRETE – koncepte komplekse akademike
    abscon_exercises = [
        ("demokraci / qeveri / parlament → parlament (konkret)", "parlament", "concrete"),
        ("kulturë / traditë / muze → muze (konkret)", "muze", "concrete"),
        ("edukim / shkollë / universitet → universitet (konkret)", "universitet", "concrete"),
        ("demokraci / qeveri / ligj → demokraci (abstrakte)", "demokraci", "abstract"),
        ("kulturë / traditë / vlerë → vlerë (abstrakte)", "vlerë", "abstract"),
        ("edukim / shkollë / njohuri → njohuri (abstrakte)", "njohuri", "abstract"),
    ]
    for i, (p, a, t) in enumerate(abscon_exercises, start=1):
        base = p.split("→")[0].strip()
        add_exercise(CategoryEnum.ABSTRACT_CONCRETE, c11, l11, f"Zgjidh fjalën e duhur: {base}", {"choices": [], "type": t}, a, i)

    # 12) BUILD_SENTENCE – fjali komplekse akademike
    builds_exercises = [
        (["Demokracia", "moderne", "kërkon", "pjesëmarrje", "aktive", "nga", "qytetarët", "në", "proceset", "vendimmarrëse"], "Demokracia moderne kërkon pjesëmarrje aktive nga qytetarët në proceset vendimmarrëse."),
        (["Edukimi", "cilësor", "është", "themeli", "i", "zhvillimit", "personal", "dhe", "shoqëror"], "Edukimi cilësor është themeli i zhvillimit personal dhe shoqëror."),
        (["Kultura", "kombëtare", "pasqyron", "traditat", "e", "lashta", "dhe", "vlerat", "e", "popullit"], "Kultura kombëtare pasqyron traditat e lashta dhe vlerat e popullit."),
    ]
    for i, (words, sentence) in enumerate(builds_exercises, start=1):
        add_exercise(CategoryEnum.BUILD_SENTENCE, c12, l12, f"Fjalë: {words}\nFjalia: ____________________________", {"words": words, "type": "build_sentence"}, sentence, i)

    db.commit()
    exercise_count = db.query(Exercise).filter(Exercise.course_id.in_([c.id for c in courses])).count()
    print(f"Successfully seeded {len(courses)} courses and {exercise_count} exercises for seventh class level")
    return seventh_class.id


def seed_eighth_class_exercises(db: Session):
    """Seed the eighth class with the same 12-category structure, most advanced content"""

    # Clear existing data for Class 8
    class_ids_to_clear = db.query(Course.id).filter(Course.name.like("Klasa 8%"))
    db.query(Exercise).filter(Exercise.course_id.in_(class_ids_to_clear)).delete()
    db.query(Level).filter(Level.course_id.in_(class_ids_to_clear)).delete()
    db.query(Course).filter(Course.name.like("Klasa 8%")).delete()

    # Create Class 8
    eighth_class = Course(
        name="Klasa 8",
        description="Klasa e tetë (13-14 vjeç) me 12 kategori ushtrimesh më të avancuara dhe më komplekse",
        order_index=8,
        category=CategoryEnum.VOCABULARY,
        required_score=80,
        enabled=True,
    )
    db.add(eighth_class)
    db.flush()

    # Create levels 1..12
    level_1 = Level(
        course_id=eighth_class.id,
        name="Niveli 1",
        description="Ushtrime më të avancuara për klasën e tetë",
        order_index=1,
        required_score=0,
        enabled=True,
    )
    db.add(level_1)
    db.flush()

    extra_levels = []
    for idx in range(2, 13):
        extra_levels.append(
            Level(
                course_id=eighth_class.id,
                name=f"Niveli {idx}",
                description=f"Niveli {idx} për Klasa 8",
                order_index=idx,
                required_score=80 if idx > 1 else 0,
                enabled=True,
            )
        )
    for lvl in extra_levels:
        db.add(lvl)
    db.flush()

    # Create 12 courses (categories) under Class 8
    courses = []
    course_defs = [
        ("Niveli 1", CategoryEnum.LISTEN_WRITE),
        ("Niveli 2", CategoryEnum.WORD_FROM_DESCRIPTION),
        ("Niveli 3", CategoryEnum.SYNONYMS_ANTONYMS),
        ("Niveli 4", CategoryEnum.ALBANIAN_OR_LOANWORD),
        ("Niveli 5", CategoryEnum.MISSING_LETTER),
        ("Niveli 6", CategoryEnum.WRONG_LETTER),
        ("Niveli 7", CategoryEnum.BUILD_WORD),
        ("Niveli 8", CategoryEnum.NUMBER_TO_WORD),
        ("Niveli 9", CategoryEnum.PHRASES),
        ("Niveli 10", CategoryEnum.SPELLING_PUNCTUATION),
        ("Niveli 11", CategoryEnum.ABSTRACT_CONCRETE),
        ("Niveli 12", CategoryEnum.BUILD_SENTENCE),
    ]
    for idx, (name, cat) in enumerate(course_defs, start=1):
        c = Course(
            name=name,
            description=name,
            order_index=idx,
            category=cat,
            required_score=0,
            enabled=True,
            parent_class_id=eighth_class.id,
        )
        db.add(c)
        courses.append(c)
    db.flush()

    # Map level 1 to all courses
    level_by_course = {}
    for c in courses:
        lvl = Level(
            course_id=c.id,
            name="Niveli 1",
            description="Ushtrime më të avancuara",
            order_index=1,
            required_score=0,
            enabled=True,
        )
        db.add(lvl)
        level_by_course[c.id] = lvl
    db.flush()

    def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
        ex = Exercise(
            category=cat,
            course_id=course.id,
            level_id=level.id,
            prompt=prompt,
            data=json.dumps(data_obj),
            answer=answer,
            points=1,
            order_index=idx,
        )
        db.add(ex)

    (
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12
    ) = courses
    l1 = level_by_course[c1.id]
    l2 = level_by_course[c2.id]
    l3 = level_by_course[c3.id]
    l4 = level_by_course[c4.id]
    l5 = level_by_course[c5.id]
    l6 = level_by_course[c6.id]
    l7 = level_by_course[c7.id]
    l8 = level_by_course[c8.id]
    l9 = level_by_course[c9.id]
    l10 = level_by_course[c10.id]
    l11 = level_by_course[c11.id]
    l12 = level_by_course[c12.id]

    # 1) LISTEN_WRITE – paragrafë kompleks dhe argumentative
    dictation_exercises = [
        ("Shkencëtarët modernë dhe inovativë studiojnë natyrën në thellësi maksimale për të kuptuar ligjet e saj themelore, për të zbuluar sekrete të reja dhe për të transformuar botën tonë në mënyrë pozitive.", "Shkencëtarët modernë dhe inovativë studiojnë natyrën në thellësi maksimale për të kuptuar ligjet e saj themelore, për të zbuluar sekrete të reja dhe për të transformuar botën tonë në mënyrë pozitive."),
        ("Demokracia moderne dhe e zhvilluar kërkon pjesëmarrje aktive, të informuar dhe të përgjegjshme nga të gjithë qytetarët në proceset vendimmarrëse që ndikojnë në të ardhmen e shoqërisë dhe të komunitetit tonë.", "Demokracia moderne dhe e zhvilluar kërkon pjesëmarrje aktive, të informuar dhe të përgjegjshme nga të gjithë qytetarët në proceset vendimmarrëse që ndikojnë në të ardhmen e shoqërisë dhe të komunitetit tonë."),
        ("Kultura jonë kombëtare e pasur dhe e larmishme pasqyron traditat e lashta, vlerat e popullit tonë dhe identitetin tonë unik që kanë kaluar brez pas brezi dhe që na bëjnë të dallueshëm në botë.", "Kultura jonë kombëtare e pasur dhe e larmishme pasqyron traditat e lashta, vlerat e popullit tonë dhe identitetin tonë unik që kanë kaluar brez pas brezi dhe që na bëjnë të dallueshëm në botë."),
        ("Teknologjia moderne dhe e avancuar transformon mënyrën se si komunikojmë, punojmë, mësojmë dhe jetojmë në shoqërinë e sotme, duke krijuar mundësi të reja, sfida të reja dhe perspektiva të reja për të ardhmen.", "Teknologjia moderne dhe e avancuar transformon mënyrën se si komunikojmë, punojmë, mësojmë dhe jetojmë në shoqërinë e sotme, duke krijuar mundësi të reja, sfida të reja dhe perspektiva të reja për të ardhmen."),
        ("Edukimi cilësor dhe i plotë është themeli i zhvillimit personal, profesional dhe shoqëror për të gjithë brezat, duke siguruar një të ardhme më të mirë, më të drejtë dhe më të qëndrueshme për të gjithë.", "Edukimi cilësor dhe i plotë është themeli i zhvillimit personal, profesional dhe shoqëror për të gjithë brezat, duke siguruar një të ardhme më të mirë, më të drejtë dhe më të qëndrueshme për të gjithë."),
    ]
    for i, (p, a) in enumerate(dictation_exercises, start=1):
        add_exercise(CategoryEnum.LISTEN_WRITE, c1, l1, "Shkruaj fjalinë që dëgjon.", {"audio_word": p, "type": "dictation"}, a, i)

    # 2) WORD_FROM_DESCRIPTION – koncepte akademike dhe filozofike komplekse
    desc_exercises = [
        ("Sistemi kompleks, i organizuar dhe i sofistikuar që administron, kontrollon dhe drejton një shtet ose organizatë më të madhe me efikasitet maksimal.", "qeveria", ["qeveria", "shkolla", "familja", "biblioteka", "spitali"]),
        ("Ndjenjë e thellë, e sinqertë dhe e vazhdueshme respekti, admirimi dhe vlerësimi për dikë ose diçka që konsiderohet e rëndësishme dhe e vlefshme.", "nderim", ["nderim", "gëzim", "frikë", "lumturi", "trishtim"]),
        ("Procesi i vazhdueshëm, i planifikuar dhe i strukturuar i mësimit, zhvillimit dhe përmirësimit të njohurive, aftësive dhe kompetencave për të arritur potencialin maksimal.", "edukim", ["edukim", "lojë", "pushim", "udhëtim", "vizitë"]),
        ("Tërësia e ligjeve, rregullave, normave dhe procedurave që rregullojnë, organizojnë dhe kontrollojnë një shoqëri ose sistem në mënyrë sistematike dhe të drejtë.", "legjislacion", ["legjislacion", "libër", "letër", "fletore", "revistë"]),
        ("Ndjenjë e përbashkët e thellë dhe e vazhdueshme e identitetit, përkatësisë dhe mbështetjes reciproke në një grup, komunitet ose shoqëri që bashkon njerëzit.", "solidaritet", ["solidaritet", "lojë", "kohë", "vend", "shtëpi"]),
    ]
    for i, (desc, word, choices) in enumerate(desc_exercises, start=1):
        add_exercise(CategoryEnum.WORD_FROM_DESCRIPTION, c2, l2, desc, {"choices": choices, "type": "multiple_choice"}, word, i)

    # 3) SYNONYMS_ANTONYMS – fjalë akademike komplekse
    syn_ant_exercises = [
        ("i analitik → _______", "i logjik", "synonym"),
        ("i inovativ → _______", "i konvencional", "antonym"),
        ("i kritik → _______", "i pranueshëm", "antonym"),
        ("i objektiv → _______", "i subjektiv", "antonym"),
        ("i racional → _______", "i emocional", "antonym"),
        ("i sistematik → _______", "i çrregullt", "antonym"),
        ("i teoretik → _______", "i praktik", "antonym"),
        ("i universal → _______", "i lokal", "antonym"),
        ("i sofistikuar → _______", "i thjeshtë", "antonym"),
        ("i kompleks → _______", "i thjeshtë", "antonym"),
    ]
    for i, (p, a, t) in enumerate(syn_ant_exercises, start=1):
        add_exercise(CategoryEnum.SYNONYMS_ANTONYMS, c3, l3, p, {"choices": [], "type": t}, a, i)

    # 4) ALBANIAN_OR_LOANWORD – fjalë akademike dhe teknike komplekse
    al_lo_exercises = [
        ("demokraci", "Huazim"), ("kulturë", "Shqip"), ("teknologji", "Huazim"),
        ("traditë", "Shqip"), ("komunikim", "Shqip"), ("sistem", "Huazim"),
        ("edukim", "Shqip"), ("organizim", "Huazim"), ("transformim", "Huazim"),
        ("identitet", "Huazim"), ("legjislacion", "Huazim"), ("solidaritet", "Huazim"),
    ]
    for i, (w, a) in enumerate(al_lo_exercises, start=1):
        add_exercise(CategoryEnum.ALBANIAN_OR_LOANWORD, c4, l4, f"'{w}' është:", {"choices": ["Shqip", "Huazim"], "type": "albanian_loanword"}, a, i)

    # 5) MISSING_LETTER – fjalë komplekse akademike
    miss_exercises = [
        ("demokr_ci", "demokraci"), ("kult_rë", "kulturë"), ("teknol_gji", "teknologji"),
        ("trad_të", "traditë"), ("komun_kim", "komunikim"), ("s_stem", "sistem"),
        ("eduk_m", "edukim"), ("organ_zim", "organizim"), ("transform_m", "transformim"),
    ]
    for i, (w, a) in enumerate(miss_exercises, start=1):
        add_exercise(CategoryEnum.MISSING_LETTER, c5, l5, f"Shkruaj fjalën: {w}", {"word_with_gap": w, "type": "missing_letter"}, a, i)

    # 6) WRONG_LETTER – fjali komplekse akademike
    wrong_exercises = [
        ("Demokracia moderne kërkon pjesmarrje aktive nga qytetarët.", "pjesëmarrje"),
        ("Edukimi cilësor është themeli i zhvillimit shoqëror.", "zhvillimit"),
        ("Kultura kombëtare pasqyron traditat dhe vlerat tona.", "traditat"),
        ("Teknologjia transformon mënyrën e komunikimit modern.", "komunikimit"),
    ]
    for i, (s, a) in enumerate(wrong_exercises, start=1):
        add_exercise(CategoryEnum.WRONG_LETTER, c6, l6, f"{s}\nFjala e saktë: __________", {"sentence": s, "type": "wrong_letter"}, a, i)

    # 7) BUILD_WORD – fjalë komplekse akademike
    buildw_exercises = [
        ("demokraci", "demokraci"), ("kulturë", "kulturë"), ("teknologji", "teknologji"),
        ("traditë", "traditë"), ("komunikim", "komunikim"), ("sistem", "sistem"),
        ("edukim", "edukim"), ("organizim", "organizim"), ("transformim", "transformim"),
    ]
    for i, (w, a) in enumerate(buildw_exercises, start=1):
        scrambled = ''.join(sorted(w, key=lambda x: hash(x) % 10))
        add_exercise(CategoryEnum.BUILD_WORD, c7, l7, f"{scrambled} → __________", {"scrambled_word": scrambled, "type": "build_word"}, a, i)

    # 8) NUMBER_TO_WORD – numra kompleks
    numw_exercises = [
        ("1250", "njëmijë e dyqind e pesëdhjetë"), ("2500", "dymijë e pesëqind"), ("3750", "tremijë e shtatëqind e pesëdhjetë"),
        ("5000", "pesëmijë"), ("7500", "shtatëmijë e pesëqind"), ("10000", "dhjetëmijë"),
    ]
    for i, (n, w) in enumerate(numw_exercises, start=1):
        add_exercise(CategoryEnum.NUMBER_TO_WORD, c8, l8, f"{n} → _____", {"number": n, "type": "number_to_word"}, w, i)

    # 9) PHRASES – koncepte akademike komplekse
    phrase_exercises = [
        ("Sistemi kompleks që organizon dhe kontrollon një shtet.", "qeveria"),
        ("Ndjenjë e thellë respekti dhe admirimi për dikë.", "nderim"),
        ("Procesi i vazhdueshëm i mësimit dhe zhvillimit.", "edukim"),
        ("Tërësia e ligjeve që rregullojnë një shoqëri.", "legjislacion"),
    ]
    for i, (desc, word) in enumerate(phrase_exercises, start=1):
        add_exercise(CategoryEnum.PHRASES, c9, l9, f"Përshkrimi: {desc}\nFjala:", {"description": desc, "type": "phrase"}, word, i)

    # 10) SPELLING_PUNCTUATION – fjali komplekse akademike
    spellp_exercises = [
        ("demokracia moderne kërkon pjesëmarrje aktive", "Demokracia moderne kërkon pjesëmarrje aktive."),
        ("edukimi cilësor është themeli i zhvillimit", "Edukimi cilësor është themeli i zhvillimit."),
        ("kultura kombëtare pasqyron traditat tona", "Kultura kombëtare pasqyron traditat tona."),
        ("teknologjia transformon komunikimin modern", "Teknologjia transformon komunikimin modern."),
    ]
    for i, (inc, corr) in enumerate(spellp_exercises, start=1):
        add_exercise(CategoryEnum.SPELLING_PUNCTUATION, c10, l10, f"{inc}\nSaktë:", {"incorrect": inc, "type": "spelling_punctuation"}, corr, i)

    # 11) ABSTRACT_CONCRETE – koncepte komplekse akademike
    abscon_exercises = [
        ("demokraci / qeveri / parlament → parlament (konkret)", "parlament", "concrete"),
        ("kulturë / traditë / muze → muze (konkret)", "muze", "concrete"),
        ("edukim / shkollë / universitet → universitet (konkret)", "universitet", "concrete"),
        ("demokraci / qeveri / ligj → demokraci (abstrakte)", "demokraci", "abstract"),
        ("kulturë / traditë / vlerë → vlerë (abstrakte)", "vlerë", "abstract"),
        ("edukim / shkollë / njohuri → njohuri (abstrakte)", "njohuri", "abstract"),
    ]
    for i, (p, a, t) in enumerate(abscon_exercises, start=1):
        base = p.split("→")[0].strip()
        add_exercise(CategoryEnum.ABSTRACT_CONCRETE, c11, l11, f"Zgjidh fjalën e duhur: {base}", {"choices": [], "type": t}, a, i)

    # 12) BUILD_SENTENCE – fjali komplekse akademike
    builds_exercises = [
        (["Demokracia", "moderne", "kërkon", "pjesëmarrje", "aktive", "nga", "qytetarët", "në", "proceset", "vendimmarrëse"], "Demokracia moderne kërkon pjesëmarrje aktive nga qytetarët në proceset vendimmarrëse."),
        (["Edukimi", "cilësor", "është", "themeli", "i", "zhvillimit", "personal", "dhe", "shoqëror"], "Edukimi cilësor është themeli i zhvillimit personal dhe shoqëror."),
        (["Kultura", "kombëtare", "pasqyron", "traditat", "e", "lashta", "dhe", "vlerat", "e", "popullit"], "Kultura kombëtare pasqyron traditat e lashta dhe vlerat e popullit."),
    ]
    for i, (words, sentence) in enumerate(builds_exercises, start=1):
        add_exercise(CategoryEnum.BUILD_SENTENCE, c12, l12, f"Fjalë: {words}\nFjalia: ____________________________", {"words": words, "type": "build_sentence"}, sentence, i)

    db.commit()
    exercise_count = db.query(Exercise).filter(Exercise.course_id.in_([c.id for c in courses])).count()
    print(f"Successfully seeded {len(courses)} courses and {exercise_count} exercises for eighth class level")
    return eighth_class.id
