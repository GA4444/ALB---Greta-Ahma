from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import os
import tempfile
import subprocess
from gtts import gTTS
import speech_recognition as sr
import uuid
import json
import time
import hashlib
from typing import Optional, Literal

router = APIRouter()

# Create temp directory for audio files
TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# Azure TTS (optional - falls back to gTTS if not configured)
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "westeurope")

try:
	import azure.cognitiveservices.speech as speechsdk
	AZURE_AVAILABLE = bool(AZURE_SPEECH_KEY)
except ImportError:
	AZURE_AVAILABLE = False
	speechsdk = None


def _generate_speech_azure(
	text: str,
	voice_name: str = "sq-AL-AnilaNeural",
	rate: str = "+0%",
	pitch: str = "+0Hz",
	output_path: str = None
) -> str:
	"""
	Generate speech using Azure TTS Neural Voices (Albanian).
	
	Available Albanian voices:
	- sq-AL-AnilaNeural (female, warm and clear)
	- sq-AL-IlirNeural (male, authoritative)
	
	Args:
		text: Text to convert to speech
		voice_name: Azure voice name
		rate: Speech rate (e.g., "+0%", "-10%", "+20%")
		pitch: Speech pitch (e.g., "+0Hz", "-2Hz", "+5Hz")
		output_path: Path to save audio file
	
	Returns:
		Path to generated audio file
	"""
	if not AZURE_AVAILABLE or not AZURE_SPEECH_KEY:
		raise ValueError("Azure TTS not configured")
	
	speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
	
	# Use SSML for advanced control
	ssml = f"""
	<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="sq-AL">
		<voice name="{voice_name}">
			<prosody rate="{rate}" pitch="{pitch}">
				{text}
			</prosody>
		</voice>
	</speak>
	"""
	
	if not output_path:
		output_path = os.path.join(TEMP_AUDIO_DIR, f"azure_tts_{uuid.uuid4()}.mp3")
	
	audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
	synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
	
	result = synthesizer.speak_ssml_async(ssml).get()
	
	if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
		raise Exception(f"Azure TTS failed: {result.reason}")
	
	return output_path


def _generate_speech_gtts(text: str, slow: bool = False, output_path: str = None) -> str:
	"""
	Generate speech using gTTS (fallback).
	
	Args:
		text: Text to convert to speech
		slow: Whether to use slow speech
		output_path: Path to save audio file
	
	Returns:
		Path to generated audio file
	"""
	if not output_path:
		output_path = os.path.join(TEMP_AUDIO_DIR, f"gtts_{uuid.uuid4()}.mp3")
	
	tts = gTTS(text=text, lang="sq", slow=slow)
	tts.save(output_path)
	
	return output_path


@router.post("/text-to-speech")
async def text_to_speech(
	text: str,
	language: str = "sq",
	voice: Literal["anila", "ilir", "default"] = "anila",
	rate: str = "+0%",
	pitch: str = "+0Hz",
	slow: bool = False
):
	"""
	Convert text to speech using Azure TTS (preferred) or gTTS (fallback).
	
	Albanian Voices (Azure):
	- anila: sq-AL-AnilaNeural (female, warm and clear - recommended for kids)
	- ilir: sq-AL-IlirNeural (male, authoritative)
	- default: falls back to gTTS
	
	Parameters:
	- rate: Speed adjustment (e.g., "+0%", "-10%" for slower, "+20%" for faster)
	- pitch: Pitch adjustment (e.g., "+0Hz", "-2Hz", "+5Hz")
	- slow: For gTTS fallback only
	"""
	try:
		filename = f"tts_{uuid.uuid4()}.mp3"
		filepath = os.path.join(TEMP_AUDIO_DIR, filename)
		
		# Try Azure TTS if available and Albanian is requested
		if AZURE_AVAILABLE and language == "sq" and voice in ["anila", "ilir"]:
			voice_map = {
				"anila": "sq-AL-AnilaNeural",
				"ilir": "sq-AL-IlirNeural"
			}
			try:
				filepath = _generate_speech_azure(
					text=text,
					voice_name=voice_map[voice],
					rate=rate,
					pitch=pitch,
					output_path=filepath
				)
				return FileResponse(
					filepath,
					media_type="audio/mpeg",
					filename=f"speech_azure_{voice}.mp3",
					headers={"X-TTS-Engine": "Azure Neural"}
				)
			except Exception as azure_err:
				print(f"[WARNING] Azure TTS failed, falling back to gTTS: {azure_err}")
		
		# Fallback to gTTS
		filepath = _generate_speech_gtts(text=text, slow=slow, output_path=filepath)
		
		return FileResponse(
			filepath, 
			media_type="audio/mpeg",
			filename=f"speech_{language}.mp3",
			headers={"X-TTS-Engine": "gTTS"}
		)
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


