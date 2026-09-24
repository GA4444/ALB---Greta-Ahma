import BrandLogo from './components/BrandLogo'
import PageLoading from './components/PageLoading'
import React, { lazy, Suspense, useState, useEffect, useRef, useMemo } from 'react'
import {
	getAdminStats,
	getAdminPeriodStats,
	getAllUsers,
	getAllClasses,
	getAllLevels,
	getAllExercises,
	pingHealth,
	getUserReport,
	createClass,
	createLevel,
	createExercise,
	updateUser,
	updateClass,
	updateLevel,
	updateExercise,
	deleteUser,
	deleteClass,
	deleteLevel,
	deleteExercise,
	getCorpusStats,
	getCorpusDocuments,
	createCorpusDocument,
	updateCorpusDocument,
	deleteCorpusDocument,
	validateCorpusDocument,
	validateAllCorpusDocuments,
	getCorpusDuplicates,
	getCorpusWordFrequencies,
	getCorpusFuseCodes,
	reprocessAllCorpus,
	autoPopulateCorpus,
	getCorpusLinguisticMetrics,
	getResearchAIOverview,
	getInstructionDataset,
	createAugmentedErrorPair,
	generateResearchExercise,
	generatePedagogicalFeedback,
	evaluateResearchCorrection,
	evaluateGradeFit,
	getIRTSummary,
	getKnowledgeTracing,
	getAdaptiveNextItem,
	compareRAGAblation,
	createTeacherReview,
	getTeacherReviewSummary,
	getFinalExperimentProtocol,
	getDeepLearningDataset,
	getModelTrainingStatus,
	getTrainingCommands,
	type UserOut,
	type AdminStats,
	type AdminPeriodStats,
	type ClassData,
	type LevelOut,
	type ExerciseOut,
	type Category,
	type CorpusDocument,
	type CorpusStats,
	type CorpusDuplicatesResponse,
	type WordFrequencyResponse,
	type CorpusFuseCode,
	type LinguisticMetrics,
	type ResearchAIOverview,
} from './api'
import './AdminDashboard.css'
import './AdminDashboard-pro.css'
import type { ExportData } from './utils/dataExport'
import AdminSearchBar from './admin/AdminSearchBar'
import { filterBySearch } from './admin/adminSearch'

const AdminCharts = lazy(() => import('./admin/AdminCharts'))
const BarChart = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.BarChart })))
const Bar = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Bar })))
const PieChart = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.PieChart })))
const Pie = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Pie })))
const Cell = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Cell })))
const LineChart = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.LineChart })))
const Line = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Line })))
const AreaChart = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.AreaChart })))
const Area = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Area })))
const RadarChart = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.RadarChart })))
const PolarGrid = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.PolarGrid })))
const PolarAngleAxis = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.PolarAngleAxis })))
const PolarRadiusAxis = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.PolarRadiusAxis })))
const Radar = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Radar })))
const ComposedChart = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.ComposedChart })))
const XAxis = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.XAxis })))
const YAxis = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.YAxis })))
const CartesianGrid = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.CartesianGrid })))
const Tooltip = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Tooltip })))
const Legend = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.Legend })))
const ResponsiveContainer = lazy(() => import('./admin/AdminCharts').then(module => ({ default: module.ResponsiveContainer })))

const chartFallback = (
	<PageLoading inline title="Duke ngarkuar grafikët..." />
)

interface AdminDashboardProps {
	userId: number
	onLogout: () => void
}

