"""
Advanced AI Chatbot with:
- LLM Integration (OpenAI/Anthropic with local fallback)
- RAG (Retrieval Augmented Generation) from corpus
- Conversation history & session management
- Real-time exercise generation
- Voice input/output support
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import uuid
import time
from ..database import get_db
from .. import models

router = APIRouter()

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

# Try to import LLM libraries
try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        OPENAI_AVAILABLE = True
    else:
        OPENAI_AVAILABLE = False
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    if ANTHROPIC_API_KEY:
        ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        ANTHROPIC_AVAILABLE = True
    else:
        ANTHROPIC_AVAILABLE = False
except ImportError:
    ANTHROPIC_AVAILABLE = False


# ============================================================================
# SCHEMAS
# ============================================================================

class AdvancedChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_token: Optional[str] = None
    use_llm: bool = False
    generate_exercise: bool = False
    voice_input: bool = False
    context: Optional[Dict[str, Any]] = None  # Current page context (exercise, level, etc.)


class AdvancedChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    response: str
    session_token: str
    suggestions: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None
    generated_exercise: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    model_used: str
    timestamp: str
    context_aware: bool = False  # If response used context
    
    
class MessageFeedback(BaseModel):
    message_id: int
    rating: int  # 1-5
    feedback_text: Optional[str] = None
    

class VoiceRequest(BaseModel):
    text: str
    voice: str = "anila"  # anila or ilir
    language: str = "sq"


# ============================================================================
# RAG SYSTEM
# ============================================================================

def _search_corpus(query: str, db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """
    RAG: Search through exercises AND corpus documents for relevant content.
    """
    query_lower = query.lower()
    keywords = query_lower.split()
    results = []

    exercises = db.query(models.Exercise).filter(models.Exercise.enabled == True).limit(1000).all()
    for ex in exercises:
        score = 0
        prompt_lower = (ex.prompt or "").lower()
        answer_lower = (ex.answer or "").lower()
        for keyword in keywords:
            if keyword in prompt_lower:
                score += 2
            if keyword in answer_lower:
                score += 1
        if score > 0:
            results.append({
                "source": "exercise",
                "exercise_id": ex.id,
                "prompt": ex.prompt,
                "answer": ex.answer,
                "category": ex.category.value if ex.category else None,
                "score": score
            })

    corpus_docs = db.query(models.CorpusDocument).filter(
        models.CorpusDocument.is_validated == True
    ).limit(500).all()
    for doc in corpus_docs:
        score = 0
        title_lower = (doc.title or "").lower()
        content_lower = (doc.content or "")[:2000].lower()
        for keyword in keywords:
            if keyword in title_lower:
                score += 3
            if keyword in content_lower:
                score += 2
        if score > 0:
            results.append({
                "source": "corpus",
                "doc_id": doc.id,
                "title": doc.title,
                "content_preview": (doc.content or "")[:300],
                "author": doc.author,
                "genre": doc.genre.value if doc.genre else None,
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def _build_rag_context(query: str, db: Session) -> str:
    """Build context from exercises and corpus documents for RAG"""
    corpus_results = _search_corpus(query, db, limit=5)

    if not corpus_results:
        return ""

    context = "Bazuar në korpusin e platformës:\n\n"
    for idx, result in enumerate(corpus_results, 1):
        if result["source"] == "exercise":
            context += f"{idx}. [Ushtrim - {result['category']}]: {result['prompt'][:100]}...\n"
        else:
            context += f"{idx}. [Korpus - {result.get('genre', 'N/A')}]: {result['title'][:80]} — {result['content_preview'][:120]}...\n"

    return context


# ============================================================================
# LLM INTEGRATION
# ============================================================================

def _call_openai(messages: List[Dict[str, str]], temperature: float = 0.7) -> tuple[str, int]:
    """Call OpenAI API"""
    if not OPENAI_AVAILABLE:
        raise ValueError("OpenAI not available")
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=temperature,
        max_tokens=800
    )
    
    content = response.choices[0].message.content
    tokens = response.usage.total_tokens
    
    return content, tokens


def _call_anthropic(messages: List[Dict[str, str]], temperature: float = 0.7) -> tuple[str, int]:
    """Call Anthropic Claude API"""
    if not ANTHROPIC_AVAILABLE:
        raise ValueError("Anthropic not available")
    
    # Convert messages format
    system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
    user_messages = [m for m in messages if m["role"] != "system"]
    
    response = ANTHROPIC_CLIENT.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=800,
        temperature=temperature,
        system=system_msg or "Ti je një asistent mësimor për gjuhën shqipe.",
        messages=user_messages
    )
    
    content = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens
    
    return content, tokens


def _clean_llm_response(text: str) -> str:
    """Strip markdown artifacts from LLM responses so they look natural."""
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'^#{1,4}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\w*\n?', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_suggestions_from_response(response: str) -> List[str]:
    """Extract suggested questions from LLM response"""
    suggestions = []
    
    # Look for patterns like:
    # - "Mund të më pyesësh edhe:"
    # - "Pyetje të tjera:"
    # - Bullet points with questions
    
    import re
    
    # Find lines with question marks
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        # Remove bullet points and numbering
        line = re.sub(r'^[•\-\*]\s*', '', line)
        line = re.sub(r'^\d+\.\s*', '', line)
        
        if '?' in line and len(line) < 100 and len(line) > 10:
            suggestions.append(line)
    
    return suggestions[:3]  # Max 3 suggestions


def _build_context_aware_prompt(
    query: str,
    user_info: Optional[Dict[str, Any]],
    context: Optional[Dict[str, Any]]
) -> str:
    """Build context-aware addition to the query"""
    context_parts = []
    
    if context:
        if "current_level" in context:
            context_parts.append(f"Përdoruesi është aktualisht në Nivelin {context['current_level']}")
        
        if "current_exercise" in context:
            context_parts.append(f"Po punon në ushtrimin: {context['current_exercise']}")
        
        if "recent_mistakes" in context:
            mistakes = ", ".join(context['recent_mistakes'][:5])
            context_parts.append(f"Gabime të fundit: {mistakes}")
    
    if user_info:
        if user_info.get("progress_count", 0) > 0:
            context_parts.append(f"Ka plotësuar {user_info['progress_count']} nivele")
        
        if user_info.get("current_streak", 0) > 0:
            context_parts.append(f"Streak aktual: {user_info['current_streak']} ditë")
    
    if context_parts:
        return f"\n\n[Kontekst: {' | '.join(context_parts)}]"
    
    return ""


def _generate_llm_response(
    query: str,
    conversation_history: List[Dict[str, str]],
    rag_context: str,
    user_info: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> tuple[str, str, int, List[str]]:
    """
    Generate response using LLM with RAG context.
    Returns: (response, model_used, tokens_used, suggestions)
    """
    # Build system prompt
    system_prompt = """Ti je asistenti i platformes AlbLingo per mesimin e gjuhes shqipe.

