from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from passlib.context import CryptContext
from .seed_albanian_corpus import (
    seed_first_class_exercises,
    seed_second_class_exercises,
    seed_third_class_exercises,
    seed_fourth_class_exercises,
    seed_fifth_class_exercises,
    seed_sixth_class_exercises,
    seed_seventh_class_exercises,
    seed_eighth_class_exercises,
)

# Must match auth.py - use pbkdf2_sha256 for password verification to work
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter()


@router.post("/seed")
def seed_database():
    db = next(get_db())
    
    try:
        # Clear existing data
        db.query(models.Exercise).delete()
        db.query(models.Level).delete()
        db.query(models.Course).delete()
        db.query(models.User).delete()
        
        # Create top-level classes 2–9 (first class will be created by seed_first_class_exercises)
        classes = []
        for i in range(2, 10):
            class_data = {
                "name": f"Klasa {i}",
                "description": f"Kurrikula e plotë për klasën {i}",
                "order_index": i,
                "enabled": False,
                "parent_class_id": None
            }
            class_obj = models.Course(**class_data)
            db.add(class_obj)
            classes.append(class_obj)
        
        db.commit()
        
        # Seed the comprehensive Albanian corpus for first class
        try:
            seed_first_class_exercises(db)
            print("Albanian corpus seeded successfully!")
        except Exception as e:
            print(f"Warning: Could not seed Albanian corpus: {e}")
        
        # Create a test user
        hashed_password = pwd_context.hash("test123")
        test_user = models.User(
            username="testuser",
            email="test@example.com",
            age=10,
            password_hash=hashed_password
        )
        db.add(test_user)
        
        db.commit()
        
        return {"message": "Database seeded successfully!"}
        
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-albanian-corpus")
def seed_albanian_corpus():
    """Seed exactly 12 courses for Class 1 with the new structure"""
    db = next(get_db())
    
    try:
        # Clear existing exercises and levels for first class
        db.query(models.Exercise).filter(models.Exercise.course_id.in_(
            db.query(models.Course.id).filter(models.Course.name.like("Klasa e Parë%"))
        )).delete()
        
        db.query(models.Level).filter(models.Level.course_id.in_(
            db.query(models.Course.id).filter(models.Course.name.like("Klasa e Parë%"))
        )).delete()
        
        db.query(models.Course).filter(models.Course.name.like("Klasa e Parë%")).delete()
        
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


@router.post("/cleanup-klasa1")
def cleanup_klasa1():
    db = next(get_db())
    try:
        # Find all top-level classes named 'Klasa 1'
        klasa1_list = db.query(models.Course).filter(
            models.Course.parent_class_id == None,
            models.Course.name.like("Klasa 1%")
        ).order_by(models.Course.id.asc()).all()
        
        if len(klasa1_list) <= 1:
            return {"deleted": 0, "kept_id": klasa1_list[0].id if klasa1_list else None}
        
        kept = klasa1_list[0]
        deleted_count = 0
        
        for duplicate in klasa1_list[1:]:
            # Delete child course data for this duplicate class
            child_course_ids = [c.id for c in db.query(models.Course).filter(models.Course.parent_class_id == duplicate.id).all()]
            if child_course_ids:
                db.query(models.Exercise).filter(models.Exercise.course_id.in_(child_course_ids)).delete(synchronize_session=False)
                db.query(models.Level).filter(models.Level.course_id.in_(child_course_ids)).delete(synchronize_session=False)
                db.query(models.Course).filter(models.Course.id.in_(child_course_ids)).delete(synchronize_session=False)
            # Delete the duplicate class itself
            db.query(models.Course).filter(models.Course.id == duplicate.id).delete(synchronize_session=False)
            deleted_count += 1
        
        db.commit()
        return {"deleted": deleted_count, "kept_id": kept.id}
    except Exception as e:
        db.rollback()
        raise e