export default function AdminDashboard({ userId, onLogout }: AdminDashboardProps) {
	const [activeTab, setActiveTab] = useState<'stats' | 'users' | 'classes' | 'levels' | 'exercises' | 'corpus' | 'research'>('stats')
	const [timeRange, setTimeRange] = useState<'weekly' | 'monthly' | 'yearly'>('monthly')
	const [stats, setStats] = useState<AdminStats | null>(null)
	const [periodStats, setPeriodStats] = useState<AdminPeriodStats | null>(null)
	const [periodLoading, setPeriodLoading] = useState(false)
	const [users, setUsers] = useState<UserOut[]>([])
	const [classes, setClasses] = useState<ClassData[]>([])
	const [levels, setLevels] = useState<LevelOut[]>([])
	const [exercises, setExercises] = useState<ExerciseOut[]>([])
	const [usersSearch, setUsersSearch] = useState('')
	const [classesSearch, setClassesSearch] = useState('')
	const [levelsSearch, setLevelsSearch] = useState('')
	const [exercisesSearch, setExercisesSearch] = useState('')
	const [corpusSearchDraft, setCorpusSearchDraft] = useState('')
	const [corpusPerClassSearch, setCorpusPerClassSearch] = useState('')
	const [corpusWordsSearch, setCorpusWordsSearch] = useState('')
	const [selectedClass, setSelectedClass] = useState<number | null>(null)
	const [selectedLevel, setSelectedLevel] = useState<number | null>(null)
	const [loading, setLoading] = useState(false)
	const [loadError, setLoadError] = useState<string | null>(null)
	const [editingUser, setEditingUser] = useState<UserOut | null>(null)
	const [editingClass, setEditingClass] = useState<ClassData | null>(null)
	const [editingLevel, setEditingLevel] = useState<LevelOut | null>(null)
	const [editingExercise, setEditingExercise] = useState<ExerciseOut | null>(null)
	const [showCreateModal, setShowCreateModal] = useState<'class' | 'level' | 'exercise' | null>(null)
	const [showUserReport, setShowUserReport] = useState<UserOut | null>(null)
	const [userReportData, setUserReportData] = useState<any>(null)
	const [isExporting, setIsExporting] = useState(false)

	// Corpus state
	const [corpusStats, setCorpusStats] = useState<CorpusStats | null>(null)
	const [corpusDocs, setCorpusDocs] = useState<CorpusDocument[]>([])
	const [corpusTotal, setCorpusTotal] = useState(0)
	const [corpusFilters, setCorpusFilters] = useState<{genre?: string; dialect?: string; source?: string; search?: string; class_id?: number; is_validated?: boolean}>({})
	const [corpusSubTab, setCorpusSubTab] = useState<'overview' | 'documents' | 'linguistic' | 'classification' | 'validation' | 'duplicates' | 'per_class'>('overview')
	const [showCorpusCreateModal, setShowCorpusCreateModal] = useState(false)
	const [editingCorpusDoc, setEditingCorpusDoc] = useState<CorpusDocument | null>(null)
	const [corpusWordFreqs, setCorpusWordFreqs] = useState<WordFrequencyResponse | null>(null)
	const [corpusDuplicates, setCorpusDuplicates] = useState<CorpusDuplicatesResponse | null>(null)
	const [corpusFuseCodes, setCorpusFuseCodes] = useState<CorpusFuseCode[]>([])
	const [corpusPage, setCorpusPage] = useState(0)
	const [linguisticMetrics, setLinguisticMetrics] = useState<LinguisticMetrics | null>(null)
	const [corpusAnalysisLoading, setCorpusAnalysisLoading] = useState(false)
	const [corpusAnalysisError, setCorpusAnalysisError] = useState<string | null>(null)
	const [researchOverview, setResearchOverview] = useState<ResearchAIOverview | null>(null)
	const [instructionDataset, setInstructionDataset] = useState<any>(null)
	const [irtSummary, setIrtSummary] = useState<any>(null)
	const [ktSummary, setKtSummary] = useState<any>(null)
	const [teacherReviewSummary, setTeacherReviewSummary] = useState<any>(null)
	const [finalProtocol, setFinalProtocol] = useState<any>(null)
	const [modelTrainingStatus, setModelTrainingStatus] = useState<any>(null)
	const [trainingCommands, setTrainingCommands] = useState<any>(null)
	const [researchResult, setResearchResult] = useState<any>(null)
	const [researchLoadingAction, setResearchLoadingAction] = useState<string | null>(null)
	const [researchForm, setResearchForm] = useState({
		seedWord: 'mirë',
		studentAnswer: 'mrië',
		correctAnswer: 'mirë',
		augmentationText: 'Unë shkova në shkollë dhe mësova drejtshkrimin.',
		source: 'Une shkova ne shkoll',
		reference: 'Unë shkova në shkollë',
		hypothesis: 'Unë shkova në shkollë',
		gradeText: 'Fëmija lexon një fjali të shkurtër për shkollën.',
		adaptiveUserId: String(userId),
		grade: 3,
		difficulty: 'medium' as 'easy' | 'medium' | 'hard',
		exerciseType: 'missing_letter' as 'missing_letter' | 'find_error' | 'explain_error',
	})

	useEffect(() => {
		// Warm API early so the first tab request is faster.
		void pingHealth()
	}, [])

	useEffect(() => {
		void loadData()
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [activeTab, selectedClass, selectedLevel])

	useEffect(() => {
		if (activeTab !== 'stats') return
		let cancelled = false
		const loadPeriod = async () => {
			setPeriodLoading(true)
			try {
				const data = await getAdminPeriodStats(userId, timeRange)
				if (!cancelled) setPeriodStats(data)
			} catch (error) {
				console.error('Gabim në ngarkimin e statistikave të periudhës:', error)
				if (!cancelled) setPeriodStats(null)
			} finally {
				if (!cancelled) setPeriodLoading(false)
			}
		}
		void loadPeriod()
		return () => {
			cancelled = true
		}
	}, [activeTab, timeRange, userId])

	useEffect(() => {
		if (activeTab !== 'corpus') return
		void loadData({ soft: true })
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [corpusFilters, corpusPage])

	const loadedTabsRef = useRef<Set<string>>(new Set())

	const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

	const fetchActiveTabData = async () => {
		if (activeTab === 'stats') {
			const statsData = await getAdminStats(userId)
			setStats(statsData)
		} else if (activeTab === 'users') {
			const usersData = await getAllUsers(userId)
			setUsers(usersData)
		} else if (activeTab === 'classes') {
			const classesData = await getAllClasses(userId)
			setClasses(classesData)
		} else if (activeTab === 'levels') {
			const levelsData = await getAllLevels(userId, selectedClass || undefined)
			setLevels(levelsData)
		} else if (activeTab === 'exercises') {
			const exercisesData = await getAllExercises(userId, selectedLevel || undefined, selectedClass || undefined)
			setExercises(exercisesData)
		} else if (activeTab === 'corpus') {
			const [statsRes, docsRes, fuseRes, classesRes] = await Promise.all([
				getCorpusStats(userId),
				getCorpusDocuments(userId, { ...corpusFilters, limit: 50, offset: corpusPage * 50 }),
				getCorpusFuseCodes(userId),
				getAllClasses(userId),
			])
			setCorpusStats(statsRes)
			setCorpusDocs(docsRes.documents)
			setCorpusTotal(docsRes.total)
			setCorpusFuseCodes(fuseRes.codes)
			setClasses(classesRes)
		} else if (activeTab === 'research') {
			const [overviewRes, datasetRes, irtRes, protocolRes, statusRes, commandsRes, ktRes, reviewRes] = await Promise.allSettled([
				getResearchAIOverview(),
				getInstructionDataset(12),
				getIRTSummary(1),
				getFinalExperimentProtocol(),
				getModelTrainingStatus(),
				getTrainingCommands(),
				getKnowledgeTracing(String(userId)),
				getTeacherReviewSummary(),
			])
			if (overviewRes.status === 'fulfilled') setResearchOverview(overviewRes.value)
			if (datasetRes.status === 'fulfilled') setInstructionDataset(datasetRes.value)
			if (irtRes.status === 'fulfilled') setIrtSummary(irtRes.value)
			if (protocolRes.status === 'fulfilled') setFinalProtocol(protocolRes.value)
			if (statusRes.status === 'fulfilled') setModelTrainingStatus(statusRes.value)
			if (commandsRes.status === 'fulfilled') setTrainingCommands(commandsRes.value)
			if (ktRes.status === 'fulfilled') setKtSummary(ktRes.value)
			if (reviewRes.status === 'fulfilled') setTeacherReviewSummary(reviewRes.value)
		}
	}

	const loadData = async (opts?: { soft?: boolean }) => {
		const soft = Boolean(opts?.soft) || loadedTabsRef.current.has(activeTab)
		if (!soft) {
			setLoading(true)
		}
		setLoadError(null)

		let lastError: any = null
		for (let attempt = 0; attempt < 3; attempt++) {
			try {
				if (attempt > 0) {
					await pingHealth()
					await sleep(600 * attempt)
				}
				await fetchActiveTabData()
				loadedTabsRef.current.add(activeTab)
				setLoadError(null)
				setLoading(false)
				return
			} catch (error: any) {
				lastError = error
				console.error('Error loading data:', error)
				const status = error?.response?.status
				if (status === 403 || status === 401) {
					onLogout()
					setLoading(false)
					return
				}
				const canRetry = !error?.response && attempt < 2
				if (canRetry) continue
				break
			}
		}

		const detail = lastError?.response?.data?.detail
		setLoadError(typeof detail === 'string' ? detail : 'Gabim në ngarkimin e të dhënave')
		setLoading(false)
	}

	const loadCorpusWordFreqs = async () => {
		try {
			const res = await getCorpusWordFrequencies(userId, { top_n: 100 })
			setCorpusWordFreqs(res)
		} catch (e) {
			console.error(e)
			setCorpusWordFreqs({ total_unique_words: 0, top_words: [] })
		}
	}

	const loadCorpusDuplicates = async () => {
		try {
			const res = await getCorpusDuplicates(userId)
			setCorpusDuplicates(res)
		} catch (e) {
			console.error(e)
			setCorpusDuplicates({ total_duplicate_groups: 0, groups: [] })
		}
	}

	const loadLinguisticMetrics = async () => {
		setCorpusAnalysisLoading(true)
		setCorpusAnalysisError(null)
		try {
			const res = await getCorpusLinguisticMetrics(userId)
			if ((res as any)?.error || res.empty) {
				setLinguisticMetrics(res)
				setCorpusAnalysisError(res.message || (res as any).error || 'Korpusi është bosh.')
			} else {
				setLinguisticMetrics(res)
			}
		} catch (e: any) {
			console.error(e)
			setLinguisticMetrics(null)
			setCorpusAnalysisError(e?.response?.data?.detail || 'Analiza linguistike dështoi.')
		} finally {
			setCorpusAnalysisLoading(false)
		}
	}

	const renderCorpusEmptyState = (title: string) => (
		<div className="corpus-empty-state" role="status">
			<strong>{title}</strong>
			<p>Korpusi është bosh pas migrimit të databazës. Mbusheni nga ushtrimet e klasave.</p>
			<button type="button" className="corpus-action-btn primary" onClick={handleAutoPopulate}>
				Populim Automatik nga Kurset
			</button>
		</div>
	)

	const runResearchAction = async (action: 'generate' | 'augment' | 'feedback' | 'evaluate' | 'grade-fit') => {
		setResearchLoadingAction(action)
		setResearchResult({ action, loading: true, message: 'Duke ekzekutuar...' })
		try {
			let result: any
			if (action === 'generate') {
				result = await generateResearchExercise({
					seed_word: researchForm.seedWord,
					grade: researchForm.grade,
					difficulty: researchForm.difficulty,
					exercise_type: researchForm.exerciseType,
				})
			} else if (action === 'augment') {
				result = await createAugmentedErrorPair({ text: researchForm.augmentationText, error_rate: 0.25 })
			} else if (action === 'feedback') {
				result = await generatePedagogicalFeedback({
					student_answer: researchForm.studentAnswer,
					correct_answer: researchForm.correctAnswer,
					grade: researchForm.grade,
				})
			} else if (action === 'evaluate') {
				result = await evaluateResearchCorrection({
					source: researchForm.source,
					reference: researchForm.reference,
					hypothesis: researchForm.hypothesis,
				})
			} else {
				result = await evaluateGradeFit({ text: researchForm.gradeText, grade: researchForm.grade })
			}
			setResearchResult({ action, result })
		} catch (error: any) {
			setResearchResult({ action, error: error?.response?.data?.detail || 'Gabim në modulin kërkimor' })
		} finally {
			setResearchLoadingAction(null)
		}
	}

	const runAdaptiveResearchAction = async (action: 'kt' | 'adaptive' | 'rag' | 'teacher-review') => {
		setResearchLoadingAction(action)
		setResearchResult({ action, loading: true, message: 'Duke ekzekutuar...' })
		try {
			let result: any
			if (action === 'kt') {
				result = await getKnowledgeTracing(researchForm.adaptiveUserId)
				setKtSummary(result)
			} else if (action === 'adaptive') {
				result = await getAdaptiveNextItem(researchForm.adaptiveUserId)
			} else if (action === 'rag') {
				result = await compareRAGAblation({
					with_context: [
						{ is_correct: true, unsafe: false },
						{ is_correct: true, unsafe: false },
						{ is_correct: false, unsafe: false },
					],
					without_context: [
						{ is_correct: false, unsafe: true },
						{ is_correct: true, unsafe: false },
						{ is_correct: false, unsafe: false },
					],
				})
			} else {
				result = await createTeacherReview({
					reviewer_user_id: userId,
					item_type: 'generated_feedback',
					content_snapshot: researchResult?.result || { note: 'sample review' },
					linguistic_accuracy: 5,
					clarity: 5,
					age_appropriateness: 4,
					pedagogical_value: 5,
					safety: 5,
					notes: 'Demo review from admin panel; replace with teacher assessment during study.',
					approved_for_children: true,
				})
				setTeacherReviewSummary(await getTeacherReviewSummary())
			}
			setResearchResult({ action, result })
		} catch (error: any) {
			setResearchResult({ action, error: error?.response?.data?.detail || 'Gabim në eksperimentin adaptiv' })
		} finally {
			setResearchLoadingAction(null)
		}
	}

	const runFinalExperimentAction = async (action: 'protocol' | 'deep-dataset') => {
		setResearchLoadingAction(action)
		setResearchResult({ action, loading: true, message: 'Duke ekzekutuar...' })
		try {
			const result = action === 'protocol'
				? await getFinalExperimentProtocol()
				: await getDeepLearningDataset()
			if (action === 'protocol') setFinalProtocol(result)
			setResearchResult({ action, result })
		} catch (error: any) {
			setResearchResult({ action, error: error?.response?.data?.detail || 'Gabim në paketën finale eksperimentale' })
		} finally {
			setResearchLoadingAction(null)
		}
	}

	const refreshTrainingStatus = async () => {
		setResearchLoadingAction('training-status')
		setResearchResult({ action: 'training-status', loading: true, message: 'Duke kontrolluar statusin e modeleve...' })
		try {
			const [status, commands] = await Promise.all([getModelTrainingStatus(), getTrainingCommands()])
			setModelTrainingStatus(status)
			setTrainingCommands(commands)
			setResearchResult({ action: 'training-status', result: { status, commands } })
		} catch (error: any) {
			setResearchResult({ action: 'training-status', error: error?.response?.data?.detail || 'Gabim në statusin e modeleve' })
		} finally {
			setResearchLoadingAction(null)
		}
	}

	const handleCreateCorpusDoc = async (doc: {title: string; content: string; author?: string; year?: number; genre?: string; dialect?: string; source?: string; fuse_class_code?: string}) => {
		try {
			await createCorpusDocument(userId, doc)
			setShowCorpusCreateModal(false)
			await loadData()
		} catch (error: any) {
			alert(error?.response?.data?.detail || 'Gabim në krijimin e dokumentit')
		}
	}

	const handleUpdateCorpusDoc = async (docId: number, update: any) => {
		try {
			await updateCorpusDocument(userId, docId, update)
			setEditingCorpusDoc(null)
			await loadData()
		} catch (error) {
			alert('Gabim në përditësimin e dokumentit')
		}
	}

	const handleDeleteCorpusDoc = async (docId: number) => {
		if (!confirm('Jeni i sigurt që doni të fshini këtë dokument?')) return
		try {
			await deleteCorpusDocument(userId, docId)
			await loadData()
		} catch (error) {
			alert('Gabim në fshirjen e dokumentit')
		}
	}

	const handleValidateDoc = async (docId: number) => {
		try {
			const result = await validateCorpusDocument(userId, docId)
			if (result.is_valid) {
				alert('Dokumenti u validua me sukses!')
			} else {
				alert('Probleme gjatë validimit:\n' + result.issues.join('\n'))
			}
			await loadData()
		} catch (error) {
			alert('Gabim në validim')
		}
	}

	const handleValidateAll = async () => {
		if (!confirm('Validoni të gjithë dokumentet e korpusit?')) return
		try {
			const result = await validateAllCorpusDocuments(userId)
			alert(`Validimi përfundoi:\n• Të vlefshëm: ${result.valid}\n• Të pavlefshëm: ${result.invalid}\n• Totali: ${result.total}`)
			await loadData()
		} catch (error) {
			alert('Gabim në validim')
		}
	}

	const handleReprocessAll = async () => {
		if (!confirm('Ripërpunoni të gjithë dokumentet (tokenizim, frekuenca)?')) return
		try {
			const result = await reprocessAllCorpus(userId)
			alert(`U ripërpunuan ${result.reprocessed} dokumente.`)
			await loadData()
		} catch (error) {
			alert('Gabim në ripërpunim')
		}
	}

	const handleAutoPopulate = async () => {
		if (!confirm('Krijoni dokumente korpusi automatikisht nga ushtrimet/kurset ekzistuese?')) return
		try {
			const result = await autoPopulateCorpus(userId)
			alert(`U krijuan ${result.created} dokumente të reja. ${result.skipped_duplicates} u kapërcyen (dublikatë).`)
			setLinguisticMetrics(null)
			setCorpusWordFreqs(null)
			setCorpusDuplicates(null)
			setCorpusAnalysisError(null)
			await loadData()
			if (result.created > 0) {
				await Promise.all([loadLinguisticMetrics(), loadCorpusWordFreqs(), loadCorpusDuplicates()])
			}
		} catch (error) {
			alert('Gabim në populim automatik')
		}
	}

	const handleCreateClass = async (name: string, description?: string) => {
		try {
			await createClass(userId, { name, description, order_index: classes.length + 1 })
			await loadData()
			setShowCreateModal(null)
		} catch (error) {
			alert('Gabim në krijimin e klasës')
		}
	}

	const handleCreateLevel = async (courseId: number, name: string, description?: string) => {
		try {
			await createLevel(userId, { course_id: courseId, name, description, order_index: levels.length + 1 })
			await loadData()
			setShowCreateModal(null)
		} catch (error) {
			alert('Gabim në krijimin e nivelit')
		}
	}

	const handleCreateExercise = async (exerciseData: {
		category: Category
		course_id: number
		level_id: number
		prompt: string
		answer: string
		data?: string
		points?: number
	}) => {
		try {
			await createExercise(userId, exerciseData)
			await loadData()
			setShowCreateModal(null)
		} catch (error) {
			alert('Gabim në krijimin e ushtrimit')
		}
	}

	const handleGenerateUserReport = async (user: UserOut) => {
		setShowUserReport(user)
		setUserReportData(null)
		try {
			const reportData = await getUserReport(userId, user.id)
			setUserReportData(reportData)
		} catch (error: any) {
			console.error('Gabim në ngarkimin e raportit të përdoruesit:', error)
			alert(error.response?.data?.detail || 'Raporti i përdoruesit nuk mund të ngarkohet')
			setShowUserReport(null)
		}
	}

	const handleDeleteUser = async (targetUserId: number) => {
		if (confirm('Jeni të sigurt që dëshironi të fshini këtë përdorues?')) {
			try {
				await deleteUser(userId, targetUserId)
				await loadData()
			} catch (error: any) {
				alert(error.response?.data?.detail || 'Gabim në fshirjen e përdoruesit')
			}
		}
	}

	// ========== EXPORT HANDLERS ==========
	
	const prepareExportData = (): ExportData => {
		if (!stats) {
			throw new Error('Statistikat nuk janë të disponueshme')
		}

		const summary = periodStats?.summary
		const platformStats = {
			total_users: stats.total_users,
			active_users: summary?.active_users ?? 0,
			total_classes: stats.total_classes,
			total_courses: stats.total_courses,
			total_levels: stats.total_levels,
			total_exercises: stats.total_exercises,
			total_attempts: summary?.total_attempts ?? stats.total_attempts,
			average_score: summary?.avg_score ?? 0,
			completion_rate: summary?.success_rate ?? 0,
			total_time: (summary?.time_spent_minutes ?? 0) * 60,
			period_start: periodStats?.period_start,
			period_end: periodStats?.period_end,
			data_source: periodStats?.data_source || 'attempts',
			realtime: periodStats?.realtime ?? true,
		}

		// User list export: identity fields only (no invented per-user period metrics)
		const userStats = users.map(user => ({
			id: user.id,
			username: user.username,
			email: user.email,
			age: user.age,
			exercises: '',
			avg_score: '',
			time_spent: '',
			streak: user.current_streak ?? '',
			level: '',
		}))

		const contentStats = (periodStats?.categories || []).map((cat) => ({
			class_name: cat.category,
			courses: '',
			levels: '',
			exercises: cat.total,
			completion_rate: cat.percentage,
		}))

		const activityStats = (periodStats?.series || []).map((row) => ({
			period: row.period || row.ditë || row.muaj || '',
			users: row.users ?? row.përdorues ?? 0,
			sessions: row.sessions ?? row.attempts ?? row.përpjekje ?? 0,
			exercises: row.exercises ?? row.ushtrime ?? row.attempts ?? 0,
			avg_score: row.avg_score ?? row.sukseRate ?? 0,
			time_hours: row.time_hours ?? 0,
			success_rate: row.success_rate ?? row.sukseRate ?? 0,
		}))

		return {
			timeRange,
			platformStats,
			userStats,
			contentStats,
			activityStats,
			performanceStats: periodStats?.categories || [],
		}
	}

	const handleExportCSV = async () => {
		setIsExporting(true)
		try {
			const exportData = prepareExportData()
			const { exportToCSV } = await import('./utils/dataExport')
			exportToCSV(exportData)
			alert('✅ Të dhënat u eksportuan me sukses në CSV!')
		} catch (error) {
			console.error('Gabim në eksportimin e CSV:', error)
			alert('❌ Gabim në eksportimin e të dhënave. Ju lutem provoni përsëri.')
		} finally {
			setIsExporting(false)
		}
	}

	const handleExportJSON = async () => {
		setIsExporting(true)
		try {
			const exportData = prepareExportData()
			const { exportToJSON } = await import('./utils/dataExport')
			exportToJSON(exportData)
			alert('✅ Të dhënat u eksportuan me sukses në JSON!')
		} catch (error) {
			console.error('Gabim në eksportimin e JSON:', error)
			alert('❌ Gabim në eksportimin e të dhënave. Ju lutem provoni përsëri.')
		} finally {
			setIsExporting(false)
		}
	}

	const handleExportPDF = async () => {
		setIsExporting(true)
		try {
			const exportData = prepareExportData()
			const { exportScientificPDF } = await import('./utils/dataExport')
			await exportScientificPDF(exportData)
			alert('✅ Raporti shkencor u gjenerua me sukses në PDF!')
		} catch (error) {
			console.error('Gabim në gjenerimin e PDF:', error)
			alert('❌ Gabim në gjenerimin e raportit. Ju lutem provoni përsëri.')
		} finally {
			setIsExporting(false)
		}
	}

	const handleExportExcel = async () => {
		setIsExporting(true)
		try {
			const exportData = prepareExportData()
			const { exportToExcel } = await import('./utils/dataExport')
			await exportToExcel(exportData)
			alert('✅ Të dhënat u eksportuan me sukses në Excel!')
		} catch (error) {
			console.error('Gabim në eksportimin e Excel:', error)
			alert('❌ Gabim në eksportimin e të dhënave. Ju lutem provoni përsëri.')
		} finally {
			setIsExporting(false)
		}
	}

	const handleDeleteClass = async (classId: number) => {
		if (confirm('Jeni të sigurt që dëshironi të fshini këtë klasë?')) {
			try {
				await deleteClass(userId, classId)
				await loadData()
			} catch (error) {
				alert('Gabim në fshirjen e klasës')
			}
		}
	}

	const handleDeleteLevel = async (levelId: number) => {
		if (confirm('Jeni të sigurt që dëshironi të fshini këtë nivel?')) {
			try {
				await deleteLevel(userId, levelId)
				await loadData()
			} catch (error) {
				alert('Gabim në fshirjen e nivelit')
			}
		}
	}

	const handleDeleteExercise = async (exerciseId: number) => {
		if (confirm('Jeni të sigurt që dëshironi të fshini këtë ushtrim?')) {
			try {
				await deleteExercise(userId, exerciseId)
				await loadData()
			} catch (error) {
				alert('Gabim në fshirjen e ushtrimit')
			}
		}
	}

	const handleUpdateUser = async (userData: Partial<UserOut>) => {
		if (!editingUser) return
		try {
			await updateUser(userId, editingUser.id, userData)
			await loadData()
			setEditingUser(null)
		} catch (error) {
			alert('Gabim në përditësimin e përdoruesit')
		}
	}

	const handleUpdateClass = async (classData: Partial<ClassData>) => {
		if (!editingClass) return
		try {
			await updateClass(userId, editingClass.id, classData)
			await loadData()
			setEditingClass(null)
		} catch (error) {
			alert('Gabim në përditësimin e klasës')
		}
	}

	const handleUpdateLevel = async (levelData: Partial<LevelOut>) => {
		if (!editingLevel) return
		try {
			await updateLevel(userId, editingLevel.id, levelData)
			await loadData()
			setEditingLevel(null)
		} catch (error) {
			alert('Gabim në përditësimin e nivelit')
		}
	}

	const handleUpdateExercise = async (exerciseData: Partial<ExerciseOut>) => {
		if (!editingExercise) return
		try {
			await updateExercise(userId, editingExercise.id, exerciseData)
			await loadData()
			setEditingExercise(null)
		} catch (error) {
			alert('Gabim në përditësimin e ushtrimit')
		}
	}

	const handleEditClass = (cls: ClassData) => {
		setEditingClass(cls)
	}

	const handleEditLevel = (level: LevelOut) => {
		setEditingLevel(level)
	}

	// Helper function to get class name for a level
	const getLevelClassName = (level: LevelOut): string => {
		// Find the course for this level
		const course = classes.flatMap(cls => cls.courses || []).find(c => c.id === level.course_id)
		if (course && course.parent_class_id) {
			// Find the class
			const classData = classes.find(cls => cls.id === course.parent_class_id)
			if (classData) {
				return classData.name
			}
		}
		return '-'
	}

	// Helper function to get level display name with class (global numbering across all classes)
	const getLevelDisplayName = (level: LevelOut): string => {
		// Find the course for this level
		const course = classes.flatMap(cls => cls.courses || []).find(c => c.id === level.course_id)
		if (course && course.parent_class_id) {
			// Find the class
			const classData = classes.find(cls => cls.id === course.parent_class_id)
			if (classData) {
				// Calculate global level number: sum of all levels in previous classes + levels in current class before this level
				let globalLevelNumber = 0
				// Sort classes by order_index
				const sortedClasses = [...classes].sort((a, b) => a.order_index - b.order_index)
				
				for (const cls of sortedClasses) {
					if (cls.id === classData.id) {
						// We're in the current class
						// Sort courses by order_index
						const sortedCourses = [...(cls.courses || [])].sort((a, b) => a.order_index - b.order_index)
						
						for (const c of sortedCourses) {
							if (c.id === course.id) {
								// We're in the current course
								// Sort levels by order_index
								const sortedLevels = [...(c.levels || [])].sort((a, b) => a.order_index - b.order_index)
								// Find the position of current level
								const levelIndex = sortedLevels.findIndex(l => l.id === level.id)
								globalLevelNumber += levelIndex + 1
								break
							} else {
								// Add all levels from this previous course in the same class
								const courseLevels = c.levels || []
								globalLevelNumber += courseLevels.length
							}
						}
						break
					} else {
						// Add all levels from this previous class
						// Sort courses by order_index and count all levels
						const sortedCourses = [...(cls.courses || [])].sort((a, b) => a.order_index - b.order_index)
						for (const c of sortedCourses) {
							const courseLevels = c.levels || []
							globalLevelNumber += courseLevels.length
						}
					}
				}
				
				// Get class number with fallback to prevent "undefined"
				const classNumber = classData.order_index || classes.findIndex(c => c.id === classData.id) + 1 || 1
				return `Niveli ${globalLevelNumber} Klasa ${classNumber}`
			}
		}
		// Fallback to original name if class not found
		return level.name
	}

	// Debounce corpus API search so typing does not spam requests
	useEffect(() => {
		if (activeTab !== 'corpus') return
		const timer = window.setTimeout(() => {
			const next = corpusSearchDraft.trim() || undefined
			setCorpusFilters((prev) => {
				if ((prev.search || undefined) === next) return prev
				return { ...prev, search: next }
			})
			setCorpusPage(0)
		}, 320)
		return () => window.clearTimeout(timer)
	}, [corpusSearchDraft, activeTab])

	const filteredUsers = useMemo(
		() =>
			filterBySearch(users, usersSearch, (user) => [
				user.id,
				user.first_name,
				user.last_name,
				user.username,
				user.email,
				user.age,
				user.is_active ? 'aktiv' : 'jo aktiv',
				user.is_admin ? 'administrator' : 'perdorues',
			]),
		[users, usersSearch]
	)

	const filteredClasses = useMemo(
		() =>
			filterBySearch(classes, classesSearch, (cls) => [
				cls.id,
				cls.name,
				cls.description,
				cls.enabled ? 'aktiv' : 'jo aktiv',
				(cls.courses || []).length,
			]),
		[classes, classesSearch]
	)

	const filteredLevels = useMemo(
		() =>
			filterBySearch(levels, levelsSearch, (level) => [
				level.id,
				level.name,
				level.description,
				level.course_id,
				level.enabled ? 'aktiv' : 'jo aktiv',
				getLevelDisplayName(level),
				getLevelClassName(level),
			]),
		// helpers depend on classes; include classes so names stay in sync
		// eslint-disable-next-line react-hooks/exhaustive-deps
		[levels, levelsSearch, classes]
	)

	const filteredExercises = useMemo(
		() =>
			filterBySearch(exercises, exercisesSearch, (exercise) => [
				exercise.id,
				exercise.prompt,
				exercise.category,
				exercise.level_id,
				exercise.points,
				(exercise as any).rule,
				(exercise as any).type,
			]),
		[exercises, exercisesSearch]
	)

	const filteredCorpusByClass = useMemo(() => {
		const rows = corpusStats?.by_class || []
		return filterBySearch(rows, corpusPerClassSearch, (row) => [
			row.class_id,
			row.class_name,
			row.documents,
			row.tokens,
			row.lemmas,
		])
	}, [corpusStats, corpusPerClassSearch])

	const filteredShortWords = useMemo(
		() =>
			filterBySearch(linguisticMetrics?.top_short_words || [], corpusWordsSearch, (row) => [
				row.word,
				row.count,
			]),
		[linguisticMetrics, corpusWordsSearch]
	)

	const filteredLongWords = useMemo(
		() =>
			filterBySearch(linguisticMetrics?.top_long_words || [], corpusWordsSearch, (row) => [
				row.word,
				row.count,
			]),
		[linguisticMetrics, corpusWordsSearch]
	)

	const filteredWordFreqs = useMemo(
		() =>
			filterBySearch(corpusWordFreqs?.top_words || [], corpusWordsSearch, (row) => [
				row.word,
				row.count,
			]),
		[corpusWordFreqs, corpusWordsSearch]
	)

	return (
		<div className="admin-dashboard">
			<Suspense fallback={chartFallback}>
			<div className="admin-header">
				<div className="admin-header-brand">
					<BrandLogo size={36} className="brand-logo-sm" decorative />
					<div>
						<span className="admin-header-eyebrow">AlbLingo</span>
						<h1>Paneli i Administratorit</h1>
					</div>
				</div>
				<button className="admin-logout-btn" onClick={onLogout}>Dil</button>
			</div>

			<div className="admin-tabs">
				<button className={activeTab === 'stats' ? 'active' : ''} onClick={() => setActiveTab('stats')}>
					Statistika
				</button>
				<button className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>
					Përdoruesit
				</button>
				<button className={activeTab === 'classes' ? 'active' : ''} onClick={() => setActiveTab('classes')}>
					Klasat
				</button>
				<button className={activeTab === 'levels' ? 'active' : ''} onClick={() => setActiveTab('levels')}>
					Nivelet
				</button>
				<button className={activeTab === 'exercises' ? 'active' : ''} onClick={() => setActiveTab('exercises')}>
					Ushtrimet
				</button>
				<button className={activeTab === 'corpus' ? 'active' : ''} onClick={() => setActiveTab('corpus')}>
					Korpusi
				</button>
				<button className={activeTab === 'research' ? 'active' : ''} onClick={() => setActiveTab('research')}>
					🤖 Sistemi AI
				</button>
			</div>

			<div className="admin-content">
				{loadError && (
					<div className="admin-loading" role="alert">
						{loadError}
						<button type="button" className="create-btn" style={{ marginLeft: 12 }} onClick={() => loadData()}>
							Provo përsëri
						</button>
					</div>
				)}
				{loading ? (
					<PageLoading className="admin-page-loading" />
				) : (
					<>
					{activeTab === 'stats' && stats && (
						<Suspense fallback={chartFallback}>
							<AdminCharts
								kind="stats"
								stats={stats}
								periodStats={periodStats}
								periodLoading={periodLoading}
								timeRange={timeRange}
								onTimeRangeChange={setTimeRange}
								isExporting={isExporting}
								onExportCSV={handleExportCSV}
								onExportJSON={handleExportJSON}
								onExportPDF={handleExportPDF}
								onExportExcel={handleExportExcel}
							/>
						</Suspense>
					)}
					{false && activeTab === 'stats' && stats && (
						<>
							<div className="stats-grid">
								<div className="stat-card">
									<div className="stat-icon">👥</div>
									<div className="stat-value">{stats.total_users}</div>
									<div className="stat-label">Përdorues</div>
								</div>
								<div className="stat-card">
									<div className="stat-icon">🏫</div>
									<div className="stat-value">{stats.total_classes}</div>
									<div className="stat-label">Klasa</div>
								</div>
								<div className="stat-card">
									<div className="stat-icon">📚</div>
									<div className="stat-value">{stats.total_courses}</div>
									<div className="stat-label">Kurse</div>
								</div>
								<div className="stat-card">
									<div className="stat-icon">📖</div>
									<div className="stat-value">{stats.total_levels}</div>
									<div className="stat-label">Nivele</div>
								</div>
								<div className="stat-card">
									<div className="stat-icon">✏️</div>
									<div className="stat-value">{stats.total_exercises}</div>
									<div className="stat-label">Ushtrime</div>
								</div>
								<div className="stat-card">
									<div className="stat-icon">🎯</div>
									<div className="stat-value">{stats.total_attempts}</div>
									<div className="stat-label">Përpjekje</div>
								</div>
							</div>

							{/* Time Range Selector */}
							<div className="time-range-selector">
								<h3 className="selector-title">📅 Zgjedh Periudhën Kohore</h3>
								<div className="selector-buttons">
									<button 
										className={`selector-btn ${timeRange === 'weekly' ? 'active' : ''}`}
										onClick={() => setTimeRange('weekly')}
									>
										📊 Javore
									</button>
									<button 
										className={`selector-btn ${timeRange === 'monthly' ? 'active' : ''}`}
										onClick={() => setTimeRange('monthly')}
									>
										📈 Mujore
									</button>
									<button 
										className={`selector-btn ${timeRange === 'yearly' ? 'active' : ''}`}
										onClick={() => setTimeRange('yearly')}
									>
										📉 Vjetore
									</button>
								</div>
							</div>

							{/* Charts Section */}
							<div className="charts-container">
								<div className="chart-card">
									<h3 className="chart-title">📊 Përmbledhje e Përgjithshme</h3>
									<ResponsiveContainer width="100%" height={300}>
										<BarChart
											data={[
												{ name: 'Përdorues', value: stats.total_users, fill: '#4A9FD4' },
												{ name: 'Klasa', value: stats.total_classes, fill: '#5BBD6C' },
												{ name: 'Kurse', value: stats.total_courses, fill: '#FFC800' },
												{ name: 'Nivele', value: stats.total_levels, fill: '#FF9600' },
												{ name: 'Ushtrime', value: stats.total_exercises, fill: '#CE82FF' },
												{ name: 'Përpjekje', value: stats.total_attempts, fill: '#FF4B8C' },
											]}
											margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
										>
											<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
											<XAxis 
												dataKey="name" 
												tick={{ fill: '#64748b', fontSize: 12 }}
												tickLine={{ stroke: '#cbd5e1' }}
											/>
											<YAxis 
												tick={{ fill: '#64748b', fontSize: 12 }}
												tickLine={{ stroke: '#cbd5e1' }}
											/>
											<Tooltip 
												contentStyle={{
													backgroundColor: 'white',
													border: '1px solid #e2e8f0',
													borderRadius: '8px',
													boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
												}}
											/>
											<Bar 
												dataKey="value" 
												radius={[8, 8, 0, 0]}
											/>
										</BarChart>
									</ResponsiveContainer>
								</div>

								<div className="charts-row">
									<div className="chart-card chart-card-half">
										<h3 className="chart-title">🥧 Shpërndarja e Përmbajtjes</h3>
										<ResponsiveContainer width="100%" height={300}>
											<PieChart>
												<Pie
													data={[
														{ name: 'Klasa', value: stats.total_classes, fill: '#5BBD6C' },
														{ name: 'Kurse', value: stats.total_courses, fill: '#FFC800' },
														{ name: 'Nivele', value: stats.total_levels, fill: '#FF9600' },
														{ name: 'Ushtrime', value: stats.total_exercises, fill: '#CE82FF' },
													]}
													cx="50%"
													cy="50%"
													labelLine={false}
													label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
													outerRadius={80}
													fill="#8884d8"
													dataKey="value"
												>
													{[
														{ name: 'Klasa', value: stats.total_classes, fill: '#5BBD6C' },
														{ name: 'Kurse', value: stats.total_courses, fill: '#FFC800' },
														{ name: 'Nivele', value: stats.total_levels, fill: '#FF9600' },
														{ name: 'Ushtrime', value: stats.total_exercises, fill: '#CE82FF' },
													].map((entry, index) => (
														<Cell key={`cell-${index}`} fill={entry.fill} />
													))}
												</Pie>
												<Tooltip 
													contentStyle={{
														backgroundColor: 'white',
														border: '1px solid #e2e8f0',
														borderRadius: '8px',
														boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
													}}
												/>
											</PieChart>
										</ResponsiveContainer>
									</div>

									<div className="chart-card chart-card-half">
										<h3 className="chart-title">📈 Aktiviteti i Përdoruesve</h3>
										<ResponsiveContainer width="100%" height={300}>
											<BarChart
												data={[
													{ name: 'Totali', përdorues: stats.total_users, përpjekje: Math.round(stats.total_attempts / 100) },
													{ name: 'Aktivë', përdorues: Math.round(stats.total_users * 0.7), përpjekje: Math.round(stats.total_attempts / 100 * 0.8) },
													{ name: 'Jo-aktivë', përdorues: Math.round(stats.total_users * 0.3), përpjekje: Math.round(stats.total_attempts / 100 * 0.2) },
												]}
												margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
											>
												<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
												<XAxis 
													dataKey="name" 
													tick={{ fill: '#64748b', fontSize: 12 }}
												/>
												<YAxis 
													tick={{ fill: '#64748b', fontSize: 12 }}
												/>
												<Tooltip 
													contentStyle={{
														backgroundColor: 'white',
														border: '1px solid #e2e8f0',
														borderRadius: '8px',
														boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
													}}
												/>
												<Legend />
												<Bar dataKey="përdorues" fill="#4A9FD4" radius={[8, 8, 0, 0]} />
												<Bar dataKey="përpjekje" fill="#5BBD6C" radius={[8, 8, 0, 0]} />
											</BarChart>
										</ResponsiveContainer>
									</div>
								</div>

								<div className="chart-card">
									<h3 className="chart-title">📉 Trend Statistikash</h3>
									<ResponsiveContainer width="100%" height={300}>
										<LineChart
											data={[
												{ muaj: 'Jan', përdorues: Math.round(stats.total_users * 0.3), ushtrime: Math.round(stats.total_exercises * 0.4) },
												{ muaj: 'Feb', përdorues: Math.round(stats.total_users * 0.4), ushtrime: Math.round(stats.total_exercises * 0.5) },
												{ muaj: 'Mar', përdorues: Math.round(stats.total_users * 0.5), ushtrime: Math.round(stats.total_exercises * 0.6) },
												{ muaj: 'Apr', përdorues: Math.round(stats.total_users * 0.6), ushtrime: Math.round(stats.total_exercises * 0.7) },
												{ muaj: 'Maj', përdorues: Math.round(stats.total_users * 0.75), ushtrime: Math.round(stats.total_exercises * 0.85) },
												{ muaj: 'Qer', përdorues: Math.round(stats.total_users * 0.9), ushtrime: Math.round(stats.total_exercises * 0.95) },
												{ muaj: 'Kor', përdorues: stats.total_users, ushtrime: stats.total_exercises },
											]}
											margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
										>
											<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
											<XAxis 
												dataKey="muaj" 
												tick={{ fill: '#64748b', fontSize: 12 }}
											/>
											<YAxis 
												tick={{ fill: '#64748b', fontSize: 12 }}
											/>
											<Tooltip 
												contentStyle={{
													backgroundColor: 'white',
													border: '1px solid #e2e8f0',
													borderRadius: '8px',
													boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
												}}
											/>
											<Legend />
											<Line 
												type="monotone" 
												dataKey="përdorues" 
												stroke="#4A9FD4" 
												strokeWidth={3}
												dot={{ fill: '#4A9FD4', r: 5 }}
												activeDot={{ r: 7 }}
											/>
											<Line 
												type="monotone" 
												dataKey="ushtrime" 
												stroke="#5BBD6C" 
												strokeWidth={3}
												dot={{ fill: '#5BBD6C', r: 5 }}
												activeDot={{ r: 7 }}
											/>
										</LineChart>
									</ResponsiveContainer>
								</div>

								{/* Scientific Analytics Section */}
								<div className="scientific-section">
									<h2 className="section-title">🔬 Analiza Shkencore</h2>
									
									{/* Weekly Analysis */}
									{timeRange === 'weekly' && (
										<>
											<div className="chart-card">
												<h3 className="chart-title">📅 Statistika Javore - Aktiviteti Ditor</h3>
												<ResponsiveContainer width="100%" height={350}>
													<ComposedChart
														data={[
															{ ditë: 'E Hënë', përdorues: Math.round(stats.total_users * 0.15), përpjekje: Math.round(stats.total_attempts * 0.12), suksese: Math.round(stats.total_attempts * 0.10), sukseRate: 83 },
															{ ditë: 'E Martë', përdorues: Math.round(stats.total_users * 0.18), përpjekje: Math.round(stats.total_attempts * 0.15), suksese: Math.round(stats.total_attempts * 0.13), sukseRate: 87 },
															{ ditë: 'E Mërkurë', përdorues: Math.round(stats.total_users * 0.20), përpjekje: Math.round(stats.total_attempts * 0.18), suksese: Math.round(stats.total_attempts * 0.16), sukseRate: 89 },
															{ ditë: 'E Enjte', përdorues: Math.round(stats.total_users * 0.17), përpjekje: Math.round(stats.total_attempts * 0.16), suksese: Math.round(stats.total_attempts * 0.14), sukseRate: 88 },
															{ ditë: 'E Premte', përdorues: Math.round(stats.total_users * 0.14), përpjekje: Math.round(stats.total_attempts * 0.14), suksese: Math.round(stats.total_attempts * 0.12), sukseRate: 86 },
															{ ditë: 'E Shtunë', përdorues: Math.round(stats.total_users * 0.10), përpjekje: Math.round(stats.total_attempts * 0.10), suksese: Math.round(stats.total_attempts * 0.08), sukseRate: 80 },
															{ ditë: 'E Diel', përdorues: Math.round(stats.total_users * 0.08), përpjekje: Math.round(stats.total_attempts * 0.08), suksese: Math.round(stats.total_attempts * 0.06), sukseRate: 75 },
														]}
														margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
													>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="ditë" tick={{ fill: '#64748b', fontSize: 12 }} />
														<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
														<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Legend />
														<Bar yAxisId="left" dataKey="përdorues" fill="#4A9FD4" radius={[8, 8, 0, 0]} name="Përdorues Aktivë" />
														<Bar yAxisId="left" dataKey="përpjekje" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Përpjekje" />
														<Line yAxisId="right" type="monotone" dataKey="sukseRate" stroke="#FF9600" strokeWidth={3} name="% Suksesi" />
													</ComposedChart>
												</ResponsiveContainer>
											</div>

											<div className="charts-row">
												<div className="chart-card chart-card-half">
													<h3 className="chart-title">🕐 Orët më të Frekuentuara (Javore)</h3>
													<ResponsiveContainer width="100%" height={300}>
														<BarChart
															data={[
																{ orë: '08:00', aktivitet: Math.round(stats.total_users * 0.05) },
																{ orë: '10:00', aktivitet: Math.round(stats.total_users * 0.15) },
																{ orë: '12:00', aktivitet: Math.round(stats.total_users * 0.20) },
																{ orë: '14:00', aktivitet: Math.round(stats.total_users * 0.25) },
																{ orë: '16:00', aktivitet: Math.round(stats.total_users * 0.30) },
																{ orë: '18:00', aktivitet: Math.round(stats.total_users * 0.20) },
																{ orë: '20:00', aktivitet: Math.round(stats.total_users * 0.15) },
																{ orë: '22:00', aktivitet: Math.round(stats.total_users * 0.08) },
															]}
															margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
														>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="orë" tick={{ fill: '#64748b', fontSize: 11 }} />
															<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Bar dataKey="aktivitet" fill="#CE82FF" radius={[8, 8, 0, 0]} name="Përdorues Aktivë" />
														</BarChart>
													</ResponsiveContainer>
												</div>

												<div className="chart-card chart-card-half">
													<h3 className="chart-title">🎯 Performanca Javore sipas Kategorisë</h3>
													<ResponsiveContainer width="100%" height={300}>
														<RadarChart data={[
															{ kategori: 'Vocabulary', pikë: 85 },
															{ kategori: 'Grammar', pikë: 78 },
															{ kategori: 'Writing', pikë: 92 },
															{ kategori: 'Reading', pikë: 88 },
															{ kategori: 'Listening', pikë: 75 },
														]}>
															<PolarGrid stroke="#e2e8f0" />
															<PolarAngleAxis dataKey="kategori" tick={{ fill: '#64748b', fontSize: 11 }} />
															<PolarRadiusAxis tick={{ fill: '#64748b', fontSize: 10 }} />
															<Radar name="Performanca %" dataKey="pikë" stroke="#4A9FD4" fill="#4A9FD4" fillOpacity={0.6} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														</RadarChart>
													</ResponsiveContainer>
												</div>
											</div>
										</>
									)}

									{/* Monthly Analysis */}
									{timeRange === 'monthly' && (
										<>
											<div className="chart-card">
												<h3 className="chart-title">📆 Statistika Mujore - Trend 12 Muaj</h3>
												<ResponsiveContainer width="100%" height={350}>
													<AreaChart
														data={[
															{ muaj: 'Jan 2025', përdorues: Math.round(stats.total_users * 0.20), ushtrime: Math.round(stats.total_exercises * 0.30), engagement: 65 },
															{ muaj: 'Shk', përdorues: Math.round(stats.total_users * 0.25), ushtrime: Math.round(stats.total_exercises * 0.35), engagement: 68 },
															{ muaj: 'Mar', përdorues: Math.round(stats.total_users * 0.35), ushtrime: Math.round(stats.total_exercises * 0.45), engagement: 72 },
															{ muaj: 'Pri', përdorues: Math.round(stats.total_users * 0.45), ushtrime: Math.round(stats.total_exercises * 0.55), engagement: 75 },
															{ muaj: 'Maj', përdorues: Math.round(stats.total_users * 0.55), ushtrime: Math.round(stats.total_exercises * 0.65), engagement: 78 },
															{ muaj: 'Qer', përdorues: Math.round(stats.total_users * 0.65), ushtrime: Math.round(stats.total_exercises * 0.75), engagement: 80 },
															{ muaj: 'Kor', përdorues: Math.round(stats.total_users * 0.70), ushtrime: Math.round(stats.total_exercises * 0.80), engagement: 82 },
															{ muaj: 'Gus', përdorues: Math.round(stats.total_users * 0.78), ushtrime: Math.round(stats.total_exercises * 0.85), engagement: 85 },
															{ muaj: 'Sht', përdorues: Math.round(stats.total_users * 0.85), ushtrime: Math.round(stats.total_exercises * 0.90), engagement: 88 },
															{ muaj: 'Tet', përdorues: Math.round(stats.total_users * 0.90), ushtrime: Math.round(stats.total_exercises * 0.93), engagement: 90 },
															{ muaj: 'Nën', përdorues: Math.round(stats.total_users * 0.95), ushtrime: Math.round(stats.total_exercises * 0.97), engagement: 92 },
															{ muaj: 'Dhj', përdorues: stats.total_users, ushtrime: stats.total_exercises, engagement: 95 },
														]}
														margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
													>
														<defs>
															<linearGradient id="colorPerdorues" x1="0" y1="0" x2="0" y2="1">
																<stop offset="5%" stopColor="#4A9FD4" stopOpacity={0.8}/>
																<stop offset="95%" stopColor="#4A9FD4" stopOpacity={0.1}/>
															</linearGradient>
															<linearGradient id="colorUshtrime" x1="0" y1="0" x2="0" y2="1">
																<stop offset="5%" stopColor="#5BBD6C" stopOpacity={0.8}/>
																<stop offset="95%" stopColor="#5BBD6C" stopOpacity={0.1}/>
															</linearGradient>
														</defs>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="muaj" tick={{ fill: '#64748b', fontSize: 11 }} />
														<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Legend />
														<Area type="monotone" dataKey="përdorues" stroke="#4A9FD4" fillOpacity={1} fill="url(#colorPerdorues)" name="Përdorues" />
														<Area type="monotone" dataKey="ushtrime" stroke="#5BBD6C" fillOpacity={1} fill="url(#colorUshtrime)" name="Ushtrime" />
													</AreaChart>
												</ResponsiveContainer>
											</div>

											<div className="charts-row">
												<div className="chart-card chart-card-half">
													<h3 className="chart-title">📊 Retention Rate Mujore</h3>
													<ResponsiveContainer width="100%" height={300}>
														<LineChart
															data={[
																{ muaj: 'M1', retention: 95, newUsers: 120 },
																{ muaj: 'M2', retention: 92, newUsers: 135 },
																{ muaj: 'M3', retention: 90, newUsers: 150 },
																{ muaj: 'M4', retention: 89, newUsers: 145 },
																{ muaj: 'M5', retention: 91, newUsers: 160 },
																{ muaj: 'M6', retention: 93, newUsers: 175 },
																{ muaj: 'M7', retention: 94, newUsers: 180 },
																{ muaj: 'M8', retention: 95, newUsers: 190 },
																{ muaj: 'M9', retention: 96, newUsers: 200 },
																{ muaj: 'M10', retention: 96, newUsers: 210 },
																{ muaj: 'M11', retention: 97, newUsers: 220 },
																{ muaj: 'M12', retention: 97, newUsers: 230 },
															]}
															margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
														>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="muaj" tick={{ fill: '#64748b', fontSize: 11 }} />
															<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
															<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Legend />
															<Line yAxisId="left" type="monotone" dataKey="retention" stroke="#5BBD6C" strokeWidth={3} name="Retention %" />
															<Line yAxisId="right" type="monotone" dataKey="newUsers" stroke="#4A9FD4" strokeWidth={3} name="Përdorues të Rinj" />
														</LineChart>
													</ResponsiveContainer>
												</div>

												<div className="chart-card chart-card-half">
													<h3 className="chart-title">🎓 Përparimi Mesatar Mujor</h3>
													<ResponsiveContainer width="100%" height={300}>
														<BarChart
															data={[
																{ nivel: 'Fillestar', përdorues: Math.round(stats.total_users * 0.35), mesatare: 65 },
																{ nivel: 'Mesatar', përdorues: Math.round(stats.total_users * 0.40), mesatare: 78 },
																{ nivel: 'I avancuar', përdorues: Math.round(stats.total_users * 0.20), mesatare: 88 },
																{ nivel: 'Ekspert', përdorues: Math.round(stats.total_users * 0.05), mesatare: 95 },
															]}
															margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
														>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="nivel" tick={{ fill: '#64748b', fontSize: 11 }} />
															<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
															<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Legend />
															<Bar yAxisId="left" dataKey="përdorues" fill="#CE82FF" radius={[8, 8, 0, 0]} name="Numri Përdoruesve" />
															<Line yAxisId="right" type="monotone" dataKey="mesatare" stroke="#FF9600" strokeWidth={3} name="Pikë Mesatare" />
														</BarChart>
													</ResponsiveContainer>
												</div>
											</div>

											<div className="chart-card">
												<h3 className="chart-title">📈 Nota e angazhimit & Koha e kaluar (minutë/sesion)</h3>
												<ResponsiveContainer width="100%" height={300}>
													<ComposedChart
														data={[
															{ muaj: 'Jan', engagement: 65, kohëMinuta: 12, përfundim: 72 },
															{ muaj: 'Shk', engagement: 68, kohëMinuta: 14, përfundim: 75 },
															{ muaj: 'Mar', engagement: 72, kohëMinuta: 16, përfundim: 78 },
															{ muaj: 'Pri', engagement: 75, kohëMinuta: 18, përfundim: 80 },
															{ muaj: 'Maj', engagement: 78, kohëMinuta: 20, përfundim: 83 },
															{ muaj: 'Qer', engagement: 80, kohëMinuta: 22, përfundim: 85 },
															{ muaj: 'Kor', engagement: 82, kohëMinuta: 24, përfundim: 87 },
															{ muaj: 'Gus', engagement: 85, kohëMinuta: 26, përfundim: 89 },
															{ muaj: 'Sht', engagement: 88, kohëMinuta: 28, përfundim: 91 },
															{ muaj: 'Tet', engagement: 90, kohëMinuta: 30, përfundim: 93 },
															{ muaj: 'Nën', engagement: 92, kohëMinuta: 32, përfundim: 95 },
															{ muaj: 'Dhj', engagement: 95, kohëMinuta: 35, përfundim: 97 },
														]}
														margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
													>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="muaj" tick={{ fill: '#64748b', fontSize: 11 }} />
														<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
														<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Legend />
														<Area yAxisId="left" type="monotone" dataKey="engagement" fill="#4A9FD4" stroke="#4A9FD4" fillOpacity={0.3} name="Engagement %" />
														<Bar yAxisId="right" dataKey="kohëMinuta" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Minutë/Sesion" />
														<Line yAxisId="left" type="monotone" dataKey="përfundim" stroke="#FF9600" strokeWidth={3} name="% Përfundimi" />
													</ComposedChart>
												</ResponsiveContainer>
											</div>
										</>
									)}

									{/* Yearly Analysis */}
									{timeRange === 'yearly' && (
										<>
											<div className="chart-card">
												<h3 className="chart-title">📅 Statistika Vjetore - Krahasim 5 Vjet</h3>
												<ResponsiveContainer width="100%" height={350}>
													<BarChart
														data={[
															{ vit: '2021', përdorues: Math.round(stats.total_users * 0.15), ushtrime: Math.round(stats.total_exercises * 0.20), revenue: 5000 },
															{ vit: '2022', përdorues: Math.round(stats.total_users * 0.35), ushtrime: Math.round(stats.total_exercises * 0.40), revenue: 12000 },
															{ vit: '2023', përdorues: Math.round(stats.total_users * 0.60), ushtrime: Math.round(stats.total_exercises * 0.65), revenue: 25000 },
															{ vit: '2024', përdorues: Math.round(stats.total_users * 0.85), ushtrime: Math.round(stats.total_exercises * 0.85), revenue: 42000 },
															{ vit: '2025', përdorues: stats.total_users, ushtrime: stats.total_exercises, revenue: 68000 },
														]}
														margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
													>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="vit" tick={{ fill: '#64748b', fontSize: 12 }} />
														<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Legend />
														<Bar dataKey="përdorues" fill="#4A9FD4" radius={[8, 8, 0, 0]} name="Përdorues" />
														<Bar dataKey="ushtrime" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Ushtrime" />
													</BarChart>
												</ResponsiveContainer>
											</div>

											<div className="charts-row">
												<div className="chart-card chart-card-half">
													<h3 className="chart-title">📊 Rritja Vjetore (%)</h3>
													<ResponsiveContainer width="100%" height={300}>
														<LineChart
															data={[
																{ vit: '2021', rritjaPërdorues: 0, rritjaUshtrime: 0 },
																{ vit: '2022', rritjaPërdorues: 133, rritjaUshtrime: 100 },
																{ vit: '2023', rritjaPërdorues: 71, rritjaUshtrime: 63 },
																{ vit: '2024', rritjaPërdorues: 42, rritjaUshtrime: 31 },
																{ vit: '2025', rritjaPërdorues: 18, rritjaUshtrime: 18 },
															]}
															margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
														>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="vit" tick={{ fill: '#64748b', fontSize: 12 }} />
															<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Legend />
															<Line type="monotone" dataKey="rritjaPërdorues" stroke="#4A9FD4" strokeWidth={3} name="Rritja Përdoruesve %" />
															<Line type="monotone" dataKey="rritjaUshtrime" stroke="#5BBD6C" strokeWidth={3} name="Rritja Ushtrimeve %" />
														</LineChart>
													</ResponsiveContainer>
												</div>

												<div className="chart-card chart-card-half">
													<h3 className="chart-title">🎯 Arritjet Vjetore</h3>
													<ResponsiveContainer width="100%" height={300}>
														<BarChart
															data={[
																{ kategori: 'Certifikata', '2023': 150, '2024': 320, '2025': 580 },
																{ kategori: 'Kurse Përfunduar', '2023': 450, '2024': 890, '2025': 1450 },
																{ kategori: 'Nivele Kaluar', '2023': 2100, '2024': 4200, '2025': 6800 },
															]}
															margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
														>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="kategori" tick={{ fill: '#64748b', fontSize: 11 }} />
															<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Legend />
															<Bar dataKey="2023" fill="#CE82FF" radius={[8, 8, 0, 0]} />
															<Bar dataKey="2024" fill="#FF9600" radius={[8, 8, 0, 0]} />
															<Bar dataKey="2025" fill="#5BBD6C" radius={[8, 8, 0, 0]} />
														</BarChart>
													</ResponsiveContainer>
												</div>
											</div>

											<div className="chart-card">
												<h3 className="chart-title">🌍 Shpërndarja Demografike Vjetore</h3>
												<ResponsiveContainer width="100%" height={300}>
													<ComposedChart
														data={[
															{ grup: '6-8 vjeç', përdorues: Math.round(stats.total_users * 0.25), engagement: 85, suksesRate: 78 },
															{ grup: '9-11 vjeç', përdorues: Math.round(stats.total_users * 0.35), engagement: 88, suksesRate: 82 },
															{ grup: '12-14 vjeç', përdorues: Math.round(stats.total_users * 0.25), engagement: 90, suksesRate: 86 },
															{ grup: '15-17 vjeç', përdorues: Math.round(stats.total_users * 0.10), engagement: 87, suksesRate: 88 },
															{ grup: '18+ vjeç', përdorues: Math.round(stats.total_users * 0.05), engagement: 92, suksesRate: 91 },
														]}
														margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
													>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="grup" tick={{ fill: '#64748b', fontSize: 11 }} />
														<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
														<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Legend />
														<Bar yAxisId="left" dataKey="përdorues" fill="#4A9FD4" radius={[8, 8, 0, 0]} name="Numri Përdoruesve" />
														<Line yAxisId="right" type="monotone" dataKey="engagement" stroke="#5BBD6C" strokeWidth={3} name="Engagement %" />
														<Line yAxisId="right" type="monotone" dataKey="suksesRate" stroke="#FF9600" strokeWidth={3} name="Sukses Rate %" />
													</ComposedChart>
												</ResponsiveContainer>
											</div>

											<div className="chart-card">
												<h3 className="chart-title">📚 Performanca e Platformës - Metriks Kyçe (KPIs)</h3>
												<ResponsiveContainer width="100%" height={300}>
													<RadarChart data={[
														{ metrik: 'Kënaqësia e përdoruesit', pikë: 92, maksimum: 100 },
														{ metrik: 'Learning Effectiveness', pikë: 88, maksimum: 100 },
														{ metrik: 'Content Quality', pikë: 95, maksimum: 100 },
														{ metrik: 'Platform Stability', pikë: 97, maksimum: 100 },
														{ metrik: 'Rikthimi i përdoruesve', pikë: 89, maksimum: 100 },
														{ metrik: 'Engagement Rate', pikë: 85, maksimum: 100 },
													]}>
														<PolarGrid stroke="#e2e8f0" />
														<PolarAngleAxis dataKey="metrik" tick={{ fill: '#64748b', fontSize: 10 }} />
														<PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
														<Radar name="Performanca Aktuale" dataKey="pikë" stroke="#4A9FD4" fill="#4A9FD4" fillOpacity={0.6} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Legend />
													</RadarChart>
												</ResponsiveContainer>
											</div>
										</>
									)}

					{/* Export Data Section */}
					<div className="export-section">
						<h3 className="export-title">📥 Eksporto të Dhënat</h3>
						<p className="export-note" style={{ marginBottom: '15px' }}>
							💡 <strong>Shënim:</strong> Të dhënat e eksportuara përfshijnë statistika të detajuara, analiza kohore ({timeRange}), 
							dhe metriks shkencorë të përshtatshëm për publikime akademike dhe punime kërkimore.
						</p>
						<div className="export-buttons">
							<button 
								className="export-btn" 
								onClick={handleExportCSV}
								disabled={isExporting || !stats}
							>
								📊 Eksporto CSV
							</button>
							<button 
								className="export-btn" 
								onClick={handleExportJSON}
								disabled={isExporting || !stats}
							>
								🔧 Eksporto JSON
							</button>
							<button 
								className="export-btn" 
								onClick={handleExportPDF}
								disabled={isExporting || !stats}
							>
								📄 Gjenero Raport PDF
							</button>
							<button 
								className="export-btn" 
								onClick={handleExportExcel}
								disabled={isExporting || !stats}
							>
								📗 Eksporto Excel
							</button>
						</div>
						{isExporting && (
							<p style={{ textAlign: 'center', marginTop: '10px', color: '#4A9FD4', fontWeight: 'bold' }}>
								⏳ Duke eksportuar të dhënat...
							</p>
						)}
					</div>
								</div>
							</div>
						</>
					)}

						{activeTab === 'users' && (
							<div className="admin-table-container admin-table-container--cards">
								<div className="table-header">
									<h2>Përdoruesit</h2>
								</div>
								<div className="admin-list-toolbar">
									<AdminSearchBar
										value={usersSearch}
										onChange={setUsersSearch}
										placeholder="Kërko përdorues…"
										ariaLabel="Kërko përdorues"
									/>
								</div>
								<table className="admin-table admin-table--cards">
									<thead>
										<tr>
											<th>ID</th>
											<th>Emri / Mbiemri</th>
											<th>Username</th>
											<th>Email</th>
											<th>Moshë</th>
											<th>Gjendja</th>
											<th>Administrator</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{filteredUsers.map(user => (
											<tr key={user.id}>
												<td data-label="ID">{user.id}</td>
												<td data-label="Emri / Mbiemri">{[user.first_name, user.last_name].filter(Boolean).join(' ') || '—'}</td>
												<td data-label="Username">{user.username}</td>
												<td data-label="Email">{user.email}</td>
												<td data-label="Moshë">{user.age || '-'}</td>
												<td data-label="Gjendja">{user.is_active ? '✅ Aktiv' : '❌ Jo aktiv'}</td>
												<td data-label="Administrator">{user.is_admin ? '🛡️ Administrator' : '👤 Përdorues'}</td>
												<td data-label="Veprime">
													<div className="admin-actions">
														<button type="button" onClick={() => handleGenerateUserReport(user)}>📊 Raport</button>
														<button type="button" onClick={() => setEditingUser(user)}>✏️ Edito</button>
														<button type="button" onClick={() => handleDeleteUser(user.id)}>🗑️ Fshi</button>
													</div>
												</td>
											</tr>
										))}
										{filteredUsers.length === 0 && (
											<tr>
												<td colSpan={8} className="admin-search-empty">Nuk u gjetën rezultate</td>
											</tr>
										)}
									</tbody>
								</table>
							</div>
						)}

						{activeTab === 'classes' && (
							<div className="admin-table-container admin-table-container--cards">
								<div className="table-header">
									<h2>Klasat</h2>
									<button className="create-btn" onClick={() => setShowCreateModal('class')}>+ Shto Klasë</button>
								</div>
								<div className="admin-list-toolbar">
									<AdminSearchBar
										value={classesSearch}
										onChange={setClassesSearch}
										placeholder="Kërko klasa…"
										ariaLabel="Kërko klasa"
									/>
								</div>
								<table className="admin-table admin-table--cards">
									<thead>
										<tr>
											<th>ID</th>
											<th>Emër</th>
											<th>Përshkrim</th>
											<th>Kurse</th>
											<th>Gjendja</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{filteredClasses.map(cls => (
											<tr key={cls.id}>
												<td data-label="ID">{cls.id}</td>
												<td data-label="Emër">{cls.name}</td>
												<td data-label="Përshkrim">{cls.description || '-'}</td>
												<td data-label="Kurse">{(cls.courses || []).length}</td>
												<td data-label="Gjendja">{cls.enabled ? '✅ Aktiv' : '❌ Jo aktiv'}</td>
												<td data-label="Veprime">
													<div className="admin-actions">
														<button type="button" onClick={() => handleEditClass(cls)}>✏️ Edito</button>
														<button type="button" onClick={() => handleDeleteClass(cls.id)}>🗑️ Fshi</button>
													</div>
												</td>
											</tr>
										))}
										{filteredClasses.length === 0 && (
											<tr>
												<td colSpan={6} className="admin-search-empty">Nuk u gjetën rezultate</td>
											</tr>
										)}
									</tbody>
								</table>
							</div>
						)}

						{activeTab === 'levels' && (
							<div className="admin-table-container admin-table-container--cards">
								<div className="table-header">
									<h2>Nivelet</h2>
									<div>
										<select value={selectedClass || ''} onChange={(e) => setSelectedClass(e.target.value ? parseInt(e.target.value) : null)}>
											<option value="">Të gjitha klasat</option>
											{classes.map(cls => (
												<option key={cls.id} value={cls.id}>{cls.name}</option>
											))}
										</select>
										<button className="create-btn" onClick={() => setShowCreateModal('level')}>+ Shto Nivel</button>
									</div>
								</div>
								<div className="admin-list-toolbar">
									<AdminSearchBar
										value={levelsSearch}
										onChange={setLevelsSearch}
										placeholder="Kërko nivele…"
										ariaLabel="Kërko nivele"
									/>
								</div>
								<table className="admin-table admin-table--cards">
									<thead>
										<tr>
											<th>ID</th>
											<th>Emër</th>
											<th>Klasa</th>
											<th>Përshkrim</th>
											<th>Kurs ID</th>
											<th>Gjendja</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{filteredLevels.map(level => (
											<tr key={level.id}>
												<td data-label="ID">{level.id}</td>
												<td data-label="Emër">{getLevelDisplayName(level)}</td>
												<td data-label="Klasa">{getLevelClassName(level)}</td>
												<td data-label="Përshkrim">{level.description || '-'}</td>
												<td data-label="Kurs ID">{level.course_id}</td>
												<td data-label="Gjendja">{level.enabled ? '✅ Aktiv' : '❌ Jo aktiv'}</td>
												<td data-label="Veprime">
													<div className="admin-actions">
														<button type="button" onClick={() => handleEditLevel(level)}>✏️ Edito</button>
														<button type="button" onClick={() => handleDeleteLevel(level.id)}>🗑️ Fshi</button>
													</div>
												</td>
											</tr>
										))}
										{filteredLevels.length === 0 && (
											<tr>
												<td colSpan={7} className="admin-search-empty">Nuk u gjetën rezultate</td>
											</tr>
										)}
									</tbody>
								</table>
							</div>
						)}

						{activeTab === 'exercises' && (
							<div className="admin-table-container admin-table-container--cards">
								<div className="table-header">
									<h2>Ushtrimet</h2>
									<div>
										<select value={selectedLevel || ''} onChange={(e) => setSelectedLevel(e.target.value ? parseInt(e.target.value) : null)}>
											<option value="">Të gjitha nivelet</option>
											{levels.map(level => (
												<option key={level.id} value={level.id}>
													{getLevelDisplayName(level)} - {getLevelClassName(level)}
												</option>
											))}
										</select>
										<button className="create-btn" onClick={() => setShowCreateModal('exercise')}>+ Shto Ushtrim</button>
									</div>
								</div>
								<div className="admin-list-toolbar">
									<AdminSearchBar
										value={exercisesSearch}
										onChange={setExercisesSearch}
										placeholder="Kërko ushtrime…"
										ariaLabel="Kërko ushtrime"
									/>
								</div>
								<table className="admin-table admin-table--cards">
									<thead>
										<tr>
											<th>ID</th>
											<th>Prompt</th>
											<th>Kategori</th>
											<th>Nivel ID</th>
											<th>Pikë</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{filteredExercises.map(exercise => (
											<tr key={exercise.id}>
												<td data-label="ID">{exercise.id}</td>
												<td data-label="Prompt">{exercise.prompt.substring(0, 50)}...</td>
												<td data-label="Kategori">{exercise.category}</td>
												<td data-label="Nivel ID">{exercise.level_id}</td>
												<td data-label="Pikë">{exercise.points}</td>
												<td data-label="Veprime">
													<div className="admin-actions">
														<button type="button" onClick={() => setEditingExercise(exercise)}>✏️ Edito</button>
														<button type="button" onClick={() => handleDeleteExercise(exercise.id)}>🗑️ Fshi</button>
													</div>
												</td>
											</tr>
										))}
										{filteredExercises.length === 0 && (
											<tr>
												<td colSpan={6} className="admin-search-empty">Nuk u gjetën rezultate</td>
											</tr>
										)}
									</tbody>
								</table>
							</div>
						)}

						{/* ===== CORPUS TAB ===== */}
						{activeTab === 'corpus' && (
							<div className="corpus-dashboard">
								<div className="corpus-subtabs">
									<button className={corpusSubTab === 'overview' ? 'active' : ''} onClick={() => setCorpusSubTab('overview')}>Pasqyrë e Përgjithshme</button>
									<button className={corpusSubTab === 'documents' ? 'active' : ''} onClick={() => setCorpusSubTab('documents')}>Menaxhimi i Dokumenteve</button>
									<button className={corpusSubTab === 'linguistic' ? 'active' : ''} onClick={() => { setCorpusSubTab('linguistic'); if (!linguisticMetrics) loadLinguisticMetrics(); if (!corpusWordFreqs) loadCorpusWordFreqs() }}>Analiza Linguistike</button>
									<button className={corpusSubTab === 'classification' ? 'active' : ''} onClick={() => setCorpusSubTab('classification')}>Klasifikimi & Segmentimi</button>
									<button className={corpusSubTab === 'per_class' ? 'active' : ''} onClick={() => setCorpusSubTab('per_class')}>Statistika Sipas Klasës</button>
									<button className={corpusSubTab === 'validation' ? 'active' : ''} onClick={() => setCorpusSubTab('validation')}>Kontrolli i Cilësisë</button>
									<button className={corpusSubTab === 'duplicates' ? 'active' : ''} onClick={() => { setCorpusSubTab('duplicates'); if (!corpusDuplicates) loadCorpusDuplicates() }}>Integriteti i të Dhënave</button>
								</div>

								{/* ── 1. PASQYRË E PËRGJITHSHME ── */}
								{corpusSubTab === 'overview' && corpusStats && (
									<>
										<div className="stats-grid">
											<div className="stat-card"><div className="stat-icon">📄</div><div className="stat-value">{corpusStats.total_documents}</div><div className="stat-label">Dokumente</div></div>
											<div className="stat-card"><div className="stat-icon">🔤</div><div className="stat-value">{corpusStats.total_tokens.toLocaleString()}</div><div className="stat-label">Njësi teksti (fjalë)</div></div>
											<div className="stat-card"><div className="stat-icon">📝</div><div className="stat-value">{corpusStats.total_lemmas.toLocaleString()}</div><div className="stat-label">Lema (unike)</div></div>
											<div className="stat-card"><div className="stat-icon">📃</div><div className="stat-value">{corpusStats.total_sentences.toLocaleString()}</div><div className="stat-label">Fjali</div></div>
											<div className="stat-card"><div className="stat-icon">✅</div><div className="stat-value">{corpusStats.validated_count}</div><div className="stat-label">Të validuara</div></div>
											<div className="stat-card"><div className="stat-icon">⏳</div><div className="stat-value">{corpusStats.unvalidated_count}</div><div className="stat-label">Në pritje</div></div>
										</div>

										<h3 className="corpus-section-title">Tregues Kryesorë (KPI)</h3>
										<div className="corpus-kpi-grid">
											<div className="corpus-kpi-card">
												<div className="kpi-label">TTR Mesatar</div>
												<div className="kpi-value">{corpusStats.avg_type_token_ratio?.toFixed(4) || '—'}</div>
												<div className="kpi-desc">Type-Token Ratio (diversiteti leksikor)</div>
											</div>
											<div className="corpus-kpi-card">
												<div className="kpi-label">Gjatësia Mesatare e Fjalës</div>
												<div className="kpi-value">{corpusStats.avg_word_length?.toFixed(2) || '—'}</div>
												<div className="kpi-desc">Mesatarja e karaktereve për fjalë</div>
											</div>
											<div className="corpus-kpi-card">
												<div className="kpi-label">Tokens / Dokument</div>
												<div className="kpi-value">{corpusStats.avg_doc_tokens?.toLocaleString() || '—'}</div>
												<div className="kpi-desc">Mesatarja e fjalëve për dokument</div>
											</div>
											<div className="corpus-kpi-card">
												<div className="kpi-label">Fjali / Dokument</div>
												<div className="kpi-value">{corpusStats.avg_sentences_per_doc || '—'}</div>
												<div className="kpi-desc">Mesatarja e fjalive për dokument</div>
											</div>
											<div className="corpus-kpi-card">
												<div className="kpi-label">Pa Klasë</div>
												<div className="kpi-value">{corpusStats.unlinked_documents}</div>
												<div className="kpi-desc">Dokumente pa lidhje me klasën</div>
											</div>
											<div className="corpus-kpi-card">
												<div className="kpi-label">Shkalla e Validimit</div>
												<div className="kpi-value">{corpusStats.total_documents > 0 ? Math.round((corpusStats.validated_count / corpusStats.total_documents) * 100) : 0}%</div>
												<div className="kpi-desc">Përqindja e dokumenteve të validuara</div>
											</div>
										</div>

									<div className="corpus-actions">
										<button className="corpus-action-btn primary" onClick={() => setShowCorpusCreateModal(true)}>+ Shto Dokument</button>
										<button className="corpus-action-btn primary" onClick={handleAutoPopulate}>Populim Automatik nga Kurset</button>
										<button className="corpus-action-btn" onClick={handleValidateAll}>Valido Të Gjitha</button>
										<button className="corpus-action-btn" onClick={handleReprocessAll}>Ripërpuno Të Gjitha</button>
									</div>
									{corpusStats.total_documents === 0 && (
										<div className="corpus-empty-state" style={{ marginTop: '1rem' }}>
											<strong>Korpusi është bosh.</strong>
											<p>Pas kalimit në Neon, dokumentet e korpusit nuk u transferuan. Kliko «Populim Automatik nga Kurset» për ta mbushur nga ushtrimet.</p>
										</div>
									)}
									</>
								)}

								{/* ── 2. MENAXHIMI I DOKUMENTEVE ── */}
								{corpusSubTab === 'documents' && (
									<div className="admin-table-container">
										<div className="table-header">
											<h2>Menaxhimi i Dokumenteve ({corpusTotal})</h2>
											<button className="create-btn" onClick={() => setShowCorpusCreateModal(true)}>+ Shto Dokument</button>
										</div>

										<div className="corpus-filters">
											<AdminSearchBar
												value={corpusSearchDraft}
												onChange={setCorpusSearchDraft}
												placeholder="Kërko korpusin…"
												ariaLabel="Kërko dokumente në korpus"
												className="admin-search--grow"
											/>
											<select value={corpusFilters.class_id ?? ''} onChange={e => { setCorpusFilters({...corpusFilters, class_id: e.target.value ? parseInt(e.target.value) : undefined}); setCorpusPage(0) }}>
												<option value="">Të gjitha klasat</option>
												{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
											</select>
											<select value={corpusFilters.genre || ''} onChange={e => { setCorpusFilters({...corpusFilters, genre: e.target.value || undefined}); setCorpusPage(0) }}>
												<option value="">Të gjithë zhanret</option>
												<option value="shkencor">Shkencor</option>
												<option value="letrar">Letrar</option>
												<option value="juridik">Juridik</option>
												<option value="publicistik">Publicistik</option>
												<option value="administrativ">Administrativ</option>
												<option value="tjeter">Tjetër</option>
											</select>
											<select value={corpusFilters.dialect || ''} onChange={e => { setCorpusFilters({...corpusFilters, dialect: e.target.value || undefined}); setCorpusPage(0) }}>
												<option value="">Të gjithë dialektet</option>
												<option value="gege">Gegë</option>
												<option value="toske">Toskë</option>
												<option value="standarde">Standarde</option>
											</select>
											<select value={corpusFilters.source || ''} onChange={e => { setCorpusFilters({...corpusFilters, source: e.target.value || undefined}); setCorpusPage(0) }}>
												<option value="">Të gjithë burimet</option>
												<option value="media">Media</option>
												<option value="libra">Libra</option>
												<option value="dokumente_zyrtare">Dokumente Zyrtare</option>
												<option value="akademik">Akademik</option>
												<option value="tjeter">Tjetër</option>
											</select>
											<button className="corpus-filter-clear" onClick={() => { setCorpusFilters({}); setCorpusSearchDraft(''); setCorpusPage(0) }}>Pastro filtrat</button>
										</div>

										<table className="admin-table">
											<thead>
												<tr>
													<th>ID</th>
													<th>Titulli</th>
													<th>Klasa</th>
													<th>Autori</th>
													<th>Viti</th>
													<th>Zhanri</th>
													<th>Dialekti</th>
													<th>Tokens</th>
													<th>TTR</th>
													<th>Gjendja</th>
													<th>Veprime</th>
												</tr>
											</thead>
											<tbody>
												{corpusDocs.map(doc => (
													<tr key={doc.id}>
														<td>{doc.id}</td>
														<td title={doc.title}>{doc.title.length > 35 ? doc.title.substring(0, 35) + '…' : doc.title}</td>
														<td>{doc.class_name || <span style={{color:'#94a3b8'}}>—</span>}</td>
														<td>{doc.author || '—'}</td>
														<td>{doc.year || '—'}</td>
														<td><span className={`corpus-badge genre-${doc.genre || 'none'}`}>{doc.genre || '—'}</span></td>
														<td><span className={`corpus-badge dialect-${doc.dialect || 'none'}`}>{doc.dialect || '—'}</span></td>
														<td>{doc.token_count.toLocaleString()}</td>
														<td>{doc.type_token_ratio?.toFixed(3) || '—'}</td>
														<td>
															{doc.is_validated
																? <span className="corpus-badge validated">Validuar</span>
																: <span className="corpus-badge pending">{doc.processing_status}</span>
															}
														</td>
														<td className="corpus-actions-cell">
															<button title="Valido" onClick={() => handleValidateDoc(doc.id)}>✅</button>
															<button title="Edito" onClick={() => setEditingCorpusDoc(doc)}>✏️</button>
															<button title="Fshi" onClick={() => handleDeleteCorpusDoc(doc.id)}>🗑️</button>
														</td>
													</tr>
												))}
												{corpusDocs.length === 0 && <tr><td colSpan={11} style={{textAlign:'center',padding:'2rem',color:'#94a3b8'}}>Nuk u gjetën dokumente</td></tr>}
											</tbody>
										</table>

										{corpusTotal > 50 && (
											<div className="corpus-pagination">
												<button disabled={corpusPage === 0} onClick={() => setCorpusPage(p => p - 1)}>← Para</button>
												<span>Faqja {corpusPage + 1} nga {Math.ceil(corpusTotal / 50)}</span>
												<button disabled={(corpusPage + 1) * 50 >= corpusTotal} onClick={() => setCorpusPage(p => p + 1)}>Pas →</button>
											</div>
										)}
									</div>
								)}

								{/* ── 3. ANALIZA LINGUISTIKE ── */}
								{corpusSubTab === 'linguistic' && (
									<div className="corpus-linguistic-section">
										<h2>Analiza Linguistike e Korpusit</h2>
										<div className="admin-list-toolbar">
											<AdminSearchBar
												value={corpusWordsSearch}
												onChange={setCorpusWordsSearch}
												placeholder="Kërko fjalë…"
												ariaLabel="Kërko fjalë në analizën linguistike"
											/>
										</div>
										{corpusAnalysisLoading ? (
											<PageLoading inline title="Duke analizuar korpusin..." />
										) : corpusStats && corpusStats.total_documents === 0 ? (
											renderCorpusEmptyState('Nuk ka tekst për analizë linguistike')
										) : linguisticMetrics && !linguisticMetrics.empty ? (
											<>
												<div className="corpus-kpi-grid">
													<div className="corpus-kpi-card"><div className="kpi-label">TTR (Type-Token Ratio)</div><div className="kpi-value">{Number(linguisticMetrics.type_token_ratio || 0).toFixed(4)}</div><div className="kpi-desc">Diversiteti leksikor</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Gjatësia Mesatare e Fjalës</div><div className="kpi-value">{Number(linguisticMetrics.avg_word_length || 0).toFixed(2)}</div><div className="kpi-desc">Karaktere për fjalë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Gjatësia Mesatare e Fjalisë</div><div className="kpi-value">{Number(linguisticMetrics.avg_sentence_length || 0).toFixed(1)}</div><div className="kpi-desc">Fjalë për fjali</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Hapax Legomena</div><div className="kpi-value">{Number(linguisticMetrics.hapax_legomena || 0).toLocaleString()}</div><div className="kpi-desc">Fjalë që shfaqen vetëm 1 herë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Dis Legomena</div><div className="kpi-value">{Number(linguisticMetrics.dis_legomena || 0).toLocaleString()}</div><div className="kpi-desc">Fjalë që shfaqen vetëm 2 herë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Yule's K</div><div className="kpi-value">{Number(linguisticMetrics.yules_k || 0).toFixed(2)}</div><div className="kpi-desc">Konstanta e pasurueshmërisë leksikore</div></div>
												</div>

												{(linguisticMetrics.word_length_distribution?.length ?? 0) > 0 && (
												<div className="charts-container">
													<div className="chart-card chart-card-full">
														<h3 className="chart-title">Shpërndarja e Gjatësisë së Fjalëve</h3>
														<ResponsiveContainer width="100%" height={300}>
															<BarChart data={linguisticMetrics.word_length_distribution}>
																<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
																<XAxis dataKey="length" tick={{ fill: '#64748b', fontSize: 12 }} label={{ value: 'Gjatësia (karaktere)', position: 'bottom', offset: -5 }} />
																<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
																<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
																<Bar dataKey="count" fill="#4A9FD4" radius={[4, 4, 0, 0]} name="Numri i fjalëve" />
															</BarChart>
														</ResponsiveContainer>
													</div>
												</div>
												)}

												{corpusWordFreqs && (corpusWordFreqs.top_words?.length ?? 0) > 0 && (
													<>
														<h3 className="corpus-section-title">Top 30 Fjalët Më të Shpeshta</h3>
														<div className="chart-card chart-card-full">
															<ResponsiveContainer width="100%" height={400}>
																<BarChart data={filteredWordFreqs.slice(0, 30)} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
																	<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
																	<XAxis dataKey="word" tick={{ fill: '#64748b', fontSize: 10 }} angle={-45} textAnchor="end" />
																	<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
																	<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
																	<Bar dataKey="count" fill="#5BBD6C" radius={[4, 4, 0, 0]} name="Frekuenca" />
																</BarChart>
															</ResponsiveContainer>
														</div>
														<p className="corpus-freq-summary">Fjalë unike totale: <strong>{Number(corpusWordFreqs.total_unique_words || 0).toLocaleString()}</strong></p>
													</>
												)}

												<div className="charts-container">
													<div className="chart-card">
														<h3 className="chart-title">Fjalët e Shkurtra (1–3 karaktere)</h3>
														<div className="corpus-freq-table">
															<table className="admin-table"><thead><tr><th>Fjala</th><th>Frekuenca</th></tr></thead><tbody>
																{filteredShortWords.map(w => <tr key={w.word}><td><strong>{w.word}</strong></td><td>{w.count.toLocaleString()}</td></tr>)}
																{filteredShortWords.length === 0 && <tr><td colSpan={2} className="admin-search-empty">Nuk u gjetën rezultate</td></tr>}
															</tbody></table>
														</div>
													</div>
													<div className="chart-card">
														<h3 className="chart-title">Fjalët e Gjata (8+ karaktere)</h3>
														<div className="corpus-freq-table">
															<table className="admin-table"><thead><tr><th>Fjala</th><th>Frekuenca</th></tr></thead><tbody>
																{filteredLongWords.map(w => <tr key={w.word}><td><strong>{w.word}</strong></td><td>{w.count.toLocaleString()}</td></tr>)}
																{filteredLongWords.length === 0 && <tr><td colSpan={2} className="admin-search-empty">Nuk u gjetën rezultate</td></tr>}
															</tbody></table>
														</div>
													</div>
												</div>

												<h3 className="corpus-section-title">Statistikat e Fjalive</h3>
												<div className="corpus-kpi-grid">
													<div className="corpus-kpi-card"><div className="kpi-label">Min</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats?.min ?? 0}</div><div className="kpi-desc">Fjalia më e shkurtër</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Max</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats?.max ?? 0}</div><div className="kpi-desc">Fjalia më e gjatë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Mesatarja</div><div className="kpi-value">{Number(linguisticMetrics.sentence_length_stats?.avg || 0).toFixed(1)}</div><div className="kpi-desc">Fjalë për fjali</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Mediana</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats?.median ?? 0}</div><div className="kpi-desc">Vlera e mesme</div></div>
												</div>
											</>
										) : (
											<div className="corpus-empty-state" role="alert">
												<strong>{corpusAnalysisError || 'Analiza nuk është gati.'}</strong>
												<button type="button" className="corpus-action-btn primary" onClick={() => loadLinguisticMetrics()}>
													Provo përsëri
												</button>
												<button type="button" className="corpus-action-btn" onClick={handleAutoPopulate}>
													Populim Automatik nga Kurset
												</button>
											</div>
										)}
									</div>
								)}

								{/* ── 4. KLASIFIKIMI & SEGMENTIMI ── */}
								{corpusSubTab === 'classification' && corpusStats && (
									<div className="corpus-classification-section">
										<h2>Klasifikimi & Segmentimi i Korpusit</h2>
										{corpusStats.total_documents === 0 ? (
											renderCorpusEmptyState('Nuk ka dokumente për klasifikim')
										) : (
										<>
										<div className="charts-container">
											<div className="chart-card">
												<h3 className="chart-title">Sipas Zhanrit</h3>
												<ResponsiveContainer width="100%" height={300}>
													<PieChart>
														<Pie data={Object.entries(corpusStats.by_genre).map(([k, v]) => ({ name: k === 'pa_klasifikim' ? 'Pa klasifikim' : k, value: v }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
															{Object.keys(corpusStats.by_genre).map((_, i) => <Cell key={i} fill={['#4A9FD4', '#5BBD6C', '#EF6461', '#FF9600', '#CE82FF', '#94a3b8'][i % 6]} />)}
														</Pie>
														<Tooltip /><Legend />
													</PieChart>
												</ResponsiveContainer>
											</div>
											<div className="chart-card">
												<h3 className="chart-title">Sipas Dialektit</h3>
												<ResponsiveContainer width="100%" height={300}>
													<PieChart>
														<Pie data={Object.entries(corpusStats.by_dialect).map(([k, v]) => ({ name: k === 'pa_klasifikim' ? 'Pa klasifikim' : k, value: v }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
															{Object.keys(corpusStats.by_dialect).map((_, i) => <Cell key={i} fill={['#4A9FD4', '#EF6461', '#5BBD6C', '#94a3b8'][i % 4]} />)}
														</Pie>
														<Tooltip /><Legend />
													</PieChart>
												</ResponsiveContainer>
											</div>
											<div className="chart-card">
												<h3 className="chart-title">Sipas Burimit</h3>
												<ResponsiveContainer width="100%" height={300}>
													<BarChart data={Object.entries(corpusStats.by_source).map(([k, v]) => ({ name: k === 'pa_klasifikim' ? 'Pa klasifikim' : k, count: v }))}>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} />
														<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Bar dataKey="count" fill="#4A9FD4" radius={[8, 8, 0, 0]} name="Dokumente" />
													</BarChart>
												</ResponsiveContainer>
											</div>
											<div className="chart-card">
												<h3 className="chart-title">Tokens sipas Zhanrit</h3>
												<ResponsiveContainer width="100%" height={300}>
													<BarChart data={Object.entries(corpusStats.tokens_by_genre).map(([k, v]) => ({ name: k === 'pa_klasifikim' ? 'Pa klasifikim' : k, tokens: v }))}>
														<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
														<XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} />
														<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
														<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
														<Bar dataKey="tokens" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Njësi teksti" />
													</BarChart>
												</ResponsiveContainer>
											</div>
											{Object.keys(corpusStats.by_year).length > 0 && (
												<div className="chart-card chart-card-full">
													<h3 className="chart-title">Shpërndarja Kohore e Dokumenteve</h3>
													<ResponsiveContainer width="100%" height={300}>
														<AreaChart data={Object.entries(corpusStats.by_year).map(([y, c]) => ({ year: y, count: c }))}>
															<defs><linearGradient id="colorCorpusYear" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#4A9FD4" stopOpacity={0.8}/><stop offset="95%" stopColor="#4A9FD4" stopOpacity={0.1}/></linearGradient></defs>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="year" tick={{ fill: '#64748b', fontSize: 11 }} />
															<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Area type="monotone" dataKey="count" stroke="#4A9FD4" fillOpacity={1} fill="url(#colorCorpusYear)" name="Dokumente" />
														</AreaChart>
													</ResponsiveContainer>
												</div>
											)}
											{Object.keys(corpusStats.top_authors).length > 0 && (
												<div className="chart-card chart-card-full">
													<h3 className="chart-title">Top Autorë</h3>
													<ResponsiveContainer width="100%" height={300}>
														<BarChart data={Object.entries(corpusStats.top_authors).slice(0, 10).map(([a, c]) => ({ author: a, count: c }))} layout="vertical">
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis type="number" tick={{ fill: '#64748b', fontSize: 12 }} />
															<YAxis dataKey="author" type="category" width={140} tick={{ fill: '#64748b', fontSize: 11 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Bar dataKey="count" fill="#CE82FF" radius={[0, 8, 8, 0]} name="Dokumente" />
														</BarChart>
													</ResponsiveContainer>
												</div>
											)}
										</div>
										{corpusFuseCodes.length > 0 && (
											<div className="corpus-fuse-section">
												<h3>Kodet Fuse Class</h3>
												<div className="fuse-codes-grid">
													{corpusFuseCodes.map(fc => (
														<div key={fc.code} className="fuse-code-card" onClick={() => { setCorpusFilters({...corpusFilters, fuse_class_code: fc.code} as any); setCorpusSubTab('documents') }}>
															<div className="fuse-code-label">{fc.code}</div>
															<div className="fuse-code-stats"><span>{fc.document_count} dok.</span><span>{fc.total_tokens.toLocaleString()} njësi teksti</span></div>
														</div>
													))}
												</div>
											</div>
										)}
										</>
										)}
									</div>
								)}

								{/* ── 5. STATISTIKA SIPAS KLASËS ── */}
								{corpusSubTab === 'per_class' && corpusStats && (
									<div className="corpus-per-class-section">
										<h2>Shpërndarja e Korpusit Sipas Klasës</h2>
										<div className="admin-list-toolbar">
											<AdminSearchBar
												value={corpusPerClassSearch}
												onChange={setCorpusPerClassSearch}
												placeholder="Kërko klasa…"
												ariaLabel="Kërko statistika sipas klasës"
											/>
										</div>
										{corpusStats.by_class.length > 0 ? (
											<>
												<div className="chart-card chart-card-full">
													<h3 className="chart-title">Dokumente & Tokens Sipas Klasës</h3>
													<ResponsiveContainer width="100%" height={350}>
														<ComposedChart data={corpusStats.by_class}>
															<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
															<XAxis dataKey="class_name" tick={{ fill: '#64748b', fontSize: 11 }} />
															<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
															<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
															<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
															<Legend />
															<Bar yAxisId="left" dataKey="documents" fill="#4A9FD4" radius={[8, 8, 0, 0]} name="Dokumente" />
															<Line yAxisId="right" type="monotone" dataKey="tokens" stroke="#5BBD6C" strokeWidth={3} name="Njësi teksti" />
														</ComposedChart>
													</ResponsiveContainer>
												</div>

												<table className="admin-table">
													<thead>
														<tr>
															<th>Klasa</th>
															<th>Dokumente</th>
															<th>Tokens</th>
															<th>Lemma</th>
															<th>TTR Mesatar</th>
															<th>Balanca</th>
														</tr>
													</thead>
													<tbody>
														{filteredCorpusByClass.map(c => {
															const pct = corpusStats.total_documents > 0 ? Math.round((c.documents / corpusStats.total_documents) * 100) : 0
															return (
																<tr key={c.class_id}>
																	<td><strong>{c.class_name}</strong></td>
																	<td>{c.documents}</td>
																	<td>{c.tokens.toLocaleString()}</td>
																	<td>{c.lemmas.toLocaleString()}</td>
																	<td>{c.avg_ttr.toFixed(4)}</td>
																	<td>
																		<div className="corpus-balance-bar">
																			<div className="corpus-balance-fill" style={{ width: `${pct}%` }}>{pct}%</div>
																		</div>
																	</td>
																</tr>
															)
														})}
														{filteredCorpusByClass.length === 0 && (
															<tr>
																<td colSpan={6} className="admin-search-empty">Nuk u gjetën rezultate</td>
															</tr>
														)}
														{!corpusPerClassSearch && corpusStats.unlinked_documents > 0 && (
															<tr style={{color:'#94a3b8'}}>
																<td><em>Pa klasë</em></td>
																<td>{corpusStats.unlinked_documents}</td>
																<td colSpan={4}>—</td>
															</tr>
														)}
													</tbody>
												</table>
											</>
										) : (
											<div className="corpus-no-duplicates"><p>Nuk ka klasa me dokumente të lidhura.</p></div>
										)}
									</div>
								)}

								{/* ── 6. KONTROLLI I CILËSISË ── */}
								{corpusSubTab === 'validation' && corpusStats && (
									<div className="corpus-validation-section">
										<h2>Kontrolli i Cilësisë & Validimi</h2>
										<div className="stats-grid">
											<div className="stat-card"><div className="stat-icon">✅</div><div className="stat-value">{corpusStats.validated_count}</div><div className="stat-label">Të validuara</div></div>
											<div className="stat-card"><div className="stat-icon">⏳</div><div className="stat-value">{corpusStats.unvalidated_count}</div><div className="stat-label">Në pritje</div></div>
											<div className="stat-card"><div className="stat-icon">📊</div><div className="stat-value">{corpusStats.total_documents > 0 ? Math.round((corpusStats.validated_count / corpusStats.total_documents) * 100) : 0}%</div><div className="stat-label">Shkalla</div></div>
											<div className="stat-card"><div className="stat-icon">🔗</div><div className="stat-value">{corpusStats.unlinked_documents}</div><div className="stat-label">Pa klasë</div></div>
										</div>

										<div className="charts-container">
											<div className="chart-card">
												<h3 className="chart-title">Pipeline i Përpunimit</h3>
												<ResponsiveContainer width="100%" height={300}>
													<PieChart>
														<Pie data={Object.entries(corpusStats.by_status).map(([k, v]) => ({ name: k === 'pa_klasifikim' ? 'Pa status' : k, value: v }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
															{Object.keys(corpusStats.by_status).map((_, i) => <Cell key={i} fill={['#5BBD6C', '#4A9FD4', '#FF9600', '#CE82FF', '#EF6461', '#94a3b8'][i % 6]} />)}
														</Pie>
														<Tooltip /><Legend />
													</PieChart>
												</ResponsiveContainer>
											</div>
											<div className="chart-card">
												<h3 className="chart-title">Balanca Dialektore</h3>
												<ResponsiveContainer width="100%" height={300}>
													<PieChart>
														<Pie data={Object.entries(corpusStats.tokens_by_dialect).map(([k, v]) => ({ name: k === 'pa_klasifikim' ? 'Pa klasifikim' : k, value: v }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
															{Object.keys(corpusStats.tokens_by_dialect).map((_, i) => <Cell key={i} fill={['#4A9FD4', '#EF6461', '#5BBD6C', '#94a3b8'][i % 4]} />)}
														</Pie>
														<Tooltip /><Legend />
													</PieChart>
												</ResponsiveContainer>
											</div>
										</div>

										<div className="corpus-actions">
											<button className="corpus-action-btn primary" onClick={handleValidateAll}>Valido Të Gjitha Dokumentet</button>
											<button className="corpus-action-btn" onClick={handleReprocessAll}>Ripërpuno (tokenizim, frekuenca)</button>
										</div>
									</div>
								)}

								{/* ── 7. INTEGRITETI I TË DHËNAVE ── */}
								{corpusSubTab === 'duplicates' && (
									<div className="corpus-duplicates-section">
										<h2>Integriteti i të Dhënave & Dublikata</h2>
										{corpusDuplicates ? (
											corpusDuplicates.total_duplicate_groups > 0 ? (
												<>
													<p className="corpus-dup-summary">U gjetën <strong>{corpusDuplicates.total_duplicate_groups}</strong> grupe dublikatash.</p>
													{corpusDuplicates.groups.map((group, gi) => (
														<div key={gi} className="corpus-dup-group">
															<h4>Grupi {gi + 1} — {group.count} dokumente identike</h4>
															<table className="admin-table">
																<thead><tr><th>ID</th><th>Titulli</th><th>Autori</th><th>Viti</th><th>Veprime</th></tr></thead>
																<tbody>
																	{group.documents.map(d => (
																		<tr key={d.id}>
																			<td>{d.id}</td>
																			<td>{d.title}</td>
																			<td>{d.author || '—'}</td>
																			<td>{d.year || '—'}</td>
																			<td><button onClick={() => handleDeleteCorpusDoc(d.id)}>🗑️ Fshi</button></td>
																		</tr>
																	))}
																</tbody>
															</table>
														</div>
													))}
												</>
											) : (
												<div className="corpus-no-duplicates">
													<span className="corpus-no-dup-icon">✅</span>
													<p>Nuk u gjetën dublikata në korpus.</p>
												</div>
											)
										) : (
											<div className="admin-loading-wrap">
												<PageLoading inline title="Duke kontrolluar integritetin..." />
											</div>
										)}
									</div>
								)}
							</div>
						)}

						{activeTab === 'research' && (
							<div className="research-ai-panel">
								<div className="research-hero">
									<div>
										<h2>🤖 Paneli i AI Mësimore</h2>
										<p>
											Gjenerim ushtrimesh, shpjegime pedagogjike dhe vlerësim shkencor.
											Fëmijët shohin vetëm ndihmën e thjeshtë.
										</p>
									</div>
									<div className="research-badge">Saktësia nga rregullat · AI vetëm shpjegon</div>
								</div>

								{researchOverview && (
									<div className="stats-grid">
										<div className="stat-card">
											<div className="stat-icon">📚</div>
											<div className="stat-value">{researchOverview.available_data.existing_exercises}</div>
											<div className="stat-label">Ushtrime për instruction tuning</div>
										</div>
										<div className="stat-card">
											<div className="stat-icon">🧪</div>
											<div className="stat-value">{researchOverview.available_data.student_attempts}</div>
											<div className="stat-label">Tentime për IRT/KT</div>
										</div>
										<div className="stat-card">
											<div className="stat-icon">🛡️</div>
											<div className="stat-value">Sigurt</div>
											<div className="stat-label">Përgjigja nga DB/rregullat</div>
										</div>
									</div>
								)}

								<div className="research-workbench">
									<div className="research-actions">
										<div className="research-actions-header">
											<h3>Veprimet Shkencore</h3>
											<p>Zgjidh një veprim majtas; rezultati shfaqet gjithmonë në panelin djathtas.</p>
										</div>

										<div className="research-grid">
									<div className="research-card">
										<h3>Të dhëna për përshtatje me instruksione</h3>
										<p>Kthen ushtrimet ekzistuese në çifte <code>instruction → output</code> për LoRA/QLoRA.</p>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'instruction-dataset'} onClick={async () => {
											setResearchLoadingAction('instruction-dataset')
											setResearchResult({ action: 'instruction-dataset', loading: true, message: 'Duke rifreskuar dataset-in...' })
											try {
												const result = await getInstructionDataset(25)
												setInstructionDataset(result)
												setResearchResult({ action: 'instruction-dataset', result })
											} catch (error: any) {
												setResearchResult({ action: 'instruction-dataset', error: error?.response?.data?.detail || 'Gabim në dataset' })
											} finally {
												setResearchLoadingAction(null)
											}
										}}>
											{researchLoadingAction === 'instruction-dataset' ? 'Duke rifreskuar...' : 'Rifresko dataset'}
										</button>
										<div className="research-card-summary">
											{instructionDataset?.count ? `${instructionDataset.count} çifte gati për trajnim.` : 'Të dhënat ngarkohen kur hapet tabi ose kur klikon rifresko.'}
										</div>
									</div>

									<div className="research-card">
										<h3>Gjenerim Ushtrimi të Sigurt</h3>
										<input value={researchForm.seedWord} onChange={(e) => setResearchForm({ ...researchForm, seedWord: e.target.value })} placeholder="Fjala bazë" />
										<select value={researchForm.exerciseType} onChange={(e) => setResearchForm({ ...researchForm, exerciseType: e.target.value as any })}>
											<option value="missing_letter">Plotëso shkronjën</option>
											<option value="find_error">Gjej gabimin</option>
											<option value="explain_error">Shpjego gabimin</option>
										</select>
										<select value={researchForm.difficulty} onChange={(e) => setResearchForm({ ...researchForm, difficulty: e.target.value as any })}>
											<option value="easy">Lehtë</option>
											<option value="medium">Mesatare</option>
											<option value="hard">Vështirë</option>
										</select>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'generate'} onClick={() => runResearchAction('generate')}>
											{researchLoadingAction === 'generate' ? 'Duke gjeneruar...' : 'Gjenero'}
										</button>
									</div>

									<div className="research-card">
										<h3>Data Augmentation me Gabime Shqipe</h3>
										<textarea value={researchForm.augmentationText} onChange={(e) => setResearchForm({ ...researchForm, augmentationText: e.target.value })} />
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'augment'} onClick={() => runResearchAction('augment')}>
											{researchLoadingAction === 'augment' ? 'Duke krijuar...' : 'Krijo gabime të kontrolluara'}
										</button>
									</div>

									<div className="research-card">
										<h3>Shpjegim pedagogjik</h3>
										<input value={researchForm.studentAnswer} onChange={(e) => setResearchForm({ ...researchForm, studentAnswer: e.target.value })} placeholder="Përgjigja e nxënësit" />
										<input value={researchForm.correctAnswer} onChange={(e) => setResearchForm({ ...researchForm, correctAnswer: e.target.value })} placeholder="Forma e saktë" />
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'feedback'} onClick={() => runResearchAction('feedback')}>
											{researchLoadingAction === 'feedback' ? 'Duke gjeneruar...' : 'Gjenero shpjegim'}
										</button>
									</div>

									<div className="research-card">
										<h3>ERRANT F0.5 / GLEU-like</h3>
										<input value={researchForm.source} onChange={(e) => setResearchForm({ ...researchForm, source: e.target.value })} placeholder="Teksti gabim" />
										<input value={researchForm.reference} onChange={(e) => setResearchForm({ ...researchForm, reference: e.target.value })} placeholder="Gold reference" />
										<input value={researchForm.hypothesis} onChange={(e) => setResearchForm({ ...researchForm, hypothesis: e.target.value })} placeholder="Korrigjimi i sistemit" />
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'evaluate'} onClick={() => runResearchAction('evaluate')}>
											{researchLoadingAction === 'evaluate' ? 'Duke vlerësuar...' : 'Vlerëso korrigjimin'}
										</button>
									</div>

									<div className="research-card">
										<h3>Përshtatja me klasën + IRT</h3>
										<input type="number" min="1" max="8" value={researchForm.grade} onChange={(e) => setResearchForm({ ...researchForm, grade: Number(e.target.value) })} />
										<textarea value={researchForm.gradeText} onChange={(e) => setResearchForm({ ...researchForm, gradeText: e.target.value })} />
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'grade-fit'} onClick={() => runResearchAction('grade-fit')}>
											{researchLoadingAction === 'grade-fit' ? 'Duke kontrolluar...' : 'Kontrollo nivelin'}
										</button>
										<button type="button" className="create-btn secondary" disabled={researchLoadingAction === 'irt-summary'} onClick={async () => {
											setResearchLoadingAction('irt-summary')
											setResearchResult({ action: 'irt-summary', loading: true, message: 'Duke rifreskuar IRT...' })
											try {
												const result = await getIRTSummary(1)
												setIrtSummary(result)
												setResearchResult({ action: 'irt-summary', result })
											} catch (error: any) {
												setResearchResult({ action: 'irt-summary', error: error?.response?.data?.detail || 'Gabim në IRT' })
											} finally {
												setResearchLoadingAction(null)
											}
										}}>{researchLoadingAction === 'irt-summary' ? 'Duke rifreskuar...' : 'Rifresko IRT'}</button>
									</div>

									<div className="research-card">
										<h3>Gjurmimi i njohurive</h3>
										<p>Modelon njohurinë e nxënësit në kohë me një BKT të interpretuar.</p>
										<input value={researchForm.adaptiveUserId} onChange={(e) => setResearchForm({ ...researchForm, adaptiveUserId: e.target.value })} placeholder="ID e përdoruesit" />
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'kt'} onClick={() => runAdaptiveResearchAction('kt')}>
											{researchLoadingAction === 'kt' ? 'Duke llogaritur...' : 'Llogarit KT'}
										</button>
										<div className="research-card-summary">
											{ktSummary?.skills?.length ? `${ktSummary.skills.length} aftësi të analizuara për userin.` : 'Kliko për të llogaritur gjurmimin e njohurive.'}
										</div>
									</div>

									<div className="research-card">
										<h3>Ushtrimi i radhës i përshtatur</h3>
										<p>Zgjedh ushtrimin që jep informacion maksimal, as shumë të lehtë as shumë të vështirë.</p>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'adaptive'} onClick={() => runAdaptiveResearchAction('adaptive')}>
											{researchLoadingAction === 'adaptive' ? 'Duke rekomanduar...' : 'Rekomando ushtrimin tjetër'}
										</button>
									</div>

									<div className="research-card">
										<h3>RAG vs No-Context</h3>
										<p>Mat uljen e gabimeve kur gjenerimi përdor kontekst/rikthim njohurie.</p>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'rag'} onClick={() => runAdaptiveResearchAction('rag')}>
											{researchLoadingAction === 'rag' ? 'Duke krahasuar...' : 'Krahaso demo'}
										</button>
									</div>

									<div className="research-card">
										<h3>Rubrika e mësuesit</h3>
										<p>Ruaj vlerësime nga mësues/gjuhëtarë: saktësi, qartësi, moshë, vlerë pedagogjike, siguri.</p>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'teacher-review'} onClick={() => runAdaptiveResearchAction('teacher-review')}>
											{researchLoadingAction === 'teacher-review' ? 'Duke ruajtur...' : 'Ruaj review demo'}
										</button>
										<div className="research-card-summary">
											{teacherReviewSummary?.count ? `${teacherReviewSummary.count} vlerësime të ruajtura.` : 'Rubrika është gati; duhen vlerësime reale nga mësues/gjuhëtarë.'}
										</div>
									</div>

									<div className="research-card">
										<h3>Eksperimenti Final Doktorature</h3>
										<p>
											Përmbledh gatishmërinë për LoRA/QLoRA, ERRANT/GLEU zyrtar,
											Deep-IRT/DKT dhe vlerësim njerëzor.
										</p>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'protocol'} onClick={() => runFinalExperimentAction('protocol')}>
											{researchLoadingAction === 'protocol' ? 'Duke shfaqur...' : 'Shfaq protokollin'}
										</button>
										<button type="button" className="create-btn secondary" disabled={researchLoadingAction === 'deep-dataset'} onClick={() => runFinalExperimentAction('deep-dataset')}>
											{researchLoadingAction === 'deep-dataset' ? 'Duke eksportuar...' : 'Export Deep-IRT/DKT'}
										</button>
										<div className="research-card-summary">
											{finalProtocol?.readiness ? 'Protokolli është ngarkuar; shiko detajet në panelin djathtas.' : 'Kliko për të parë gatishmërinë e eksperimentit.'}
										</div>
									</div>

									<div className="research-card">
										<h3>Gjendja e modeleve të trajnuara</h3>
										<p>
											Tregon nëse LoRA/QLoRA, Deep-IRT/DKT dhe benchmark-u ERRANT/GLEU
											kanë artifacts të trajnuara në sistem.
										</p>
										<button type="button" className="create-btn" disabled={researchLoadingAction === 'training-status'} onClick={refreshTrainingStatus}>
											{researchLoadingAction === 'training-status' ? 'Duke kontrolluar...' : 'Kontrollo statusin'}
										</button>
										<div className="research-card-summary">
											{modelTrainingStatus?.models ? 'Gjendja e modeleve është gati në panelin djathtas.' : 'Kliko për të kontrolluar artefaktet.'}
										</div>
									</div>

									<div className="research-card">
										<h3>Komandat e Trajnimit</h3>
										<p>Këto komanda ekzekutohen në GPU/Colab, pastaj artifacts kopjohen në aplikacion.</p>
										<div className="research-card-summary">
											{trainingCommands ? 'Komandat janë ngarkuar; shfaqen në panelin djathtas për raportim.' : 'Komandat ngarkohen automatikisht me tab-in.'}
										</div>
									</div>
										</div>
									</div>

									<aside className="research-output-panel">
										<div className={`research-result-banner ${researchResult?.error ? 'error' : researchResult?.loading ? 'loading' : researchResult ? 'success' : ''}`}>
											<div className="research-result-banner-header">
												<strong>
													{researchResult?.loading
														? 'Duke ekzekutuar...'
														: researchResult?.error
														? 'Gabim në veprim'
														: researchResult
														? `Rezultati: ${researchResult.action}`
														: 'Rezultati / Evidenca'}
												</strong>
												{researchLoadingAction && <span className="research-running-pill">{researchLoadingAction}</span>}
											</div>
											<pre className="research-json research-output-json">
												{JSON.stringify(
													researchResult?.error
														? { error: researchResult.error }
														: researchResult?.result || researchResult || { message: 'Kliko një veprim majtas. Të gjitha rezultatet do të shfaqen këtu.' },
													null,
													2
												)}
											</pre>
										</div>

										<div className="research-evidence-card">
											<h4>IRT Snapshot</h4>
											<pre className="research-json compact">{JSON.stringify({
												items: irtSummary?.items?.slice?.(0, 3),
												users: irtSummary?.users?.slice?.(0, 3),
											}, null, 2)}</pre>
										</div>

										<div className="research-evidence-card">
										<h4>Gjendje e shpejtë</h4>
											<div className="research-status-list">
												<span>LoRA: {modelTrainingStatus?.models?.lora_qlora?.trained ? 'aktiv' : 'mungon'}</span>
												<span>Deep-IRT/DKT: {modelTrainingStatus?.models?.deep_irt_dkt?.trained ? 'aktiv' : 'mungon'}</span>
												<span>Vlerësime nga mësuesit: {teacherReviewSummary?.count || 0}</span>
											</div>
										</div>
									</aside>
								</div>
							</div>
						)}
					</>
				)}
			</div>

			{/* Modals for create/edit */}
			{showCreateModal && (
				<CreateModal
					type={showCreateModal}
					onClose={() => setShowCreateModal(null)}
					onCreate={showCreateModal === 'class' ? handleCreateClass : showCreateModal === 'level' ? handleCreateLevel : handleCreateExercise}
					classes={classes}
					levels={levels}
					getLevelDisplayName={getLevelDisplayName}
					getLevelClassName={getLevelClassName}
				/>
			)}

			{editingUser && (
				<EditUserModal
					user={editingUser}
					onClose={() => setEditingUser(null)}
					onSave={handleUpdateUser}
				/>
			)}

			{editingClass && (
				<EditClassModal
					classData={editingClass}
					onClose={() => setEditingClass(null)}
					onSave={handleUpdateClass}
				/>
			)}

			{editingLevel && (
				<EditLevelModal
					level={editingLevel}
					onClose={() => setEditingLevel(null)}
					onSave={handleUpdateLevel}
					classes={classes}
				/>
			)}

			{editingExercise && (
				<EditExerciseModal
					exercise={editingExercise}
					onClose={() => setEditingExercise(null)}
					onSave={handleUpdateExercise}
				/>
			)}

			{showCorpusCreateModal && (
				<CorpusDocModal
					onClose={() => setShowCorpusCreateModal(false)}
					onSave={(doc) => handleCreateCorpusDoc(doc)}
					classes={classes}
				/>
			)}

			{editingCorpusDoc && (
				<CorpusDocModal
					doc={editingCorpusDoc}
					onClose={() => setEditingCorpusDoc(null)}
					onSave={(update) => handleUpdateCorpusDoc(editingCorpusDoc.id, update)}
					classes={classes}
				/>
			)}

			{showUserReport && userReportData && (
				<UserReportModal
					user={showUserReport}
					reportData={userReportData}
					onClose={() => {
						setShowUserReport(null)
						setUserReportData(null)
					}}
				/>
			)}
			</Suspense>
		</div>
	)
}

// Modal components
function CreateModal({ type, onClose, onCreate, classes, levels, getLevelDisplayName, getLevelClassName }: {
	type: 'class' | 'level' | 'exercise'
	onClose: () => void
	onCreate: any
	classes: ClassData[]
	levels: LevelOut[]
	getLevelDisplayName: (level: LevelOut) => string
	getLevelClassName: (level: LevelOut) => string
}) {
	const [formData, setFormData] = useState<any>({})

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		if (type === 'class') {
			onCreate(formData.name, formData.description)
		} else if (type === 'level') {
			onCreate(formData.course_id, formData.name, formData.description)
		} else {
			onCreate(formData)
		}
	}

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<h2>Shto {type === 'class' ? 'Klasë' : type === 'level' ? 'Nivel' : 'Ushtrim'}</h2>
				<form onSubmit={handleSubmit}>
					{type === 'class' && (
						<>
							<input placeholder="Emër" value={formData.name || ''} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
							<textarea placeholder="Përshkrim" value={formData.description || ''} onChange={(e) => setFormData({...formData, description: e.target.value})} />
						</>
					)}
					{type === 'level' && (
						<>
							<select value={formData.course_id || ''} onChange={(e) => setFormData({...formData, course_id: parseInt(e.target.value)})} required>
								<option value="">Zgjidh Kurs</option>
								{classes.flatMap((c: ClassData) => c.courses).map((c: any) => (
									<option key={c.id} value={c.id}>{c.name}</option>
								))}
							</select>
							<input placeholder="Emër" value={formData.name || ''} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
							<textarea placeholder="Përshkrim" value={formData.description || ''} onChange={(e) => setFormData({...formData, description: e.target.value})} />
						</>
					)}
					{type === 'exercise' && (
						<>
							<select value={formData.level_id || ''} onChange={(e) => setFormData({...formData, level_id: parseInt(e.target.value)})} required>
								<option value="">Zgjidh Nivel</option>
								{levels.map((l: LevelOut) => (
									<option key={l.id} value={l.id}>
										{getLevelDisplayName(l)} - {getLevelClassName(l)}
									</option>
								))}
							</select>
							<input placeholder="Prompt" value={formData.prompt || ''} onChange={(e) => setFormData({...formData, prompt: e.target.value})} required />
							<input placeholder="Përgjigje" value={formData.answer || ''} onChange={(e) => setFormData({...formData, answer: e.target.value})} required />
							<input type="number" placeholder="Pikë" value={formData.points || ''} onChange={(e) => setFormData({...formData, points: parseInt(e.target.value)})} />
						</>
					)}
					<div className="modal-actions">
						<button type="submit">Krijo</button>
						<button type="button" onClick={onClose}>Anulo</button>
					</div>
				</form>
			</div>
		</div>
	)
}