@router.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...), language: str = "sq-AL"):
	"""
	Convert speech to text using Google Speech Recognition
	Language codes: 'sq-AL' for Albanian, 'en-US' for English
	"""
	try:
		# Save uploaded file temporarily
		temp_filename = f"stt_{uuid.uuid4()}.wav"
		temp_filepath = os.path.join(TEMP_AUDIO_DIR, temp_filename)
		
		with open(temp_filepath, "wb") as buffer:
			buffer.write(await audio_file.read())
		
		# Convert to proper format if needed (lazy import to avoid ffmpeg warning at startup)
		from pydub import AudioSegment
		audio = AudioSegment.from_file(temp_filepath)
		audio = audio.set_frame_rate(16000).set_channels(1)
		audio.export(temp_filepath, format="wav")
		
		# Initialize recognizer
		recognizer = sr.Recognizer()
		
		# Load audio file
		with sr.AudioFile(temp_filepath) as source:
			audio_data = recognizer.record(source)
		
		# Recognize speech
		text = recognizer.recognize_google(audio_data, language=language)
		
		# Clean up temp files
		os.remove(temp_filepath)
		
		return {
			"text": text,
			"confidence": 0.9,  # Google doesn't provide confidence for free tier
			"language": language
		}
		
	except sr.UnknownValueError:
		raise HTTPException(status_code=400, detail="Could not understand audio")
	except sr.RequestError as e:
		raise HTTPException(status_code=500, detail=f"Speech recognition service error: {str(e)}")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")
	finally:
		# Clean up temp files
		if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
			os.remove(temp_filepath)


