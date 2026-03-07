"""
Gjenerues PDF për Korpusin e Gjuhës Shqipe
Krijon një dokument PDF të plotë me të gjitha klasat, nivelet dhe zgjidhjet
"""

import fitz  # PyMuPDF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Course, Level, Exercise, CategoryEnum
from datetime import datetime
import os

# Database configuration
DATABASE_URL = "sqlite:///./dev.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# PDF styling constants
TITLE_COLOR = (74/255, 159/255, 212/255)  # #4A9FD4
SUCCESS_COLOR = (91/255, 189/255, 108/255)  # #5BBD6C
ERROR_COLOR = (239/255, 100/255, 97/255)  # #EF6461
TEXT_COLOR = (0, 0, 0)
GRAY_COLOR = (0.5, 0.5, 0.5)

def add_header(page, text, y_pos, font_size=24, color=TITLE_COLOR):
    """Shto titull në faqe"""
    # Përdor fontin e thjeshtë pa fontname (përdor default)
    page.insert_text(
        (50, y_pos),
        text,
        fontsize=font_size,
        color=color
    )
    return y_pos + font_size + 10

def add_text(page, text, y_pos, font_size=12, color=TEXT_COLOR, indent=0, bold=False):
    """Shto tekst normal në faqe"""
    # Përdor fontin e thjeshtë pa fontname (përdor default)
    page.insert_text(
        (50 + indent, y_pos),
        text,
        fontsize=font_size,
        color=color
    )
    return y_pos + font_size + 5

def add_line(page, y_pos, color=GRAY_COLOR, width=1):
    """Shto vijë horizontale"""
    page.draw_line((50, y_pos), (545, y_pos), color=color, width=width)
    return y_pos + 10