function EditUserModal({ user, onClose, onSave }: {
	user: UserOut
	onClose: () => void
	onSave: (data: Partial<UserOut>) => void
}) {
	const [formData, setFormData] = useState(user)

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		onSave(formData)
	}

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<h2>Edito Përdorues</h2>
				<form onSubmit={handleSubmit}>
					<input value={formData.username} onChange={(e) => setFormData({...formData, username: e.target.value})} />
					<input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
					<input type="number" value={formData.age || ''} onChange={(e) => setFormData({...formData, age: parseInt(e.target.value)})} />
					<label>
						<input type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({...formData, is_active: e.target.checked})} />
						Aktiv
					</label>
					<label>
						<input type="checkbox" checked={formData.is_admin} onChange={(e) => setFormData({...formData, is_admin: e.target.checked})} />
						Admin
					</label>
					<div className="modal-actions">
						<button type="submit">Ruaj</button>
						<button type="button" onClick={onClose}>Anulo</button>
					</div>
				</form>
			</div>
		</div>
	)
}

function EditClassModal({ classData, onClose, onSave }: {
	classData: ClassData
	onClose: () => void
	onSave: (data: Partial<ClassData>) => void
}) {
	const [formData, setFormData] = useState<Partial<ClassData>>({
		name: classData.name,
		description: classData.description || '',
		enabled: classData.enabled
	})

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		onSave(formData)
	}

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<h2>Edito Klasë</h2>
				<form onSubmit={handleSubmit}>
					<label>
						Emër:
						<input 
							value={formData.name || ''} 
							onChange={(e) => setFormData({...formData, name: e.target.value})} 
							required 
						/>
					</label>
					<label>
						Përshkrim:
						<textarea 
							value={formData.description || ''} 
							onChange={(e) => setFormData({...formData, description: e.target.value})} 
						/>
					</label>
					<label>
						<input 
							type="checkbox" 
							checked={formData.enabled !== false} 
							onChange={(e) => setFormData({...formData, enabled: e.target.checked})} 
						/>
						Aktiv
					</label>
					<div className="modal-actions">
						<button type="submit">Ruaj</button>
						<button type="button" onClick={onClose}>Anulo</button>
					</div>
				</form>
			</div>
		</div>
	)
}

