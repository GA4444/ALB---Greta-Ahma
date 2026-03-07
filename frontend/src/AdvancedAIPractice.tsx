import { useState, useEffect } from 'react'
import './AdvancedAIPractice.css'

interface PersonalizedExercise {
	id: string
	type: string
	prompt: string
	answer: string
	choices?: string[]
	hint: string
	difficulty: string
	reason: string
	focus_word: string
	mistake_pattern?: string | null
}

interface AdvancedPracticeAnalysis {
	overall_accuracy: number
	trend: string
	total_attempts: number
	weak_count: number
	mastered_count: number
	top_patterns: Array<{
		name: string
		name_key: string
		count: number
		severity: string
		severity_sq: string
		description: string
	}>
}

interface AdvancedPracticeResponse {
	exercises: PersonalizedExercise[]
	analysis: AdvancedPracticeAnalysis
	recommendations: string[]
	next_focus: string
}

interface Props {
	userId: string
	levelId: number
	onGenerateRequest?: () => Promise<AdvancedPracticeResponse>
}

export default function AdvancedAIPractice({ userId, levelId, onGenerateRequest }: Props) {
	const [loading, setLoading] = useState(false)
	const [exercises, setExercises] = useState<PersonalizedExercise[]>([])
	const [analysis, setAnalysis] = useState<AdvancedPracticeAnalysis | null>(null)
	const [recommendations, setRecommendations] = useState<string[]>([])
	const [nextFocus, setNextFocus] = useState<string>('')
	
	const [responses, setResponses] = useState<Record<string, string>>({})
	const [feedback, setFeedback] = useState<Record<string, { correct: boolean; message: string }>>({})
	const [currentIndex, setCurrentIndex] = useState(0)
	const [showAnalysis, setShowAnalysis] = useState(false)

	const handleGenerate = async () => {
		if (!onGenerateRequest) return

		setLoading(true)
		setExercises([])
		setAnalysis(null)
		setResponses({})
		setFeedback({})
		setCurrentIndex(0)

		try {
			const result = await onGenerateRequest()
			
			setExercises(result.exercises)
			setAnalysis(result.analysis)
			setRecommendations(result.recommendations)
			setNextFocus(result.next_focus)
			setShowAnalysis(true)
		} catch (error) {
			console.error('Failed to generate practice:', error)
		} finally {
			setLoading(false)
		}
	}

	const handleCheck = (exercise: PersonalizedExercise) => {
		const userAnswer = responses[exercise.id]?.trim()
		
		if (!userAnswer) {
			setFeedback({
				...feedback,
				[exercise.id]: {
					correct: false,
					message: 'Shkruaj një përgjigje për ta kontrolluar.'
				}
			})
			return
		}

		const normalize = (s: string) => s.toLowerCase().trim().replace(/\s+/g, ' ')
		const isCorrect = normalize(userAnswer) === normalize(exercise.answer)

		setFeedback({
			...feedback,
			[exercise.id]: {
				correct: isCorrect,
				message: isCorrect
					? '✅ Saktë! Shkëlqyer!'
					: `❌ Jo saktë. Përgjigja e saktë është: "${exercise.answer}"`
			}
		})

		if (isCorrect) {
			// Auto-advance after correct answer
			setTimeout(() => {
				if (currentIndex < exercises.length - 1) {
					setCurrentIndex(currentIndex + 1)
				}
			}, 1500)
		}
	}

	const getTrendIcon = (trend: string) => {
		switch (trend) {
			case 'improving': return '📈'
			case 'declining': return '📉'
			case 'stable': return '➡️'
			default: return '📊'
		}
	}

	const getSeverityColor = (severity: string) => {
		// Use platform colors from CSS variables
		switch (severity) {
			case 'high': return '#EF6461'    // Platform error color
			case 'medium': return '#f59e0b'  // Warning orange
			case 'low': return '#5BBD6C'     // Platform success color
			default: return '#64748b'        // Gray
		}
	}

	return (
		<div className="advanced-ai-practice">
			<div className="ai-practice-header">
				<div className="header-left">
					<div className="ai-avatar">🤖</div>
					<div>
						<h3>Ushtrime të Personalizuara me AI</h3>
						<p className="subtitle">Bazuar 100% në performancën dhe gabimet e tua</p>
					</div>
				</div>
				<button
					className="generate-btn-primary"
					onClick={handleGenerate}
					disabled={loading}
				>
					{loading ? (
						<>
							<span className="spinner"></span>
							Po analizoj...
						</>
					) : (
						<>
							✨ Gjenero Ushtrime
						</>
					)}
				</button>
			</div>

			{/* Analysis Panel */}
			{analysis && showAnalysis && (
				<div className="analysis-panel">
					<div className="analysis-header">
						<h4>📊 Analiza e Performancës Tënde</h4>
						<button
							className="toggle-btn"
							onClick={() => setShowAnalysis(!showAnalysis)}
						>
							{showAnalysis ? '▼' : '▶'}
						</button>
					</div>

					<div className="analysis-grid">
						<div className="stat-card">
							<div className="stat-value">
								{(analysis.overall_accuracy * 100).toFixed(0)}%
							</div>
							<div className="stat-label">Saktësi e Përgjithshme</div>
						</div>

						<div className="stat-card">
							<div className="stat-value">
								{getTrendIcon(analysis.trend)} {analysis.trend}
							</div>
							<div className="stat-label">Trendi</div>
						</div>

						<div className="stat-card">
							<div className="stat-value">{analysis.weak_count}</div>
							<div className="stat-label">Fjalë të Dobëta</div>
						</div>

						<div className="stat-card">
							<div className="stat-value">{analysis.mastered_count}</div>
							<div className="stat-label">Fjalë të Zotëruara</div>
						</div>
					</div>

					{/* Top Patterns */}
					{analysis.top_patterns && analysis.top_patterns.length > 0 && (
						<div className="patterns-section">
							<h5>🎯 Gabimet Kryesore:</h5>
							<div className="patterns-list">
								{analysis.top_patterns.map((pattern, idx) => (
									<div key={idx} className="pattern-item">
										<div
											className="pattern-badge"
											style={{ backgroundColor: getSeverityColor(pattern.severity) }}
										>
											{pattern.severity_sq || pattern.severity.toUpperCase()}
										</div>
										<div className="pattern-details">
										<div className="pattern-name">
											{pattern.name}
										</div>
											<div className="pattern-count">
												{pattern.count} {pattern.count === 1 ? 'gabim' : 'gabime'}
											</div>
											{pattern.description && (
												<div className="pattern-description">
													{pattern.description}
												</div>
											)}
										</div>
									</div>
								))}
							</div>
						</div>
					)}

					{/* Next Focus */}
					{nextFocus && (
						<div className="next-focus-card">
							<div className="focus-icon">🎯</div>
							<div className="focus-content">
								<strong>Fokusi i Ardhshëm:</strong>
								<p>{nextFocus}</p>
							</div>
						</div>
					)}

					{/* Recommendations */}
					{recommendations && recommendations.length > 0 && (
						<div className="recommendations-section">
							<h5>💡 Rekomandime për Ty:</h5>
							<ul className="recommendations-list">
								{recommendations.map((rec, idx) => (
									<li key={idx} className="recommendation-item">
										{rec}
									</li>
								))}
							</ul>
						</div>
					)}
				</div>
			)}

			{/* Exercises List */}
			{exercises.length > 0 && (
				<div className="exercises-container">
					<div className="exercises-progress">
						<div className="progress-text">
							Ushtrimi {currentIndex + 1} / {exercises.length}
						</div>
						<div className="progress-bar">
							<div
								className="progress-fill"
								style={{
									width: `${((currentIndex + 1) / exercises.length) * 100}%`
								}}
							/>
						</div>
					</div>

					<div className="exercise-card">
						{exercises.map((exercise, idx) => (
							<div
								key={exercise.id}
								className={`exercise-item ${idx === currentIndex ? 'active' : 'hidden'}`}
							>
								<div className="exercise-header-meta">
									<span className="exercise-type-badge">
										{exercise.type}
									</span>
									<span className="difficulty-badge">
										{exercise.difficulty}
									</span>
								</div>

								<div className="exercise-reason">
									<strong>Arsyeja:</strong> {exercise.reason}
								</div>

								<div className="exercise-prompt">
									{exercise.prompt.split('\n').map((line, i) => (
										<p key={i}>{line}</p>
									))}
								</div>

								{exercise.choices && (
									<div className="choices-info">
										<em>Opsionet e dhëna më sipër</em>
									</div>
								)}

								<div className="answer-section">
									<input
										type="text"
										className="answer-input-ai"
										placeholder="Shkruaj përgjigjen..."
										value={responses[exercise.id] || ''}
										onChange={(e) =>
											setResponses({
												...responses,
												[exercise.id]: e.target.value
											})
										}
										onKeyPress={(e) => {
											if (e.key === 'Enter') {
												handleCheck(exercise)
											}
										}}
									/>
									<button
										className="check-btn-ai"
										onClick={() => handleCheck(exercise)}
										disabled={!responses[exercise.id]?.trim()}
									>
										Kontrollo
									</button>
								</div>

								{feedback[exercise.id] && (
									<div
										className={`feedback-box ${
											feedback[exercise.id].correct ? 'correct' : 'incorrect'
										}`}
									>
										{feedback[exercise.id].message}
									</div>
								)}

								<div className="exercise-hint">
									<strong>💡 Këshillë:</strong> {exercise.hint}
								</div>

								{/* Navigation */}
								<div className="exercise-navigation">
									<button
										className="nav-btn"
										onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
										disabled={currentIndex === 0}
									>
										← Mëparshmi
									</button>
									<button
										className="nav-btn"
										onClick={() =>
											setCurrentIndex(Math.min(exercises.length - 1, currentIndex + 1))
										}
										disabled={currentIndex === exercises.length - 1}
									>
										Tjetri →
									</button>
								</div>
							</div>
						))}
					</div>
				</div>
			)}

			{/* Empty State */}
			{!loading && exercises.length === 0 && (
				<div className="empty-state">
					<div className="empty-icon">🎯</div>
					<h4>Gati për Ushtrime të Personalizuara?</h4>
					<p>
						Kliko "Gjenero Ushtrime" dhe AI do të analizojë performancën tënde
						për të krijuar ushtrime SPECIFIKE për dobësitë e tua!
					</p>
					<ul className="benefits-list">
						<li>✅ Fokus në gabimet e tua specifike</li>
						<li>✅ Pattern recognition dhe eliminim</li>
						<li>✅ Rekomandime të personalizuara</li>
						<li>✅ Track progress në kohë reale</li>
					</ul>
				</div>
			)}
		</div>
	)
}
