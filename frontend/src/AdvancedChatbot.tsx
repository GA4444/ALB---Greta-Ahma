import { useState, useEffect, useRef } from 'react'
import type {
	AdvancedChatRequest,
	AdvancedChatResponse,
	ChatHistoryResponse,
	MessageFeedback
} from './api'
import {
	askAdvancedChatbot,
	getChatHistory,
	clearChatSession,
	submitChatFeedback,
	textToSpeech,
	speechToText,
	exportConversation,
	getChatSuggestions
} from './api'
import './AdvancedChatbot.css'

interface Message {
	id?: number
	role: 'user' | 'assistant'
	content: string
	suggestions?: string[]
	timestamp: string
	model_used?: string
	tokens_used?: number
	response_time_ms?: number
	rating?: number
}

interface AdvancedChatbotProps {
	userId?: string
	onClose?: () => void
	context?: {
		current_level?: string
		current_exercise?: string
		recent_mistakes?: string[]
	}
}

export default function AdvancedChatbot({ userId, onClose, context }: AdvancedChatbotProps) {
	const [messages, setMessages] = useState<Message[]>([])
	const [inputValue, setInputValue] = useState('')
	const [isLoading, setIsLoading] = useState(false)
	const [sessionToken, setSessionToken] = useState<string | null>(null)
	const [suggestions, setSuggestions] = useState<string[]>([])
	const [showSettings, setShowSettings] = useState(false)
	const [useLLM, setUseLLM] = useState(false)
	const [generateExercise, setGenerateExercise] = useState(false)
	
	// New Settings
	const [responseLength, setResponseLength] = useState<'short' | 'medium' | 'detailed'>('medium')
	const [autoAudio, setAutoAudio] = useState(false)
	const [chatbotTone, setChatbotTone] = useState<'friendly' | 'professional' | 'playful'>('friendly')
	const [showStats, setShowStats] = useState(false)
	const [difficultyLevel, setDifficultyLevel] = useState<'easy' | 'medium' | 'advanced'>('medium')
	
	// Voice features
	const [isRecording, setIsRecording] = useState(false)
	const [isPlayingAudio, setIsPlayingAudio] = useState(false)
	const mediaRecorderRef = useRef<MediaRecorder | null>(null)
	const audioChunksRef = useRef<Blob[]>([])
	
	// UI refs
	const messagesEndRef = useRef<HTMLDivElement>(null)
	const inputRef = useRef<HTMLTextAreaElement>(null)

	// Auto-scroll to bottom
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
	}, [messages])

	// Load suggestions on mount
	useEffect(() => {
		getChatSuggestions()
			.then((data) => setSuggestions(data.suggestions))
			.catch(console.error)
	}, [])

	// Load history if session exists
	useEffect(() => {
		const savedSession = localStorage.getItem('chatbot_session_token')
		if (savedSession) {
			setSessionToken(savedSession)
			loadHistory(savedSession)
		}
	}, [])

	const loadHistory = async (token: string) => {
		try {
			const history = await getChatHistory(token)
			const formattedMessages: Message[] = history.messages.map((msg) => ({
				id: msg.id,
				role: msg.role,
				content: msg.content,
				timestamp: msg.created_at,
				model_used: msg.model_used,
				tokens_used: msg.tokens_used,
				response_time_ms: msg.response_time_ms
			}))
			setMessages(formattedMessages)
		} catch (error) {
			console.error('Failed to load history:', error)
			// Clear invalid session
			localStorage.removeItem('chatbot_session_token')
			setSessionToken(null)
		}
	}

	const sendMessage = async (messageText?: string) => {
		const text = messageText || inputValue.trim()
		if (!text || isLoading) return

		setInputValue('')
		setIsLoading(true)

		const userMessage: Message = {
			role: 'user',
			content: text,
			timestamp: new Date().toISOString()
		}

		setMessages((prev) => [...prev, userMessage])

		try {
			const request: AdvancedChatRequest = {
				message: text,
				user_id: userId,
				session_token: sessionToken || undefined,
				use_llm: useLLM,
				generate_exercise: generateExercise,
				context: {
					...context,
					response_length: responseLength,
					chatbot_tone: chatbotTone,
					difficulty_level: difficultyLevel
				}
			}

			const response: AdvancedChatResponse = await askAdvancedChatbot(request)

			// Save session token
			if (response.session_token && response.session_token !== sessionToken) {
				setSessionToken(response.session_token)
				localStorage.setItem('chatbot_session_token', response.session_token)
			}

			const assistantMessage: Message = {
				role: 'assistant',
				content: response.response,
				suggestions: response.suggestions,
				timestamp: response.timestamp,
				model_used: response.model_used,
				tokens_used: response.tokens_used,
				response_time_ms: response.response_time_ms
			}

			setMessages((prev) => [...prev, assistantMessage])

			// Auto-play audio if enabled
			if (autoAudio) {
				try {
					const audioBlob = await textToSpeech({ text: response.response })
					const audioUrl = URL.createObjectURL(audioBlob)
					const audio = new Audio(audioUrl)
					audio.play()
				} catch (error) {
					console.error('Auto-audio failed:', error)
				}
			}

			// Update suggestions from response
			if (response.suggestions && response.suggestions.length > 0) {
				setSuggestions(response.suggestions)
			}
		} catch (error) {
			console.error('Chat error:', error)
			const errorMessage: Message = {
				role: 'assistant',
				content: '❌ Më fal, ndodhi një gabim. Ju lutem provoni përsëri.',
				timestamp: new Date().toISOString()
			}
			setMessages((prev) => [...prev, errorMessage])
		} finally {
			setIsLoading(false)
		}
	}

	const handleClearChat = async () => {
		if (!sessionToken || !confirm('A jeni të sigurt që dëshironi të fshini historikun?')) return

		try {
			await clearChatSession(sessionToken)
			setMessages([])
			setSessionToken(null)
			localStorage.removeItem('chatbot_session_token')
		} catch (error) {
			console.error('Failed to clear session:', error)
		}
	}

	const handleExport = async (format: 'json' | 'txt') => {
		if (!sessionToken) return

		try {
			const data = await exportConversation(sessionToken, format)
			
			if (format === 'json') {
				const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
				const url = URL.createObjectURL(blob)
				const a = document.createElement('a')
				a.href = url
				a.download = `conversation_${sessionToken.substring(0, 8)}.json`
				a.click()
				URL.revokeObjectURL(url)
			}
			// For txt, the backend returns the file directly
		} catch (error) {
			console.error('Export failed:', error)
		}
	}

	const handleFeedback = async (messageId: number | undefined, rating: number) => {
		if (!messageId) return

		try {
			const feedback: MessageFeedback = {
				message_id: messageId,
				rating
			}
			await submitChatFeedback(feedback)

			// Update message with rating
			setMessages((prev) =>
				prev.map((msg) =>
					msg.id === messageId ? { ...msg, rating } : msg
				)
			)
		} catch (error) {
			console.error('Feedback failed:', error)
		}
	}

	const handleTextToSpeech = async (text: string) => {
		try {
			setIsPlayingAudio(true)
			const response = await textToSpeech(text, 'anila')
			
			if (response.audio_url) {
				const audio = new Audio(response.audio_url)
				audio.onended = () => setIsPlayingAudio(false)
				audio.onerror = () => setIsPlayingAudio(false)
				await audio.play()
			}
		} catch (error) {
			console.error('TTS failed:', error)
			setIsPlayingAudio(false)
		}
	}

	const startRecording = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
			const mediaRecorder = new MediaRecorder(stream)
			mediaRecorderRef.current = mediaRecorder
			audioChunksRef.current = []

			mediaRecorder.ondataavailable = (event) => {
				audioChunksRef.current.push(event.data)
			}

			mediaRecorder.onstop = async () => {
				const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
				
				try {
					const response = await speechToText(audioBlob)
					if (response.text) {
						setInputValue(response.text)
					}
				} catch (error) {
					console.error('STT failed:', error)
					alert('Nuk mund të kuptoja zërin. Ju lutem provoni përsëri.')
				}

				stream.getTracks().forEach((track) => track.stop())
			}

			mediaRecorder.start()
			setIsRecording(true)
		} catch (error) {
			console.error('Recording failed:', error)
			alert('Nuk mund të hynte në mikrofon. Ju lutem kontrolloni lejet.')
		}
	}

	const stopRecording = () => {
		if (mediaRecorderRef.current && isRecording) {
			mediaRecorderRef.current.stop()
			setIsRecording(false)
		}
	}

	const formatResponse = (text: string): React.ReactNode => {
		let cleaned = text
			.replace(/\*\*(.+?)\*\*/g, '$1')
			.replace(/\*(.+?)\*/g, '$1')
			.replace(/__(.+?)__/g, '$1')
			.replace(/^#{1,3}\s+/gm, '')
			.replace(/```[\s\S]*?```/g, (match) => match.replace(/```\w*\n?/g, '').trim())

		const lines = cleaned.split('\n')
		const elements: React.ReactNode[] = []

		lines.forEach((line, i) => {
			const trimmed = line.trim()
			if (!trimmed) {
				elements.push(<br key={`br-${i}`} />)
				return
			}

			const bulletMatch = trimmed.match(/^[•\-]\s+(.+)$/)
			const numMatch = trimmed.match(/^(\d+)\.\s+(.+)$/)
			const checkMatch = trimmed.match(/^[✅✔️☑️]\s*(.+)$/)
			const trophyMatch = trimmed.match(/^🏆\s*(.+)$/)

			if (bulletMatch) {
				elements.push(<div key={i} style={{ paddingLeft: '0.75rem', marginBottom: '0.25rem' }}>{'· '}{bulletMatch[1]}</div>)
			} else if (numMatch) {
				elements.push(<div key={i} style={{ paddingLeft: '0.5rem', marginBottom: '0.25rem' }}>{numMatch[1]}. {numMatch[2]}</div>)
			} else if (checkMatch) {
				elements.push(<div key={i} style={{ paddingLeft: '0.5rem', marginBottom: '0.25rem' }}>{'✓ '}{checkMatch[1]}</div>)
			} else if (trophyMatch) {
				elements.push(<div key={i} style={{ paddingLeft: '0.5rem', marginBottom: '0.25rem' }}>{'· '}{trophyMatch[1]}</div>)
			} else {
				elements.push(<div key={i} style={{ marginBottom: '0.25rem' }}>{trimmed}</div>)
			}
		})

		return <>{elements}</>
	}

	const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault()
			sendMessage()
		}
	}

	return (
		<div className="advanced-chatbot">
			<div className="chatbot-header">
				<div className="header-left">
					<div className="chatbot-avatar-large">🤖</div>
					<div>
						<h3>AI Chatbot {useLLM && <span className="llm-badge">✨ LLM</span>}</h3>
						<p className="chatbot-subtitle">
							{context ? '📍 Context-Aware' : 'Pyetni çdo gjë për platformën'}
						</p>
					</div>
				</div>
				<div className="header-right">
					<button
						className="icon-btn"
						onClick={() => setShowSettings(!showSettings)}
						title="Cilësimet"
					>
						⚙️
					</button>
					{sessionToken && messages.length > 0 && (
						<>
							<button
								className="icon-btn"
								onClick={() => handleExport('json')}
								title="Eksporto si JSON"
							>
								💾
							</button>
							<button
								className="icon-btn"
								onClick={handleClearChat}
								title="Fshi historikun"
							>
								🗑️
							</button>
						</>
					)}
					{onClose && (
						<button className="icon-btn" onClick={onClose} title="Mbyll">
							✕
						</button>
					)}
				</div>
			</div>

			{showSettings && (
				<div className="chatbot-settings">
					<div className="settings-grid">
						{/* AI Options */}
						<div className="setting-group">
							<label className="setting-label">🤖 Opsionet AI</label>
							<label className="setting-item checkbox">
								<input
									type="checkbox"
									checked={useLLM}
									onChange={(e) => setUseLLM(e.target.checked)}
								/>
								<span>Përdor LLM (AI i avancuar) ✨</span>
							</label>
							<label className="setting-item checkbox">
								<input
									type="checkbox"
									checked={generateExercise}
									onChange={(e) => setGenerateExercise(e.target.checked)}
								/>
								<span>Gjeneroje ushtrime të reja 📝</span>
							</label>
						</div>

						{/* Response Settings */}
						<div className="setting-group">
							<label className="setting-label">💬 Gjatësia e Përgjigjes</label>
							<select
								value={responseLength}
								onChange={(e) => setResponseLength(e.target.value as any)}
								className="setting-select"
							>
								<option value="short">E shkurtër (disa fjali)</option>
								<option value="medium">Mesatare (1-2 paragrafe)</option>
								<option value="detailed">E detajuar (me shembuj)</option>
							</select>
						</div>

						{/* Difficulty Level */}
						<div className="setting-group">
							<label className="setting-label">🎯 Niveli i Vështirësisë</label>
							<select
								value={difficultyLevel}
								onChange={(e) => setDifficultyLevel(e.target.value as any)}
								className="setting-select"
							>
								<option value="easy">I Lehtë (për fëmijë)</option>
								<option value="medium">Mesatar (standard)</option>
								<option value="advanced">I Avancuar (profesional)</option>
							</select>
						</div>

						{/* Chatbot Tone */}
						<div className="setting-group">
							<label className="setting-label">😊 Toni i Chatbot-it</label>
							<select
								value={chatbotTone}
								onChange={(e) => setChatbotTone(e.target.value as any)}
								className="setting-select"
							>
								<option value="friendly">Miqësor (i ngrohtë)</option>
								<option value="professional">Profesional (formal)</option>
								<option value="playful">Argëtues (me humor)</option>
							</select>
						</div>

						{/* Audio & Display Options */}
						<div className="setting-group">
							<label className="setting-label">🔊 Opsione Shtesë</label>
							<label className="setting-item checkbox">
								<input
									type="checkbox"
									checked={autoAudio}
									onChange={(e) => setAutoAudio(e.target.checked)}
								/>
								<span>Audio automatikisht 🔊</span>
							</label>
							<label className="setting-item checkbox">
								<input
									type="checkbox"
									checked={showStats}
									onChange={(e) => setShowStats(e.target.checked)}
								/>
								<span>Shfaq statistika 📊</span>
							</label>
						</div>
					</div>

					<div className="setting-note">
						💡 LLM përdor modele të avancuara si GPT-4 ose Claude për përgjigje më të mira.
					</div>
				</div>
			)}

			<div className="chatbot-messages">
				{messages.length === 0 ? (
					<div className="chatbot-welcome">
						<div className="welcome-avatar">🤖</div>
						<h4>Mirësevini te AI Chatbot i avancuar!</h4>
						<p>Si mund t'ju ndihmoj sot?</p>
						{context && (
							<div className="context-info">
								<p><strong>📍 Kontekst aktual:</strong></p>
								{context.current_level && <p>Niveli: {context.current_level}</p>}
								{context.current_exercise && <p>Ushtrim: {context.current_exercise}</p>}
							</div>
						)}
						{suggestions.length > 0 && (
							<div className="quick-suggestions">
								<p className="suggestions-title">Pyetje të shpeshta:</p>
								{suggestions.map((suggestion, idx) => (
									<button
										key={idx}
										className="suggestion-chip"
										onClick={() => sendMessage(suggestion)}
									>
										{suggestion}
									</button>
								))}
							</div>
						)}
					</div>
				) : (
					<>
						{messages.map((msg, idx) => (
							<div key={idx} className={`chat-message ${msg.role}`}>
								{msg.role === 'assistant' && (
									<div className="message-avatar">🤖</div>
								)}
								<div className="message-content-wrapper">
									<div className="message-content">
										{msg.role === 'assistant' ? formatResponse(msg.content) : msg.content}
										{msg.role === 'assistant' && showStats && (
											<div className="message-meta">
												{msg.model_used && (
													<span className="model-badge">🤖 {msg.model_used}</span>
												)}
												{msg.response_time_ms && (
													<span className="time-badge">⏱️ {msg.response_time_ms}ms</span>
												)}
												{msg.tokens_used && (
													<span className="tokens-badge">🔢 {msg.tokens_used} tokens</span>
												)}
											</div>
										)}
									</div>
									{msg.suggestions && msg.suggestions.length > 0 && (
										<div className="inline-suggestions">
											{msg.suggestions.map((sugg, sidx) => (
												<button
													key={sidx}
													className="suggestion-chip-small"
													onClick={() => sendMessage(sugg)}
												>
													{sugg}
												</button>
											))}
										</div>
									)}
									{msg.role === 'assistant' && (
										<div className="message-actions">
											<button
												className="action-btn"
												onClick={() => handleTextToSpeech(msg.content)}
												disabled={isPlayingAudio}
												title="Dëgjo me zë"
											>
												{isPlayingAudio ? '🔊' : '🔉'}
											</button>
											<button
												className="action-btn"
												onClick={() => navigator.clipboard.writeText(msg.content)}
												title="Kopjo"
											>
												📋
											</button>
											{msg.id && (
												<div className="feedback-buttons">
													<button
														className={`action-btn ${msg.rating === 5 ? 'active' : ''}`}
														onClick={() => handleFeedback(msg.id, 5)}
														title="E shkëlqyer"
													>
														👍
													</button>
													<button
														className={`action-btn ${msg.rating === 1 ? 'active' : ''}`}
														onClick={() => handleFeedback(msg.id, 1)}
														title="E dobët"
													>
														👎
													</button>
												</div>
											)}
										</div>
									)}
								</div>
								{msg.role === 'user' && (
									<div className="message-avatar user-avatar">👤</div>
								)}
							</div>
						))}
						{isLoading && (
							<div className="chat-message assistant">
								<div className="message-avatar">🤖</div>
								<div className="message-content">
									<div className="typing-indicator">
										<span></span>
										<span></span>
										<span></span>
									</div>
								</div>
							</div>
						)}
						<div ref={messagesEndRef} />
					</>
				)}
			</div>

			<div className="chatbot-input-area">
				<button
					className={`voice-btn ${isRecording ? 'recording' : ''}`}
					onClick={isRecording ? stopRecording : startRecording}
					disabled={isLoading}
					title={isRecording ? 'Ndalo regjistrimin' : 'Filloni të flisni'}
				>
					{isRecording ? '🎙️' : '🎤'}
				</button>
				<textarea
					ref={inputRef}
					className="chatbot-input"
					placeholder="Shkruani një pyetje..."
					value={inputValue}
					onChange={(e) => setInputValue(e.target.value)}
					onKeyPress={handleKeyPress}
					disabled={isLoading || isRecording}
					rows={1}
				/>
				<button
					className="send-btn"
					onClick={() => sendMessage()}
					disabled={isLoading || !inputValue.trim() || isRecording}
				>
					{isLoading ? '⏳' : '➤'}
				</button>
			</div>
		</div>
	)
}