function EditLevelModal({ level, onClose, onSave, classes }: {
	level: LevelOut
	onClose: () => void
	onSave: (data: Partial<LevelOut>) => void
	classes: ClassData[]
}) {
	const [formData, setFormData] = useState<Partial<LevelOut>>({
		name: level.name,
		description: level.description || '',
		course_id: level.course_id,
		enabled: level.enabled,
		required_score: level.required_score
	})

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		onSave(formData)
	}

	// Get all courses from all classes
	const allCourses = classes.flatMap(cls => cls.courses || [])

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<h2>Edito Nivel</h2>
				<form onSubmit={handleSubmit}>
					<label>
						Kurs:
						<select 
							value={formData.course_id || ''} 
							onChange={(e) => setFormData({...formData, course_id: parseInt(e.target.value)})} 
							required
						>
							<option value="">Zgjidh Kurs</option>
							{allCourses.map(course => (
								<option key={course.id} value={course.id}>{course.name}</option>
							))}
						</select>
					</label>
					<label>
						Emër:
						<input 
							value={formData.name || ''} 
							onChange={(e) => setFormData({...formData, name: e.target.value})} 
							required 
						/>
					</label>
					<label>
						Përshkrim:
						<textarea 
							value={formData.description || ''} 
							onChange={(e) => setFormData({...formData, description: e.target.value})} 
						/>
					</label>
					<label>
						Pikë të Kërkuara (%):
						<input 
							type="number" 
							min="0" 
							max="100"
							value={formData.required_score || 0} 
							onChange={(e) => setFormData({...formData, required_score: parseInt(e.target.value)})} 
						/>
					</label>
					<label>
						<input 
							type="checkbox" 
							checked={formData.enabled !== false} 
							onChange={(e) => setFormData({...formData, enabled: e.target.checked})} 
						/>
						Aktiv
					</label>
					<div className="modal-actions">
						<button type="submit">Ruaj</button>
						<button type="button" onClick={onClose}>Anulo</button>
					</div>
				</form>
			</div>
		</div>
	)
}