@router.post("/normalize-klasa1")
def normalize_klasa1():
    db = next(get_db())
    try:
        # Find all top-level 'Klasa 1' entries
        klasa1_list = db.query(models.Course).filter(
            models.Course.parent_class_id == None,
            models.Course.name.like("Klasa 1%")
        ).order_by(models.Course.id.asc()).all()
        
        if not klasa1_list:
            return {"kept_id": None, "deleted": 0, "levels": 0}
        
        kept = klasa1_list[0]
        deleted = 0
        
        # Remove duplicate top-level classes and their children
        for duplicate in klasa1_list[1:]:
            child_course_ids = [c.id for c in db.query(models.Course).filter(models.Course.parent_class_id == duplicate.id).all()]
            if child_course_ids:
                db.query(models.Exercise).filter(models.Exercise.course_id.in_(child_course_ids)).delete(synchronize_session=False)
                db.query(models.Level).filter(models.Level.course_id.in_(child_course_ids)).delete(synchronize_session=False)
                db.query(models.Course).filter(models.Course.id.in_(child_course_ids)).delete(synchronize_session=False)
            db.query(models.Level).filter(models.Level.course_id == duplicate.id).delete(synchronize_session=False)
            db.query(models.Course).filter(models.Course.id == duplicate.id).delete(synchronize_session=False)
            deleted += 1
        
        # Ensure exactly 12 levels on kept class with order_index 1..12
        existing_levels = db.query(models.Level).filter(models.Level.course_id == kept.id).order_by(models.Level.order_index, models.Level.id).all()
        # Drop duplicate order_index (keep first), and map present indexes
        seen = set()
        for lvl in existing_levels:
            if lvl.order_index in seen or lvl.order_index is None or lvl.order_index < 1 or lvl.order_index > 12:
                db.delete(lvl)
            else:
                seen.add(lvl.order_index)
        
        # Create missing levels 1..12
        created = 0
        for idx in range(1, 13):
            if idx not in seen:
                level = models.Level(
                    course_id=kept.id,
                    name=f"Niveli {idx}",
                    description=f"Niveli {idx} për Klasa 1",
                    order_index=idx,
                    required_score=0 if idx == 1 else 80,
                    enabled=True
                )
                db.add(level)
                created += 1
        
        db.commit()
        levels = db.query(models.Level).filter(models.Level.course_id == kept.id).count()
        return {"kept_id": kept.id, "deleted": deleted, "levels": levels, "created_levels": created}
    except Exception as e:
        db.rollback()
        raise e


@router.post("/klasa1-levels-only")
def klasa1_levels_only():
    db = next(get_db())
    try:
        # Find the top-level Klasa 1
        klasa1 = db.query(models.Course).filter(
            models.Course.parent_class_id == None,
            models.Course.name.like("Klasa 1%")
        ).order_by(models.Course.id.asc()).first()
        if not klasa1:
            return {"updated": False, "reason": "Klasa 1 not found"}

        # Delete all child courses (categories) under Klasa 1
        child_course_ids = [c.id for c in db.query(models.Course).filter(models.Course.parent_class_id == klasa1.id).all()]
        if child_course_ids:
            db.query(models.Exercise).filter(models.Exercise.course_id.in_(child_course_ids)).delete(synchronize_session=False)
            db.query(models.Level).filter(models.Level.course_id.in_(child_course_ids)).delete(synchronize_session=False)
            db.query(models.Course).filter(models.Course.id.in_(child_course_ids)).delete(synchronize_session=False)

        # Ensure exactly 12 levels on Klasa 1
        existing_levels = db.query(models.Level).filter(models.Level.course_id == klasa1.id).order_by(models.Level.order_index, models.Level.id).all()
        seen = set()
        for lvl in existing_levels:
            if lvl.order_index in seen or lvl.order_index is None or lvl.order_index < 1 or lvl.order_index > 12:
                db.delete(lvl)
            else:
                seen.add(lvl.order_index)
        created = 0
        for idx in range(1, 13):
            if idx not in seen:
                level = models.Level(
                    course_id=klasa1.id,
                    name=f"Niveli {idx}",
                    description=f"Niveli {idx} për Klasa 1",
                    order_index=idx,
                    required_score=0 if idx == 1 else 80,
                    enabled=True
                )
                db.add(level)
                created += 1

        db.commit()
        levels = db.query(models.Level).filter(models.Level.course_id == klasa1.id).count()
        return {"updated": True, "kept_id": klasa1.id, "levels": levels, "created_levels": created, "removed_child_courses": len(child_course_ids)}
    except Exception as e:
        db.rollback()
        raise e