Detyrat:
- Pergjigju ne shqip, me ton profesional dhe te qarte
- Jep keshilla per drejtshkrim dhe gramatike shqipe
- Ndihmo perdoruesit me platformen
- Ofro rekomandime bazuar ne progresin e tyre

Rregullat e formatimit (SHUME TE RENDESISHME):
- ASNJEHERE mos perdor ** per bold, * per italic, apo ## per tituj
- Mos perdor markdown fare ne pergjigje
- Shkruaj tekst te thjesht, te lexueshem
- Per lista perdor vetem: 1. 2. 3. ose - per pika
- Mos perdor emoji te tepruar, vetem aty ku eshte e nevojshme
- Pergjigjet duhet te duken profesionale, jo si te gjeneruara me AI
- Ne fund, sugjeroje 2-3 pyetje te lidhura qe perdoruesi mund te beje"""

    if rag_context:
        system_prompt += f"\n\n{rag_context}"
    
    if user_info:
        system_prompt += f"\n\nInformacion për përdoruesin: {json.dumps(user_info, ensure_ascii=False)}"
    
    # Add context awareness
    context_addition = _build_context_aware_prompt(query, user_info, context)
    query_with_context = query + context_addition
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-10:])  # Last 10 messages for context
    messages.append({"role": "user", "content": query_with_context})
    
    # Try OpenAI first, then Anthropic, then fallback
    try:
        if OPENAI_AVAILABLE:
            content, tokens = _call_openai(messages)
            content = _clean_llm_response(content)
            suggestions = _extract_suggestions_from_response(content)
            return content, "gpt-4-turbo", tokens, suggestions
    except Exception as e:
        print(f"[WARNING] OpenAI failed: {e}")
    
    try:
        if ANTHROPIC_AVAILABLE:
            content, tokens = _call_anthropic(messages)
            content = _clean_llm_response(content)
            suggestions = _extract_suggestions_from_response(content)
            return content, "claude-3-sonnet", tokens, suggestions
    except Exception as e:
        print(f"[WARNING] Anthropic failed: {e}")
    
    # Fallback to local logic
    from .chatbot import _get_contextual_response
    result = _get_contextual_response(query, user_info.get("user_id") if user_info else None, None)
    return _clean_llm_response(result["response"]), "local-advanced", 0, result.get("suggestions", [])


# ============================================================================
# EXERCISE GENERATION
# ============================================================================

def _generate_exercise_with_llm(
    topic: str,
    difficulty: str,
    user_mistakes: List[str],
    db: Session
) -> Optional[Dict[str, Any]]:
    """Generate a new exercise using LLM based on conversation context"""
    
    prompt = f"""Gjeneroje një ushtrim të ri për drejtshkrimin shqip:

Tema: {topic}
Vështirësia: {difficulty}
Gabimet e zakonshme të përdoruesit: {', '.join(user_mistakes) if user_mistakes else 'None'}

Formati i ushtrimittë jetë JSON me këto fusha:
{{
    "prompt": "Pyetja/Udhëzimi për ushtrimin",
    "answer": "Përgjigja e saktë",
    "hint": "Një këshillë ndihmëse",
    "category": "spelling"
}}

Sigurohu që ushtrimi të jetë i përshtatshëm për fëmijë dhe të fokusohet në gabimet e përmendura."""

    try:
        if OPENAI_AVAILABLE:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ti je një gjenerues ushtrimesh për mësimin e gjuhës shqipe."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            
            content = response.choices[0].message.content
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                exercise_data = json.loads(json_match.group())
                return exercise_data
    except Exception as e:
        print(f"[ERROR] Exercise generation failed: {e}")
    
    return None


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def _get_or_create_session(
    user_id: Optional[str],
    session_token: Optional[str],
    db: Session
) -> models.ChatSession:
    """Get existing session or create new one"""
    
    if session_token:
        session = db.query(models.ChatSession).filter(
            models.ChatSession.session_token == session_token,
            models.ChatSession.is_active == True
        ).first()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
            return session
    
    # Create new session
    session = models.ChatSession(
        user_id=user_id,
        session_token=str(uuid.uuid4()),
        started_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


def _get_conversation_history(session: models.ChatSession, db: Session) -> List[Dict[str, str]]:
    """Get conversation history for context"""
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


# ============================================================================
# ADVANCED CHATBOT ENDPOINT
# ============================================================================

@router.post("/chatbot/advanced/ask", response_model=AdvancedChatResponse)
async def advanced_chatbot_ask(request: AdvancedChatRequest, db: Session = Depends(get_db)):
    """
    Advanced AI Chatbot with LLM, RAG, conversation history, and exercise generation.
    
    Features:
    - LLM integration (OpenAI/Anthropic) with local fallback
    - RAG from corpus
    - Persistent conversation history
    - Real-time exercise generation
    - Voice output (TTS)
    """
    start_time = time.time()
    
    if not request.message or len(request.message.strip()) < 2:
        raise HTTPException(status_code=400, detail="Mesazhi është shumë i shkurtër")
    
    # Get or create session
    session = _get_or_create_session(request.user_id, request.session_token, db)
    
    # Get conversation history
    conversation_history = _get_conversation_history(session, db)
    
    # Get user info if logged in
    user_info = None
    if request.user_id:
        user = db.query(models.User).filter(models.User.id == int(request.user_id)).first()
        if user:
            progress_count = db.query(models.Progress).filter(models.Progress.user_id == request.user_id).count()
            user_info = {
                "user_id": request.user_id,
                "username": user.username,
                "progress_count": progress_count,
                "current_streak": user.current_streak,
                "total_achievements": user.total_achievements
            }
    
    # RAG: Search corpus
    rag_context = _build_rag_context(request.message, db) if (request.use_llm or USE_LLM) else ""
    
    # Check if context-aware
    context_aware = request.context is not None and len(request.context) > 0
    
    # Generate response
    suggestions = []
    if request.use_llm or USE_LLM:
        response_text, model_used, tokens_used, suggestions = _generate_llm_response(
            query=request.message,
            conversation_history=conversation_history,
            rag_context=rag_context,
            user_info=user_info,
            context=request.context
        )
    else:
        from .chatbot import _get_contextual_response
        result = _get_contextual_response(request.message, request.user_id, db)
        response_text = _clean_llm_response(result["response"])
        model_used = "local-basic"
        tokens_used = 0
        suggestions = result.get("suggestions", [])
    
    # Save user message
    user_msg = models.ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message,
        created_at=datetime.utcnow()
    )
    db.add(user_msg)
    
    # Generate exercise if requested
    generated_exercise = None
    if request.generate_exercise:
        # Detect topic and user mistakes
        user_mistakes = []  # TODO: Extract from progress
        generated_exercise = _generate_exercise_with_llm(
            topic=request.message,
            difficulty="medium",
            user_mistakes=user_mistakes,
            db=db
        )
    
    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Save assistant message
    assistant_msg = models.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response_text,
        model_used=model_used,
        tokens_used=tokens_used if tokens_used > 0 else None,
        response_time_ms=response_time_ms,
        created_at=datetime.utcnow()
    )
    db.add(assistant_msg)
    
    # Update session
    session.total_messages += 2
    session.last_activity = datetime.utcnow()
    
    db.commit()
    db.refresh(assistant_msg)
    
    return AdvancedChatResponse(
        response=response_text,
        session_token=session.session_token,
        suggestions=suggestions if suggestions else None,
        related_topics=None,
        generated_exercise=generated_exercise,
        audio_url=None,  # Could be generated via /chatbot/advanced/tts
        model_used=model_used,
        timestamp=datetime.utcnow().isoformat() + "Z",
        context_aware=context_aware
    )


@router.get("/chatbot/advanced/history/{session_token}")
async def get_session_history(session_token: str, db: Session = Depends(get_db)):
    """Get conversation history for a session"""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_token == session_token
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    return {
        "session_token": session.session_token,
        "started_at": session.started_at.isoformat(),
        "total_messages": session.total_messages,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "model_used": msg.model_used,
                "created_at": msg.created_at.isoformat(),
                "tokens_used": msg.tokens_used,
                "response_time_ms": msg.response_time_ms
            }
            for msg in messages
        ]
    }


@router.delete("/chatbot/advanced/session/{session_token}")
async def clear_session(session_token: str, db: Session = Depends(get_db)):
    """Clear/delete a chat session and its messages"""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_token == session_token
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all messages
    db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).delete()
    
    # Mark session as inactive
    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": "Sesioni u fshi me sukses"}


@router.post("/chatbot/advanced/feedback")
async def submit_message_feedback(feedback: MessageFeedback, db: Session = Depends(get_db)):
    """Submit feedback for a message"""
    message = db.query(models.ChatMessage).filter(
        models.ChatMessage.id == feedback.message_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Store feedback in context_data (as JSON)
    import json
    context = json.loads(message.context_data) if message.context_data else {}
    context["feedback"] = {
        "rating": feedback.rating,
        "text": feedback.feedback_text,
        "timestamp": datetime.utcnow().isoformat()
    }
    message.context_data = json.dumps(context, ensure_ascii=False)
    db.commit()
    
    return {"status": "success", "message": "Feedback u ruajt"}


@router.post("/chatbot/advanced/tts")
async def text_to_speech(request: VoiceRequest):
    """Generate speech audio from text (Albanian TTS)"""
    try:
        # Try to use Azure Neural TTS if available
        import azure.cognitiveservices.speech as speechsdk
        
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "westeurope")
        
        if not speech_key:
            raise HTTPException(status_code=503, detail="TTS service not configured")
        
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        
        # Select voice (Anila or Ilir for Albanian)
        voice_map = {
            "anila": "sq-AL-AnilaNeural",
            "ilir": "sq-AL-IlirNeural"
        }
        speech_config.speech_synthesis_voice_name = voice_map.get(request.voice, "sq-AL-AnilaNeural")
        
        # Create output file
        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        audio_path = f"./audio_cache/{audio_filename}"
        os.makedirs("./audio_cache", exist_ok=True)
        
        audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # Synthesize
        result = synthesizer.speak_text_async(request.text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return {
                "status": "success",
                "audio_url": f"/audio/{audio_filename}",
                "voice": request.voice
            }
        else:
            raise HTTPException(status_code=500, detail="TTS synthesis failed")
            
    except ImportError:
        raise HTTPException(status_code=503, detail="Azure Speech SDK not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


@router.post("/chatbot/advanced/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech audio to text (STT)"""
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "westeurope")
        
        if not speech_key:
            raise HTTPException(status_code=503, detail="STT service not configured")
        
        # Save uploaded audio temporarily
        audio_filename = f"stt_{uuid.uuid4().hex[:8]}.wav"
        audio_path = f"./audio_cache/{audio_filename}"
        os.makedirs("./audio_cache", exist_ok=True)
        
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Configure speech recognition
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_recognition_language = "sq-AL"  # Albanian
        
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        # Recognize
        result = recognizer.recognize_once_async().get()
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {
                "status": "success",
                "text": result.text,
                "confidence": 1.0  # Azure doesn't provide confidence directly
            }
        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise HTTPException(status_code=400, detail="Nuk u njoh asnjë fjalë në audio")
        else:
            raise HTTPException(status_code=500, detail="STT recognition failed")
            
    except ImportError:
        raise HTTPException(status_code=503, detail="Azure Speech SDK not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@router.get("/chatbot/advanced/export/{session_token}")
async def export_conversation(session_token: str, format: str = "json", db: Session = Depends(get_db)):
    """Export conversation history as JSON or text"""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_token == session_token
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    if format == "json":
        export_data = {
            "session_token": session.session_token,
            "started_at": session.started_at.isoformat(),
            "total_messages": session.total_messages,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
        return export_data
    
    elif format == "txt":
        lines = [
            f"Konverzacion i ruajtur: {session.started_at.strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            ""
        ]
        
        for msg in messages:
            role_label = "TI" if msg.role == "user" else "AI CHATBOT"
            timestamp = msg.created_at.strftime('%H:%M:%S')
            lines.append(f"[{timestamp}] {role_label}:")
            lines.append(msg.content)
            lines.append("")
        
        text_content = "\n".join(lines)
        
        from fastapi.responses import Response
        return Response(
            content=text_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{session_token[:8]}.txt"
            }
        )
    
    else:
        raise HTTPException(status_code=400, detail="Format not supported. Use 'json' or 'txt'")


@router.get("/chatbot/advanced/stats")
async def get_chatbot_stats(db: Session = Depends(get_db)):
    """Get chatbot usage statistics"""
    total_sessions = db.query(models.ChatSession).count()
    active_sessions = db.query(models.ChatSession).filter(
        models.ChatSession.is_active == True
    ).count()
    total_messages = db.query(models.ChatMessage).count()
    
    # Average messages per session
    avg_messages = total_messages / total_sessions if total_sessions > 0 else 0
    
    # Model usage breakdown
    model_stats = {}
    messages_with_model = db.query(models.ChatMessage).filter(
        models.ChatMessage.model_used.isnot(None)
    ).all()
    
    for msg in messages_with_model:
        model = msg.model_used or "unknown"
        model_stats[model] = model_stats.get(model, 0) + 1
    
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "total_messages": total_messages,
        "avg_messages_per_session": round(avg_messages, 2),
        "model_usage": model_stats
    }