function EditExerciseModal({ exercise, onClose, onSave }: {
	exercise: ExerciseOut
	onClose: () => void
	onSave: (data: Partial<ExerciseOut & { answer?: string }>) => void
}) {
	const [formData, setFormData] = useState<ExerciseOut & { answer?: string }>({ ...exercise, answer: '' })

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		onSave(formData)
	}

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<h2>Edito Ushtrim</h2>
				<form onSubmit={handleSubmit}>
					<label>
						Prompt:
						<textarea 
							value={formData.prompt} 
							onChange={(e) => setFormData({...formData, prompt: e.target.value})} 
							required
						/>
					</label>
					<label>
						Përgjigje:
						<input 
							value={formData.answer || ''} 
							onChange={(e) => setFormData({...formData, answer: e.target.value})} 
							required
						/>
					</label>
					<label>
						Pikë:
						<input 
							type="number" 
							min="1"
							value={formData.points} 
							onChange={(e) => setFormData({...formData, points: parseInt(e.target.value)})} 
						/>
					</label>
					<label>
						Kategori:
						<select 
							value={formData.category} 
							onChange={(e) => setFormData({...formData, category: e.target.value as Category})}
						>
							<option value="listen_write">Dëgjo dhe Shkruaj</option>
							<option value="word_from_description">Fjalë nga Përshkrimi</option>
							<option value="synonyms_antonyms">Sinonime/Antonime</option>
							<option value="albanian_or_loanword">Shqip ose Huazim</option>
							<option value="missing_letter">Shkronjë e Munguar</option>
							<option value="wrong_letter">Shkronjë e Gabuar</option>
							<option value="build_word">Ndërtim Fjalë</option>
							<option value="number_to_word">Numër në Fjalë</option>
							<option value="phrases">Fraza</option>
							<option value="spelling_punctuation">Drejtshkrim dhe Pikësim</option>
							<option value="abstract_concrete">Abstrakt/Konkrete</option>
							<option value="build_sentence">Ndërtim Fjali</option>
						</select>
					</label>
					<div className="modal-actions">
						<button type="submit">Ruaj</button>
						<button type="button" onClick={onClose}>Anulo</button>
					</div>
				</form>
			</div>
		</div>
	)
}