@router.post("/klasa1-add-courses-with-exercises")
def klasa1_add_courses_with_exercises():
    db = next(get_db())
    try:
        # Find Klasa 1 (top-level)
        klasa1 = db.query(models.Course).filter(
            models.Course.parent_class_id == None,
            models.Course.name.like("Klasa 1%")
        ).order_by(models.Course.id.asc()).first()
        if not klasa1:
            return {"created": False, "reason": "Klasa 1 not found"}

        # Remove existing child courses (and their data) under Klasa 1
        child_course_ids = [c.id for c in db.query(models.Course).filter(models.Course.parent_class_id == klasa1.id).all()]
        if child_course_ids:
            db.query(models.Exercise).filter(models.Exercise.course_id.in_(child_course_ids)).delete(synchronize_session=False)
            db.query(models.Level).filter(models.Level.course_id.in_(child_course_ids)).delete(synchronize_session=False)
            db.query(models.Course).filter(models.Course.id.in_(child_course_ids)).delete(synchronize_session=False)

        # Define the 12 courses (categories)
        from app.models import CategoryEnum
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

        new_courses = []
        for idx, (name, cat) in enumerate(course_defs, start=1):
            c = models.Course(
                name=name,
                description=name,
                order_index=idx,
                category=cat,
                required_score=0,
                enabled=True,
                parent_class_id=klasa1.id
            )
            db.add(c)
            new_courses.append(c)
        db.flush()

        # Create Niveli 1 per course
        level_by_course = {}
        for c in new_courses:
            lvl = models.Level(
                course_id=c.id,
                name="Niveli 1",
                description="Ushtrime bazike",
                order_index=1,
                required_score=0,
                enabled=True
            )
            db.add(lvl)
            level_by_course[c.id] = lvl
        db.flush()

        # Build exercises lists
        import json
        # 1. Diktim
        dictation = [("Zogu","zogu"),("Topi","topi"),("Dritë","dritë"),("Këngë","këngë"),("Shkollë","shkollë")]
        # 2. Përshkrimi
        desc = [
            ("Ata që kujdesen gjithmonë për ne.", "prindërit"),
            ("Personi që na mëson në shkollë.", "mësuesi"),
            ("Ngjyra e gjakut.", "e kuqe"),
            ("Na mbron nga shiu.", "çadra"),
            ("Ku ulemi kur jemi të lodhur.", "karrige"),
        ]
        desc_choices = ["prindërit","e kuqe","çadra","karrige","mësuesi"]
        # 3. Sinonime & Antonime
        syn_ant = [
            ("i mirë → _______", "i keq", "antonym"),
            ("i gjatë →_______", "i shkurtër", "antonym"),
            ("i lumtur → _______", "i trishtuar", "antonym"),
            ("i ftohtë →_______", "i nxehtë", "antonym"),
            ("i shpejtë → ______", "i ngadaltë", "antonym"),
            ("i lumtur → ______", "i gëzuar", "synonym"),
            ("i bukur → ______", "i hijshëm", "synonym"),
            ("i mençur → ______", "i zgjuar", "synonym"),
            ("i qetë → ______", "i heshtur", "synonym"),
            ("i guximshëm → ______", "trim", "synonym"),
        ]
        # 4. Shqipe apo Huazim
        al_lo = [("shmang","Shqip"),("evitoj","Huazim"),("libër","Shqip"),("kompjuter","Huazim"),("telefon","Huazim"),("ushqim","Shqip"),("celular","Huazim"),("shtëpi","Shqip"),("lojë","Shqip"),("internet","Huazim")]
        # 5. Shkronja që mungon
        miss = [("g_ysh","gjysh"),("fs_at","fshat"),("z_g","zog"),("l_ps","laps"),("b_ba","baba"),("_ënë","nënë"),("t_p","top"),("m_l","mal")]
        # 6. Shkronja e gabuar
        wrong = [
            ("Shoku im është i mrië.", "mirë"),("Babi bleu një makin.", "makinë"),("Rina ka një lapsi.", "laps"),("Qeni është kafshe.", "kafshë"),("Lumi është i madsh.", "madh"),("Ola ka një librr.", "libër"),("Hëna ndriçon natn.", "natën"),("Dielli ndriçon dotën.", "ditën"),("Yjet janë në qaell.", "qiell"),("Flutura fluturon lert.", "lart")
        ]
        # 7. Ndërto fjalën
        buildw = [("ėmep","pemë"),("lleid","diell"),("lėmu","lumë"),("zgo","zog"),("klaë","kalë"),("Pot","top"),("sapl","laps"),("edër","derë"),("bbaa","baba"),("nëën","nënë")]
        # 8. Numri me fjalë
        numw = [("0","zero"),("1","një"),("2","dy"),("3","tre"),("4","katër"),("5","pesë"),("6","gjashtë"),("7","shtatë"),("8","tetë"),("9","nëntë"),("10","dhjetë")]
        # 9. Shprehje
        phrases = [("Një njeri që jep mësim në një shkollë.","Mësuesi"),("Kafshë që jeton në ujë.","Peshku"),("Rritet në tokë, ka degë e gjethe.","Pema"),("Shkëlqen në qiell ditën.","Dielli")]
        # 10. Drejtshkrim & Pikësim
        spellp = [("babi bleu një top të kuq","Babi bleu një top të kuq."),("shiu bie në kopsht","Shiu bie në kopsht."),("hëna ndriçon natën","Hëna ndriçon natën."),("unë dua të shkoj në shkollë","Unë dua të shkoj në shkollë."),("gjyshi lexon përralla","Gjyshi lexon përralla.")]
        # 11. Abstrakte vs Konkrete
        abscon = [
            ("trishtim / libër / baba → libër (konkret)", "libër", "concrete"),
            ("gëzim / lumturi / derë → shishe (konkret)", "shishe", "concrete"),
            ("mendim / guxim / top → top (konkret)", "top", "concrete"),
            ("dashuri / frikë / karrige → pemë (konkret)", "pemë", "concrete"),
            ("frikë / laps / dritare → laps (konkret)", "laps", "concrete"),
            ("lumturi / top / laps → lumturi (abstrakte)", "lumturi", "abstract"),
            ("trishtim / libër / karrige → trishtim (abstrakte)", "trishtim", "abstract"),
            ("dashuri / shishe / derë → dashuri (abstrakte)", "dashuri", "abstract"),
            ("frikë / libër / pemë → frikë (abstrakte)", "frikë", "abstract"),
            ("mendim / top / dritare → mendim (abstrakte)", "mendim", "abstract"),
        ]
        # 12. Ndërto fjalinë
        builds = [
            (["laps","Rina","një","ka"], "Rina ka një laps."),
            (["kafshë","Qeni","është"], "Qeni është kafshë."),
            (["natën","ndriçon","Hëna"], "Hëna ndriçon natën."),
            (["top","Macja","me","luan"], "Macja luan me top."),
            (["Gjyshi","tregon","përralla"], "Gjyshi tregon përralla."),
        ]

        # Helper to add exercises
        def add_exercise(cat, course, level, prompt, data_obj, answer, idx):
            ex = models.Exercise(
                category=cat,
                course_id=course.id,
                level_id=level.id,
                prompt=prompt,
                data=json.dumps(data_obj),
                answer=answer,
                points=1,
                order_index=idx
            )
            db.add(ex)

        # Map order to specific courses
        c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12 = new_courses
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

        # 1) Diktim (hide the target word in prompt)
        for i,(p,a) in enumerate(dictation, start=1):
            add_exercise(CategoryEnum.LISTEN_WRITE, c1, l1, "Shkruaj fjalën që dëgjon.", {"audio_word": p, "type": "dictation"}, a, i)
        # 2) Përshkrimi
        for i,(p,a) in enumerate(desc, start=1):
            add_exercise(CategoryEnum.WORD_FROM_DESCRIPTION, c2, l2, p, {"choices": desc_choices, "type": "multiple_choice"}, a, i)
        # 3) Sinonime & Antonime
        for i,(p,a,t) in enumerate(syn_ant, start=1):
            add_exercise(CategoryEnum.SYNONYMS_ANTONYMS, c3, l3, p, {"choices": [], "type": t}, a, i)
        # 4) Shqipe apo Huazim?
        for i,(w,a) in enumerate(al_lo, start=1):
            add_exercise(CategoryEnum.ALBANIAN_OR_LOANWORD, c4, l4, f"'{w}' është:", {"choices": ["Shqip","Huazim"], "type": "albanian_loanword"}, a, i)
        # 5) Shkronja që mungon
        for i,(w,a) in enumerate(miss, start=1):
            add_exercise(CategoryEnum.MISSING_LETTER, c5, l5, f"Shkruaj fjalën: {w}", {"word_with_gap": w, "type": "missing_letter"}, a, i)
        # 6) Shkronja e gabuar
        for i,(s,a) in enumerate(wrong, start=1):
            add_exercise(CategoryEnum.WRONG_LETTER, c6, l6, f"{s}\nFjala e saktë: __________", {"sentence": s, "type": "wrong_letter"}, a, i)
        # 7) Ndërto fjalën
        for i,(w,a) in enumerate(buildw, start=1):
            add_exercise(CategoryEnum.BUILD_WORD, c7, l7, f"{w} → __________", {"scrambled_word": w, "type": "build_word"}, a, i)
        # 8) Numri me fjalë
        for i,(n,w) in enumerate(numw, start=1):
            add_exercise(CategoryEnum.NUMBER_TO_WORD, c8, l8, f"{n} → _____", {"number": n, "type": "number_to_word"}, w, i)
        # 9) Shprehje
        for i,(d,w) in enumerate(phrases, start=1):
            add_exercise(CategoryEnum.PHRASES, c9, l9, f"Përshkrimi: {d}\nFjala:", {"description": d, "type": "phrase"}, w, i)
        # 10) Drejtshkrim & Pikësim
        for i,(inc,corr) in enumerate(spellp, start=1):
            add_exercise(CategoryEnum.SPELLING_PUNCTUATION, c10, l10, f"{inc}\nSaktë:", {"incorrect": inc, "type": "spelling_punctuation"}, corr, i)
        # 11) Abstrakte vs Konkrete (remove explicit correct-answer hint from prompt)
        for i,(p,a,t) in enumerate(abscon, start=1):
            base = p.split("→")[0].strip()
            instruction = "Zgjidh fjalën e duhur: " + base
            add_exercise(CategoryEnum.ABSTRACT_CONCRETE, c11, l11, instruction, {"choices": [], "type": t}, a, i)
        # 12) Ndërto fjalinë
        for i,(words,sentence) in enumerate(builds, start=1):
            add_exercise(CategoryEnum.BUILD_SENTENCE, c12, l12, f"Fjalë: {words}\nFjalia: ____________________________", {"words": words, "type": "build_sentence"}, sentence, i)

        db.commit()
        return {"created": True, "courses": len(new_courses)}
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-class-2")
def seed_class_2():
    """Seed Class 2 with advanced exercises following Class 1 structure"""
    db = next(get_db())
    
    try:
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


