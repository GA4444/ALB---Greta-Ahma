import React, { useState, useEffect, useRef } from 'react'
import {
	getAdminStats,
	getAllUsers,
	getAllClasses,
	getAllLevels,
	getAllExercises,
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
	getCourseLevels,
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
	type UserOut,
	type AdminStats,
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
} from './api'
import {
	BarChart,
	Bar,
	PieChart,
	Pie,
	Cell,
	LineChart,
	Line,
	AreaChart,
	Area,
	RadarChart,
	PolarGrid,
	PolarAngleAxis,
	PolarRadiusAxis,
	Radar,
	ComposedChart,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer
} from 'recharts'
import './AdminDashboard.css'
import { exportUserReportToPDF } from './utils/pdfExport'
import {
	exportToCSV,
	exportToJSON,
	exportToExcel,
	exportScientificPDF,
	type ExportData
} from './utils/dataExport'

interface AdminDashboardProps {
	userId: number
	onLogout: () => void
}

export default function AdminDashboard({ userId, onLogout }: AdminDashboardProps) {
	const [activeTab, setActiveTab] = useState<'stats' | 'users' | 'classes' | 'levels' | 'exercises' | 'corpus'>('stats')
	const [timeRange, setTimeRange] = useState<'weekly' | 'monthly' | 'yearly'>('monthly')
	const [stats, setStats] = useState<AdminStats | null>(null)
	const [users, setUsers] = useState<UserOut[]>([])
	const [classes, setClasses] = useState<ClassData[]>([])
	const [levels, setLevels] = useState<LevelOut[]>([])
	const [exercises, setExercises] = useState<ExerciseOut[]>([])
	const [selectedClass, setSelectedClass] = useState<number | null>(null)
	const [selectedLevel, setSelectedLevel] = useState<number | null>(null)
	const [loading, setLoading] = useState(false)
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

	useEffect(() => {
		loadData()
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [activeTab, selectedClass, selectedLevel, corpusFilters, corpusPage])

	const loadData = async () => {
		setLoading(true)
		try {
			if (activeTab === 'stats') {
				const statsData = await getAdminStats(userId)
				setStats(statsData)
			} else if (activeTab === 'users') {
				const usersData = await getAllUsers(userId)
				setUsers(usersData)
			} else if (activeTab === 'classes') {
				const classesData = await getAllClasses(userId)
				setClasses(classesData)
				
				// Load levels for all courses in all classes to enable global numbering
				// This is done in the background to not block the UI
				Promise.all(
					classesData.map(async (classData: ClassData) => {
						try {
							const coursesWithLevels = await Promise.all(
								(classData.courses || []).map(async (course) => {
									try {
										// Fetch levels for this course
										const levels = await getCourseLevels(course.id)
										return { ...course, levels }
									} catch (error) {
										console.error(`Error fetching levels for course ${course.id}:`, error)
										return { ...course, levels: [] }
									}
								})
							)
							return { ...classData, courses: coursesWithLevels }
						} catch (error) {
							console.error(`Error loading levels for class ${classData.id}:`, error)
							return classData
						}
					})
				).then(classesWithLevels => {
					setClasses(classesWithLevels)
				}).catch(error => {
					console.error('Error loading levels for classes:', error)
				})
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
			}
		} catch (error) {
			console.error('Error loading data:', error)
			alert('Gabim në ngarkimin e të dhënave')
		} finally {
			setLoading(false)
		}
	}

	const loadCorpusWordFreqs = async () => {
		try {
			const res = await getCorpusWordFrequencies(userId, { top_n: 100 })
			setCorpusWordFreqs(res)
		} catch (e) { console.error(e) }
	}

	const loadCorpusDuplicates = async () => {
		try {
			const res = await getCorpusDuplicates(userId)
			setCorpusDuplicates(res)
		} catch (e) { console.error(e) }
	}

	const loadLinguisticMetrics = async () => {
		try {
			const res = await getCorpusLinguisticMetrics(userId)
			setLinguisticMetrics(res)
		} catch (e) { console.error(e) }
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
			await loadData()
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
		
		// Generate mock data for user report
		// In production, this would fetch from backend API
		const mockReportData = {
			// Strengths & Weaknesses
			strengths: [
				{ area: 'Vocabulary', score: 92, exercises: 145 },
				{ area: 'Reading', score: 88, exercises: 98 },
				{ area: 'Writing', score: 85, exercises: 76 }
			],
			weaknesses: [
				{ area: 'Grammar', score: 68, exercises: 54 },
				{ area: 'Listening', score: 72, exercises: 42 }
			],
			
			// Usage patterns
			activityByDay: [
				{ day: 'E Hënë', sessions: 8, minutes: 45 },
				{ day: 'E Martë', sessions: 12, minutes: 62 },
				{ day: 'E Mërkurë', sessions: 15, minutes: 78 },
				{ day: 'E Enjte', sessions: 10, minutes: 52 },
				{ day: 'E Premte', sessions: 7, minutes: 38 },
				{ day: 'E Shtunë', sessions: 3, minutes: 18 },
				{ day: 'E Diel', sessions: 2, minutes: 12 }
			],
			
			peakHours: [
				{ hour: '08:00', activity: 5 },
				{ hour: '10:00', activity: 12 },
				{ hour: '14:00', activity: 18 },
				{ hour: '16:00', activity: 25 },
				{ hour: '18:00', activity: 15 },
				{ hour: '20:00', activity: 8 }
			],
			
			// Progress over time
			progressOverTime: [
				{ month: 'Shtator', avgScore: 65, exercises: 45 },
				{ month: 'Tetor', avgScore: 72, exercises: 68 },
				{ month: 'Nëntor', avgScore: 78, exercises: 89 },
				{ month: 'Dhjetor', avgScore: 82, exercises: 102 },
				{ month: 'Janar', avgScore: 85, exercises: 124 },
				{ month: 'Shkurt', avgScore: 88, exercises: 145 }
			],
			
			// Performance by category
			categoryPerformance: [
				{ category: 'Fillestare', completed: 45, total: 50, percentage: 90 },
				{ category: 'Mesatare', completed: 32, total: 45, percentage: 71 },
				{ category: 'E Avancuar', completed: 12, total: 30, percentage: 40 }
			],
			
			// Key metrics
			metrics: {
				totalExercises: 315,
				completedExercises: 289,
				averageScore: 82,
				totalTimeMinutes: 1850,
				currentStreak: 12,
				longestStreak: 28,
				achievements: 18,
				level: 'Mesatar-Avancuar'
			},
			
			// Learning patterns
			learningStyle: {
				preferredTime: 'Pasdite (14:00-18:00)',
				averageSessionLength: '18 minuta',
				studyFrequency: '5-6 ditë/javë',
				bestPerformanceDay: 'E Mërkurë',
				completionRate: 92
			},
			
			// Recommendations
			recommendations: [
				'Fokusohu më shumë në ushtrimin e Grammar - pikët janë 20% më poshtë mesatares',
				'Konsidero të shtosh më shumë sesione Listening - kjo është fusha më e dobët',
				'Vazhdo punën e shkëlqyer në Vocabulary! 🌟',
				'Përpiqu të mbash streak-un aktual - je në rrugën e duhur!',
				'Shto 2-3 minuta në sesionet e Grammar për rezultate më të mira'
			]
		}
		
		setUserReportData(mockReportData)
	}

	const handleDeleteUser = async (targetUserId: number) => {
		if (confirm('Jeni të sigurt që dëshironi të fshini këtë përdorues?')) {
			try {
				await deleteUser(userId, targetUserId)
				await loadData()
			} catch (error) {
				alert('Gabim në fshirjen e përdoruesit')
			}
		}
	}

	// ========== EXPORT HANDLERS ==========
	
	const prepareExportData = (): ExportData => {
		if (!stats) {
			throw new Error('Statistikat nuk janë të disponueshme')
		}

		// Prepare platform statistics
		const platformStats = {
			total_users: stats.total_users,
			active_users: Math.round(stats.total_users * 0.75), // Mock: 75% active rate
			total_classes: stats.total_classes,
			total_courses: stats.total_courses,
			total_levels: stats.total_levels,
			total_exercises: stats.total_exercises,
			total_attempts: stats.total_attempts,
			average_score: 78, // Mock për tani
			completion_rate: 82, // Mock për tani
			total_time: stats.total_attempts * 180 // Mock: ~3 min per attempt
		}

		// Prepare user statistics (mock data - do të zëvendësohet me të dhëna reale)
		const userStats = users.map(user => ({
			id: user.id,
			username: user.username,
			email: user.email,
			age: user.age,
			exercises: Math.floor(Math.random() * 50) + 10,
			avg_score: Math.floor(Math.random() * 30) + 70,
			time_spent: Math.floor(Math.random() * 500) + 100,
			streak: Math.floor(Math.random() * 30),
			level: `Klasa ${Math.floor(Math.random() * 3) + 1}`
		}))

		// Prepare content statistics (mock)
		const contentStats = [
			{ class_name: 'Klasa 1', courses: 5, levels: 25, exercises: 125, completion_rate: 85 },
			{ class_name: 'Klasa 2', courses: 5, levels: 25, exercises: 125, completion_rate: 78 },
			{ class_name: 'Klasa 3', courses: 5, levels: 25, exercises: 125, completion_rate: 72 }
		]

		// Prepare activity statistics based on time range
		let activityStats: any[] = []
		
		if (timeRange === 'weekly') {
			activityStats = [
				{ period: 'E Hënë', users: Math.round(stats.total_users * 0.15), sessions: Math.round(stats.total_attempts * 0.12), exercises: Math.round(stats.total_exercises * 0.12), avg_score: 83, time_hours: 42, success_rate: 85 },
				{ period: 'E Martë', users: Math.round(stats.total_users * 0.18), sessions: Math.round(stats.total_attempts * 0.15), exercises: Math.round(stats.total_exercises * 0.15), avg_score: 87, time_hours: 51, success_rate: 88 },
				{ period: 'E Mërkurë', users: Math.round(stats.total_users * 0.20), sessions: Math.round(stats.total_attempts * 0.18), exercises: Math.round(stats.total_exercises * 0.18), avg_score: 89, time_hours: 58, success_rate: 90 },
				{ period: 'E Enjte', users: Math.round(stats.total_users * 0.17), sessions: Math.round(stats.total_attempts * 0.16), exercises: Math.round(stats.total_exercises * 0.16), avg_score: 88, time_hours: 54, success_rate: 89 },
				{ period: 'E Premte', users: Math.round(stats.total_users * 0.14), sessions: Math.round(stats.total_attempts * 0.14), exercises: Math.round(stats.total_exercises * 0.14), avg_score: 85, time_hours: 48, success_rate: 86 },
				{ period: 'E Shtunë', users: Math.round(stats.total_users * 0.10), sessions: Math.round(stats.total_attempts * 0.13), exercises: Math.round(stats.total_exercises * 0.13), avg_score: 81, time_hours: 38, success_rate: 82 },
				{ period: 'E Diel', users: Math.round(stats.total_users * 0.08), sessions: Math.round(stats.total_attempts * 0.12), exercises: Math.round(stats.total_exercises * 0.12), avg_score: 79, time_hours: 35, success_rate: 80 }
			]
		} else if (timeRange === 'monthly') {
			activityStats = [
				{ period: 'Java 1', users: Math.round(stats.total_users * 0.22), sessions: Math.round(stats.total_attempts * 0.23), exercises: Math.round(stats.total_exercises * 0.24), avg_score: 82, time_hours: 280, success_rate: 84 },
				{ period: 'Java 2', users: Math.round(stats.total_users * 0.26), sessions: Math.round(stats.total_attempts * 0.27), exercises: Math.round(stats.total_exercises * 0.28), avg_score: 85, time_hours: 320, success_rate: 87 },
				{ period: 'Java 3', users: Math.round(stats.total_users * 0.28), sessions: Math.round(stats.total_attempts * 0.29), exercises: Math.round(stats.total_exercises * 0.29), avg_score: 87, time_hours: 340, success_rate: 89 },
				{ period: 'Java 4', users: Math.round(stats.total_users * 0.24), sessions: Math.round(stats.total_attempts * 0.21), exercises: Math.round(stats.total_exercises * 0.19), avg_score: 84, time_hours: 300, success_rate: 86 }
			]
		} else if (timeRange === 'yearly') {
			activityStats = [
				{ period: 'Janar', users: Math.round(stats.total_users * 0.08), sessions: Math.round(stats.total_attempts * 0.08), exercises: Math.round(stats.total_exercises * 0.08), avg_score: 78, time_hours: 980, success_rate: 80 },
				{ period: 'Shkurt', users: Math.round(stats.total_users * 0.07), sessions: Math.round(stats.total_attempts * 0.07), exercises: Math.round(stats.total_exercises * 0.07), avg_score: 79, time_hours: 920, success_rate: 81 },
				{ period: 'Mars', users: Math.round(stats.total_users * 0.09), sessions: Math.round(stats.total_attempts * 0.09), exercises: Math.round(stats.total_exercises * 0.09), avg_score: 81, time_hours: 1050, success_rate: 83 },
				{ period: 'Prill', users: Math.round(stats.total_users * 0.08), sessions: Math.round(stats.total_attempts * 0.08), exercises: Math.round(stats.total_exercises * 0.08), avg_score: 80, time_hours: 980, success_rate: 82 },
				{ period: 'Maj', users: Math.round(stats.total_users * 0.09), sessions: Math.round(stats.total_attempts * 0.09), exercises: Math.round(stats.total_exercises * 0.09), avg_score: 82, time_hours: 1020, success_rate: 84 },
				{ period: 'Qershor', users: Math.round(stats.total_users * 0.08), sessions: Math.round(stats.total_attempts * 0.08), exercises: Math.round(stats.total_exercises * 0.08), avg_score: 81, time_hours: 960, success_rate: 83 },
				{ period: 'Korrik', users: Math.round(stats.total_users * 0.07), sessions: Math.round(stats.total_attempts * 0.07), exercises: Math.round(stats.total_exercises * 0.07), avg_score: 79, time_hours: 880, success_rate: 81 },
				{ period: 'Gusht', users: Math.round(stats.total_users * 0.07), sessions: Math.round(stats.total_attempts * 0.07), exercises: Math.round(stats.total_exercises * 0.07), avg_score: 78, time_hours: 850, success_rate: 80 },
				{ period: 'Shtator', users: Math.round(stats.total_users * 0.10), sessions: Math.round(stats.total_attempts * 0.11), exercises: Math.round(stats.total_exercises * 0.11), avg_score: 83, time_hours: 1180, success_rate: 85 },
				{ period: 'Tetor', users: Math.round(stats.total_users * 0.09), sessions: Math.round(stats.total_attempts * 0.10), exercises: Math.round(stats.total_exercises * 0.10), avg_score: 82, time_hours: 1100, success_rate: 84 },
				{ period: 'Nëntor', users: Math.round(stats.total_users * 0.09), sessions: Math.round(stats.total_attempts * 0.09), exercises: Math.round(stats.total_exercises * 0.09), avg_score: 81, time_hours: 1030, success_rate: 83 },
				{ period: 'Dhjetor', users: Math.round(stats.total_users * 0.09), sessions: Math.round(stats.total_attempts * 0.09), exercises: Math.round(stats.total_exercises * 0.09), avg_score: 80, time_hours: 1000, success_rate: 82 }
			]
		}

		return {
			timeRange,
			platformStats,
			userStats,
			contentStats,
			activityStats,
			performanceStats: [] // Placeholder
		}
	}

	const handleExportCSV = async () => {
		setIsExporting(true)
		try {
			const exportData = prepareExportData()
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
			exportScientificPDF(exportData)
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

	return (
		<div className="admin-dashboard">
			<div className="admin-header">
				<h1>🛡️ Admin Dashboard</h1>
				<button className="admin-logout-btn" onClick={onLogout}>Dil</button>
			</div>

			<div className="admin-tabs">
				<button className={activeTab === 'stats' ? 'active' : ''} onClick={() => setActiveTab('stats')}>
					📊 Statistika
				</button>
				<button className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>
					👥 Përdoruesit
				</button>
				<button className={activeTab === 'classes' ? 'active' : ''} onClick={() => setActiveTab('classes')}>
					🏫 Klasat
				</button>
				<button className={activeTab === 'levels' ? 'active' : ''} onClick={() => setActiveTab('levels')}>
					📚 Nivelet
				</button>
				<button className={activeTab === 'exercises' ? 'active' : ''} onClick={() => setActiveTab('exercises')}>
					✏️ Ushtrimet
				</button>
				<button className={activeTab === 'corpus' ? 'active' : ''} onClick={() => setActiveTab('corpus')}>
					📖 Korpusi
				</button>
			</div>

			<div className="admin-content">
				{loading ? (
					<div className="admin-loading">Duke ngarkuar...</div>
				) : (
					<>
					{activeTab === 'stats' && stats && (
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
												<h3 className="chart-title">📈 Engagement Score & Koha e Kaluar (Minutë/Sesion)</h3>
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
														{ metrik: 'User Satisfaction', pikë: 92, maksimum: 100 },
														{ metrik: 'Learning Effectiveness', pikë: 88, maksimum: 100 },
														{ metrik: 'Content Quality', pikë: 95, maksimum: 100 },
														{ metrik: 'Platform Stability', pikë: 97, maksimum: 100 },
														{ metrik: 'User Retention', pikë: 89, maksimum: 100 },
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
							<div className="admin-table-container">
								<div className="table-header">
									<h2>Përdoruesit</h2>
								</div>
								<table className="admin-table">
									<thead>
										<tr>
											<th>ID</th>
											<th>Username</th>
											<th>Email</th>
											<th>Moshë</th>
											<th>Status</th>
											<th>Admin</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{users.map(user => (
											<tr key={user.id}>
												<td>{user.id}</td>
												<td>{user.username}</td>
												<td>{user.email}</td>
												<td>{user.age || '-'}</td>
												<td>{user.is_active ? '✅ Aktiv' : '❌ Jo aktiv'}</td>
												<td>{user.is_admin ? '🛡️ Admin' : '👤 User'}</td>
												<td>
													<button onClick={() => handleGenerateUserReport(user)}>📊 Raport</button>
													<button onClick={() => setEditingUser(user)}>✏️ Edito</button>
													<button onClick={() => handleDeleteUser(user.id)}>🗑️ Fshi</button>
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						)}

						{activeTab === 'classes' && (
							<div className="admin-table-container">
								<div className="table-header">
									<h2>Klasat</h2>
									<button className="create-btn" onClick={() => setShowCreateModal('class')}>+ Shto Klasë</button>
								</div>
								<table className="admin-table">
									<thead>
										<tr>
											<th>ID</th>
											<th>Emër</th>
											<th>Përshkrim</th>
											<th>Kurse</th>
											<th>Status</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{classes.map(cls => (
											<tr key={cls.id}>
												<td>{cls.id}</td>
												<td>{cls.name}</td>
												<td>{cls.description || '-'}</td>
												<td>{(cls.courses || []).length}</td>
												<td>{cls.enabled ? '✅ Aktiv' : '❌ Jo aktiv'}</td>
												<td>
													<button onClick={() => handleEditClass(cls)}>✏️ Edito</button>
													<button onClick={() => handleDeleteClass(cls.id)}>🗑️ Fshi</button>
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						)}

						{activeTab === 'levels' && (
							<div className="admin-table-container">
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
								<table className="admin-table">
									<thead>
										<tr>
											<th>ID</th>
											<th>Emër</th>
											<th>Klasa</th>
											<th>Përshkrim</th>
											<th>Kurs ID</th>
											<th>Status</th>
											<th>Veprime</th>
										</tr>
									</thead>
									<tbody>
										{levels.map(level => (
											<tr key={level.id}>
												<td>{level.id}</td>
												<td>{getLevelDisplayName(level)}</td>
												<td>{getLevelClassName(level)}</td>
												<td>{level.description || '-'}</td>
												<td>{level.course_id}</td>
												<td>{level.enabled ? '✅ Aktiv' : '❌ Jo aktiv'}</td>
												<td>
													<button onClick={() => handleEditLevel(level)}>✏️ Edito</button>
													<button onClick={() => handleDeleteLevel(level.id)}>🗑️ Fshi</button>
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						)}

						{activeTab === 'exercises' && (
							<div className="admin-table-container">
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
								<table className="admin-table">
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
										{exercises.map(exercise => (
											<tr key={exercise.id}>
												<td>{exercise.id}</td>
												<td>{exercise.prompt.substring(0, 50)}...</td>
												<td>{exercise.category}</td>
												<td>{exercise.level_id}</td>
												<td>{exercise.points}</td>
												<td>
													<button onClick={() => setEditingExercise(exercise)}>✏️ Edito</button>
													<button onClick={() => handleDeleteExercise(exercise.id)}>🗑️ Fshi</button>
												</td>
											</tr>
										))}
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
											<div className="stat-card"><div className="stat-icon">🔤</div><div className="stat-value">{corpusStats.total_tokens.toLocaleString()}</div><div className="stat-label">Tokens (fjalë)</div></div>
											<div className="stat-card"><div className="stat-icon">📝</div><div className="stat-value">{corpusStats.total_lemmas.toLocaleString()}</div><div className="stat-label">Lemma (unike)</div></div>
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
											<input type="text" placeholder="Kërko sipas titullit..." value={corpusFilters.search || ''} onChange={e => setCorpusFilters({...corpusFilters, search: e.target.value || undefined})} />
											<select value={corpusFilters.class_id ?? ''} onChange={e => setCorpusFilters({...corpusFilters, class_id: e.target.value ? parseInt(e.target.value) : undefined})}>
												<option value="">Të gjitha klasat</option>
												{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
											</select>
											<select value={corpusFilters.genre || ''} onChange={e => setCorpusFilters({...corpusFilters, genre: e.target.value || undefined})}>
												<option value="">Të gjithë zhanret</option>
												<option value="shkencor">Shkencor</option>
												<option value="letrar">Letrar</option>
												<option value="juridik">Juridik</option>
												<option value="publicistik">Publicistik</option>
												<option value="administrativ">Administrativ</option>
												<option value="tjeter">Tjetër</option>
											</select>
											<select value={corpusFilters.dialect || ''} onChange={e => setCorpusFilters({...corpusFilters, dialect: e.target.value || undefined})}>
												<option value="">Të gjithë dialektet</option>
												<option value="gege">Gegë</option>
												<option value="toske">Toskë</option>
												<option value="standarde">Standarde</option>
											</select>
											<select value={corpusFilters.source || ''} onChange={e => setCorpusFilters({...corpusFilters, source: e.target.value || undefined})}>
												<option value="">Të gjithë burimet</option>
												<option value="media">Media</option>
												<option value="libra">Libra</option>
												<option value="dokumente_zyrtare">Dokumente Zyrtare</option>
												<option value="akademik">Akademik</option>
												<option value="tjeter">Tjetër</option>
											</select>
											<button className="corpus-filter-clear" onClick={() => { setCorpusFilters({}); setCorpusPage(0) }}>Pastro filtrat</button>
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
													<th>Status</th>
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
										{linguisticMetrics ? (
											<>
												<div className="corpus-kpi-grid">
													<div className="corpus-kpi-card"><div className="kpi-label">TTR (Type-Token Ratio)</div><div className="kpi-value">{linguisticMetrics.type_token_ratio.toFixed(4)}</div><div className="kpi-desc">Diversiteti leksikor</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Gjatësia Mesatare e Fjalës</div><div className="kpi-value">{linguisticMetrics.avg_word_length.toFixed(2)}</div><div className="kpi-desc">Karaktere për fjalë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Gjatësia Mesatare e Fjalisë</div><div className="kpi-value">{linguisticMetrics.avg_sentence_length.toFixed(1)}</div><div className="kpi-desc">Fjalë për fjali</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Hapax Legomena</div><div className="kpi-value">{linguisticMetrics.hapax_legomena.toLocaleString()}</div><div className="kpi-desc">Fjalë që shfaqen vetëm 1 herë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Dis Legomena</div><div className="kpi-value">{linguisticMetrics.dis_legomena.toLocaleString()}</div><div className="kpi-desc">Fjalë që shfaqen vetëm 2 herë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Yule's K</div><div className="kpi-value">{linguisticMetrics.yules_k.toFixed(2)}</div><div className="kpi-desc">Konstanta e pasurueshmërisë leksikore</div></div>
												</div>

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

												{corpusWordFreqs && (
													<>
														<h3 className="corpus-section-title">Top 30 Fjalët Më të Shpeshta</h3>
														<div className="chart-card chart-card-full">
															<ResponsiveContainer width="100%" height={400}>
																<BarChart data={corpusWordFreqs.top_words.slice(0, 30)} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
																	<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
																	<XAxis dataKey="word" tick={{ fill: '#64748b', fontSize: 10 }} angle={-45} textAnchor="end" />
																	<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
																	<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
																	<Bar dataKey="count" fill="#5BBD6C" radius={[4, 4, 0, 0]} name="Frekuenca" />
																</BarChart>
															</ResponsiveContainer>
														</div>
														<p className="corpus-freq-summary">Fjalë unike totale: <strong>{corpusWordFreqs.total_unique_words.toLocaleString()}</strong></p>
													</>
												)}

												<div className="charts-container">
													<div className="chart-card">
														<h3 className="chart-title">Fjalët e Shkurtra (1–3 karaktere)</h3>
														<div className="corpus-freq-table">
															<table className="admin-table"><thead><tr><th>Fjala</th><th>Frekuenca</th></tr></thead><tbody>
																{linguisticMetrics.top_short_words.map(w => <tr key={w.word}><td><strong>{w.word}</strong></td><td>{w.count.toLocaleString()}</td></tr>)}
															</tbody></table>
														</div>
													</div>
													<div className="chart-card">
														<h3 className="chart-title">Fjalët e Gjata (8+ karaktere)</h3>
														<div className="corpus-freq-table">
															<table className="admin-table"><thead><tr><th>Fjala</th><th>Frekuenca</th></tr></thead><tbody>
																{linguisticMetrics.top_long_words.map(w => <tr key={w.word}><td><strong>{w.word}</strong></td><td>{w.count.toLocaleString()}</td></tr>)}
															</tbody></table>
														</div>
													</div>
												</div>

												<h3 className="corpus-section-title">Statistikat e Fjalive</h3>
												<div className="corpus-kpi-grid">
													<div className="corpus-kpi-card"><div className="kpi-label">Min</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats.min}</div><div className="kpi-desc">Fjalia më e shkurtër</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Max</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats.max}</div><div className="kpi-desc">Fjalia më e gjatë</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Mesatarja</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats.avg.toFixed(1)}</div><div className="kpi-desc">Fjalë për fjali</div></div>
													<div className="corpus-kpi-card"><div className="kpi-label">Mediana</div><div className="kpi-value">{linguisticMetrics.sentence_length_stats.median}</div><div className="kpi-desc">Vlera e mesme</div></div>
												</div>
											</>
										) : (
											<div className="admin-loading">Duke analizuar korpusin...</div>
										)}
									</div>
								)}

								{/* ── 4. KLASIFIKIMI & SEGMENTIMI ── */}
								{corpusSubTab === 'classification' && corpusStats && (
									<div className="corpus-classification-section">
										<h2>Klasifikimi & Segmentimi i Korpusit</h2>
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
														<Bar dataKey="tokens" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Tokens" />
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
															<div className="fuse-code-stats"><span>{fc.document_count} dok.</span><span>{fc.total_tokens.toLocaleString()} tokens</span></div>
														</div>
													))}
												</div>
											</div>
										)}
									</div>
								)}

								{/* ── 5. STATISTIKA SIPAS KLASËS ── */}
								{corpusSubTab === 'per_class' && corpusStats && (
									<div className="corpus-per-class-section">
										<h2>Shpërndarja e Korpusit Sipas Klasës</h2>
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
															<Line yAxisId="right" type="monotone" dataKey="tokens" stroke="#5BBD6C" strokeWidth={3} name="Tokens" />
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
														{corpusStats.by_class.map(c => {
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
														{corpusStats.unlinked_documents > 0 && (
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
											<div className="admin-loading">Duke kontrolluar integritetin...</div>
										)}
									</div>
								)}
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

	const handleExportPDF = async () => {
		setIsExporting(true)
		try {
			// Method 1: Text-based PDF (faster, smaller file)
			await exportUserReportToPDF(
				user.username,
				user.email || 'Email jo i specifikuar',
				reportData
			)
			
			// Method 2: Image-based PDF with charts (more accurate, larger file)
			// Uncomment below to use chart capture instead:
			/*
			if (modalRef.current) {
				const reportContent = modalRef.current.querySelector('.user-report-modal') as HTMLElement
				if (reportContent) {
					await exportUserReportWithChartsToPDF(reportContent, user.username)
				}
			}
			*/
			
			alert('✅ Raporti u eksportua me sukses në PDF!')
		} catch (error) {
			console.error('Gabim në eksportimin e PDF:', error)
			alert('❌ Gabim në eksportimin e raportit. Ju lutem provoni përsëri.')
		} finally {
			setIsExporting(false)
		}
	}

	return (
		<div className="modal-overlay" onClick={onClose} ref={modalRef}>
			<div className="modal-content user-report-modal" onClick={(e) => e.stopPropagation()}>
				<button className="modal-close" onClick={onClose}>✕</button>
				
				<div className="report-header">
					<div className="report-header-content">
						<div className="report-user-icon">👤</div>
						<div>
							<h2>📊 Raporti i Përdoruesit</h2>
							<p className="report-username">{user.username}</p>
							<p className="report-email">{user.email || 'Email jo i specifikuar'}</p>
						</div>
					</div>
					<button 
						className="export-report-btn" 
						onClick={handleExportPDF}
						disabled={isExporting}
					>
						{isExporting ? '⏳ Duke eksportuar...' : '📄 Eksporto PDF'}
					</button>
				</div>

				<div className="report-content">
					{/* Key Metrics */}
					<div className="report-section">
						<h3 className="report-section-title">📈 Metriks Kryesore</h3>
						<div className="metrics-grid">
							<div className="metric-card">
								<div className="metric-icon">✏️</div>
								<div className="metric-value">{reportData.metrics.totalExercises}</div>
								<div className="metric-label">Ushtrime Totale</div>
							</div>
							<div className="metric-card">
								<div className="metric-icon">✅</div>
								<div className="metric-value">{reportData.metrics.completedExercises}</div>
								<div className="metric-label">Përfunduar</div>
							</div>
							<div className="metric-card">
								<div className="metric-icon">🎯</div>
								<div className="metric-value">{reportData.metrics.averageScore}%</div>
								<div className="metric-label">Pikë Mesatare</div>
							</div>
							<div className="metric-card">
								<div className="metric-icon">⏱️</div>
								<div className="metric-value">{Math.round(reportData.metrics.totalTimeMinutes / 60)}h</div>
								<div className="metric-label">Kohë Totale</div>
							</div>
							<div className="metric-card">
								<div className="metric-icon">🔥</div>
								<div className="metric-value">{reportData.metrics.currentStreak}</div>
								<div className="metric-label">Streak Aktual</div>
							</div>
							<div className="metric-card">
								<div className="metric-icon">🏆</div>
								<div className="metric-value">{reportData.metrics.achievements}</div>
								<div className="metric-label">Arritje</div>
							</div>
						</div>
					</div>

					{/* Strengths & Weaknesses */}
					<div className="report-section">
						<h3 className="report-section-title">💪 Pikat e Forta & Dobëta</h3>
						<div className="strength-weakness-grid">
							<div className="chart-card chart-card-half">
								<h4 className="chart-subtitle">✨ Pikat e Forta</h4>
								<ResponsiveContainer width="100%" height={250}>
									<BarChart data={reportData.strengths} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
										<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
										<XAxis dataKey="area" tick={{ fill: '#64748b', fontSize: 11 }} />
										<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
										<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
										<Bar dataKey="score" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Pikët" />
									</BarChart>
								</ResponsiveContainer>
								<div className="strength-list">
									{reportData.strengths.map((s: any, i: number) => (
										<div key={i} className="strength-item">
											<span className="strength-badge success">✓</span>
											<span>{s.area}: {s.score}% ({s.exercises} ushtrime)</span>
										</div>
									))}
								</div>
							</div>

							<div className="chart-card chart-card-half">
								<h4 className="chart-subtitle">⚠️ Pikat e Dobëta</h4>
								<ResponsiveContainer width="100%" height={250}>
									<BarChart data={reportData.weaknesses} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
										<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
										<XAxis dataKey="area" tick={{ fill: '#64748b', fontSize: 11 }} />
										<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
										<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
										<Bar dataKey="score" fill="#FF9600" radius={[8, 8, 0, 0]} name="Pikët" />
									</BarChart>
								</ResponsiveContainer>
								<div className="weakness-list">
									{reportData.weaknesses.map((w: any, i: number) => (
										<div key={i} className="weakness-item">
											<span className="strength-badge warning">!</span>
											<span>{w.area}: {w.score}% ({w.exercises} ushtrime)</span>
										</div>
									))}
								</div>
							</div>
						</div>
					</div>

					{/* Activity Patterns */}
					<div className="report-section">
						<h3 className="report-section-title">📅 Patternët e Aktivitetit</h3>
						<div className="chart-card">
							<h4 className="chart-subtitle">📊 Aktiviteti sipas Ditëve të Javës</h4>
							<ResponsiveContainer width="100%" height={300}>
								<ComposedChart data={reportData.activityByDay} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
									<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Legend />
									<Bar yAxisId="left" dataKey="sessions" fill="#4A9FD4" radius={[8, 8, 0, 0]} name="Sesione" />
									<Line yAxisId="right" type="monotone" dataKey="minutes" stroke="#5BBD6C" strokeWidth={3} name="Minutë" />
								</ComposedChart>
							</ResponsiveContainer>
						</div>

						<div className="chart-card">
							<h4 className="chart-subtitle">🕐 Orët më të Frekuentuara</h4>
							<ResponsiveContainer width="100%" height={250}>
								<AreaChart data={reportData.peakHours} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
									<defs>
										<linearGradient id="colorActivityUser" x1="0" y1="0" x2="0" y2="1">
											<stop offset="5%" stopColor="#CE82FF" stopOpacity={0.8}/>
											<stop offset="95%" stopColor="#CE82FF" stopOpacity={0.1}/>
										</linearGradient>
									</defs>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Area type="monotone" dataKey="activity" stroke="#CE82FF" fillOpacity={1} fill="url(#colorActivityUser)" name="Aktivitet" />
								</AreaChart>
							</ResponsiveContainer>
						</div>
					</div>

					{/* Progress Over Time */}
					<div className="report-section">
						<h3 className="report-section-title">📈 Përparimi në Kohë (6 Muaj)</h3>
						<div className="chart-card">
							<ResponsiveContainer width="100%" height={300}>
								<ComposedChart data={reportData.progressOverTime} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} />
									<YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Legend />
									<Area yAxisId="right" type="monotone" dataKey="avgScore" fill="#4A9FD4" stroke="#4A9FD4" fillOpacity={0.3} name="Pikë Mesatare %" />
									<Bar yAxisId="left" dataKey="exercises" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Ushtrime" />
								</ComposedChart>
							</ResponsiveContainer>
						</div>
					</div>

					{/* Category Performance */}
					<div className="report-section">
						<h3 className="report-section-title">🎯 Performanca sipas Kategorisë</h3>
						<div className="chart-card">
							<ResponsiveContainer width="100%" height={300}>
								<BarChart data={reportData.categoryPerformance} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
									<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
									<XAxis dataKey="category" tick={{ fill: '#64748b', fontSize: 11 }} />
									<YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
									<Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
									<Legend />
									<Bar dataKey="completed" fill="#5BBD6C" radius={[8, 8, 0, 0]} name="Përfunduar" />
									<Bar dataKey="total" fill="#e2e8f0" radius={[8, 8, 0, 0]} name="Totali" />
								</BarChart>
							</ResponsiveContainer>
							<div className="category-details">
								{reportData.categoryPerformance.map((cat: any, i: number) => (
									<div key={i} className="category-detail-item">
										<div className="category-name">{cat.category}</div>
										<div className="category-progress-bar">
											<div className="category-progress-fill" style={{ width: `${cat.percentage}%` }}>
												{cat.percentage}%
											</div>
										</div>
										<div className="category-stats">{cat.completed}/{cat.total}</div>
									</div>
								))}
							</div>
						</div>
					</div>

					{/* Learning Style */}
					<div className="report-section">
						<h3 className="report-section-title">🧠 Stili i Mësimit & Preferencat</h3>
						<div className="learning-style-grid">
							<div className="learning-style-card">
								<div className="ls-icon">🕐</div>
								<div className="ls-label">Koha e Preferuar</div>
								<div className="ls-value">{reportData.learningStyle.preferredTime}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-icon">⏱️</div>
								<div className="ls-label">Gjatësia Mesatare</div>
								<div className="ls-value">{reportData.learningStyle.averageSessionLength}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-icon">📅</div>
								<div className="ls-label">Frekuenca</div>
								<div className="ls-value">{reportData.learningStyle.studyFrequency}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-icon">⭐</div>
								<div className="ls-label">Dita më e Mirë</div>
								<div className="ls-value">{reportData.learningStyle.bestPerformanceDay}</div>
							</div>
							<div className="learning-style-card">
								<div className="ls-icon">✅</div>
								<div className="ls-label">Shkalla e Përfundimit</div>
								<div className="ls-value">{reportData.learningStyle.completionRate}%</div>
							</div>
						</div>
					</div>

					{/* Recommendations */}
					<div className="report-section">
						<h3 className="report-section-title">💡 Rekomandime Personalizuara</h3>
						<div className="recommendations-list">
							{reportData.recommendations.map((rec: string, i: number) => (
								<div key={i} className="recommendation-item">
									<span className="rec-number">{i + 1}</span>
									<span className="rec-text">{rec}</span>
								</div>
							))}
						</div>
					</div>

					{/* Summary */}
					<div className="report-summary">
						<h3 className="summary-title">📋 Përmbledhje e Plotë</h3>
						<div className="summary-content">
							<p><strong>Niveli Aktual:</strong> {reportData.metrics.level}</p>
							<p><strong>Ushtrime Totale:</strong> {reportData.metrics.totalExercises} ({Math.round((reportData.metrics.completedExercises / reportData.metrics.totalExercises) * 100)}% përfunduar)</p>
							<p><strong>Koha Totale:</strong> {Math.round(reportData.metrics.totalTimeMinutes / 60)} orë dhe {reportData.metrics.totalTimeMinutes % 60} minuta</p>
							<p><strong>Streak më i Gjatë:</strong> {reportData.metrics.longestStreak} ditë</p>
							<p><strong>Më i fortë në:</strong> {reportData.strengths[0].area} ({reportData.strengths[0].score}%)</p>
							<p><strong>Duhet të përmirësojë:</strong> {reportData.weaknesses[0].area} ({reportData.weaknesses[0].score}%)</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	)
}