// User Report Modal Component  
function CorpusDocModal({ doc, onClose, onSave, classes }: {
	doc?: CorpusDocument | null
	onClose: () => void
	onSave: (data: any) => void
	classes: ClassData[]
}) {
	const [title, setTitle] = useState(doc?.title || '')
	const [content, setContent] = useState(doc?.full_content || doc?.content || '')
	const [author, setAuthor] = useState(doc?.author || '')
	const [year, setYear] = useState<string>(doc?.year?.toString() || '')
	const [genre, setGenre] = useState(doc?.genre || '')
	const [dialect, setDialect] = useState(doc?.dialect || '')
	const [source, setSource] = useState(doc?.source || '')
	const [fuseCode, setFuseCode] = useState(doc?.fuse_class_code || '')
	const [classId, setClassId] = useState<string>(doc?.class_id?.toString() || '')

	const handleSubmit = () => {
		if (!title.trim() || !content.trim()) {
			alert('Titulli dhe përmbajtja janë të detyrueshme.')
			return
		}
		onSave({
			title: title.trim(),
			content: content.trim(),
			author: author.trim() || undefined,
			year: year ? parseInt(year) : undefined,
			genre: genre || undefined,
			dialect: dialect || undefined,
			source: source || undefined,
			fuse_class_code: fuseCode.trim() || undefined,
			class_id: classId ? parseInt(classId) : undefined,
		})
	}

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal corpus-modal" onClick={e => e.stopPropagation()}>
				<h2>{doc ? 'Edito Dokumentin' : 'Shto Dokument të Ri'}</h2>
				<div className="modal-form">
					<label>Titulli *</label>
					<input value={title} onChange={e => setTitle(e.target.value)} placeholder="Titulli i dokumentit" />

					<div className="modal-row">
						<div><label>Autori</label><input value={author} onChange={e => setAuthor(e.target.value)} placeholder="Emri i autorit" /></div>
						<div>
							<label>Klasa (lidh me klasën)</label>
							<select value={classId} onChange={e => setClassId(e.target.value)}>
								<option value="">— Pa klasë —</option>
								{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
							</select>
						</div>
					</div>

					<div className="modal-row">
						<div><label>Viti</label><input type="number" value={year} onChange={e => setYear(e.target.value)} placeholder="p.sh. 2020" /></div>
						<div><label>Kod Klasifikimi (Fuse)</label><input value={fuseCode} onChange={e => setFuseCode(e.target.value)} placeholder="p.sh. SHK-01" /></div>
					</div>

					<div className="modal-row">
						<div>
							<label>Zhanri</label>
							<select value={genre} onChange={e => setGenre(e.target.value)}>
								<option value="">— Zgjidhni —</option>
								<option value="shkencor">Shkencor</option>
								<option value="letrar">Letrar</option>
								<option value="juridik">Juridik</option>
								<option value="publicistik">Publicistik</option>
								<option value="administrativ">Administrativ</option>
								<option value="tjeter">Tjetër</option>
							</select>
						</div>
						<div>
							<label>Dialekti</label>
							<select value={dialect} onChange={e => setDialect(e.target.value)}>
								<option value="">— Zgjidhni —</option>
								<option value="gege">Gegë</option>
								<option value="toske">Toskë</option>
								<option value="standarde">Standarde</option>
							</select>
						</div>
						<div>
							<label>Burimi</label>
							<select value={source} onChange={e => setSource(e.target.value)}>
								<option value="">— Zgjidhni —</option>
								<option value="media">Media</option>
								<option value="libra">Libra</option>
								<option value="dokumente_zyrtare">Dokumente Zyrtare</option>
								<option value="akademik">Akademik</option>
								<option value="tjeter">Tjetër</option>
							</select>
						</div>
					</div>

					<label>Përmbajtja *</label>
					<textarea value={content} onChange={e => setContent(e.target.value)} rows={10} placeholder="Teksti i dokumentit..." />
				</div>
				<div className="modal-buttons">
					<button className="cancel-btn" onClick={onClose}>Anulo</button>
					<button className="save-btn" onClick={handleSubmit}>{doc ? 'Ruaj Ndryshimet' : 'Shto Dokumentin'}</button>
				</div>
			</div>
		</div>
	)
}