@router.post("/seed-class-3")
def seed_class_3():
    """Seed Class 3 with advanced exercises following the same structure"""
    db = next(get_db())

    try:
        course_id = seed_third_class_exercises(db)
        return {
            "message": "Successfully seeded 12 courses for Class 3",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": 93,
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-class-4")
def seed_class_4():
    """Seed Class 4 with advanced exercises following the same structure"""
    db = next(get_db())

    try:
        course_id = seed_fourth_class_exercises(db)
        return {
            "message": "Successfully seeded 12 courses for Class 4",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": 60,
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-class-5")
def seed_class_5():
    """Seed Class 5 with very advanced exercises following the same structure"""
    db = next(get_db())

    try:
        course_id = seed_fifth_class_exercises(db)
        exercise_count = db.query(models.Exercise).filter(
            models.Exercise.course_id.in_(
                db.query(models.Course.id).filter(models.Course.parent_class_id == course_id)
            )
        ).count()
        return {
            "message": "Successfully seeded 12 courses for Class 5",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": exercise_count,
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-class-6")
def seed_class_6():
    """Seed Class 6 with extremely advanced exercises following the same structure"""
    db = next(get_db())

    try:
        course_id = seed_sixth_class_exercises(db)
        exercise_count = db.query(models.Exercise).filter(
            models.Exercise.course_id.in_(
                db.query(models.Course.id).filter(models.Course.parent_class_id == course_id)
            )
        ).count()
        return {
            "message": "Successfully seeded 12 courses for Class 6",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": exercise_count,
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-class-7")
def seed_class_7():
    """Seed Class 7 with highly advanced exercises following the same structure"""
    db = next(get_db())

    try:
        course_id = seed_seventh_class_exercises(db)
        exercise_count = db.query(models.Exercise).filter(
            models.Exercise.course_id.in_(
                db.query(models.Course.id).filter(models.Course.parent_class_id == course_id)
            )
        ).count()
        return {
            "message": "Successfully seeded 12 courses for Class 7",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": exercise_count,
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/seed-class-8")
def seed_class_8():
    """Seed Class 8 with most advanced exercises following the same structure"""
    db = next(get_db())

    try:
        course_id = seed_eighth_class_exercises(db)
        exercise_count = db.query(models.Exercise).filter(
            models.Exercise.course_id.in_(
                db.query(models.Course.id).filter(models.Course.parent_class_id == course_id)
            )
        ).count()
        return {
            "message": "Successfully seeded 12 courses for Class 8",
            "course_id": course_id,
            "courses_count": 12,
            "exercises_count": exercise_count,
        }
    except Exception as e:
        db.rollback()
        raise e