@router.post("/pronunciation-check")
async def pronunciation_check(
	audio_file: UploadFile = File(...), 
	target_text: str = "",
	language: str = "sq-AL"
):
	"""
	Check pronunciation by comparing spoken text with target text
	"""
	try:
		# Convert speech to text
		recognized_text = await speech_to_text(audio_file, language)
		
		# Simple similarity check (can be enhanced with more sophisticated algorithms)
		similarity = calculate_similarity(recognized_text["text"], target_text)
		
		return {
			"spoken_text": recognized_text["text"],
			"target_text": target_text,
			"similarity_score": similarity,
			"is_correct": similarity > 0.7,
			"feedback": get_pronunciation_feedback(similarity, recognized_text["text"], target_text)
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Pronunciation check failed: {str(e)}")


def calculate_similarity(text1: str, text2: str) -> float:
	"""Calculate similarity between two texts"""
	if not text1 or not text2:
		return 0.0
	
	# Convert to lowercase and remove punctuation for comparison
	text1_clean = ''.join(c.lower() for c in text1 if c.isalnum() or c.isspace())
	text2_clean = ''.join(c.lower() for c in text2 if c.isalnum() or c.isspace())
	
	# Simple word-based similarity
	words1 = set(text1_clean.split())
	words2 = set(text2_clean.split())
	
	if not words1 or not words2:
		return 0.0
	
	intersection = words1.intersection(words2)
	union = words1.union(words2)
	
	return len(intersection) / len(union) if union else 0.0


def get_pronunciation_feedback(similarity: float, spoken: str, target: str) -> str:
	"""Generate feedback based on pronunciation accuracy"""
	if similarity > 0.9:
		return "Shumë mirë! Shqiptimi yt është i saktë."
	elif similarity > 0.7:
		return "Mirë! Mund të përmirësosh pak shqiptimin."
	elif similarity > 0.5:
		return "Provo sërish. Fokuso më shumë në shqiptimin e duhur."
	else:
		return "Duhet të praktikosh më shumë. Dëgjo përsëri fjalën dhe provo sërish."


@router.get("/audio-exercises/{exercise_id}")
async def get_audio_exercise(
	exercise_id: int,
	slow: bool = True,
	voice: Literal["anila", "ilir", "default"] = "anila"
):
	"""
	Get audio version of an exercise for listening practice.
	Uses Azure TTS Neural Voices for professional, natural Albanian pronunciation.
	
	Features:
	- Audio caching (reuses existing files)
	- Validates text exists before generation
	- Fast response for cached files
	
	Parameters:
	- slow: Adjust speech rate (Azure: -15% rate, gTTS: slow=True)
	- voice: "anila" (female, kid-friendly), "ilir" (male), or "default" (gTTS)
	"""
	try:
		from ..database import get_db
		from .. import models
		
		# Get exercise from database
		db = next(get_db())
		exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
		
		if not exercise:
			raise HTTPException(status_code=404, detail="Exercise not found")
		
		# Extract text to be spoken
		exercise_text = ""
		if exercise.data:
			try:
				data = json.loads(exercise.data)
				if "audio_word" in data and data["audio_word"]:
					exercise_text = data["audio_word"]
				if "audio_text" in data:
					exercise_text = data["audio_text"]
			except:
				pass
		
		# Fallback to answer if no audio_text specified
		if not exercise_text:
			exercise_text = exercise.answer
		
		# Validate text exists
		if not exercise_text or not exercise_text.strip():
			print(f"[ERROR] Exercise {exercise_id} has no text for audio (answer: {exercise.answer}, data: {exercise.data})")
			raise HTTPException(
				status_code=400,
				detail=f"Exercise {exercise_id} has no text to generate audio. Please check exercise data."
			)
		
		exercise_text = exercise_text.strip()
		
		text_hash = hashlib.md5(exercise_text.encode("utf-8")).hexdigest()[:10]

		# Check for cached audio file keyed by exercise text too, so content changes
		# immediately generate a fresh voice file instead of reusing stale audio.
		engine_suffix = "azure" if (AZURE_AVAILABLE and voice in ["anila", "ilir"]) else "gtts"
		rate_suffix = "slow" if slow else "normal"
		cached_filename = f"exercise_{exercise_id}_{text_hash}_{voice}_{rate_suffix}_{engine_suffix}.mp3"
		cached_filepath = os.path.join(TEMP_AUDIO_DIR, cached_filename)
		
		# Return cached file if exists and is recent (< 24 hours old)
		if os.path.exists(cached_filepath):
			file_age_seconds = time.time() - os.path.getmtime(cached_filepath)
			if file_age_seconds < 86400:  # 24 hours
				print(f"[INFO] Serving cached audio for exercise {exercise_id}")
				return FileResponse(
					cached_filepath,
					media_type="audio/mpeg",
					filename=f"exercise_{exercise_id}.mp3",
					headers={"X-TTS-Engine": f"{engine_suffix}-cached"}
				)
			else:
				# Remove old cached file
				try:
					os.remove(cached_filepath)
				except:
					pass
		
		# Generate new audio
		print(f"[INFO] Generating new audio for exercise {exercise_id}: '{exercise_text[:50]}...'")
		
		# Try Azure TTS for Albanian
		if AZURE_AVAILABLE and voice in ["anila", "ilir"]:
			voice_map = {
				"anila": "sq-AL-AnilaNeural",
				"ilir": "sq-AL-IlirNeural"
			}
			rate = "-15%" if slow else "+0%"  # Slower for dictation
			
			try:
				filepath = _generate_speech_azure(
					text=exercise_text,
					voice_name=voice_map[voice],
					rate=rate,
					pitch="+0Hz",
					output_path=cached_filepath
				)
				return FileResponse(
					filepath,
					media_type="audio/mpeg",
					filename=f"exercise_{exercise_id}.mp3",
					headers={"X-TTS-Engine": "Azure Neural"}
				)
			except Exception as azure_err:
				print(f"[WARNING] Azure TTS failed for exercise {exercise_id}, falling back to gTTS: {azure_err}")
		
		# Fallback to gTTS
		filepath = _generate_speech_gtts(text=exercise_text, slow=slow, output_path=cached_filepath)
		
		return FileResponse(
			filepath,
			media_type="audio/mpeg",
			filename=f"exercise_{exercise_id}.mp3",
			headers={"X-TTS-Engine": "gTTS"}
		)
		
	except HTTPException:
		raise
	except Exception as e:
		print(f"[ERROR] Audio generation failed for exercise {exercise_id}: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Audio exercise generation failed: {str(e)}")


@router.post("/albanian-pronunciation-check")
async def albanian_pronunciation_check(
	audio_file: UploadFile = File(...), 
	exercise_id: int = 0,
	target_text: str = ""
):
	"""
	Specialized pronunciation check for Albanian corpus exercises
	Includes Albanian-specific phonetic considerations
	"""
	try:
		from ..database import get_db
		from .. import models
		
		# Get target text from exercise if not provided
		if not target_text and exercise_id:
			db = next(get_db())
			exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
			if exercise:
				target_text = exercise.answer
		
		# Convert speech to text with Albanian language model
		recognized_text = await speech_to_text(audio_file, "sq-AL")
		
		# Enhanced similarity check for Albanian
		similarity = calculate_albanian_similarity(recognized_text["text"], target_text)
		
		# Determine score based on Albanian corpus rules
		is_correct = similarity > 0.8  # Higher threshold for Albanian
		score = get_albanian_score(similarity)
		
		return {
			"spoken_text": recognized_text["text"],
			"target_text": target_text,
			"similarity_score": similarity,
			"is_correct": is_correct,
			"score": score,
			"feedback": get_albanian_feedback(similarity, recognized_text["text"], target_text),
			"pronunciation_tips": get_albanian_pronunciation_tips(recognized_text["text"], target_text)
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Albanian pronunciation check failed: {str(e)}")


def calculate_albanian_similarity(text1: str, text2: str) -> float:
	"""Enhanced similarity calculation for Albanian language"""
	if not text1 or not text2:
		return 0.0
	
	# Albanian-specific character normalization
	albanian_chars = {
		'ë': 'e', 'ç': 'c', 'rr': 'r', 'll': 'l', 'nj': 'n', 'gj': 'g', 
		'dh': 'd', 'th': 't', 'sh': 's', 'zh': 'z', 'xh': 'x'
	}
	
	def normalize_albanian(text):
		text = text.lower().strip()
		for alb_char, replacement in albanian_chars.items():
			text = text.replace(alb_char, replacement)
		return ''.join(c for c in text if c.isalnum() or c.isspace())
	
	text1_norm = normalize_albanian(text1)
	text2_norm = normalize_albanian(text2)
	
	# Exact match gets perfect score
	if text1_norm == text2_norm:
		return 1.0
	
	# Character-level similarity for short words
	if len(text2_norm.split()) == 1:
		return character_similarity(text1_norm, text2_norm)
	
	# Word-level similarity for sentences
	words1 = set(text1_norm.split())
	words2 = set(text2_norm.split())
	
	if not words1 or not words2:
		return 0.0
	
	intersection = words1.intersection(words2)
	union = words1.union(words2)
	
	return len(intersection) / len(union) if union else 0.0


def character_similarity(text1: str, text2: str) -> float:
	"""Calculate character-level similarity"""
	if not text1 or not text2:
		return 0.0
	
	# Levenshtein distance approximation
	if len(text1) == len(text2):
		matches = sum(c1 == c2 for c1, c2 in zip(text1, text2))
		return matches / len(text1)
	
	# For different lengths, use a simple approach
	shorter, longer = (text1, text2) if len(text1) < len(text2) else (text2, text1)
	matches = sum(c in longer for c in shorter)
	return matches / len(longer)


def get_albanian_score(similarity: float) -> int:
	"""Convert similarity to Albanian corpus scoring system"""
	if similarity >= 0.95:
		return 3  # Perfect - 3 stars
	elif similarity >= 0.85:
		return 2  # Good - 2 stars  
	elif similarity >= 0.7:
		return 1  # Acceptable - 1 star
	else:
		return 0  # Needs improvement


def get_albanian_feedback(similarity: float, spoken: str, target: str) -> str:
	"""Albanian-specific pronunciation feedback"""
	if similarity >= 0.95:
		return "🌟 Përgëzime! Shqiptimi yt është i përsosur!"
	elif similarity >= 0.85:
		return "👍 Shumë mirë! Shqiptimi yt është pothuajse i saktë."
	elif similarity >= 0.7:
		return "📈 Mirë! Mund të përmirësosh pak më shumë shqiptimin."
	elif similarity >= 0.5:
		return "🔄 Provo sërish. Fokuso në secilën shkronjë."
	else:
		return "📚 Dëgjo me kujdes dhe provo përsëri. Merr kohën tënde."


def get_albanian_pronunciation_tips(spoken: str, target: str) -> list:
	"""Provide specific tips for Albanian pronunciation"""
	tips = []
	
	if not spoken or not target:
		return ["Dëgjo me kujdes fjalën dhe provo të flasësh qartë."]
	
	spoken_lower = spoken.lower()
	target_lower = target.lower()
	
	# Check for common Albanian pronunciation issues
	if 'ë' in target_lower and 'e' in spoken_lower:
		tips.append("💡 Kujdes me shkronjën 'ë' - shqiptohet si 'uh' në anglisht.")
	
	if 'rr' in target_lower and 'r' in spoken_lower:
		tips.append("💡 Shkronja 'rr' duhet të jetë më e fortë se 'r' e thjeshtë.")
	
	if 'ç' in target_lower and 'c' in spoken_lower:
		tips.append("💡 Shkronja 'ç' shqiptohet si 'ch' në anglisht.")
	
	if 'll' in target_lower and 'l' in spoken_lower:
		tips.append("💡 Shkronja 'll' ka një tingull të veçantë shqip.")
	
	if not tips:
		tips.append("🎯 Përqendrohu në shqiptimin e qartë të çdo shkronje.")
	
	return tips


@router.delete("/cleanup-audio")
async def cleanup_audio_files():
	"""Clean up temporary audio files"""
	try:
		for filename in os.listdir(TEMP_AUDIO_DIR):
			filepath = os.path.join(TEMP_AUDIO_DIR, filename)
			if os.path.isfile(filepath):
				os.remove(filepath)
		return {"message": "Audio files cleaned up successfully"}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