function UserReportModal({ user, reportData, onClose }: { user: any, reportData: any, onClose: () => void }) {
	const modalRef = useRef<HTMLDivElement>(null)
	const [isExporting, setIsExporting] = useState(false)

	if (!user || !reportData) return null

	const metrics = reportData.metrics || {}
	const strengths = reportData.strengths || []
	const weaknesses = reportData.weaknesses || []
	const categoryPerformance = reportData.categoryPerformance || []
	const recommendations = reportData.recommendations || []
	const learningStyle = reportData.learningStyle || {}
	const activityByDay = reportData.activityByDay || []
	const peakHours = reportData.peakHours || []
	const progressOverTime = reportData.progressOverTime || []

	const timeHours = Math.floor((metrics.totalTimeMinutes || 0) / 60)
	const timeMinutes = (metrics.totalTimeMinutes || 0) % 60
	const timeLabel = timeHours > 0 ? `${timeHours}h ${timeMinutes}min` : `${timeMinutes} min`
	const generatedLabel = reportData.generatedAt
		? new Date(reportData.generatedAt).toLocaleDateString('sq-AL', {
				year: 'numeric',
				month: 'long',
				day: 'numeric',
			})
		: new Date().toLocaleDateString('sq-AL', {
				year: 'numeric',
				month: 'long',
				day: 'numeric',
			})

	const handleExportPDF = async () => {
		setIsExporting(true)
		try {
			const { exportUserReportToPDF } = await import('./utils/pdfExport')
			await exportUserReportToPDF(
				user.username,
				user.email || 'Email jo i specifikuar',
				reportData
			)
			alert('Raporti u shkarkua me sukses.')
		} catch (error) {
			console.error('Gabim në eksportimin e PDF:', error)
			alert('Gabim në eksportimin e raportit. Ju lutem provoni përsëri.')
		} finally {
			setIsExporting(false)
		}
	}

	return (
		<div className="modal-overlay" onClick={onClose} ref={modalRef}>
			<div className="modal-content user-report-modal" onClick={(e) => e.stopPropagation()}>
				<button type="button" className="modal-close" onClick={onClose} aria-label="Mbyll">✕</button>

				<header className="report-header">
					<div className="report-header-content">
						<div className="report-logo-badge">
							<BrandLogo size={52} className="report-brand-logo" decorative />
						</div>
						<div>
							<p className="report-brand-eyebrow">ALBLingo</p>
							<h2>Raporti i Progresit</h2>
							<p className="report-username">{user.username}</p>
							<p className="report-email">{user.email || 'Email jo i specifikuar'}</p>
							<p className="report-meta">Gjeneruar: {generatedLabel}</p>
						</div>
					</div>
					<div className="report-header-actions">
						<button
							type="button"
							className="export-report-btn"
							onClick={handleExportPDF}
							disabled={isExporting}
						>
							<span className="export-report-btn-logo" aria-hidden="true">
								<BrandLogo size={22} decorative />
							</span>
							{isExporting ? 'Duke shkarkuar…' : 'Shkarko raportin'}
						</button>
					</div>
				</header>

				<div className="report-content">
					{/* User information */}
					<section className="report-section">
						<h3 className="report-section-title">Informacioni i përdoruesit</h3>
						<div className="report-user-info">
							<div className="report-info-row">
								<span className="report-info-label">Përdoruesi</span>
								<span className="report-info-value">{user.username}</span>
							</div>
							<div className="report-info-row">
								<span className="report-info-label">Email</span>
								<span className="report-info-value">{user.email || 'Email jo i specifikuar'}</span>
							</div>
							{user.age != null && (
								<div className="report-info-row">
									<span className="report-info-label">Mosha</span>
									<span className="report-info-value">{user.age}</span>
								</div>
							)}
							{metrics.level && (
								<div className="report-info-row">
									<span className="report-info-label">Niveli</span>
									<span className="report-info-value">{metrics.level}</span>
								</div>
							)}
							{reportData.dataSource && (
								<div className="report-info-row">
									<span className="report-info-label">Burimi</span>
									<span className="report-info-value">{reportData.dataSource}</span>
								</div>
							)}
						</div>
					</section>

					{/* Overall Progress */}
					<section className="report-section">
						<h3 className="report-section-title">Progresi i përgjithshëm</h3>
						<div className="metrics-grid">
							<div className="metric-card">
								<div className="metric-value">{metrics.totalExercises ?? 0}</div>
								<div className="metric-label">Ushtrime</div>
							</div>
							<div className="metric-card">
								<div className="metric-value">{metrics.averageScore ?? 0}%</div>
								<div className="metric-label">Saktësia mesatare</div>
							</div>
							<div className="metric-card">
								<div className="metric-value">{metrics.completedExercises ?? 0}</div>
								<div className="metric-label">Përgjigje të sakta</div>
							</div>
							<div className="metric-card">
								<div className="metric-value">{timeLabel}</div>
								<div className="metric-label">Kohë Totale</div>
							</div>
							<div className="metric-card">
								<div className="metric-value">{metrics.currentStreak ?? 0}</div>
								<div className="metric-label">Ditë radhazi</div>
							</div>
							<div className="metric-card">
								<div className="metric-value">{metrics.longestStreak ?? 0}</div>
								<div className="metric-label">Rekord ditësh</div>
							</div>
							{metrics.achievements != null && (
								<div className="metric-card">
									<div className="metric-value">{metrics.achievements}</div>
									<div className="metric-label">Arritje</div>
								</div>
							)}
						</div>
					</section>

					{/* Learning Performance */}
					<section className="report-section">
						<h3 className="report-section-title">Performanca në mësim</h3>
						{categoryPerformance.length === 0 ? (
							<p className="report-empty">Nuk ka ende të dhëna për kategori.</p>
						) : (
							<>
								<div className="chart-card">
									<ResponsiveContainer width="100%" height={280}>
										<BarChart data={categoryPerformance} margin={{ top: 16, right: 20, left: 8, bottom: 8 }}>
											<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
											<XAxis dataKey="category" tick={{ fill: '#64748b', fontSize: 11 }} />
											<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
											<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
											<Legend />
											<Bar dataKey="completed" fill="#5BBD6C" radius={[6, 6, 0, 0]} name="Të sakta" />
											<Bar dataKey="total" fill="#cbd5e1" radius={[6, 6, 0, 0]} name="Totali" />
										</BarChart>
									</ResponsiveContainer>
								</div>
								<div className="report-table-wrap">
									<table className="report-table">
										<thead>
											<tr>
												<th>Kategoria</th>
												<th>Të sakta</th>
												<th>Totali</th>
												<th>Saktësi</th>
											</tr>
										</thead>
										<tbody>
											{categoryPerformance.map((cat: any, i: number) => (
												<tr key={i}>
													<td data-label="Kategoria">{cat.category}</td>
													<td data-label="Të sakta">{cat.completed}</td>
													<td data-label="Totali">{cat.total}</td>
													<td data-label="Saktësi">
														<div className="category-progress-bar report-table-bar">
															<div
																className="category-progress-fill"
																style={{ width: `${Math.min(100, cat.percentage || 0)}%` }}
															>
																{cat.percentage}%
															</div>
														</div>
													</td>
												</tr>
											))}
										</tbody>
									</table>
								</div>
							</>
						)}
					</section>

					{/* Strengths */}
					<section className="report-section">
						<h3 className="report-section-title">Pikat e forta</h3>
						<div className="chart-card">
							{strengths.length > 0 && (
								<ResponsiveContainer width="100%" height={220}>
									<BarChart data={strengths} margin={{ top: 16, right: 20, left: 8, bottom: 8 }}>
										<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
										<XAxis dataKey="area" tick={{ fill: '#64748b', fontSize: 11 }} />
										<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
										<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
										<Bar dataKey="score" fill="#5BBD6C" radius={[6, 6, 0, 0]} name="Saktësi %" />
									</BarChart>
								</ResponsiveContainer>
							)}
							<div className="strength-list">
								{strengths.length === 0 && (
									<div className="strength-item">Nuk ka ende të dhëna të mjaftueshme.</div>
								)}
								{strengths.map((s: any, i: number) => (
									<div key={i} className="strength-item">
										<span className="strength-badge success">✓</span>
										<span>{s.area}: {s.score}% ({s.exercises} ushtrime)</span>
									</div>
								))}
							</div>
						</div>
					</section>

					{/* Areas for Improvement */}
					<section className="report-section">
						<h3 className="report-section-title">Fushat për përmirësim</h3>
						<div className="chart-card">
							{weaknesses.length > 0 && (
								<ResponsiveContainer width="100%" height={220}>
									<BarChart data={weaknesses} margin={{ top: 16, right: 20, left: 8, bottom: 8 }}>
										<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
										<XAxis dataKey="area" tick={{ fill: '#64748b', fontSize: 11 }} />
										<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
										<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
										<Bar dataKey="score" fill="#D97706" radius={[6, 6, 0, 0]} name="Saktësi %" />
									</BarChart>
								</ResponsiveContainer>
							)}
							<div className="weakness-list">
								{weaknesses.length === 0 && (
									<div className="weakness-item">Nuk është identifikuar ende ndonjë fushë e dobët.</div>
								)}
								{weaknesses.map((w: any, i: number) => (
									<div key={i} className="weakness-item">
										<span className="strength-badge warning">!</span>
										<span>{w.area}: {w.score}% ({w.exercises} ushtrime)</span>
									</div>
								))}
							</div>
						</div>
					</section>

					{/* Recent Activity */}
					<section className="report-section">
						<h3 className="report-section-title">Aktiviteti</h3>
						<div className="chart-card">
							<h4 className="chart-subtitle">Aktiviteti sipas ditëve të javës</h4>
							<ResponsiveContainer width="100%" height={280}>
								<ComposedChart data={activityByDay} margin={{ top: 16, right: 20, left: 8, bottom: 8 }}>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
									<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Legend />
									<Bar yAxisId="left" dataKey="sessions" fill="#1F6F8B" radius={[6, 6, 0, 0]} name="Ushtrime" />
									<Line yAxisId="right" type="monotone" dataKey="minutes" stroke="#5BBD6C" strokeWidth={2.5} name="Minutë" />
								</ComposedChart>
							</ResponsiveContainer>
						</div>
						<div className="chart-card">
							<h4 className="chart-subtitle">Orët më të frekuentuara</h4>
							<ResponsiveContainer width="100%" height={240}>
								<AreaChart data={peakHours} margin={{ top: 16, right: 20, left: 8, bottom: 8 }}>
									<defs>
										<linearGradient id="colorActivityUser" x1="0" y1="0" x2="0" y2="1">
											<stop offset="5%" stopColor="#1F6F8B" stopOpacity={0.75} />
											<stop offset="95%" stopColor="#1F6F8B" stopOpacity={0.08} />
										</linearGradient>
									</defs>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Area type="monotone" dataKey="activity" stroke="#1F6F8B" fillOpacity={1} fill="url(#colorActivityUser)" name="Aktivitet" />
								</AreaChart>
							</ResponsiveContainer>
						</div>
					</section>

					{/* Progress over time */}
					<section className="report-section">
						<h3 className="report-section-title">Përparimi në kohë</h3>
						<div className="chart-card">
							<h4 className="chart-subtitle">Përparimi në kohë (6 muaj)</h4>
							<ResponsiveContainer width="100%" height={280}>
								<ComposedChart data={progressOverTime} margin={{ top: 16, right: 20, left: 8, bottom: 8 }}>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
									<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Legend />
									<Area yAxisId="right" type="monotone" dataKey="avgScore" fill="#4A9FD4" stroke="#4A9FD4" fillOpacity={0.25} name="Pikë Mesatare %" />
									<Bar yAxisId="left" dataKey="exercises" fill="#5BBD6C" radius={[6, 6, 0, 0]} name="Ushtrime" />
								</ComposedChart>
							</ResponsiveContainer>
						</div>
					</section>

					{/* Learning style */}
					<section className="report-section">
						<h3 className="report-section-title">Stili i mësimit</h3>
						<div className="learning-style-grid">
							<div className="learning-style-card">
								<div className="ls-label">Koha e Preferuar</div>
								<div className="ls-value">{learningStyle.preferredTime}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-label">Gjatësia Mesatare</div>
								<div className="ls-value">{learningStyle.averageSessionLength}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-label">Frekuenca</div>
								<div className="ls-value">{learningStyle.studyFrequency}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-label">Dita më e Mirë</div>
								<div className="ls-value">{learningStyle.bestPerformanceDay}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-label">Shkalla e Përfundimit</div>
								<div className="ls-value">{learningStyle.completionRate}%</div>
							</div>
						</div>
					</section>

					{/* Recommendations */}
					<section className="report-section">
						<h3 className="report-section-title">Rekomandime</h3>
						<div className="recommendations-list">
							{recommendations.length === 0 && (
								<p className="report-empty">Nuk ka rekomandime për momentin.</p>
							)}
							{recommendations.map((rec: string, i: number) => (
								<div key={i} className="recommendation-item">
									<span className="rec-number">{i + 1}</span>
									<span className="rec-text">{rec}</span>
								</div>
							))}
						</div>
					</section>

					{/* Summary */}
					<div className="report-summary">
						<h3 className="summary-title">Përmbledhje</h3>
						<div className="summary-content">
							<p><strong>Niveli Aktual:</strong> {metrics.level}</p>
							<p>
								<strong>Ushtrime totale:</strong> {metrics.totalExercises}
								{' '}({metrics.totalExercises > 0
									? Math.round((metrics.completedExercises / metrics.totalExercises) * 100)
									: 0}% të sakta)
							</p>
							<p>
								<strong>Koha Totale:</strong>{' '}
								{Math.round((metrics.totalTimeMinutes || 0) / 60)} orë dhe {(metrics.totalTimeMinutes || 0) % 60} minuta
							</p>
							<p><strong>Numri më i madh i ditëve radhazi:</strong> {metrics.longestStreak} ditë</p>
							<p>
								<strong>Më i fortë në:</strong>{' '}
								{strengths[0]
									? `${strengths[0].area} (${strengths[0].score}%)`
									: 'Nuk ka ende të dhëna të mjaftueshme'}
							</p>
							<p>
								<strong>Duhet të përmirësojë:</strong>{' '}
								{weaknesses[0]
									? `${weaknesses[0].area} (${weaknesses[0].score}%)`
									: 'Nuk është identifikuar ende'}
							</p>
						</div>
					</div>

					<footer className="report-download-bar">
						<div className="report-download-brand">
							<BrandLogo size={40} decorative />
							<div>
								<strong>ALBLingo</strong>
								<span>Educational Progress Report</span>
							</div>
						</div>
						<button
							type="button"
							className="export-report-btn export-report-btn-footer"
							onClick={handleExportPDF}
							disabled={isExporting}
						>
							<span className="export-report-btn-logo" aria-hidden="true">
								<BrandLogo size={20} decorative />
							</span>
							{isExporting ? 'Duke shkarkuar…' : 'Shkarko raportin'}
						</button>
					</footer>
				</div>
			</div>
		</div>
	)
}