def wrap_text(text, max_width=70):
    """Nda tekstin në rreshta të shkurtër"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def add_wrapped_text(page, text, y_pos, font_size=12, color=TEXT_COLOR, indent=0, bold=False):
    """Shto tekst me mbështjellje automatike"""
    lines = wrap_text(text, max_width=int(70 - indent/10))
    for line in lines:
        y_pos = add_text(page, line, y_pos, font_size, color, indent, bold)
    return y_pos

def generate_corpus_pdf():
    """Gjeneron PDF me të gjitha klasat dhe nivelet"""
    
    # Merr të dhënat nga database
    db = SessionLocal()
    
    try:
        # Merr të gjitha kurset parent (klasat)
        classes = db.query(Course).filter(
            Course.parent_class_id == None
        ).order_by(Course.order_index).all()
        
        if not classes:
            print("⚠️  Nuk u gjetën klasa në database!")
            return
        
        # Krijo PDF
        doc = fitz.open()
        
        # Faqja e parë - Cover Page
        page = doc.new_page(width=595, height=842)  # A4
        
        # Titulli kryesor
        y = 100
        y = add_header(page, "KORPUSI I GJUHËS SHQIPE", y, 28, TITLE_COLOR)
        y = add_header(page, "Klasa 1-8 • Nivelet dhe Zgjidhjet", y + 10, 16, GRAY_COLOR)
        
        # Statistika
        y += 40
        y = add_line(page, y, TITLE_COLOR, 2)
        y += 10
        
        total_courses = db.query(Course).filter(Course.parent_class_id != None).count()
        total_levels = db.query(Level).count()
        total_exercises = db.query(Exercise).count()
        
        y = add_text(page, f"📚 Total Kurse: {total_courses}", y, 14, SUCCESS_COLOR, bold=True)
        y = add_text(page, f"📊 Total Nivele: {total_levels}", y, 14, SUCCESS_COLOR, bold=True)
        y = add_text(page, f"✏️  Total Ushtrime: {total_exercises}", y, 14, SUCCESS_COLOR, bold=True)
        
        y += 20
        y = add_line(page, y, TITLE_COLOR, 2)
        
        # Data e gjenerimit
        y += 30
        y = add_text(page, f"Gjeneruar më: {datetime.now().strftime('%d %B %Y, %H:%M')}", y, 10, GRAY_COLOR)
        
        # Info footer
        page.insert_text(
            (50, 800),
            "AlbLingo - Platforma e Mesimit te Gjuhes Shqipe",
            fontsize=10,
            color=GRAY_COLOR
        )
        
        print(f"\n{'='*70}")
        print(f"🎨 Duke gjeneruar PDF për {len(classes)} klasa...")
        print(f"{'='*70}\n")
        
        # Për çdo klasë
        for class_idx, class_obj in enumerate(classes, 1):
            # Merr nivelet (kurset) për këtë klasë
            courses = db.query(Course).filter(
                Course.parent_class_id == class_obj.id
            ).order_by(Course.order_index).all()
            
            print(f"📚 Klasa {class_idx}: {class_obj.name} - {len(courses)} nivele")
            
            # Faqe e re për klasën
            page = doc.new_page(width=595, height=842)
            y = 50
            
            # Titulli i klasës
            y = add_header(page, f"KLASA {class_idx}", y, 26, TITLE_COLOR)
            y = add_text(page, class_obj.description or "", y, 12, GRAY_COLOR)
            y += 5
            y = add_line(page, y, TITLE_COLOR, 2)
            y += 15
            
            # Për çdo nivel në këtë klasë
            for course_idx, course in enumerate(courses, 1):
                # Check nëse duhet faqe e re
                if y > 750:
                    page = doc.new_page(width=595, height=842)
                    y = 50
                
                # Titulli i nivelit
                y = add_header(page, f"  {course.name}", y, 16, SUCCESS_COLOR)
                y = add_wrapped_text(page, course.description or "", y, 11, TEXT_COLOR, indent=20)
                y += 5
                
                # Merr nivelet për këtë kurs
                levels = db.query(Level).filter(
                    Level.course_id == course.id
                ).order_by(Level.order_index).all()
                
                if levels:
                    y = add_text(page, f"    📊 {len(levels)} nivele", y, 10, GRAY_COLOR, indent=20)
                    y += 5
                    
                    # Për çdo nivel
                    for level_idx, level in enumerate(levels, 1):
                        # Check nëse duhet faqe e re
                        if y > 780:
                            page = doc.new_page(width=595, height=842)
                            y = 50
                        
                        # Info e nivelit
                        level_title = f"      • Niveli {level_idx}"
                        if level.description:
                            level_title += f": {level.description}"
                        
                        y = add_wrapped_text(page, level_title, y, 10, TEXT_COLOR, indent=40)
                        
                        # Merr ushtrimin për këtë nivel
                        exercises = db.query(Exercise).filter(
                            Exercise.level_id == level.id
                        ).all()
                        
                        if exercises:
                            for ex_idx, exercise in enumerate(exercises, 1):
                                # Check nëse duhet faqe e re
                                if y > 770:
                                    page = doc.new_page(width=595, height=842)
                                    y = 50
                                
                                # Pyetja
                                question = exercise.prompt or "N/A"
                                y = add_wrapped_text(page, f"        ? {question}", y, 9, TEXT_COLOR, indent=60)
                                
                                # Zgjidhja e saktë
                                correct = exercise.answer
                                y = add_text(page, f"        => Zgjidhja: {correct}", y, 9, SUCCESS_COLOR, indent=60, bold=True)
                                
                                # Opsionet (nëse ka)
                                if exercise.data:
                                    try:
                                        import json
                                        data_obj = json.loads(exercise.data) if isinstance(exercise.data, str) else exercise.data
                                        
                                        # Provo të merrësh choices nga data
                                        choices = None
                                        if isinstance(data_obj, dict):
                                            choices = data_obj.get('choices') or data_obj.get('options')
                                        elif isinstance(data_obj, list):
                                            choices = data_obj
                                        
                                        if choices and len(choices) > 0:
                                            y = add_text(page, f"        Opsionet:", y, 8, GRAY_COLOR, indent=60)
                                            for choice_idx, choice in enumerate(choices, 1):
                                                is_correct = str(choice).strip() == str(correct).strip()
                                                symbol = "v" if is_correct else "-"
                                                choice_color = SUCCESS_COLOR if is_correct else TEXT_COLOR
                                                y = add_wrapped_text(page, f"           {symbol} {choice}", y, 8, choice_color, indent=70)
                                    except Exception as e:
                                        pass
                                
                                y += 3
                    
                    y += 5
                
                y += 10
            
            print(f"   ✅ Përfundoi Klasa {class_idx}")
        
        # Ruaj PDF-në
        output_path = "/Users/Apple/Desktop/Phd 08:02:2026/KORPUSI_SHQIP_FULL.pdf"
        page_count = doc.page_count  # Merr page count para se të mbyllësh
        doc.save(output_path)
        doc.close()
        
        file_size = os.path.getsize(output_path) / 1024  # KB
        
        print(f"\n{'='*70}")
        print(f"✅ PDF u gjenerua me sukses!")
        print(f"{'='*70}")
        print(f"📄 File: {output_path}")
        print(f"💾 Madhësia: {file_size:.2f} KB")
        print(f"📊 Statistika:")
        print(f"   • {len(classes)} Klasa")
        print(f"   • {total_courses} Kurse/Nivele")
        print(f"   • {total_levels} Nivele të Brendshme")
        print(f"   • {total_exercises} Ushtrime")
        print(f"   • {page_count} Faqe PDF")
        print(f"{'='*70}\n")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🚀 Duke filluar gjenerimin e PDF-së...\n")
    result = generate_corpus_pdf()
    
    if result:
        print("🎉 PDF është gati për përdorim!")
    else:
        print("⚠️  Ndodhi një gabim gjatë gjenerimit.")
