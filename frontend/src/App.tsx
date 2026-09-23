// Updated: 2026-01-05 18:21 - Fixed cls.courses iteration bug
import { lazy, Suspense, useState, useEffect, useRef } from 'react'
import type { ChangeEvent } from 'react'
import type { CourseOut, LevelOut, ExerciseOut, ProgressOut, ClassData, AIPracticeExercise, AICoachResponse, UserAchievementsResponse, StreakData, DailyChallenge, SRSStatsResponse } from './api'
import { getClasses, getClassCourses, getCourseLevels, getLevelExercises, submitAnswer, fetchUserOverview, fetchUserTotals, login, getAIRecommendations, getAdaptiveDifficulty, getLearningPath, getProgressInsights, getLeaderboard, getUserRank, getPublicStats, fetchAIPersonalizedPractice, fetchAICoach, analyzeOCR, getUserAchievements, getUserStreak, getDailyChallenge, getSRSStats, getUserProfile, updateUserProfile, getAdminStats, type LeaderboardEntry, generateAdvancedPractice, browseCorpus, browseCorpusDocument, generatePedagogicalFeedback, getAdaptiveNextItem } from './api'
import type { CorpusDocument } from './api'
import { AppFooter, AppHeader } from './components/AppChrome'
import LazyErrorBoundary from './components/LazyErrorBoundary'
import WelcomeLanding from './components/WelcomeLanding'
import BrandLogo from './components/BrandLogo'
import { IconBook, IconCalendar, IconFlame, IconSparkle, IconStar, IconTrophy } from './components/ProgressIcons'
import RegisterForm from './components/RegisterForm'
import { useModalAccessibility } from './hooks/useModalAccessibility'
import './App.css'
import './mobile-refinements.css'
import './professional-polish.css'
import './professional-pro.css'
import './mobile-app.css'
import './brand-consistency.css'
import './child-learning-ui.css'

const AdminDashboard = lazy(() => import('./AdminDashboard'))
const AdvancedAIPractice = lazy(() => import('./AdvancedAIPractice'))
const ChatbotFloating = lazy(() => import('./ChatbotFloating'))

const LEADERBOARD_TITLE = 'Vendi yt në renditje'

const getToastTone = (text: string): 'info' | 'success' | 'error' | 'warning' => {
    const m = text.toLowerCase()
    if (/gabim|pasakt|fail|error|❌|kredencialet|nuk mbështet|nuk përputhen/.test(m)) return 'error'
    if (/mirësevini|saktë|sukses|urime|bravo|✅|🎉|u krye|u përditësua/.test(m)) return 'success'
    if (/⚠️|mbyllur|kujdes|warning|bosh/.test(m)) return 'warning'
    return 'info'
}

const getToastIcon = (tone: 'info' | 'success' | 'error' | 'warning') => {
    if (tone === 'success') return '✓'
    if (tone === 'error') return '!'
    if (tone === 'warning') return '!'
    return 'i'
}

const cleanToastText = (text: string) =>
    text.replace(/^[\s]*(?:✅|❌|⚠️|🎉|✔️|✖️)+\s*/u, '').trim() || text

function AppToast({ message }: { message: string }) {
    const tone = getToastTone(message)
    return (
        <div className={`app-toast app-toast--${tone}`} role="status" aria-live="polite">
            <span className="app-toast-icon" aria-hidden="true">{getToastIcon(tone)}</span>
            <span className="app-toast-text">{cleanToastText(message)}</span>
        </div>
    )
}

/** Curriculum "Niveli N" lives on the Course; each course often has a single Level with order_index=1. */
const getClassNumber = (selectedClass: ClassData | null | undefined, classes: ClassData[] = []): number => {
	if (!selectedClass) return 1
	if (selectedClass.order_index && selectedClass.order_index > 0) return selectedClass.order_index
	const fromName = selectedClass.name?.match(/Klasa\s+(\d+)/i)
	if (fromName) return parseInt(fromName[1], 10)
	const idx = classes.findIndex((c) => c.id === selectedClass.id)
	return idx >= 0 ? idx + 1 : 1
}

const getCurriculumLevelNumber = (
	selectedCourse: CourseOut | null | undefined,
	selectedLevel: LevelOut | null | undefined,
): number => {
	if (selectedCourse?.order_index && selectedCourse.order_index > 0) return selectedCourse.order_index
	const fromCourseName = selectedCourse?.name?.match(/Niveli\s+(\d+)/i)
	if (fromCourseName) return parseInt(fromCourseName[1], 10)
	if (selectedLevel?.order_index && selectedLevel.order_index > 0) return selectedLevel.order_index
	const fromLevelName = selectedLevel?.name?.match(/Niveli\s+(\d+)/i)
	if (fromLevelName) return parseInt(fromLevelName[1], 10)
	return 1
}

const formatCurriculumLabel = (
	selectedClass: ClassData | null | undefined,
	selectedCourse: CourseOut | null | undefined,
	selectedLevel: LevelOut | null | undefined,
	classes: ClassData[] = [],
): string => {
	const classNumber = getClassNumber(selectedClass, classes)
	const levelNumber = getCurriculumLevelNumber(selectedCourse, selectedLevel)
	return `Niveli ${levelNumber} Klasa ${classNumber}`
}

const normalizeText = (value: string) => {
    return value.normalize('NFKC').toLowerCase().trim().replace(/\s+/g, ' ')
}

const inferExerciseAnswer = (exercise?: ExerciseOut | null): string | null => {
    if (!exercise?.data) return null
    try {
        const data = JSON.parse(exercise.data)
        const candidates = [
            data.answer,
            data.correct_answer,
            data.correct,
            data.solution,
            data.zgjidhja,
            data.word,
            data.fjala,
            data.term,
        ]
        const value = candidates.find(item => typeof item === 'string' && item.trim())
        return value ? String(value) : null
    } catch {
        return null
    }
}

const SESSION_EPOCH = 'neon-2026-08-23'

function readFreshSession(): { userId: string | null; isAdmin: boolean } {
    try {
        if (localStorage.getItem('session_epoch') !== SESSION_EPOCH) {
            localStorage.removeItem('user_id')
            localStorage.removeItem('is_admin')
            localStorage.removeItem('username')
            localStorage.setItem('session_epoch', SESSION_EPOCH)
            return { userId: null, isAdmin: false }
        }
        const stored = localStorage.getItem('user_id')
        const userId = stored && stored !== 'null' && stored !== 'undefined' && stored.trim() !== ''
            ? stored
            : null
        return {
            userId,
            isAdmin: userId !== null && localStorage.getItem('is_admin') === 'true',
        }
    } catch {
        return { userId: null, isAdmin: false }
    }
}

function persistSession(userId: string, username: string, isAdmin: boolean) {
    localStorage.setItem('session_epoch', SESSION_EPOCH)
    localStorage.setItem('user_id', userId)
    localStorage.setItem('username', username)
    localStorage.setItem('is_admin', String(isAdmin))
}

function App() {
    const initialSession = readFreshSession()
    const [userId, setUserId] = useState<string | null>(initialSession.userId)
    const [isAdmin, setIsAdmin] = useState<boolean>(initialSession.isAdmin)
    const [auth, setAuth] = useState({ username: '', password: '' })
    
    const clearStoredSession = () => {
        localStorage.removeItem('user_id')
        localStorage.removeItem('is_admin')
        localStorage.removeItem('username')
        localStorage.setItem('session_epoch', SESSION_EPOCH)
        setUserId(null)
        setIsAdmin(false)
    }

    // Data state
    const [classes, setClasses] = useState<ClassData[]>([])
    const [selectedClass, setSelectedClass] = useState<ClassData | null>(null)
    const [selectedCourse, setSelectedCourse] = useState<CourseOut | null>(null)
    const [selectedLevel, setSelectedLevel] = useState<LevelOut | null>(null)
    const [exercises, setExercises] = useState<ExerciseOut[]>([])
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0)
    const exerciseStartedAtRef = useRef(Date.now())

    useEffect(() => {
        exerciseStartedAtRef.current = Date.now()
    }, [currentExerciseIndex, exercises])
    
    // Public stats for welcome screen
    const [publicStats, setPublicStats] = useState({
        total_classes: 0,
        total_exercises: 0,
        total_categories: 0,
        total_levels: 0
    })

    // Progress and gamification state
    const [answers, setAnswers] = useState<Record<number, string>>({})
    const [progress, setProgress] = useState<ProgressOut[]>([])

    const [message, setMessage] = useState<string>('')
    const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false)
    const [showAuth, setShowAuth] = useState(false)
    const [showWelcome, setShowWelcome] = useState(true)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        if (!isAdmin || !userId) return

        const adminUserId = parseInt(userId, 10)
        if (Number.isNaN(adminUserId)) {
            clearStoredSession()
            return
        }

        let cancelled = false
        getAdminStats(adminUserId)
            .catch((error: any) => {
                if (cancelled) return
                const status = error?.response?.status
                if (status === 403 || status === 404) {
                    clearStoredSession()
                }
            })

        return () => {
            cancelled = true
        }
    }, [isAdmin, userId])

    // Auto-clear message after 3 seconds
    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => {
                setMessage('')
            }, 3000) // 3 seconds
            
            return () => clearTimeout(timer)
        }
    }, [message])

    // Fetch public stats for welcome screen
    useEffect(() => {
        const fetchPublicStats = async () => {
            try {
                const stats = await getPublicStats()
                setPublicStats(stats)
            } catch (error) {
                console.error('Error fetching public stats:', error)
            }
        }
        fetchPublicStats()
    }, [])

    // Advanced gamification state
    const [userStats, setUserStats] = useState({
        totalPoints: 0,
        totalStars: 0,
        streakDays: 0,
        level: 1,
        experience: 0,
        nextLevelExp: 100
    })

    // AI-powered features state
    const [aiRecommendations, setAiRecommendations] = useState<any>(null)
    const [adaptiveDifficulty, setAdaptiveDifficulty] = useState<any>(null)
    const [learningPath, setLearningPath] = useState<any>(null)
    const [progressInsights, setProgressInsights] = useState<any>(null)
    const [aiCoach, setAiCoach] = useState<AICoachResponse | null>(null)
    const [aiCoachLoading, setAiCoachLoading] = useState(false)
    const [aiCoachError, setAiCoachError] = useState<string | null>(null)
    const [aiCoachLevel, setAiCoachLevel] = useState<AICoachResponse | null>(null)
    const [aiCoachLevelLoading, setAiCoachLevelLoading] = useState(false)
    const [aiCoachLevelError, setAiCoachLevelError] = useState<string | null>(null)
    const [showAIInsights, setShowAIInsights] = useState(false)
    const [childLearningSupport, setChildLearningSupport] = useState<any>(null)
    const [childLearningLoading, setChildLearningLoading] = useState(false)
    const [childFeedback, setChildFeedback] = useState<any>(null)
    const [childPracticeAnswer, setChildPracticeAnswer] = useState('')
    const [childPracticeMessage, setChildPracticeMessage] = useState<string | null>(null)
    const [showProfile, setShowProfile] = useState(false)

    // Gamification state
    const [userAchievements, setUserAchievements] = useState<UserAchievementsResponse | null>(null)
    const [userStreak, setUserStreak] = useState<StreakData | null>(null)
    const [dailyChallenge, setDailyChallenge] = useState<DailyChallenge | null>(null)
    const [srsStats, setSrsStats] = useState<SRSStatsResponse | null>(null)
    const [showGamification, setShowGamification] = useState(false)

    // Corpus browse state
    const [showCorpusBrowse, setShowCorpusBrowse] = useState(false)
    const [corpusBrowseDocs, setCorpusBrowseDocs] = useState<CorpusDocument[]>([])
    const [corpusBrowseTotal, setCorpusBrowseTotal] = useState(0)
    const [corpusBrowseSearch, setCorpusBrowseSearch] = useState('')
    const [corpusBrowseClassId, setCorpusBrowseClassId] = useState<number | undefined>(undefined)
    const [corpusBrowseLoading, setCorpusBrowseLoading] = useState(false)
    const [selectedCorpusDoc, setSelectedCorpusDoc] = useState<CorpusDocument | null>(null)
    const [corpusBrowseOffset, setCorpusBrowseOffset] = useState(0)

    const [showLeaderboard, setShowLeaderboard] = useState(false)
    const [leaderboardData, setLeaderboardData] = useState<LeaderboardEntry[]>([])
    const [userRank, setUserRank] = useState<any>(null)
    const [showLevelInfo, setShowLevelInfo] = useState(false)
    const [classProgressData, setClassProgressData] = useState<any[]>([])
    const [userProfile, setUserProfile] = useState<any>(null)
    const [profileImage, setProfileImage] = useState<string | null>(null)
    const [isEditingProfile, setIsEditingProfile] = useState(false)
    const [profileFormData, setProfileFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        age: '',
        date_of_birth: '',
        address: '',
        phone_number: ''
    })
    const [profileLoading, setProfileLoading] = useState(false)
    const [profileError, setProfileError] = useState<string | null>(null)
    const profileModalRef = useModalAccessibility(showProfile, () => setShowProfile(false))
    const leaderboardModalRef = useModalAccessibility(showLeaderboard, () => setShowLeaderboard(false))
    const levelInfoModalRef = useModalAccessibility(showLevelInfo, () => setShowLevelInfo(false))
    const corpusModalRef = useModalAccessibility(showCorpusBrowse, () => {
        setShowCorpusBrowse(false)
        setSelectedCorpusDoc(null)
    })

    // Audio features state
    const [isRecording, setIsRecording] = useState(false)



    // Course levels state
    const [courseLevels, setCourseLevels] = useState<LevelOut[]>([])
    const [classCourses, setClassCourses] = useState<CourseOut[]>([])

    // AI practice state
    const [aiExercises, setAiExercises] = useState<AIPracticeExercise[]>([])
    const [aiResponses, setAiResponses] = useState<Record<string, string>>({})
    const [aiFeedback, setAiFeedback] = useState<Record<string, string>>({})
    const [aiMessage, setAiMessage] = useState<string | null>(null)
    const [aiError, setAiError] = useState<string | null>(null)
    const [aiLoading, setAiLoading] = useState<boolean>(false)

    const [ocrFile, setOcrFile] = useState<File | null>(null)
    const [ocrExpected, setOcrExpected] = useState<string>('')
    const [ocrResult, setOcrResult] = useState<any>(null)
    const [ocrLoading, setOcrLoading] = useState<boolean>(false)
    const [ocrError, setOcrError] = useState<string | null>(null)






    // Fetch classes on component mount
    useEffect(() => {
        if (userId) {
            fetchClasses()
            fetchUserStats()
        }
    }, [userId])

    // Fetch AI data when user is logged in (optimized with prioritization)
    useEffect(() => {
        if (userId) {
            // Priority 1: Essential AI features loaded immediately
            const essentialPromises = [
                getAIRecommendations(userId).catch(e => { console.error('AI Recs error:', e); return null; }),
                getUserStreak(userId).catch(e => { console.error('Streak error:', e); return null; })
            ]
            
            Promise.all(essentialPromises).then(([recs, streak]) => {
                if (recs) setAiRecommendations(recs)
                if (streak) setUserStreak(streak)
            })

            // Priority 2: Secondary features loaded with slight delay (debounced)
            const secondaryTimer = setTimeout(() => {
                Promise.all([
                    getAdaptiveDifficulty(userId).catch(e => { console.error('Difficulty error:', e); return null; }),
                    getLearningPath(userId).catch(e => { console.error('Path error:', e); return null; }),
                    getProgressInsights(userId).catch(e => { console.error('Insights error:', e); return null; }),
                    getUserAchievements(userId).catch(e => { console.error('Achievements error:', e); return null; }),
                    getDailyChallenge(userId).catch(e => { console.error('Challenge error:', e); return null; }),
                ]).then(([diff, path, insights, achievements, challenge]) => {
                    if (diff) setAdaptiveDifficulty(diff)
                    if (path) setLearningPath(path)
                    if (insights) setProgressInsights(insights)
                    if (achievements) setUserAchievements(achievements)
                    if (challenge) setDailyChallenge(challenge)
                })
            }, 2500) // Keep network free for class/exercise navigation first

            // Priority 3: AI Coach and SRS loaded last (heavier operations)
            const tertiaryTimer = setTimeout(() => {
                // AI Coach (overall)
                setAiCoachLoading(true)
                setAiCoachError(null)
                fetchAICoach({ user_id: userId }).then((data) => {
                    setAiCoach(data)
                }).catch((e) => {
                    console.error('AI Coach error:', e)
                    setAiCoachError('AI Coach nuk është i disponueshëm tani.')
                }).finally(() => setAiCoachLoading(false))

                // SRS Stats
                getSRSStats(userId).then(setSrsStats).catch(e => console.error('SRS error:', e))
            }, 4000) // After navigation/API traffic settles

            // Cleanup timers on unmount
            return () => {
                clearTimeout(secondaryTimer)
                clearTimeout(tertiaryTimer)
            }
        }
    }, [userId])

    // AI Coach (current level) – refresh when level changes
    useEffect(() => {
        if (!userId) return
        if (!selectedLevel) {
            setAiCoachLevel(null)
            setAiCoachLevelError(null)
            setAiCoachLevelLoading(false)
            return
        }

        setAiCoachLevelLoading(true)
        setAiCoachLevelError(null)
        fetchAICoach({ user_id: userId, level_id: selectedLevel.id }).then((data) => {
            setAiCoachLevel(data)
        }).catch((e) => {
            console.error('AI Coach (level) error:', e)
            setAiCoachLevelError('AI Coach për këtë nivel nuk është i disponueshëm tani.')
        }).finally(() => setAiCoachLevelLoading(false))
    }, [userId, selectedLevel?.id])

    // Load corpus browse data
    const loadCorpusBrowse = async () => {
        setCorpusBrowseLoading(true)
        try {
            const res = await browseCorpus({
                class_id: corpusBrowseClassId,
                search: corpusBrowseSearch || undefined,
                limit: 20,
                offset: corpusBrowseOffset,
            })
            setCorpusBrowseDocs(res.documents)
            setCorpusBrowseTotal(res.total)
        } catch (error) {
            console.error('Corpus browse error:', error)
        } finally {
            setCorpusBrowseLoading(false)
        }
    }

    const loadCorpusDocument = async (docId: number) => {
        try {
            const doc = await browseCorpusDocument(docId)
            setSelectedCorpusDoc(doc)
        } catch (error) {
            console.error('Corpus doc error:', error)
        }
    }

    useEffect(() => {
        if (showCorpusBrowse) {
            loadCorpusBrowse()
        }
    }, [showCorpusBrowse, corpusBrowseClassId, corpusBrowseOffset])

    // Simple cache to avoid re-fetching classes unnecessarily
    const [classesCache, setClassesCache] = useState<{ data: ClassData[], timestamp: number } | null>(null)
    const CACHE_DURATION = 120000 // 2 minutes

    const fetchClasses = async (forceRefresh = false) => {
        // Return cached data if available and not expired
        if (!forceRefresh && classesCache && (Date.now() - classesCache.timestamp < CACHE_DURATION)) {
            setClasses(classesCache.data)
            setIsLoading(false)
            return
        }

        try {
            const classesData = await getClasses(userId || undefined)
            setClasses(classesData)
            setClassesCache({ data: classesData, timestamp: Date.now() })
            setIsLoading(false)
        } catch (error) {
            console.error('Error fetching classes:', error)
            setIsLoading(false)
        }
    }

    const fetchUserStats = async () => {
        if (userId) {
            try {
                const [totals, streak] = await Promise.all([
                    fetchUserTotals(userId),
                    getUserStreak(userId).catch((e) => {
                        console.error('Streak error:', e)
                        return null
                    }),
                ])
                if (streak !== null) {
                    setUserStreak(streak)
                }
                if (totals) {
                    setUserStats(prev => ({
                        totalPoints: totals.total_points,
                        totalStars: totals.total_stars,
                        streakDays: streak !== null ? (streak.current_streak || 0) : prev.streakDays,
                        level: Math.floor(totals.total_points / 100) + 1,
                        experience: totals.total_points % 100,
                        nextLevelExp: 100
                    }))
                    // Set user profile data - use localStorage for user info
                    const storedUsername = localStorage.getItem('username') || ''
                    setUserProfile({
                        username: storedUsername,
                        email: '', // Will be fetched separately if needed
                        age: null, // Will be fetched separately if needed
                        created_at: '',
                        last_login: null
                    })
                    // Load profile image from localStorage if exists
                    const savedImage = localStorage.getItem(`profile_image_${userId}`)
                    if (savedImage) {
                        setProfileImage(savedImage)
                    }
                }
            } catch (error) {
                console.error('Error fetching user stats:', error)
            }
        }
    }





    const handleClassClick = async (classData: ClassData | null) => {
        if (classData === null) {
            // Go back to classes view - refresh classes to get updated progress
            if (userId) {
                fetchClasses()
            }
            setSelectedClass(null)
            setSelectedCourse(null)
            setSelectedLevel(null)
            setExercises([])
            setCurrentExerciseIndex(0)
            setCourseLevels([])
            return
        }

        if (!classData.unlocked) {
            setMessage('Kjo klasë është e mbyllur. Duhet të përfundosh klasën e mëparshme. 🔒')
            return
        }

        setSelectedClass(classData)
        setSelectedCourse(null)
        setSelectedLevel(null)
        setExercises([])
        setCurrentExerciseIndex(0)
        setCourseLevels([])
        setClassCourses([])
        setIsLoading(true)
        
        try {
            // One request returns courses and their levels (no N+1 round-trips).
            const coursesWithLevels = await getClassCourses(classData.id, userId!, true)
            setClassCourses(coursesWithLevels)
            setClasses(prevClasses => prevClasses.map(cls => {
                if (cls.id === classData.id) {
                    return { ...cls, courses: coursesWithLevels }
                }
                return cls
            }))
        } catch (error) {
            console.error('Error fetching class courses:', error)
            setClassCourses([])
        } finally {
            setIsLoading(false)
        }
    }

    const handleCourseClick = async (course: CourseOut | null) => {
        if (course === null) {
            // Go back to courses view
            setSelectedCourse(null)
            setSelectedLevel(null)
            setExercises([])
            setCurrentExerciseIndex(0)
            setCourseLevels([])
            return
        }

        if (!course.enabled) {
            setMessage('Ky kurs është i mbyllur. Duhet të përfundosh kursin e mëparshme me 80% saktësi. 🔒')
            return
        }

        setSelectedCourse(course)
        setSelectedLevel(null)
        setExercises([])
        setCurrentExerciseIndex(0)
        
		try {
			// Prefer levels already loaded with the class courses payload.
			const levelsData = course.levels?.length
				? course.levels
				: await getCourseLevels(course.id)
			setCourseLevels(levelsData)
			
			// If there are levels, automatically select the first one and fetch its exercises
			if (levelsData && levelsData.length > 0) {
				const firstLevel = levelsData[0]
				setSelectedLevel(firstLevel)
				
				// Fetch exercises for the first level
				const exercisesData = await getLevelExercises(firstLevel.id)
				setExercises(exercisesData)
				setCurrentExerciseIndex(0)
			}
		} catch (error) {
			console.error('Error fetching course levels:', error)
			setCourseLevels([])
		}
    }

    const handleLevelClick = async (level: LevelOut | null) => {
        if (level === null) {
            // Go back to levels view
            setSelectedLevel(null)
            setExercises([])
            setCurrentExerciseIndex(0)
            return
        }

        setSelectedLevel(level)
        try {
            const exercisesData = await getLevelExercises(level.id)
            setExercises(exercisesData)
            setCurrentExerciseIndex(0)
        } catch (error) {
            console.error('Error fetching exercises:', error)
        }
    }

    // Preload audio for current exercise to reduce latency
    useEffect(() => {
        if (exercises.length > 0 && currentExerciseIndex < exercises.length) {
            const currentExercise = exercises[currentExerciseIndex]
            // Preload audio for listen_write exercises (dictation)
            if (currentExercise && currentExercise.category === 'listen_write') {
                // Preload audio in background
                const audioUrl = `/api/audio-exercises/${currentExercise.id}?slow=true&voice=anila`
                const preloadAudio = new Audio(audioUrl)
                preloadAudio.preload = 'auto'
                preloadAudio.load()
                console.log(`[Audio] Preloading audio for exercise ${currentExercise.id}`)
                
                // Cleanup
                return () => {
                    preloadAudio.pause()
                    preloadAudio.src = ''
                }
            }
        }
    }, [exercises, currentExerciseIndex])

    useEffect(() => {
        if (!userId || !selectedLevel || exercises.length === 0) {
            setChildLearningSupport(null)
            return
        }

        let cancelled = false
        setChildLearningLoading(true)
        getAdaptiveNextItem(userId)
            .then((result) => {
                if (!cancelled) setChildLearningSupport(result)
            })
            .catch((error) => {
                console.error('Child adaptive support error:', error)
                if (!cancelled) setChildLearningSupport(null)
            })
            .finally(() => {
                if (!cancelled) setChildLearningLoading(false)
            })

        return () => {
            cancelled = true
        }
    }, [userId, selectedLevel?.id, exercises.length])

    useEffect(() => {
        setChildFeedback(null)
        setChildPracticeAnswer('')
        setChildPracticeMessage(null)
    }, [currentExerciseIndex, selectedLevel?.id])

    const handleSubmitAnswer = async () => {
        if (!selectedLevel || !exercises[currentExerciseIndex] || isSubmittingAnswer) return

        const answer = answers[exercises[currentExerciseIndex].id] || ''
        if (!answer.trim()) {
            setMessage('Ju lutem shkruani një përgjigje! 📝')
            return
        }

        // Ruaj vlerat aktuale para async operacionit
        const currentIndex = currentExerciseIndex
        const currentExercises = exercises
        const currentSelectedClass = selectedClass

        try {
            setIsSubmittingAnswer(true)
            setMessage('Duke kontrolluar... ⏳')
            // Trim the answer to remove any leading/trailing whitespace
            const trimmedAnswer = answer.trim()
            console.log('[DEBUG] Submitting answer:', {
                exerciseId: exercises[currentIndex].id,
                userId: userId,
                response: trimmedAnswer
            })
            
            const durationSeconds = Math.max(
                0,
                Math.min(3600, Math.round((Date.now() - exerciseStartedAtRef.current) / 1000))
            )
            const result = await submitAnswer(exercises[currentIndex].id, {
                user_id: userId!,
                response: trimmedAnswer,
                duration_seconds: durationSeconds,
            })
            
            console.log('[DEBUG] Submit result:', result)
            
            // Advanced gamification feedback
            if (result.is_correct) {
                setChildFeedback(null)
                const pointsEarned = result.score_delta
                const newTotalPoints = userStats.totalPoints + pointsEarned
                const newLevel = Math.floor(newTotalPoints / 100) + 1
                const newExperience = newTotalPoints % 100
                
                console.log('[DEBUG] Correct answer! Points earned:', pointsEarned)
                console.log('[DEBUG] Course completed:', result.course_completed)
                console.log('[DEBUG] Current exercises length:', currentExercises.length)
                console.log('[DEBUG] Current index:', currentIndex)
                
                setUserStats(prev => ({
                    ...prev,
                    totalPoints: newTotalPoints,
                    level: newLevel,
                    experience: newExperience
                }))
                
                // Update user stats from server to ensure accuracy
                fetchUserStats()
                
                setMessage(`Përgjigja e saktë! 🎉 +${pointsEarned} pikë`)
                
                console.log('[DEBUG] Before setTimeout - exercises length:', exercises.length)
                console.log('[DEBUG] Before setTimeout - currentExerciseIndex:', currentExerciseIndex)
                console.log('[DEBUG] Before setTimeout - selectedLevel:', selectedLevel?.id)
                
                // Move to next exercise after a short delay
                setTimeout(() => {
                    console.log('[DEBUG] Timeout executed')
                    console.log('[DEBUG] currentIndex:', currentIndex)
                    console.log('[DEBUG] currentExercises.length:', currentExercises.length)
                    console.log('[DEBUG] result.course_completed:', result.course_completed)
                    console.log('[DEBUG] result.level_completed:', result.level_completed)
                    
                    // Përdor vlerat e ruajtura, jo state variables që mund të kenë ndryshuar
                    if (result.course_completed) {
                        console.log('[DEBUG] Course completed - going back to course selection')
                        // Course completed with >=80% accuracy → go back to course selection section
                        setMessage('🎉 Bravo! Ky nivel mbaroi. Zgjidh nivelin tjetër! 🚀')
                        setSelectedLevel(null)
                        setSelectedCourse(null)
                        setExercises([])
                        setCurrentExerciseIndex(0)
                        // Go back to course selection section (div class course section)
                        if (currentSelectedClass?.id && userId) {
                            getClassCourses(currentSelectedClass.id, userId).then(setClassCourses).catch(() => {})
                        }
                        // Refresh classes after course is completed
                        if (userId) {
                            fetchClasses()
                        }
                        return
                    }

                    // Kontrollo nëse ka më shumë ushtrime duke përdorur vlerat e ruajtura
                    if (currentIndex < currentExercises.length - 1) {
                        console.log('[DEBUG] Moving to next exercise:', currentIndex, '->', currentIndex + 1)
                        const nextIndex = currentIndex + 1
                        setCurrentExerciseIndex(nextIndex)
                        // Clear the answer field for the next exercise
                        setAnswers(prev => ({ ...prev, [currentExercises[nextIndex].id]: '' }))
                        setMessage('Ushtrim i ri! Vazhdoni mësimin! 📚')
                    } else {
                        console.log('[DEBUG] All exercises completed in this level')
                        // Finished all exercises in current level - go back to course preview grid
                        setMessage('Urime! I mbarove të gjitha! Kthehu te nivelet. 🏆')
                        setSelectedLevel(null)
                        setSelectedCourse(null)
                        setExercises([])
                        setCurrentExerciseIndex(0)
                        // Refresh classes after level is completed
                        if (userId) {
                            fetchClasses()
                        }
                    }
                }, 900)
            } else {
                console.log('[DEBUG] Incorrect answer')
                setMessage(`Përgjigja e pasaktë. Provo përsëri! 💪`)
                const correctAnswer = result.correct_answer || inferExerciseAnswer(currentExercises[currentIndex])
                if (correctAnswer) {
                    // Non-blocking: feedback card can load after the instant incorrect message
                    void generatePedagogicalFeedback({
                        student_answer: trimmedAnswer,
                        correct_answer: correctAnswer,
                        grade: selectedClass?.order_index || 3,
                    })
                        .then(setChildFeedback)
                        .catch((feedbackError) => {
                            console.error('Child feedback error:', feedbackError)
                            setChildFeedback(null)
                        })
                } else {
                    setChildFeedback({
                        child_message: {
                            title: 'Ndihmë',
                            what_you_wrote: `Ti shkrove: ${trimmedAnswer}`,
                            correct_form: 'Kontrollo edhe një herë kërkesën e ushtrimit.',
                            rule: currentExercises[currentIndex].rule || 'Lexoje pyetjen ngadalë dhe krahasoje përgjigjen me fjalën që kërkohet.',
                            why: 'Gabimet janë pjesë e mësimit. Provo përsëri me kujdes.',
                            example: 'Shembull: kontrollo çdo shkronjë dhe çdo shenjë si ë/ç.',
                            try_next: 'Provo përsëri këtë ushtrim duke kontrolluar çdo shkronjë.',
                            full_text: 'Lexoje pyetjen ngadalë dhe provo përsëri.',
                        },
                        simple_rule: currentExercises[currentIndex].rule || 'Lexoje pyetjen ngadalë dhe krahasoje përgjigjen me fjalën që kërkohet.',
                        why: 'Gabimet janë pjesë e mësimit. Provo përsëri me kujdes.',
                        next_practice: {
                            prompt: 'Provo përsëri këtë ushtrim duke kontrolluar çdo shkronjë.',
                            difficulty: 'easy',
                        },
                    })
                }
            }
        } catch (error) {
            console.error('[ERROR] Error submitting answer:', error)
            setMessage('Gabim në dërgimin e përgjigjes. Provo përsëri! ❌')
        } finally {
            setIsSubmittingAnswer(false)
        }
    }

    const handleChildPracticeCheck = () => {
        const expected = childFeedback?.next_practice?.answer || childFeedback?.correct_form
        if (!expected) {
            setChildPracticeMessage('Provo ta shkruash edhe një herë me kujdes.')
            return
        }
        if (normalizeText(childPracticeAnswer) === normalizeText(expected)) {
            setChildPracticeMessage('Saktë! Shumë mirë, tani provo përsëri ushtrimin kryesor. ✅')
        } else {
            setChildPracticeMessage('Afër! Krahasoje me formën e saktë dhe provo edhe një herë. 💪')
        }
    }

    const handleGenerateAIPractice = async () => {
        if (!selectedLevel || !selectedClass || !userId) {
            setAiError('Zgjidhni një nivel dhe identifikohuni për të marrë ushtrime AI.')
            return
        }

        setAiLoading(true)
        setAiError(null)
        setAiMessage(null)

        try {
            const result = await fetchAIPersonalizedPractice({
                user_id: userId,
                class_id: selectedClass.id,
                level_id: selectedLevel.id
            })

            setAiExercises(result.exercises)
            setAiMessage(result.message)
            setAiResponses({})
            setAiFeedback({})
        } catch (error) {
            console.error('Error generating AI practice:', error)
            setAiError('Nuk arritëm të gjenerojmë ushtrime AI tani. Provo përsëri pak më vonë.')
        } finally {
            setAiLoading(false)
        }
    }

    const handleAIResponseChange = (exerciseId: string, value: string) => {
        setAiResponses(prev => ({ ...prev, [exerciseId]: value }))
        setAiFeedback(prev => ({ ...prev, [exerciseId]: '' }))
    }

    const handleAIExerciseCheck = (exercise: AIPracticeExercise) => {
        const answer = aiResponses[exercise.id] || ''
        if (!answer.trim()) {
            setAiFeedback(prev => ({ ...prev, [exercise.id]: 'Shkruaj një përgjigje për ta kontrolluar.' }))
            return
        }

        const isCorrect = normalizeText(answer) === normalizeText(exercise.answer)
        setAiFeedback(prev => ({
            ...prev,
            [exercise.id]: isCorrect
                ? '🎉 Saktë! Vazhdoni me ushtrimin tjetër.'
                : '❌ Nuk është saktë. Kontrollo drejtshkrimin dhe provo një herë tjetër.'
        }))
    }

    const handleSelectOCRFile = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0]
        if (file) {
            setOcrFile(file)
            setOcrError(null)
        }
    }

    const handleOCRSubmit = async () => {
        if (!ocrFile) {
            setOcrError('Ngarko një imazh me diktim për ta analizuar.')
            return
        }

        setOcrLoading(true)
        setOcrError(null)
        setOcrResult(null)

        try {
            const formData = new FormData()
            formData.append('image', ocrFile)
            if (ocrExpected.trim()) {
                formData.append('expected_text', ocrExpected.trim())
            }

            const result = await analyzeOCR(formData)
            setOcrResult(result)
        } catch (error) {
            console.error('Error analyzing OCR:', error)
            setOcrError('Nuk mund të analizojmë imazhin tani. Kontrollo formatin dhe provo përsëri.')
        } finally {
            setOcrLoading(false)
        }
    }

    const handleLogout = () => {
        setUserId(null)
        setIsAdmin(false)
        setShowWelcome(true)
        setShowAuth(false)
        setSelectedClass(null)
        setSelectedCourse(null)
        setSelectedLevel(null)
        setExercises([])
        setCurrentExerciseIndex(0)
        setAnswers({})
        setProgress([])
        setUserStats({
            totalPoints: 0,
            totalStars: 0,
            streakDays: 0,
            level: 1,
            experience: 0,
            nextLevelExp: 100
        })
        setAiRecommendations(null)
        setAdaptiveDifficulty(null)
        setLearningPath(null)
        setProgressInsights(null)
        setShowAIInsights(false)
        setMessage('Ju keni dalë nga llogaria. Mirëupafshim! 👋')
        
        // Clear localStorage
        localStorage.removeItem('user_id')
        localStorage.removeItem('is_admin')
        localStorage.removeItem('username')
        localStorage.removeItem('full_name')
    }

    const fetchUserProfileData = async () => {
        if (!userId) return
        try {
            setProfileLoading(true)
            setProfileError(null)
            const profile = await getUserProfile(parseInt(userId))
            setUserProfile(profile)
            setProfileFormData({
                first_name: profile.first_name || '',
                last_name: profile.last_name || '',
                email: profile.email || '',
                age: profile.age?.toString() || '',
                date_of_birth: profile.date_of_birth 
                    ? new Date(profile.date_of_birth).toISOString().split('T')[0]
                    : '',
                address: profile.address || '',
                phone_number: profile.phone_number || ''
            })
        } catch (error: any) {
            console.error('Error fetching user profile:', error)
            setProfileError('Nuk arritëm të ngarkojmë profilin. Provo përsëri.')
        } finally {
            setProfileLoading(false)
        }
    }

    const handleSaveProfile = async () => {
        if (!userId) return
        try {
            setProfileLoading(true)
            setProfileError(null)
            
            const updateData: any = {}
            if (profileFormData.first_name) updateData.first_name = profileFormData.first_name.trim()
            if (profileFormData.last_name) updateData.last_name = profileFormData.last_name.trim()
            if (profileFormData.email) updateData.email = profileFormData.email
            if (profileFormData.age) {
                const ageNum = parseInt(profileFormData.age)
                if (ageNum >= 5 && ageNum <= 18) {
                    updateData.age = ageNum
                } else {
                    setProfileError('Mosha duhet të jetë midis 5 dhe 18 vjeç.')
                    setProfileLoading(false)
                    return
                }
            }
            if (profileFormData.date_of_birth) {
                updateData.date_of_birth = new Date(profileFormData.date_of_birth).toISOString()
            }
            if (profileFormData.address) updateData.address = profileFormData.address
            if (profileFormData.phone_number) updateData.phone_number = profileFormData.phone_number

            const updatedProfile = await updateUserProfile(parseInt(userId), updateData)
            setUserProfile(updatedProfile)
            setIsEditingProfile(false)
            setMessage('Profili u përditësua me sukses! ✅')
        } catch (error: any) {
            console.error('Error updating profile:', error)
            setProfileError(error.response?.data?.detail || 'Nuk arritëm të përditësojmë profilin. Provo përsëri.')
        } finally {
            setProfileLoading(false)
        }
    }

    const handleShowProfile = () => {
        setShowProfile(true)
        if (userId) {
            fetchUserProfileData()
        }
    }





    // getClassProgress removed - now using progress_percent from API directly

    const getLevelProgress = (levelId: number) => {
        const levelProgress = progress.filter(p => p.level_id === levelId)
        if (levelProgress.length === 0) return 0
        
        // Calculate progress based on completion
        const completedCount = levelProgress.filter(p => p.completed).length
        const totalCount = levelProgress.length
        
        return totalCount > 0 ? (completedCount / totalCount) * 100 : 0
    }



    const playAudio = async (exerciseId: number) => {
        try {
            // Generate audio URL for the exercise with cache-busting for debugging
            const audioUrl = `/api/audio-exercises/${exerciseId}?slow=true&voice=anila`
            
            console.log(`[Audio] Starting playback for exercise ${exerciseId}`)
            setMessage('🎵 Duke ngarkuar audion...')
            
            const audio = new Audio()
            
            // Track loading state
            let audioLoaded = false
            
            // Set up event listeners
            audio.onloadstart = () => {
                console.log(`[Audio] Load started for exercise ${exerciseId}`)
                setMessage('🔊 Duke luajtur audion...')
            }
            
            audio.onloadedmetadata = () => {
                console.log(`[Audio] Metadata loaded, duration: ${audio.duration}s`)
                if (audio.duration === 0 || isNaN(audio.duration)) {
                    console.error(`[Audio] Invalid duration for exercise ${exerciseId}`)
                    setMessage('⚠️ Audio është bosh. Provoni një ushtrim tjetër ose kontaktoni mbështetjen.')
                }
            }
            
            audio.oncanplay = () => {
                console.log(`[Audio] Can play exercise ${exerciseId}`)
                audioLoaded = true
            }
            
            audio.onplaying = () => {
                console.log(`[Audio] Playing exercise ${exerciseId}`)
                setMessage('🔊 Duke luajtur...')
            }
            
            audio.onended = () => {
                console.log(`[Audio] Ended exercise ${exerciseId}`)
                setMessage('✅ Audio u përfundua. Tani shkruaj përgjigjen! ✍️')
            }
            
            audio.onerror = (event) => {
                console.error(`[Audio] Error for exercise ${exerciseId}:`, event)
                console.error(`[Audio] Error details:`, audio.error)
                
                if (audio.error) {
                    const errorCode = audio.error.code
                    const errorMessages: Record<number, string> = {
                        1: 'Ngarkimi u ndërpre (MEDIA_ERR_ABORTED)',
                        2: 'Gabim rrjeti (MEDIA_ERR_NETWORK)',
                        3: 'Gabim dekodimi (MEDIA_ERR_DECODE)',
                        4: 'Format audio i pambështetur (MEDIA_ERR_SRC_NOT_SUPPORTED)'
                    }
                    const errorMsg = errorMessages[errorCode] || 'Gabim i panjohur'
                    setMessage(`❌ Gabim audio për ushtrimin ${exerciseId}: ${errorMsg}`)
                } else {
                    setMessage(`❌ Gabim në luajtjen e audios për ushtrimin ${exerciseId}`)
                }
            }
            
            // Set the source and load
            audio.src = audioUrl
            audio.load()
            
            // Wait for audio to be ready (with timeout)
            const loadTimeout = setTimeout(() => {
                if (!audioLoaded) {
                    console.warn(`[Audio] Load timeout for exercise ${exerciseId}`)
                    setMessage('⏳ Audio po ngarkohet ngadalë. Ju lutem prisni...')
                }
            }, 3000)
            
            // Try to play
            const playPromise = audio.play()
            if (playPromise !== undefined) {
                await playPromise
                clearTimeout(loadTimeout)
            }
            
            console.log(`[Audio] Playback started successfully for exercise ${exerciseId}`)
            
        } catch (error) {
            console.error(`[Audio] Catch error for exercise ${exerciseId}:`, error)
            
            if (error instanceof Error) {
                if (error.name === 'NotAllowedError') {
                    setMessage('🔒 Duhet të lejoni luajtjen e audios në shfletues. Klikoni sërish butonin!')
                } else if (error.name === 'NotSupportedError') {
                    setMessage('❌ Shfletuesi juaj nuk mbështet formatin audio. Provoni Chrome/Firefox/Safari!')
                } else if (error.name === 'AbortError') {
                    setMessage('⚠️ Audio u ndërpre. Klikoni përsëri për ta dëgjuar!')
                } else {
                    setMessage(`❌ Gabim audio: ${error.message}. Kontrolloni lidhjen me internet!`)
                }
            } else {
                setMessage('❌ Gabim në luajtjen e audios. Provo përsëri!')
            }
        }
    }

    const startRecording = async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setMessage('Regjistrimi i zërit nuk mbështetet në këtë shfletues! 🎤')
            return
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                } 
            })
            
            setIsRecording(true)
            setMessage('Duke regjistruar... Fol qartë! 🎤')
            
            // Try different audio formats based on browser support
            let mimeType = 'audio/webm;codecs=opus'
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm'
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4'
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = '' // Use default
                    }
                }
            }
            
            const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {})
            const audioChunks: Blob[] = []
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data)
                }
            }
            
            mediaRecorder.onstop = async () => {
                setIsRecording(false)
                stream.getTracks().forEach(track => track.stop())
                
                try {
                    // Create audio blob with detected mime type
                    const audioBlob = new Blob(audioChunks, { type: mimeType || 'audio/webm' })
                    
                    // Send to backend for Albanian pronunciation check
                    const formData = new FormData()
                    const extension = mimeType.includes('webm') ? 'webm' : mimeType.includes('mp4') ? 'mp4' : 'webm'
                    formData.append('audio_file', audioBlob, `recording.${extension}`)
                    formData.append('exercise_id', exercises[currentExerciseIndex].id.toString())
                    
                    setMessage('Duke kontrolluar shqiptimin... 🔍')
                    
                    const response = await fetch('/api/albanian-pronunciation-check', {
                        method: 'POST',
                        body: formData
                    })
                    
                    if (response.ok) {
                        const result = await response.json()
                        
                        // Show pronunciation feedback
                        const feedback = `${result.feedback}\n\nShqiptimi yt: "${result.spoken_text}"\nSaktësia: ${Math.round(result.similarity_score * 100)}%`
                        setMessage(feedback)
                        
                        // Auto-fill the answer if pronunciation is good
                        if (result.is_correct && result.spoken_text) {
                            setAnswers(prev => ({ 
                                ...prev, 
                                [exercises[currentExerciseIndex].id]: result.spoken_text 
                            }))
                        }
                    } else {
                        throw new Error('Pronunciation check failed')
                    }
                } catch (error) {
                    console.error('Error processing recording:', error)
                    setMessage('Gabim në përpunimin e regjistrimit. Provo përsëri! 🎤')
                }
            }
            
            mediaRecorder.start()
            
            // Stop recording after 5 seconds
            setTimeout(() => {
                if (mediaRecorder.state === 'recording') {
                    mediaRecorder.stop()
                }
            }, 5000)
            
        } catch (error) {
            console.error('Error accessing microphone:', error)
            setMessage('Gabim në aksesin e mikrofonit. Kontrolloni lejet e mikrofonit! 🎤')
            setIsRecording(false)
        }
    }

    const showPronunciationHint = () => {
        setMessage('💡 Këshillë: Dëgjoni me kujdes zërin dhe përpiquni ta imitoni atë! 🎵')
    }

    // If not logged in, show welcome then authentication
    const shouldShowAuth = !userId || userId === 'null' || userId === 'undefined' || (typeof userId === 'string' && userId.trim() === '')
    
    // Entry page before login/register (frontend-only gate)
    if (shouldShowAuth && showWelcome) {
        return (
            <WelcomeLanding
                onRegister={() => {
                    setShowAuth(true)
                    setShowWelcome(false)
                }}
                onLogin={() => {
                    setShowAuth(false)
                    setShowWelcome(false)
                }}
            />
        )
    }

    // Always show auth form if no valid userId
    if (shouldShowAuth) {
        const goToWelcome = () => {
            setShowWelcome(true)
            setMessage('')
        }

        return (
            <div className="app auth-app">
                <div className="auth-container">
                    <div className="auth-card">
                        <button
                            type="button"
                            className="auth-back-link"
                            onClick={goToWelcome}
                        >
                            ← Kthehu
                        </button>
                        <div className="auth-header">
                            <div className="auth-logo">
                                <BrandLogo size={48} className="brand-logo-lg" />
                            </div>
                            <h2>Mirë se erdhe në ALBLingo</h2>
                            <p>Mëso drejtshkrimin në mënyrë argëtuese</p>
                            <div className="auth-lang-badge" aria-label="Gjuha e faqes">
                                Gjuha e faqes: Shqip
                            </div>
                        </div>

                        <div className="auth-tabs">
                            <button
                                className={`auth-tab ${!showAuth ? 'active' : ''}`}
                                onClick={() => setShowAuth(false)}
                            >
                                Hyr
                            </button>
                            <button
                                className={`auth-tab ${showAuth ? 'active' : ''}`}
                                onClick={() => setShowAuth(true)}
                            >
                                Regjistrohu
                            </button>
                        </div>

                        {!showAuth ? (
                            // Login Form
                            <div className="auth-form">
                                <input
                                    className="auth-input"
                                    placeholder="Emri i përdoruesit"
                                    autoComplete="username"
                                    value={auth.username}
                                    onChange={(e) => setAuth({ ...auth, username: e.target.value })}
                                />
                                <input
                                    className="auth-input"
                                    placeholder="Fjalëkalimi"
                                    type="password"
                                    autoComplete="current-password"
                                    value={auth.password}
                                    onChange={(e) => setAuth({ ...auth, password: e.target.value })}
                                />

                                <button
                                    className="auth-submit"
                                    onClick={async () => {
                                        const username = auth.username?.trim()
                                        const password = auth.password
                                        if (!username || !password) {
                                            setMessage('Shkruaj emrin e përdoruesit dhe fjalëkalimin për të hyrë. 🙂')
                                            return
                                        }
                                        try {
                                            setMessage('Po hyjmë... 🔄')
                                            const res = await login(username, password)
                                            setUserId(String(res.user_id))
                                            setIsAdmin(res.is_admin || false)
                                            setMessage('Mirësevini! 👋')
                                            persistSession(String(res.user_id), res.username, Boolean(res.is_admin))
                                        } catch (e: any) {
                                            const status = e?.response?.status
                                            const detail = e?.response?.data?.detail || e?.message
                                            if (status === 401) {
                                                setMessage('Hmm… emri i përdoruesit ose fjalëkalimi nuk është i saktë. Kontrollo edhe një herë! 🙂')
                                            } else if (e?.code === 'ECONNREFUSED' || e?.code === 'ECONNABORTED' || e?.message?.includes('timeout') || e?.message?.includes('Network') || !e?.response) {
                                                setMessage('Po pret pak… provo përsëri pas një çasti. ⏳')
                                            } else {
                                                setMessage(detail || 'Diçka nuk shkoi mirë. Provo përsëri! 🙂')
                                            }
                                        }
                                    }}
                                >
                                    Hyr
                                </button>
                                <p className="auth-switch-hint">
                                    Nuk ke llogari?{' '}
                                    <button type="button" className="auth-switch-link" onClick={() => setShowAuth(true)}>
                                        Regjistrohu
                                    </button>
                                </p>
                            </div>
                        ) : (
                            <RegisterForm
                                onSuccess={(username) => {
                                    setMessage('Bravo! Llogaria u krijua. Tani hyr me emrin e përdoruesit. 🌟')
                                    setShowAuth(false)
                                    setAuth({ username, password: '' })
                                }}
                                onSwitchToLogin={() => setShowAuth(false)}
                                onMessage={setMessage}
                            />
                        )}
                        {message && <AppToast message={message} />}
                    </div>
                </div>
            </div>
        )
    }

    // Show admin dashboard if user is admin
    if (isAdmin && userId && userId !== 'null' && userId !== 'undefined') {
        try {
            const adminUserId = parseInt(userId)
            if (!isNaN(adminUserId)) {
                return (
                    <LazyErrorBoundary label="panelit të administratorit">
                        <Suspense fallback={
                            <div className="route-loading page-loading" role="status" aria-live="polite" aria-busy="true">
                                <div className="page-loading-progress" aria-hidden="true">
                                    <span className="page-loading-progress-bar"></span>
                                </div>
                                <div className="page-loading-inner">
                                    <div className="page-loading-mark" aria-hidden="true"><BrandLogo size={52} decorative /></div>
                                    <p className="page-loading-brand">AlbLingo</p>
                                    <p className="page-loading-title">Duke ngarkuar</p>
                                    <p className="page-loading-subtitle">Paneli i administratorit</p>
                                </div>
                            </div>
                        }>
                            <AdminDashboard
                                userId={adminUserId}
                                onLogout={() => {
                                    setUserId(null)
                                    setIsAdmin(false)
                                    setShowWelcome(true)
                                    setShowAuth(false)
                                    localStorage.removeItem('user_id')
                                    localStorage.removeItem('is_admin')
                                    localStorage.removeItem('username')
                                }}
                            />
                        </Suspense>
                    </LazyErrorBoundary>
                )
            }
        } catch (e) {
            console.error('Error parsing admin user ID:', e)
        }
    }

    // Main application after login
    return (
        <div className="app">
            {/* HEADER SECTION */}
            <AppHeader
                userStats={userStats}
                selectedClass={selectedClass}
                selectedCourse={selectedCourse}
                curriculumLabel={
                    selectedClass && selectedCourse
                        ? formatCurriculumLabel(selectedClass, selectedCourse, selectedLevel, classes)
                        : selectedClass
                            ? `Klasa ${getClassNumber(selectedClass, classes)}`
                            : null
                }
                onBackToClasses={() => handleClassClick(null)}
                onBackToCourses={() => handleCourseClick(null)}
                onLogout={handleLogout}
                onShowProfile={handleShowProfile}
                profileOpen={showProfile}
                leaderboardOpen={showLeaderboard}
                onShowLeaderboard={async () => {
                    setShowLeaderboard(true)
                    try {
                        // Fetch all users for full leaderboard (limit=0 returns all)
                        const data = await getLeaderboard(0)
                        setLeaderboardData(data)
                        if (userId) {
                            const rank = await getUserRank(parseInt(userId))
                            setUserRank(rank)
                        }
                    } catch (error) {
                        console.error('Error fetching leaderboard:', error)
                    }
                }}
                onShowLevelInfo={async () => {
                    setShowLevelInfo(true)
                    if (userId && classes.length > 0) {
                        try {
                            const progressPromises = classes.map(async (cls) => {
                                try {
                                    const courses = await getClassCourses(cls.id, userId)
                                    const completedCourses = courses.filter((c: CourseOut) => c.progress?.is_completed).length
                                    const totalCourses = courses.length
                                    const progressPercent = totalCourses > 0 ? (completedCourses / totalCourses) * 100 : 0
                                    return {
                                        classId: cls.id,
                                        className: cls.name,
                                        completedCourses,
                                        totalCourses,
                                        progressPercent,
                                        unlocked: cls.unlocked,
                                        courses: courses
                                    }
                                } catch (error) {
                                    return {
                                        classId: cls.id,
                                        className: cls.name,
                                        completedCourses: 0,
                                        totalCourses: 0,
                                        progressPercent: 0,
                                        unlocked: cls.unlocked,
                                        courses: []
                                    }
                                }
                            })
                            const progressData = await Promise.all(progressPromises)
                            setClassProgressData(progressData)
                        } catch (error) {
                            console.error('Error fetching class progress:', error)
                        }
                    }
                }}
            />

            {/* MAIN CONTENT SECTION */}
            <main className="main">
                <MainContent
                    isLoading={isLoading}
                    classes={classes}
                    selectedClass={selectedClass}
                    selectedCourse={selectedCourse}
                    selectedLevel={selectedLevel}
                    courseLevels={courseLevels}
                    classCourses={classCourses}
                    userId={userId || ''}
                    aiRecommendations={aiRecommendations}
                    adaptiveDifficulty={adaptiveDifficulty}
                    childLearningSupport={childLearningSupport}
                    childLearningLoading={childLearningLoading}
                    childFeedback={childFeedback}
                    childPracticeAnswer={childPracticeAnswer}
                    setChildPracticeAnswer={setChildPracticeAnswer}
                    childPracticeMessage={childPracticeMessage}
                    handleChildPracticeCheck={handleChildPracticeCheck}
                    learningPath={learningPath}
                    progressInsights={progressInsights}
                    aiCoach={aiCoach}
                    aiCoachLoading={aiCoachLoading}
                    aiCoachError={aiCoachError}
                    aiCoachLevel={aiCoachLevel}
                    aiCoachLevelLoading={aiCoachLevelLoading}
                    aiCoachLevelError={aiCoachLevelError}
                    showAIInsights={showAIInsights}
                    userAchievements={userAchievements}
                    userStreak={userStreak}
                    dailyChallenge={dailyChallenge}
                    srsStats={srsStats}
                    showGamification={showGamification}
                    setShowGamification={setShowGamification}
                    onClassClick={handleClassClick}
                    onCourseClick={handleCourseClick}
                    onLevelClick={handleLevelClick}
                    onToggleAIInsights={() => setShowAIInsights(!showAIInsights)}
                    getLevelProgress={getLevelProgress}
                    publicStats={publicStats}
                    exercises={exercises}
                    currentExerciseIndex={currentExerciseIndex}
                    answers={answers}
                    setAnswers={setAnswers}
                    handleSubmitAnswer={handleSubmitAnswer}
                    isSubmittingAnswer={isSubmittingAnswer}
                    playAudio={playAudio}
                    startRecording={startRecording}
                    isRecording={isRecording}
                    showPronunciationHint={showPronunciationHint}
                    setCurrentExerciseIndex={setCurrentExerciseIndex}
                    setMessage={setMessage}
                    // AI Practice props
                    aiExercises={aiExercises}
                    aiResponses={aiResponses}
                    aiFeedback={aiFeedback}
                    aiLoading={aiLoading}
                    aiError={aiError}
                    aiMessage={aiMessage}
                    handleGenerateAIPractice={handleGenerateAIPractice}
                    handleAIResponseChange={handleAIResponseChange}
                    handleAIExerciseCheck={handleAIExerciseCheck}
                    // OCR props
                    ocrLoading={ocrLoading}
                    ocrError={ocrError}
                    ocrResult={ocrResult}
                    ocrExpected={ocrExpected}
                    setOcrExpected={setOcrExpected}
                    handleOCRSubmit={handleOCRSubmit}
                    handleSelectOCRFile={handleSelectOCRFile}
                />
            </main>

            {/* Advanced AI Chatbot (floating) */}
            <LazyErrorBoundary label="bashkëbiseduesit">
                <Suspense fallback={null}>
                    <ChatbotFloating
                        userId={userId || undefined}
                        context={selectedLevel ? {
                            current_level: selectedLevel.name,
                            current_exercise: exercises[currentExerciseIndex]?.prompt,
                        } : undefined}
                    />
                </Suspense>
            </LazyErrorBoundary>

                {showProfile && (
                    <div className="profile-overlay" onClick={() => { setShowProfile(false); setIsEditingProfile(false) }}>
                        <div
                            ref={profileModalRef}
                            className="profile-card enhanced-profile-card"
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="profile-modal-title"
                            tabIndex={-1}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="profile-header">
                                <div className="profile-title" id="profile-modal-title">👤 Profili im</div>
                                <button className="profile-close" aria-label="Mbyll profilin" onClick={() => { setShowProfile(false); setIsEditingProfile(false) }}>×</button>
                            </div>
                            
                            <div className="profile-content-enhanced">
                                {/* Profile Header with Avatar */}
                                <div className="profile-header-section">
                                    <div className="profile-avatar-container">
                                        <div className="profile-avatar-wrapper">
                                            {profileImage ? (
                                                <img 
                                                    src={profileImage} 
                                                    alt="Profile" 
                                                    className="profile-avatar-image"
                                                />
                                            ) : (
                                                <div className="profile-avatar-placeholder">
                                                    {(userProfile?.first_name || userProfile?.username || 'P').charAt(0).toUpperCase()}
                                                </div>
                                            )}
                                            <label className="profile-avatar-upload">
                                                <input
                                                    type="file"
                                                    accept="image/*"
                                                    style={{ display: 'none' }}
                                                    onChange={(e) => {
                                                        const file = e.target.files?.[0]
                                                        if (file) {
                                                            const reader = new FileReader()
                                                            reader.onloadend = () => {
                                                                const result = reader.result as string
                                                                setProfileImage(result)
                                                                if (userId) {
                                                                    localStorage.setItem(`profile_image_${userId}`, result)
                                                                }
                                                            }
                                                            reader.readAsDataURL(file)
                                                        }
                                                    }}
                                                />
                                                <span className="upload-icon">📷</span>
                                            </label>
                                        </div>
                                    </div>
                                    
                                    <div className="profile-info-header">
                                        <h2 className="profile-username">
                                            {[userProfile?.first_name, userProfile?.last_name].filter(Boolean).join(' ')
                                                || userProfile?.username
                                                || localStorage.getItem('username')
                                                || 'Përdorues'}
                                        </h2>
                                        <p className="profile-email">{userProfile?.email || 'Nuk është vendosur email'}</p>
                                        {userProfile?.username && (
                                            <p className="profile-username-sub">Username: {userProfile.username}</p>
                                        )}
                                    </div>
                                </div>

                                {/* Personal Information */}
                                <div className="profile-section-enhanced">
                                    <div className="profile-section-toolbar">
                                        <h3 className="profile-section-title">📋 Informacione Personale</h3>
                                        {!isEditingProfile ? (
                                            <button
                                                type="button"
                                                className="profile-edit-btn"
                                                onClick={() => setIsEditingProfile(true)}
                                            >
                                                ✏️ Edito
                                            </button>
                                        ) : (
                                            <div className="profile-edit-actions">
                                                <button
                                                    type="button"
                                                    className="profile-save-btn"
                                                    onClick={handleSaveProfile}
                                                    disabled={profileLoading}
                                                >
                                                    {profileLoading ? 'Duke ruajtur...' : '💾 Ruaj'}
                                                </button>
                                                <button
                                                    type="button"
                                                    className="profile-cancel-btn"
                                                    onClick={() => {
                                                        setIsEditingProfile(false)
                                                        setProfileError(null)
                                                        if (userProfile) {
                                                            setProfileFormData({
                                                                first_name: userProfile.first_name || '',
                                                                last_name: userProfile.last_name || '',
                                                                email: userProfile.email || '',
                                                                age: userProfile.age?.toString() || '',
                                                                date_of_birth: userProfile.date_of_birth
                                                                    ? new Date(userProfile.date_of_birth).toISOString().split('T')[0]
                                                                    : '',
                                                                address: userProfile.address || '',
                                                                phone_number: userProfile.phone_number || ''
                                                            })
                                                        }
                                                    }}
                                                >
                                                    ❌ Anulo
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                    {profileError && (
                                        <div className="profile-error-banner">
                                            {profileError}
                                        </div>
                                    )}
                                    <div className="profile-info-grid">
                                        <div className="profile-info-item">
                                            <span className="info-label">🧾 Emri:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="text"
                                                    value={profileFormData.first_name}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, first_name: e.target.value })}
                                                    className="profile-field-input"
                                                    placeholder="Emri"
                                                />
                                            ) : (
                                                <span className="info-value">{userProfile?.first_name || 'Nuk është vendosur'}</span>
                                            )}
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">🧾 Mbiemri:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="text"
                                                    value={profileFormData.last_name}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, last_name: e.target.value })}
                                                    className="profile-field-input"
                                                    placeholder="Mbiemri"
                                                />
                                            ) : (
                                                <span className="info-value">{userProfile?.last_name || 'Nuk është vendosur'}</span>
                                            )}
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">👤 Username (login):</span>
                                            <span className="info-value">{userProfile?.username || localStorage.getItem('username') || 'N/A'}</span>
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">📧 Email:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="email"
                                                    value={profileFormData.email}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, email: e.target.value })}
                                                    className="profile-field-input"
                                                    placeholder="Email"
                                                />
                                            ) : (
                                                <span className="info-value">{userProfile?.email || 'Nuk është vendosur'}</span>
                                            )}
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">🎂 Mosha:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="number"
                                                    min="5"
                                                    max="18"
                                                    value={profileFormData.age}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, age: e.target.value })}
                                                    className="profile-field-input"
                                                    placeholder="Mosha"
                                                />
                                            ) : (
                                                <span className="info-value">{userProfile?.age ? `${userProfile.age} vjeç` : 'Nuk është vendosur'}</span>
                                            )}
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">📅 Data e lindjes:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="date"
                                                    value={profileFormData.date_of_birth}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, date_of_birth: e.target.value })}
                                                    className="profile-field-input"
                                                />
                                            ) : (
                                                <span className="info-value">
                                                    {userProfile?.date_of_birth
                                                        ? new Date(userProfile.date_of_birth).toLocaleDateString('sq-AL')
                                                        : 'Nuk është vendosur'}
                                                </span>
                                            )}
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">📍 Adresa:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="text"
                                                    value={profileFormData.address}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, address: e.target.value })}
                                                    className="profile-field-input"
                                                    placeholder="Adresa"
                                                />
                                            ) : (
                                                <span className="info-value">{userProfile?.address || 'Nuk është vendosur'}</span>
                                            )}
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">📞 Telefoni:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="tel"
                                                    value={profileFormData.phone_number}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, phone_number: e.target.value })}
                                                    className="profile-field-input"
                                                    placeholder="+355..."
                                                />
                                            ) : (
                                                <span className="info-value">{userProfile?.phone_number || 'Nuk është vendosur'}</span>
                                            )}
                                        </div>
                                        {userProfile?.created_at && (
                                            <div className="profile-info-item">
                                                <span className="info-label">📅 Anëtar që nga:</span>
                                                <span className="info-value">{new Date(userProfile.created_at).toLocaleDateString('sq-AL')}</span>
                                            </div>
                                        )}
                                        {userProfile?.last_login && (
                                            <div className="profile-info-item">
                                                <span className="info-label">🕐 Hyrja e fundit:</span>
                                                <span className="info-value">{new Date(userProfile.last_login).toLocaleDateString('sq-AL')}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Statistics */}
                                <div className="profile-section-enhanced">
                                    <h3 className="profile-section-title">📊 Statistikat</h3>
                                    <div className="profile-stats-enhanced">
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large" aria-hidden="true"><IconStar size={28} /></div>
                                            <div className="stat-content">
                                                <div className="stat-label">Niveli</div>
                                                <div className="stat-value-large">{userStats.level}</div>
                                            </div>
                                        </div>
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large" aria-hidden="true"><IconTrophy size={28} /></div>
                                            <div className="stat-content">
                                                <div className="stat-label">Pikë Totale</div>
                                                <div className="stat-value-large">{userStats.totalPoints.toLocaleString()}</div>
                                            </div>
                                        </div>
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large" aria-hidden="true"><IconFlame size={28} /></div>
                                            <div className="stat-content">
                                                <div className="stat-label">Varg Ditësh</div>
                                                <div className="stat-value-large">{userStats.streakDays}</div>
                                            </div>
                                        </div>
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large" aria-hidden="true"><IconSparkle size={28} /></div>
                                            <div className="stat-content">
                                                <div className="stat-label">Yje</div>
                                                <div className="stat-value-large">{userStats.totalStars}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* AI Insights */}
                                <div className="profile-section-enhanced">
                                    <h3 className="profile-section-title">🤖 AI i Personalizuar</h3>
                                    <div className="profile-ai-enhanced">
                                        {aiRecommendations && (
                                            <div className="ai-card-enhanced">
                                                <div className="ai-card-title">💡 Rekomandime</div>
                                                <div className="ai-card-text">{aiRecommendations.message}</div>
                                                <div className="ai-card-meta">Saktësia: {Math.round(aiRecommendations.accuracy * 100)}%</div>
                                            </div>
                                        )}
                                        {adaptiveDifficulty && (
                                            <div className="ai-card-enhanced">
                                                <div className="ai-card-title">⚡ Vështirësia</div>
                                                <div className="ai-card-text">{adaptiveDifficulty.message}</div>
                                                <div className="ai-card-meta">Multiplikatori: {adaptiveDifficulty.multiplier}x</div>
                                            </div>
                                        )}
                                        {learningPath && (
                                            <div className="ai-card-enhanced">
                                                <div className="ai-card-title">🛤️ Rruga e Mësimit</div>
                                                <div className="ai-card-text">{learningPath.message}</div>
                                                <div className="ai-card-meta">Tipi: {learningPath.path}</div>
                                            </div>
                                        )}
                                        {progressInsights && progressInsights.insights && (
                                            <div className="ai-card-enhanced">
                                                <div className="ai-card-title">📈 Njohuri</div>
                                                <ul className="ai-list-enhanced">
                                                    {progressInsights.insights.slice(0, 5).map((ins: string, i: number) => (
                                                        <li key={i}>💭 {ins}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Streak Information */}
                                {userStreak && (
                                    <div className="profile-section-enhanced">
                                        <h3 className="profile-section-title">🔥 Varg Ditësh</h3>
                                        <div className="profile-stats-enhanced">
                                            <div className="profile-stat-card profile-stat-card-muted">
                                                <div className="stat-icon-large" aria-hidden="true"><IconFlame size={28} /></div>
                                                <div className="stat-content">
                                                    <div className="stat-label">Vargu Aktual</div>
                                                    <div className="stat-value-large">{userStreak.current_streak}</div>
                                                    <div className="stat-sub-label">ditë</div>
                                                </div>
                                            </div>
                                            <div className="profile-stat-card profile-stat-card-muted">
                                                <div className="stat-icon-large" aria-hidden="true"><IconStar size={28} /></div>
                                                <div className="stat-content">
                                                    <div className="stat-label">Vargu Më i Gjatë</div>
                                                    <div className="stat-value-large">{userStreak.longest_streak}</div>
                                                    <div className="stat-sub-label">ditë</div>
                                                </div>
                                            </div>
                                            {userStreak.last_activity_date && (
                                                <div className="profile-stat-card profile-stat-card-muted">
                                                    <div className="stat-icon-large" aria-hidden="true"><IconCalendar size={28} /></div>
                                                    <div className="stat-content">
                                                        <div className="stat-label">Aktiviteti i Fundit</div>
                                                        <div className="stat-value-large stat-value-date">
                                                            {new Date(userStreak.last_activity_date).toLocaleDateString('sq-AL')}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        {userStreak.current_streak > 0 && (
                                            <div className="profile-streak-tip">
                                                <p>
                                                    🎉 Vazhdo të praktikosh çdo ditë për të mbajtur vargun tënd!
                                                    {userStreak.current_streak >= 7 && ' Ju tashmë keni një varg të fortë!'}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {showLeaderboard && (
                    <div className="profile-overlay" onClick={() => setShowLeaderboard(false)}>
                        <div
                            ref={leaderboardModalRef}
                            className="profile-card leaderboard-card"
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="leaderboard-modal-title"
                            tabIndex={-1}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="leaderboard-sheet-handle" aria-hidden="true"></div>
                            <div className="profile-header">
                                <div className="profile-title" id="leaderboard-modal-title">🏆 {LEADERBOARD_TITLE}</div>
                                <button className="profile-close" aria-label="Mbyll renditjen" onClick={() => setShowLeaderboard(false)}>×</button>
                            </div>
                            <div className="leaderboard-content">
                                {userRank && (
                                    <div className="user-rank-badge">
                                        <div className="rank-info">
                                            <span className="rank-label">Renditja juaj</span>
                                            <span className="rank-value">#{userRank.rank}</span>
                                        </div>
                                        <div className="rank-stats">
                                            <span className="rank-stat-pill">Nga {userRank.total_users} përdorues</span>
                                            <span className="rank-stat-pill">Top {userRank.percentile}%</span>
                                        </div>
                                    </div>
                                )}
                                <div className="leaderboard-table">
                                    <div className="leaderboard-header" aria-hidden="true">
                                        <div className="lb-col rank-col">#</div>
                                        <div className="lb-col user-col">Përdoruesi</div>
                                        <div className="lb-col points-col">Pikë</div>
                                        <div className="lb-col level-col">Niveli</div>
                                        <div className="lb-col accuracy-col">Saktësi</div>
                                        <div className="lb-col courses-col">Kurset</div>
                                    </div>
                                    <div className="leaderboard-body">
                                        {leaderboardData.map((entry) => {
                                            const isCurrentUser = userId && entry.user_id === parseInt(userId)
                                            const avatarLetter = (entry.username?.trim()?.charAt(0) || '?').toUpperCase()
                                            return (
                                                <div
                                                    key={entry.user_id}
                                                    className={`leaderboard-row ${isCurrentUser ? 'current-user' : ''} ${entry.rank <= 3 ? `lb-top-${entry.rank}` : ''}`}
                                                >
                                                    <div className="lb-col rank-col" data-label="Vend">
                                                        {entry.rank === 1 && '🥇'}
                                                        {entry.rank === 2 && '🥈'}
                                                        {entry.rank === 3 && '🥉'}
                                                        {entry.rank > 3 && `#${entry.rank}`}
                                                    </div>
                                                    <div className="lb-avatar" aria-hidden="true">{avatarLetter}</div>
                                                    <div className="lb-col user-col" data-label="Përdoruesi">
                                                        <strong>{entry.username}</strong>
                                                        {isCurrentUser && <span className="you-badge">Ti</span>}
                                                    </div>
                                                    <div className="lb-col points-col" data-label="Pikë">
                                                        <span className="lb-stat-value">{entry.total_points.toLocaleString()}</span>
                                                        <span className="lb-stat-unit">pikë</span>
                                                    </div>
                                                    <div className="lb-meta">
                                                        <div className="lb-col level-col" data-label="Niveli">
                                                            <span className="lb-stat-value">⭐ {entry.level}</span>
                                                        </div>
                                                        <div className="lb-col accuracy-col" data-label="Saktësi">
                                                            <span className="lb-stat-value">{entry.accuracy.toFixed(1)}%</span>
                                                        </div>
                                                        <div className="lb-col courses-col" data-label="Kurset">
                                                            <span className="lb-stat-value">{entry.completed_courses}</span>
                                                            <span className="lb-stat-unit">kurse</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {showLevelInfo && (
                    <div className="profile-overlay" onClick={() => setShowLevelInfo(false)}>
                        <div
                            ref={levelInfoModalRef}
                            className="profile-card level-info-card"
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="level-info-modal-title"
                            tabIndex={-1}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="profile-header">
                                <div className="profile-title" id="level-info-modal-title">⭐ Informacion i Nivelit</div>
                                <button className="profile-close" aria-label="Mbyll informacionin e nivelit" onClick={() => setShowLevelInfo(false)}>×</button>
                            </div>
                            <div className="level-info-content">
                                <div className="level-summary">
                                    <div className="level-badge-large">
                                        <div className="level-number">{userStats.level}</div>
                                        <div className="level-label">Niveli Aktual</div>
                                    </div>
                                    <div className="level-stats-summary">
                                        <div className="stat-summary-item">
                                            <span className="stat-icon-large" aria-hidden="true"><IconTrophy size={28} /></span>
                                            <div>
                                                <div className="stat-value-large">{userStats.totalPoints}</div>
                                                <div className="stat-label-small">Pikë totale</div>
                                            </div>
                                        </div>
                                        <div className="stat-summary-item">
                                            <span className="stat-icon-large" aria-hidden="true"><IconBook size={28} /></span>
                                            <div>
                                                <div className="stat-value-large">{userStats.experience}/{userStats.nextLevelExp}</div>
                                                <div className="stat-label-small">Për nivelin tjetër</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="level-progress-section">
                                    <h3>📊 Progresi në Klasa</h3>
                                    <div className="classes-progress-list">
                                        {classProgressData.map((classData) => {
                                            const isCurrentClass = selectedClass && selectedClass.id === classData.classId
                                            return (
                                                <div 
                                                    key={classData.classId} 
                                                    className={`class-progress-item ${isCurrentClass ? 'current-class' : ''} ${!classData.unlocked ? 'locked' : ''}`}
                                                >
                                                    <div className="class-progress-header">
                                                        <div className="class-name-progress">
                                                            <span className="class-icon">📖</span>
                                                            <strong>{classData.className}</strong>
                                                            {isCurrentClass && <span className="current-badge">Aktual</span>}
                                                            {!classData.unlocked && <span className="locked-badge">🔒</span>}
                                                        </div>
                                                        <div className="class-progress-percent">
                                                            {classData.unlocked ? `${Math.round(classData.progressPercent)}%` : '🔒'}
                                                        </div>
                                                    </div>
                                                    {classData.unlocked && (
                                                        <>
                                                            <div className="class-progress-bar-container">
                                                                <div 
                                                                    className="class-progress-bar-fill" 
                                                                    style={{ width: `${classData.progressPercent}%` }}
                                                                ></div>
                                                            </div>
                                                            <div className="class-progress-details">
                                                                <span>{classData.completedCourses}/{classData.totalCourses} nivele të përfunduara</span>
                                                                {classData.progressPercent >= 80 && (
                                                                    <span className="unlock-badge">✅ Klasa tjetër e hapur</span>
                                                                )}
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>

                                {selectedClass && (
                                    <div className="current-class-details">
                                        <h3>🎯 Klasa Aktuale: {selectedClass.name}</h3>
                                        {classCourses.length > 0 && (
                                            <div className="current-class-courses">
                                                <p className="courses-summary">
                                                    {classCourses.filter(c => c.progress?.is_completed).length} nga {classCourses.length} nivele të përfunduara
                                                </p>
                                                <div className="courses-grid-mini">
                                                    {classCourses.slice(0, 6).map((course) => (
                                                        <div 
                                                            key={course.id} 
                                                            className={`course-mini-card ${course.progress?.is_completed ? 'completed' : course.enabled ? 'active' : 'locked'}`}
                                                        >
                                                            <div className="course-mini-icon">
                                                                {course.progress?.is_completed ? '✅' : course.enabled ? '📝' : '🔒'}
                                                            </div>
                                                            <div className="course-mini-name">{course.name}</div>
                                                            {course.progress && (
                                                                <div className="course-mini-progress">
                                                                    {course.progress.completed_exercises}/{course.progress.total_exercises}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Corpus Browse Overlay */}
                {showCorpusBrowse && (
                    <div className="profile-overlay" onClick={() => { setShowCorpusBrowse(false); setSelectedCorpusDoc(null) }}>
                        <div
                            ref={corpusModalRef}
                            className="profile-card corpus-browse-card"
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="corpus-modal-title"
                            tabIndex={-1}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="profile-header">
                                <div className="profile-title" id="corpus-modal-title">📖 Korpusi i Drejtshkrimit</div>
                                <button className="profile-close" aria-label="Mbyll korpusin" onClick={() => { setShowCorpusBrowse(false); setSelectedCorpusDoc(null) }}>×</button>
                            </div>
                            <div className="corpus-browse-content">
                                {selectedCorpusDoc ? (
                                    <div className="corpus-doc-detail">
                                        <button className="corpus-back-btn" onClick={() => setSelectedCorpusDoc(null)}>← Kthehu te lista</button>
                                        <h3>{selectedCorpusDoc.title}</h3>
                                        <div className="corpus-doc-meta">
                                            {selectedCorpusDoc.author && <span>✍️ {selectedCorpusDoc.author}</span>}
                                            {selectedCorpusDoc.year && <span>📅 {selectedCorpusDoc.year}</span>}
                                            {selectedCorpusDoc.genre && <span>📂 {selectedCorpusDoc.genre}</span>}
                                            {selectedCorpusDoc.dialect && <span>🗣️ {selectedCorpusDoc.dialect}</span>}
                                            {selectedCorpusDoc.class_name && <span>📚 {selectedCorpusDoc.class_name}</span>}
                                            {selectedCorpusDoc.token_count !== undefined && <span>📊 {selectedCorpusDoc.token_count} fjalë</span>}
                                        </div>
                                        <div className="corpus-doc-body">{selectedCorpusDoc.content}</div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="corpus-browse-filters">
                                            <input
                                                type="text"
                                                placeholder="Kërko dokumente..."
                                                value={corpusBrowseSearch}
                                                onChange={(e) => setCorpusBrowseSearch(e.target.value)}
                                                onKeyDown={(e) => { if (e.key === 'Enter') { setCorpusBrowseOffset(0); loadCorpusBrowse() } }}
                                                className="corpus-search-input"
                                            />
                                            <select
                                                value={corpusBrowseClassId || ''}
                                                onChange={(e) => { setCorpusBrowseClassId(e.target.value ? parseInt(e.target.value) : undefined); setCorpusBrowseOffset(0) }}
                                                className="corpus-filter-select"
                                            >
                                                <option value="">Të gjitha klasat</option>
                                                {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                            </select>
                                            <button className="corpus-search-btn" onClick={() => { setCorpusBrowseOffset(0); loadCorpusBrowse() }}>Kërko</button>
                                        </div>
                                        {corpusBrowseLoading ? (
                                            <div className="corpus-loading">Duke ngarkuar...</div>
                                        ) : corpusBrowseDocs.length === 0 ? (
                                            <div className="corpus-empty">Nuk u gjetën dokumente.</div>
                                        ) : (
                                            <>
                                                <p className="corpus-results-count">{corpusBrowseTotal} dokumente gjithsej</p>
                                                <div className="corpus-doc-list">
                                                    {corpusBrowseDocs.map(doc => (
                                                        <div key={doc.id} className="corpus-doc-card" onClick={() => loadCorpusDocument(doc.id)}>
                                                            <h4>{doc.title}</h4>
                                                            <p className="corpus-doc-preview">{doc.content?.substring(0, 200)}...</p>
                                                            <div className="corpus-doc-tags">
                                                                {doc.class_name && <span className="corpus-tag class">{doc.class_name}</span>}
                                                                {doc.genre && <span className="corpus-tag genre">{doc.genre}</span>}
                                                                {doc.author && <span className="corpus-tag author">{doc.author}</span>}
                                                                {doc.token_count !== undefined && <span className="corpus-tag tokens">{doc.token_count} fjalë</span>}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                                {corpusBrowseTotal > 20 && (
                                                    <div className="corpus-pagination">
                                                        <button disabled={corpusBrowseOffset === 0} onClick={() => setCorpusBrowseOffset(Math.max(0, corpusBrowseOffset - 20))}>← Para</button>
                                                        <span>Faqja {Math.floor(corpusBrowseOffset / 20) + 1} / {Math.ceil(corpusBrowseTotal / 20)}</span>
                                                        <button disabled={corpusBrowseOffset + 20 >= corpusBrowseTotal} onClick={() => setCorpusBrowseOffset(corpusBrowseOffset + 20)}>Pas →</button>
                                                    </div>
                                                )}
                                            </>
                                        )}
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                )}

            {/* FOOTER SECTION */}
            <AppFooter />
            {message && <AppToast message={message} />}
        </div>
    )
}

// Main Content Component
function MainContent({
    isLoading,
    classes,
    selectedClass,
    selectedCourse,
    selectedLevel,
    courseLevels,
    classCourses,
    userId,
    aiRecommendations,
    adaptiveDifficulty,
    childLearningSupport,
    childLearningLoading,
    childFeedback,
    childPracticeAnswer,
    setChildPracticeAnswer,
    childPracticeMessage,
    handleChildPracticeCheck,
    learningPath: _learningPath,
    progressInsights: _progressInsights,
    aiCoach,
    aiCoachLoading: _aiCoachLoading,
    aiCoachError: _aiCoachError,
    aiCoachLevel: _aiCoachLevel,
    aiCoachLevelLoading: _aiCoachLevelLoading,
    aiCoachLevelError: _aiCoachLevelError,
    showAIInsights,
    userAchievements,
    userStreak,
    dailyChallenge,
    srsStats: _srsStats,
    showGamification,
    setShowGamification,
    onClassClick,
    onCourseClick,
    onLevelClick,
    onToggleAIInsights,
    getLevelProgress,
    publicStats,
    exercises,
    currentExerciseIndex,
    answers,
    setAnswers,
    handleSubmitAnswer,
    isSubmittingAnswer = false,
    playAudio,
    startRecording,
    isRecording,
    showPronunciationHint,
    setCurrentExerciseIndex,
    setMessage,
    // AI Practice props
    aiExercises: _aiExercises,
    aiResponses: _aiResponses,
    aiFeedback: _aiFeedback,
    aiLoading: _aiLoading,
    aiError: _aiError,
    aiMessage: _aiMessage,
    handleGenerateAIPractice: _handleGenerateAIPractice,
    handleAIResponseChange: _handleAIResponseChange,
    handleAIExerciseCheck: _handleAIExerciseCheck,
    // OCR props
    ocrLoading,
    ocrError,
    ocrResult,
    ocrExpected,
    setOcrExpected,
    handleOCRSubmit,
    handleSelectOCRFile
}: {
    isLoading: boolean
    classes: ClassData[]
    selectedClass: ClassData | null
    selectedCourse: CourseOut | null
    selectedLevel: LevelOut | null
    courseLevels: LevelOut[]
    classCourses: CourseOut[]
    userId: string
    aiRecommendations: any
    adaptiveDifficulty: any
    childLearningSupport: any
    childLearningLoading: boolean
    childFeedback: any
    childPracticeAnswer: string
    setChildPracticeAnswer: React.Dispatch<React.SetStateAction<string>>
    childPracticeMessage: string | null
    handleChildPracticeCheck: () => void
    learningPath: any
    progressInsights: any
    aiCoach: AICoachResponse | null
    aiCoachLoading: boolean
    aiCoachError: string | null
    aiCoachLevel: AICoachResponse | null
    aiCoachLevelLoading: boolean
    aiCoachLevelError: string | null
    showAIInsights: boolean
    userAchievements: UserAchievementsResponse | null
    userStreak: StreakData | null
    dailyChallenge: DailyChallenge | null
    srsStats: SRSStatsResponse | null
    showGamification: boolean
    setShowGamification: (value: boolean) => void
    onClassClick: (classData: ClassData | null) => void
    onCourseClick: (course: CourseOut | null) => void
    onLevelClick: (level: LevelOut | null) => void
    onToggleAIInsights: () => void
    getLevelProgress: (levelId: number) => number
    publicStats: {
        total_classes: number
        total_exercises: number
        total_categories: number
        total_levels: number
    }
    exercises: ExerciseOut[]
    currentExerciseIndex: number
    answers: Record<number, string>
    setAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>
    handleSubmitAnswer: () => Promise<void>
    isSubmittingAnswer?: boolean
    playAudio: (exerciseId: number) => Promise<void>
    startRecording: () => Promise<void>
    isRecording: boolean
    showPronunciationHint: () => void
    setCurrentExerciseIndex: React.Dispatch<React.SetStateAction<number>>
    setMessage: React.Dispatch<React.SetStateAction<string>>
    // AI Practice types
    aiExercises: AIPracticeExercise[]
    aiResponses: Record<string, string>
    aiFeedback: Record<string, string>
    aiLoading: boolean
    aiError: string | null
    aiMessage: string | null
    handleGenerateAIPractice: () => void
    handleAIResponseChange: (exerciseId: string, value: string) => void
    handleAIExerciseCheck: (exercise: AIPracticeExercise) => void
    // OCR types
    ocrLoading: boolean
    ocrError: string | null
    ocrResult: any
    ocrExpected: string
    setOcrExpected: React.Dispatch<React.SetStateAction<string>>
    handleOCRSubmit: () => void
    handleSelectOCRFile: (event: ChangeEvent<HTMLInputElement>) => void
}) {
    // Suppress unused variable warnings for simplified layout
    void _learningPath; void _progressInsights; void _aiCoachLoading; void _aiCoachError;
    void _aiCoachLevel; void _aiCoachLevelLoading; void _aiCoachLevelError; void _srsStats;
    void _aiExercises; void _aiResponses; void _aiFeedback; void _aiLoading; void _aiError;
    void _aiMessage; void _handleGenerateAIPractice; void _handleAIResponseChange; void _handleAIExerciseCheck;

    const [isOCRWorkspaceOpen, setIsOCRWorkspaceOpen] = useState(false)
    const ocrModalRef = useModalAccessibility<HTMLElement>(
        isOCRWorkspaceOpen,
        () => setIsOCRWorkspaceOpen(false)
    )

    const getOCRIssueLabel = (type?: string) => {
        const labels: Record<string, string> = {
            missing_word: 'Fjalë e munguar',
            extra_word: 'Fjalë shtesë',
            missing_letter: 'Shkronjë e munguar',
            extra_letter: 'Shkronjë e tepërt',
            letter_substitution: 'Zëvendësim shkronje',
            letter_transposition: 'Ndërrim shkronjash',
            digraph_suspected: 'Grup shkronjash shqip',
            vowel_confusion: 'Ngatërrim zanor',
            diacritics_suspected: 'Ë/Ç dhe diakritikë',
            ending_ë_suspected: 'Ë fundore',
            ç_suspected: 'Ç/C',
            double_consonant_suspected: 'Bashkëtingëllore e dyfishtë',
            capitalization: 'Shkronjë e madhe/vogël',
            low_confidence: 'Besueshmëri e ulët OCR',
            unknown_word: 'Fjalë e panjohur',
            mismatch_expected: 'Nuk përputhet'
        }
        return labels[type || ''] || 'Drejtshkrim'
    }

    const currentExercise = exercises[currentExerciseIndex]
    const classLabel = selectedClass ? `Klasa ${getClassNumber(selectedClass, classes)}` : 'klasa jote'
    const levelLabel = selectedCourse || selectedLevel
        ? formatCurriculumLabel(selectedClass, selectedCourse, selectedLevel, classes)
        : 'niveli yt'
    const getExerciseCategoryLabel = (category?: string) => {
        const labels: Record<string, string> = {
            listen_write: 'diktim me dëgjim',
            missing_letter: 'plotësim shkronje',
            wrong_letter: 'gjetje gabimi',
            synonyms_antonyms: 'kuptim fjalësh',
            number_to_word: 'numra me fjalë',
            build_sentence: 'ndërtim fjalie',
            build_word: 'ndërtim fjale',
            phrases: 'shprehje',
            spelling_punctuation: 'drejtshkrim dhe pikësim',
            albanian_or_loanword: 'fjalë shqipe dhe huazime',
            abstract_concrete: 'fjalë konkrete/abstrakte',
            word_from_description: 'gjetje fjale',
        }
        return labels[category || ''] || 'drejtshkrim'
    }
    const getChildGuideText = () => {
        if (!currentExercise) return 'Po të ndihmojmë të vazhdosh me ritmin tënd.'
        const focus = getExerciseCategoryLabel(currentExercise.category)
        if (currentExercise.category === 'listen_write') {
            return `Në ${classLabel}, ${levelLabel}, ky është ushtrim diktimi. Shtyp “Dëgjo”, dëgjo fjalën ose fjalinë, pastaj shkruaje përgjigjen te fusha poshtë.`
        }
        if (currentExercise.category === 'synonyms_antonyms') {
            return `Në ${classLabel}, ${levelLabel}, fokusi është kuptimi i fjalëve. Lexo pyetjen dhe zgjidh fjalën që përshtatet më mirë.`
        }
        return `Në ${classLabel}, ${levelLabel}, fokusi yt tani është ${focus}. Lexo pyetjen ngadalë dhe kontrollo përgjigjen para se ta dërgosh.`
    }
    const getAnswerPlaceholder = () => {
        if (currentExercise?.category === 'listen_write') return 'Dëgjo, pastaj shkruaj këtu...'
        if (currentExercise?.category === 'synonyms_antonyms') return 'Zgjidh ose shkruaj përgjigjen...'
        return 'Shkruaj përgjigjen këtu...'
    }

    // Mobile: open class/course/level as a dedicated top-of-screen view (not below the class list).
    useEffect(() => {
        if (!selectedClass) return
        if (typeof window === 'undefined') return
        if (!window.matchMedia('(max-width: 768px)').matches) return
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
        const content = document.querySelector('.app .content-area')
        if (content instanceof HTMLElement) {
            content.scrollTop = 0
        }
    }, [selectedClass?.id, selectedCourse?.id, selectedLevel?.id])
    
    return (
        <div className={`main-content ${selectedLevel ? 'with-ai-panel' : ''} ${!selectedClass ? 'main-content--home' : 'main-content--class-view'}`}>
            {/* Compact Left Sidebar - Navigation Only */}
            <aside className="sidebar sidebar-compact">
                <div className="sidebar-section sidebar-section-classes alblingo-world">
                    <div className="sidebar-section-header compact">
                        <h3>Klasat</h3>
                        <span className="classes-count-badge">{classes.length}</span>
                    </div>
                    <div className="class-list-compact alblingo-path" role="list">
                        {isLoading && classes.length === 0 ? (
                            <>
                                {[1, 2, 3].map((i) => (
                                    <div key={`skeleton-${i}`} className="skeleton-item-compact">
                                        <div className="skeleton" style={{width: '28px', height: '28px', borderRadius: '8px'}}></div>
                                        <div className="skeleton" style={{flex: 1, height: '16px'}}></div>
                                    </div>
                                ))}
                            </>
                        ) : classes.map((classData, classIndex) => {
                            const progress = classData.progress_percent || 0
                            const isSelected = selectedClass?.id === classData.id
                            const isCompleted = Boolean(classData.completed) || progress >= 100
                            const isInProgress = Boolean(classData.unlocked) && !isCompleted && progress > 0
                            const pathState = !classData.unlocked
                                ? 'path-locked'
                                : isCompleted
                                    ? 'path-completed'
                                    : isInProgress
                                        ? 'path-progress'
                                        : 'path-available'
                            return (
                                <button
                                    type="button"
                                    key={classData.id}
                                    role="listitem"
                                    className={`class-item-compact path-stage ${pathState} ${classData.unlocked ? 'unlocked' : 'locked'} ${isSelected ? 'selected' : ''} ${classIndex % 2 === 0 ? 'path-side-a' : 'path-side-b'}`}
                                    onClick={() => onClassClick(classData)}
                                    aria-current={isSelected ? 'page' : undefined}
                                    aria-disabled={!classData.unlocked}
                                    aria-label={`${classData.name}${classData.unlocked ? `, ${Math.round(progress)}%` : ', i mbyllur'}`}
                                >
                                    <span className="path-rail" aria-hidden="true"></span>
                                    <div className="class-item-left">
                                        <span
                                            className={`path-node ${isSelected ? 'is-current' : ''}`}
                                            aria-hidden="true"
                                            style={isInProgress ? { ['--path-progress' as string]: `${Math.max(8, Math.min(100, progress))}%` } : undefined}
                                        >
                                            <span className={`class-num ${isSelected ? 'active' : ''}`}>
                                                {classData.order_index}
                                            </span>
                                        </span>
                                        <span className="class-label">{classData.name}</span>
                                    </div>
                                    <div className="class-item-right">
                                        {isCompleted ? (
                                            <span className="path-complete-mark" aria-hidden="true">
                                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M20 6 9 17l-5-5" />
                                                </svg>
                                            </span>
                                        ) : classData.unlocked ? (
                                            <div className="progress-mini" title={`${Math.round(progress)}%`}>
                                                <div className="progress-mini-fill" style={{ width: `${progress}%` }}></div>
                                            </div>
                                        ) : (
                                            <span className="lock-mini" aria-hidden="true">
                                                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <rect x="5" y="11" width="14" height="10" rx="2" />
                                                    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
                                                </svg>
                                            </span>
                                        )}
                                    </div>
                                </button>
                            )
                        })}
                    </div>
                </div>

                {/* Compact progress: streak + AI insights in one place */}
                {userId && (userStreak || aiRecommendations) && (
                    <div className="sidebar-section sidebar-section-progress">
                        <div className="sidebar-section-header compact">
                            <h3>Progresi yt</h3>
                            <button
                                type="button"
                                className="toggle-btn-compact"
                                onClick={() => setShowGamification(!showGamification)}
                                aria-expanded={showGamification}
                            >
                                {showGamification ? '−' : '+'}
                            </button>
                        </div>
                        <div className="progress-panel-compact">
                            {userStreak && (
                                <div className="streak-compact">
                                    <span className="streak-num">{userStreak.current_streak}</span>
                                    <span className="streak-txt">ditë</span>
                                </div>
                            )}
                            {showGamification && (
                                <div className="progress-panel-details">
                                    {aiRecommendations && (
                                        <div className="ai-stats-compact">
                                            <div className="stat-row-compact">
                                                <span className="stat-label-compact">Saktësia</span>
                                                <span className="stat-value-compact">{Math.round(aiRecommendations.accuracy * 100)}%</span>
                                            </div>
                                            {adaptiveDifficulty && (
                                                <div className="stat-row-compact">
                                                    <span className="stat-label-compact">Nivel</span>
                                                    <span className="stat-value-compact">{adaptiveDifficulty.multiplier}x</span>
                                                </div>
                                            )}
                                            {aiCoach && (
                                                <div className="stat-row-compact">
                                                    <span className="stat-label-compact">Tentativa</span>
                                                    <span className="stat-value-compact">{aiCoach.total_attempts_analyzed}</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {dailyChallenge && dailyChallenge.user_progress && (
                                        <div className="challenge-compact">
                                            <div className="challenge-label">Sfida</div>
                                            <div className="challenge-bar-compact">
                                                <div
                                                    className="challenge-fill-compact"
                                                    style={{ width: `${Math.min(100, (dailyChallenge.user_progress.current_value / (dailyChallenge.target_value || 1)) * 100)}%` }}
                                                ></div>
                                            </div>
                                            <span className="challenge-count">{dailyChallenge.user_progress.current_value}/{dailyChallenge.target_value}</span>
                                        </div>
                                    )}
                                    {userAchievements && userAchievements.total_achievements > 0 && (
                                        <div className="achievements-compact">
                                            <span>{userAchievements.total_achievements} arritje</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {selectedLevel && currentExercise && (
                    <div className="sidebar-section child-ai-sidebar-section">
                        <div className="child-ai-side-card">
                            <div className="child-ai-side-header">
                                <strong>Ndihma jote</strong>
                            </div>
                            <p>{getChildGuideText()}</p>
                            {childLearningLoading ? (
                                <div className="child-ai-side-status">Po përshtatim hapin tjetër...</div>
                            ) : childLearningSupport?.recommended ? (
                                <div className="child-ai-side-status">
                                    Hapi tjetër do të zgjidhet sipas ritmit tënd.
                                </div>
                            ) : (
                                <div className="child-ai-side-status muted">
                                    Vazhdo ushtrimin dhe sistemi mëson nga progresi yt.
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Compact OCR entry remains in the sidebar; the workspace opens in a focused modal. */}
                {!selectedClass && !selectedCourse && !selectedLevel && (
                    <>
                        <section className="ocr-launch-card">
                            <div className="ocr-launch-copy">
                                <h3>Kontrollo diktimin</h3>
                                <p>Ngarko një foto dhe merr korrigjime të qarta të drejtshkrimit.</p>
                            </div>
                            <button type="button" className="ocr-launch-button" onClick={() => setIsOCRWorkspaceOpen(true)}>
                                Hap kontrollin
                            </button>
                        </section>

                        {isOCRWorkspaceOpen && (
                            <div
                                className="ocr-modal-overlay"
                                role="dialog"
                                aria-modal="true"
                                aria-labelledby="ocr-modal-title"
                                onClick={() => setIsOCRWorkspaceOpen(false)}
                            >
                                <section
                                    ref={ocrModalRef}
                                    className="ocr-main-container ocr-workspace-modal"
                                    tabIndex={-1}
                                    onClick={(event) => event.stopPropagation()}
                                >
                                    <button
                                        type="button"
                                        className="ocr-modal-close"
                                        onClick={() => setIsOCRWorkspaceOpen(false)}
                                        aria-label="Mbyll"
                                        title="Mbyll"
                                    >
                                        ✕
                                    </button>

                                    <header className="ocr-header">
                                        <div className="ocr-header-copy">
                                            <h3 id="ocr-modal-title">📝 Kontrollo diktimin tënd</h3>
                                            <p className="ocr-subtitle">
                                                Bëj një foto të diktimit tënd dhe ne do ta kontrollojmë së bashku! Do të shohim nëse ka gabime dhe do të mësojmë si t'i rregullojmë. 🎯
                                            </p>
                                        </div>
                                    </header>

                                    <div className="ocr-form">
                                        <label className="ocr-field">
                                            <span>📷 Foto e diktimit:</span>
                                            <input type="file" accept="image/*" onChange={handleSelectOCRFile} />
                                        </label>
                                        <label className="ocr-field">
                                            <span>✍️ Teksti që duhet të jetë (nëse e di):</span>
                                            <textarea
                                                rows={3}
                                                value={ocrExpected}
                                                onChange={(e) => setOcrExpected(e.target.value)}
                                                placeholder="Shkruaj këtu tekstin që duhet të jetë në diktim..."
                                            />
                                        </label>
                                    </div>

                                    <div className="ocr-modal-actions">
                                        {ocrLoading ? (
                                            <div className="ocr-loading-header">
                                                <div className="ocr-spinner-small"></div>
                                                <span>Po kontrollojmë... ⏳</span>
                                            </div>
                                        ) : (
                                            <button type="button" className="ocr-button" onClick={handleOCRSubmit}>
                                                🚀 Kontrollo Diktimin
                                            </button>
                                        )}
                                    </div>

                                    {ocrLoading && (
                                        <div className="ocr-loading-overlay">
                                            <div className="ocr-spinner"></div>
                                            <p>Po lexojmë diktimin tënd dhe po kontrollojmë gabimet... 🤔</p>
                                        </div>
                                    )}

                                    {ocrError && <div className="ocr-error">{ocrError}</div>}

                                    {ocrResult && (
                                        <div className="ocr-result-container">
                                            {/* Stage 1: Raw OCR Output */}
                                            <div className="ocr-section ocr-extracted-section">
                                                <div className="ocr-section-header">
                                                    <h4>📄 Çfarë lexuam nga fotoja:</h4>
                                                    <div className="ocr-meta-pills">
                                                        {ocrResult.meta?.ocr_confidence_avg !== undefined && (
                                                            <span className={`ocr-confidence-pill ${ocrResult.meta.ocr_confidence_avg > 80 ? 'high' : ocrResult.meta.ocr_confidence_avg > 50 ? 'medium' : 'low'}`}>
                                                                Saktësia: {Math.round(ocrResult.meta.ocr_confidence_avg)}%
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="ocr-text-box">
                                                    {ocrResult.extracted_text ? (
                                                        <p className="ocr-text">{ocrResult.extracted_text}</p>
                                                    ) : ocrResult.issues && ocrResult.issues.length > 0 ? (
                                                        <p className="ocr-text">
                                                            {ocrResult.issues.map((issue: any) => issue.token || issue.recognized).filter(Boolean).join(' ')}
                                                        </p>
                                                    ) : (
                                                        <p className="ocr-text-empty">😕 Nuk mundëm të lexojmë tekstin nga fotoja. Provo të bësh një foto më të qartë dhe me më shumë dritë! 💡</p>
                                                    )}
                                                </div>
                                                
                                                {/* Fjalët e detektuara (lista) */}
                                                {ocrResult.issues && ocrResult.issues.length > 0 && (
                                                    <div className="ocr-tokens-list">
                                                        <span className="tokens-label">Fjalët që lexuam:</span>
                                                        {ocrResult.issues.map((issue: any, idx: number) => (
                                                            <span key={idx} className="ocr-token-chip">
                                                                {issue.token || issue.recognized}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Stage 2: LLM-Refined Text (if available) */}
                                            {ocrResult.refined_text && (
                                                <div className="ocr-section ocr-refined-section">
                                                    <div className="ocr-section-header">
                                                        <h4>🤖 Teksti i përmirësuar:</h4>
                                                        <div className="ocr-meta-pills">
                                                            {ocrResult.meta?.llm_model && (
                                                                <span className="ocr-llm-pill">{ocrResult.meta.llm_model}</span>
                                                            )}
                                                            {ocrResult.meta?.llm_confidence !== undefined && (
                                                                <span className={`ocr-confidence-pill ${ocrResult.meta.llm_confidence > 0.8 ? 'high' : ocrResult.meta.llm_confidence > 0.5 ? 'medium' : 'low'}`}>
                                                                    AI: {Math.round(ocrResult.meta.llm_confidence * 100)}%
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="ocr-text-box refined">
                                                        <p className="ocr-text">{ocrResult.refined_text}</p>
                                                    </div>
                                                    
                                                    {/* LLM Corrections */}
                                                    {ocrResult.llm_corrections && ocrResult.llm_corrections.length > 0 && (
                                                        <div className="llm-corrections">
                                                            <h5>✨ Ndryshimet që bëmë:</h5>
                                                            <ul>
                                                                {ocrResult.llm_corrections.map((corr: any, idx: number) => (
                                                                    <li key={idx} className="llm-correction-item">
                                                                        <span className="correction-original">{corr.original}</span>
                                                                        <span className="correction-arrow">→</span>
                                                                        <span className="correction-fixed">{corr.corrected}</span>
                                                                        {corr.reason && <span className="correction-reason">({corr.reason})</span>}
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {/* Stage 3: Orthography Analysis */}
                                            <div className="ocr-section ocr-analysis-section">
                                                <h4>🔍 Çfarë gjetëm:</h4>
                                                {(ocrResult.issues?.length || ocrResult.errors?.length) > 0 ? (
                                                    <div className="ocr-errors-list">
                                                        <ul>
                                                            {(ocrResult.issues || ocrResult.errors).map((err: any, idx: number) => (
                                                                <li key={idx} className="ocr-error-item">
                                                                    <div className="ocr-error-main">
                                                                        {err.expected ? (
                                                                            <>
                                                                                <span className="ocr-type-tag type-orth">
                                                                                    {getOCRIssueLabel(err.type)}
                                                                                </span>
                                                                                Pozicioni {err.position}: Fjala <strong>"{err.recognized || err.token}"</strong> duhet të shkruhet <strong>"{err.expected}"</strong>. {err.message}
                                                                            </>
                                                                        ) : (
                                                                            <>
                                                                                <span className={`ocr-type-tag ${err.source === 'ocr' ? 'type-ocr' : 'type-orth'}`}>
                                                                                    {err.source === 'ocr' ? 'OCR' : 'Drejtshkrim'}
                                                                                </span>
                                                                                <span className="ocr-type-tag type-orth">
                                                                                    {getOCRIssueLabel(err.type)}
                                                                                </span>
                                                                                Fjala <strong>"{err.token || err.recognized}"</strong>: {err.message}
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                    {err.suggestions?.length > 0 && (
                                                                        <div className="ocr-error-suggestions">
                                                                            Sugjerime: {err.suggestions.map((s: string, si: number) => <span key={si} className="sugg-tag">{s}</span>)}
                                                                        </div>
                                                                    )}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                ) : (
                                                    <div className="ocr-clean-box">
                                                        <p>🎉 Bravo! Nuk gjetëm asnjë gabim! Diktimi yt është perfekt! ⭐</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </section>
                            </div>
                        )}
                    </>
                )}
            </aside>

            {/* Main Content Area */}
            <div className="content-area">
                {isLoading ? (
                    <div className="loading page-loading" role="status" aria-live="polite" aria-busy="true">
                        <div className="page-loading-progress" aria-hidden="true">
                            <span className="page-loading-progress-bar"></span>
                        </div>
                        <div className="page-loading-inner">
                            <div className="page-loading-mark" aria-hidden="true">
                                <BrandLogo size={52} decorative />
                            </div>
                            <p className="page-loading-brand">AlbLingo</p>
                            <p className="page-loading-title">Duke ngarkuar</p>
                            <p className="page-loading-subtitle">Po përgatitim platformën për ju</p>
                        </div>
                    </div>
                ) : !selectedClass ? (
                    <div className="welcome-screen-modern">
                        {/* Hero Section */}
                        <div className="hero-section-modern">
                            <div className="hero-content-modern">
                                <div className="welcome-brand-hero" aria-hidden="true">
                                    <BrandLogo size={72} decorative />
                                </div>
                                <h1 className="hero-title-modern">AlbLingo</h1>
                                <p className="hero-description-modern">
                                    Mëso të shkruash shqip. Zgjidh klasën dhe fillo!
                                </p>
                                <div className="hero-stats-modern">
                                    <div className="hero-stat-modern">
                                        <div className="stat-number-modern">{publicStats.total_classes || 0}</div>
                                        <div className="stat-label-modern">Klasa</div>
                                    </div>
                                    <div className="hero-stat-modern">
                                        <div className="stat-number-modern">{publicStats.total_exercises > 0 ? `${publicStats.total_exercises}+` : '0'}</div>
                                        <div className="stat-label-modern">Ushtrime</div>
                                    </div>
                                    <div className="hero-stat-modern">
                                        <div className="stat-number-modern">{publicStats.total_categories || 0}</div>
                                        <div className="stat-label-modern">Kategori</div>
                                    </div>
                                    <div className="hero-stat-modern">
                                        <div className="stat-number-modern">{publicStats.total_levels || 0}</div>
                                        <div className="stat-label-modern">Nivele</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Learning Features Section */}
                        <div className="features-section-modern">
                            <div className="section-header-modern">
                                <h3 className="section-title-modern">Veçoritë e Platformës</h3>
                                <p className="section-subtitle-modern">Teknologji moderne për mësim efektiv</p>
                            </div>
                            
                            <div className="features-grid-modern">
                                <div className="features-row features-row-3">
                                    <div className="feature-card-modern">
                                        <div className="feature-icon-wrapper">
                                            <div className="feature-icon-modern icon-audio" aria-hidden="true"></div>
                                        </div>
                                        <h4 className="feature-title-modern">Audio Interaktiv</h4>
                                        <p className="feature-description-modern">Dëgjoni dhe përsëritni me cilësi të lartë audio</p>
                                    </div>
                                    <div className="feature-card-modern">
                                        <div className="feature-icon-wrapper">
                                            <div className="feature-icon-modern icon-chart" aria-hidden="true"></div>
                                        </div>
                                        <h4 className="feature-title-modern">Progres i Detajuar</h4>
                                        <p className="feature-description-modern">Ndiqni përparimin tuaj me statistika të hollësishme</p>
                                    </div>
                                    <div className="feature-card-modern">
                                        <div className="feature-icon-wrapper">
                                            <div className="feature-icon-modern icon-trophy" aria-hidden="true"></div>
                                        </div>
                                        <h4 className="feature-title-modern">Sistem Pikësh</h4>
                                        <p className="feature-description-modern">Fitoni pikë, yje dhe nivele për të qenë të motivuar</p>
                                    </div>
                                </div>
                                <div className="features-row features-row-2">
                                    <div className="feature-card-modern">
                                        <div className="feature-icon-wrapper">
                                            <div className="feature-icon-modern icon-ai" aria-hidden="true"></div>
                                        </div>
                                        <h4 className="feature-title-modern">AI i Personalizuar</h4>
                                        <p className="feature-description-modern">Rekomandime inteligjente bazuar në progresin tuaj</p>
                                    </div>
                                    <div className="feature-card-modern">
                                        <div className="feature-icon-wrapper">
                                            <div className="feature-icon-modern icon-rank" aria-hidden="true"></div>
                                        </div>
                                        <h4 className="feature-title-modern">{LEADERBOARD_TITLE}</h4>
                                        <p className="feature-description-modern">Krahasoni rezultatet me përdorues të tjerë</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : !selectedCourse ? (
                    <section className="course-selection level-picker" aria-labelledby="class-levels-heading">
                        <header className="course-selection-header level-picker-header">
                            <button type="button" className="back-button-modern" onClick={() => onClassClick(null)}>
                                <span className="back-icon" aria-hidden="true">←</span>
                                <span>Kthehu te Klasat</span>
                            </button>
                            <div className="class-header-info level-picker-intro">
                                <div className="class-title-section level-picker-title">
                                    <h2 id="class-levels-heading" className="class-title">{selectedClass.name}</h2>
                                    <p className="class-subtitle">Zgjidh një nivel dhe fillo</p>
                                </div>
                                <div className="class-overall-progress level-picker-progress" aria-label="Progresi i Përgjithshëm">
                                    <div className="overall-progress-label">
                                        <span className="overall-progress-title">Progresi i Përgjithshëm</span>
                                        <span className="progress-percentage">
                                            {classCourses.length > 0
                                                ? Math.round((classCourses.filter(c => c.progress?.is_completed).length / classCourses.length) * 100)
                                                : 0}%
                                        </span>
                                    </div>
                                    <div
                                        className="overall-progress-bar"
                                        role="progressbar"
                                        aria-valuemin={0}
                                        aria-valuemax={100}
                                        aria-valuenow={classCourses.length > 0 ? Math.round((classCourses.filter(c => c.progress?.is_completed).length / classCourses.length) * 100) : 0}
                                    >
                                        <div
                                            className="overall-progress-fill"
                                            style={{
                                                width: `${classCourses.length > 0
                                                    ? (classCourses.filter(c => c.progress?.is_completed).length / classCourses.length) * 100
                                                    : 0}%`
                                            }}
                                        ></div>
                                    </div>
                                    <div className="overall-progress-stats">
                                        <span>{classCourses.filter(c => c.progress?.is_completed).length} nga {classCourses.length} nivele të përfunduara</span>
                                    </div>
                                </div>
                            </div>
                        </header>
                        
                        <div className="course-preview-grid-modern level-picker-grid" role="list">
                            {isLoading && classCourses.length === 0 ? (
                                <div className="skeleton-grid">
                                    {[1, 2, 3, 4, 5, 6].map((i) => (
                                        <div key={`skeleton-course-${i}`} className="skeleton-card">
                                            <div className="skeleton skeleton-circle" style={{width: '48px', height: '48px', marginBottom: '10px'}}></div>
                                            <div className="skeleton skeleton-title" style={{marginBottom: '10px'}}></div>
                                            <div className="skeleton skeleton-text medium"></div>
                                        </div>
                                    ))}
                                </div>
                            ) : classCourses.map((course) => {
                                const progressPercent = course.progress 
                                    ? Math.min(100, (course.progress.completed_exercises / Math.max(1, course.progress.total_exercises)) * 100)
                                    : 0
                                const isCompleted = course.progress?.is_completed || false
                                const statusLabel = isCompleted ? 'I përfunduar' : course.enabled ? 'I hapur' : 'I mbyllur'
                                
                                return (
                                    <button
                                        type="button"
                                        key={course.id}
                                        role="listitem"
                                        className={`course-card-modern level-picker-card ${course.enabled ? 'unlocked' : 'locked'} ${isCompleted ? 'completed' : ''}`}
                                        onClick={() => course.enabled && onCourseClick(course)}
                                        disabled={!course.enabled}
                                        aria-label={`${course.name}, ${statusLabel}`}
                                    >
                                        <div className="course-card-top">
                                            <h4 className="course-name-modern">{course.name}</h4>
                                            <span className={`status-badge ${isCompleted ? 'completed-badge' : course.enabled ? 'active-badge' : 'locked-badge'}`}>
                                                {statusLabel}
                                            </span>
                                        </div>

                                        {course.progress ? (
                                            <div className="course-progress-modern">
                                                <div className="progress-header-modern">
                                                    <span className="progress-label">Progresi</span>
                                                    <span className="progress-percent">{Math.round(progressPercent)}%</span>
                                                </div>
                                                <div className="progress-bar-modern">
                                                    <div 
                                                        className="progress-fill-modern" 
                                                        style={{ width: `${progressPercent}%` }}
                                                    ></div>
                                                </div>
                                                <div className="progress-details-modern">
                                                    <div className="progress-stat-item">
                                                        <span>{course.progress.completed_exercises}/{course.progress.total_exercises} ushtrime</span>
                                                    </div>
                                                    {course.progress.accuracy_percentage > 0 && (
                                                        <div className="progress-stat-item">
                                                            <span>{course.progress.accuracy_percentage.toFixed(0)}% saktësi</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ) : course.enabled ? (
                                            <div className="course-start-prompt">
                                                <span>Kliko për të filluar</span>
                                            </div>
                                        ) : null}
                                    </button>
                                )
                            })}
                        </div>
                    </section>
                ) : !selectedLevel ? (
                    <div className="level-selection-modern">
                        <div className="level-selection-header">
                            <button className="back-button-modern" onClick={() => onCourseClick(null)}>
                                <span className="back-icon">←</span>
                                <span>Kthehu te Nivelet</span>
                            </button>
                            <div className="course-header-info">
                                <div className="course-title-section">
                                    <div className="course-badge-modern">{selectedCourse.name}</div>
                                    <h2 className="course-title-modern">{selectedCourse.name}</h2>
                                    <p className="course-subtitle-modern">Zgjidh dhe fillo ushtrimet</p>
                                </div>
                            </div>
                        </div>
                        
                        {/* Show levels for the selected course */}
                        <div className="level-grid-modern">
                            {isLoading && courseLevels.length === 0 ? (
                                // Skeleton loading for levels
                                <>
                                    {[1, 2, 3, 4, 5, 6].map((i) => (
                                        <div key={`skeleton-level-${i}`} className="skeleton-card">
                                            <div className="skeleton skeleton-circle" style={{width: '50px', height: '50px', marginBottom: '12px'}}></div>
                                            <div className="skeleton skeleton-title"></div>
                                            <div className="skeleton skeleton-text short"></div>
                                            <div className="skeleton skeleton-text" style={{width: '80%', marginTop: '12px'}}></div>
                                        </div>
                                    ))}
                                </>
                            ) : courseLevels.map((level, index) => {
                                const levelProgress = getLevelProgress(level.id)
                                const levelDisplayName = selectedClass && selectedCourse
                                    ? formatCurriculumLabel(selectedClass, selectedCourse, level, classes)
                                    : selectedClass
                                        ? `Niveli ${getCurriculumLevelNumber(selectedCourse, level)} Klasa ${getClassNumber(selectedClass, classes)}`
                                        : level.name
                                return (
                                    <div
                                        key={level.id}
                                        className="level-card-modern"
                                        onClick={() => onLevelClick(level)}
                                    >
                                        <div className="level-card-header-modern">
                                            <div className="level-number-circle">
                                                {getCurriculumLevelNumber(selectedCourse, level) || index + 1}
                                            </div>
                                            <div className="level-info-wrapper">
                                                <h3 className="level-name-modern">{levelDisplayName}</h3>
                                                <p className="level-description-modern">{level.description}</p>
                                            </div>
                                        </div>
                                        <div className="level-progress-section-modern">
                                            <div className="level-progress-header-modern">
                                                <span className="level-progress-label">Progresi</span>
                                                <span className="level-progress-percent">{Math.round(levelProgress)}%</span>
                                            </div>
                                            <div className="level-progress-bar-modern">
                                                <div 
                                                    className="level-progress-fill-modern" 
                                                    style={{ width: `${levelProgress}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                        <div className="level-card-footer-modern">
                                            <div className="level-requirement">
                                                <span className="requirement-icon">🎯</span>
                                                <span>Kërkohet: {level.required_score}%</span>
                                            </div>
                                            <div className="level-action">
                                                <span className="action-text">Fillo →</span>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                ) : selectedLevel && exercises.length > 0 ? (
                    <div className="exercise-area-modern exercise-workspace">
                        <header className="exercise-header-modern exercise-workspace-header">
                            <button type="button" className="back-button-modern" onClick={() => onLevelClick(null)}>
                                <span className="back-icon" aria-hidden="true">←</span>
                                <span>Kthehu te Nivelet</span>
                            </button>
                            <div className="exercise-title-section exercise-workspace-title">
                                <span className="exercise-badge-modern">Ushtrimet</span>
                                <h2 className="exercise-title-modern">
                                    {selectedLevel && selectedClass && selectedCourse
                                        ? formatCurriculumLabel(selectedClass, selectedCourse, selectedLevel, classes)
                                        : selectedLevel?.name || 'Ushtrimet'
                                    }
                                </h2>
                                <p className="exercise-subtitle-modern">
                                    {selectedLevel.description ? selectedLevel.description : (() => {
                                        if (selectedLevel && selectedClass && selectedCourse) {
                                            return `Përgjigjuni pyetjeve për të përfunduar ${formatCurriculumLabel(selectedClass, selectedCourse, selectedLevel, classes)}`
                                        }
                                        return `Përgjigjuni pyetjeve për të përfunduar ${selectedLevel?.name || 'ushtrimet'}`
                                    })()}
                                </p>
                            </div>
                        </header>
                        
                        <div className="exercise-container-modern">
                            <div className="exercise-progress-modern">
                                <div className="exercise-progress-header-modern">
                                    <span className="progress-label-exercise">Progresi</span>
                                    <span className="progress-counter-exercise">
                                        {currentExerciseIndex + 1} / {exercises.length}
                                    </span>
                                </div>
                                <div className="exercise-progress-bar-modern">
                                    <div 
                                        className="exercise-progress-fill-modern" 
                                        style={{ width: `${((currentExerciseIndex + 1) / exercises.length) * 100}%` }}
                                    ></div>
                                </div>
                            </div>

                            <div className="exercise-card-modern">
                                <div className="exercise-card-header-modern">
                                    <div className="exercise-points-badge-modern">
                                        +{exercises[currentExerciseIndex].points} pikë
                                    </div>
                                </div>
                                
                                {/* Instruction text for synonyms/antonyms exercises */}
                                {exercises.length > 0 && 
                                 exercises[currentExerciseIndex] && 
                                 exercises[currentExerciseIndex].category === 'synonyms_antonyms' && (
                                    <div className="exercise-instruction-text">
                                        {(() => {
                                            // For Class 1, Niveli 3 (course): first 5 are antonyms, rest are synonyms
                                            const isClass1 = getClassNumber(selectedClass, classes) === 1
                                            const isLevel3 = getCurriculumLevelNumber(selectedCourse, selectedLevel) === 3
                                            
                                            if (isClass1 && isLevel3) {
                                                // First 5 exercises (0-4) are antonyms
                                                if (currentExerciseIndex < 5) {
                                                    return <p>💡 Gjej fjalën që ka kuptim të kundërt.</p>
                                                } else {
                                                    // Rest (5+) are synonyms
                                                    return <p>💡 Gjej fjalën që ka kuptim të njëjtë ose të ngjashëm.</p>
                                                }
                                            }
                                            
                                            // For other cases, determine based on exercise index
                                            // First half = antonyms, second half = synonyms
                                            const totalExercises = exercises.length
                                            const midpoint = Math.ceil(totalExercises / 2)
                                            const isFirstHalf = currentExerciseIndex < midpoint
                                            
                                            if (isFirstHalf) {
                                                return <p>💡 Gjej fjalën që ka kuptim të kundërt.</p>
                                            } else {
                                                return <p>💡 Gjej fjalën që ka kuptim të njëjtë ose të ngjashëm.</p>
                                            }
                                        })()}
                                    </div>
                                )}

                                <div className="exercise-content-modern">
                                    <div className="exercise-prompt-modern">
                                        <h3 className="exercise-question">{exercises[currentExerciseIndex].prompt}</h3>
                                    </div>

                                    {exercises[currentExerciseIndex].category === 'listen_write' && (
                                        <div className="dictation-helper-modern">
                                            <div className="dictation-helper-text">
                                                <strong>Si ta bësh këtë ushtrim:</strong> Shtyp “Dëgjo”, pastaj shkruaj fjalën ose fjalinë që dëgjove.
                                            </div>
                                            <div className="voice-controls-modern">
                                                <button
                                                    type="button"
                                                    className="voice-btn-modern primary"
                                                    onClick={() => playAudio(exercises[currentExerciseIndex].id)}
                                                >
                                                    <span>Dëgjo</span>
                                                </button>
                                                <button
                                                    type="button"
                                                    className="voice-btn-modern secondary"
                                                    onClick={() => startRecording()}
                                                    disabled={isRecording}
                                                >
                                                    <span>{isRecording ? 'Duke regjistruar...' : 'Regjistro'}</span>
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {exercises[currentExerciseIndex].rule && (
                                        <div className="exercise-hint-modern">
                                            <div className="hint-content">
                                                <strong>Këshillë:</strong> {exercises[currentExerciseIndex].rule}
                                            </div>
                                        </div>
                                    )}

                                    {/* Word Choices for exercises with choices */}
                                    {exercises[currentExerciseIndex].data && (() => {
                                        try {
                                            const exerciseData = JSON.parse(exercises[currentExerciseIndex].data);
                                            if (exerciseData.choices && Array.isArray(exerciseData.choices)) {
                                                return (
                                                    <div className="word-choices-modern">
                                                        <p className="choices-label-modern">Zgjidh fjalën e saktë:</p>
                                                        <div className="choice-buttons-modern">
                                                            {exerciseData.choices.map((choice: string, index: number) => (
                                                                <button
                                                                    key={index}
                                                                    className={`choice-btn-modern ${answers[exercises[currentExerciseIndex].id] === choice ? 'selected' : ''}`}
                                                                    onClick={() => setAnswers(prev => ({ ...prev, [exercises[currentExerciseIndex].id]: choice }))}
                                                                >
                                                                    {choice}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                );
                                            }
                                        } catch (e) {
                                            // If JSON parsing fails, fall back to text input
                                        }
                                        return null;
                                    })()}

                                    <div className="answer-input-modern">
                                        <input
                                            type="text"
                                            className="answer-input-field"
                                            placeholder={getAnswerPlaceholder()}
                                            value={answers[exercises[currentExerciseIndex].id] || ''}
                                            onChange={(e) => setAnswers(prev => ({ ...prev, [exercises[currentExerciseIndex].id]: e.target.value }))}
                                            onKeyPress={(e) => e.key === 'Enter' && handleSubmitAnswer()}
                                            autoFocus
                                        />
                                    </div>

                                    {childFeedback && (
                                        <div className="child-feedback-card">
                                            <div className="child-feedback-header">
                                                <strong>{childFeedback.child_message?.title || 'Ndihmë'}</strong>
                                            </div>
                                            {(childFeedback.child_message?.what_you_wrote || childFeedback.comparison?.student_to_correct) && (
                                                <p>
                                                    <strong>Çfarë shkrove:</strong>{' '}
                                                    {childFeedback.child_message?.what_you_wrote || childFeedback.comparison?.student_to_correct}
                                                </p>
                                            )}
                                            <p><strong>Forma e saktë:</strong> {childFeedback.child_message?.correct_form || childFeedback.correct_form}</p>
                                            <p><strong>Rregulli:</strong> {childFeedback.child_message?.rule || childFeedback.simple_rule}</p>
                                            <p><strong>Pse?</strong> {childFeedback.child_message?.why || childFeedback.why}</p>
                                            {(childFeedback.child_message?.example || childFeedback.example) && (
                                                <p><strong>Shembull:</strong> {childFeedback.child_message?.example || childFeedback.example}</p>
                                            )}
                                            {childFeedback.next_practice?.prompt && (
                                                <div className="child-practice-box">
                                                    <span>Provo këtë më të lehtë:</span>
                                                    <strong>{childFeedback.child_message?.try_next || childFeedback.next_practice.prompt}</strong>
                                                    <div className="child-practice-input-row">
                                                        <input
                                                            type="text"
                                                            value={childPracticeAnswer}
                                                            onChange={(e) => setChildPracticeAnswer(e.target.value)}
                                                            onKeyDown={(e) => e.key === 'Enter' && handleChildPracticeCheck()}
                                                            placeholder="Shkruaje këtu..."
                                                            className="child-practice-input"
                                                        />
                                                        <button type="button" onClick={handleChildPracticeCheck} className="child-practice-check-btn">
                                                            Kontrollo
                                                        </button>
                                                    </div>
                                                    {childPracticeMessage && (
                                                        <div className="child-practice-message">{childPracticeMessage}</div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div className="exercise-actions-modern">
                                    <button
                                        type="button"
                                        className="submit-btn-modern"
                                        onClick={handleSubmitAnswer}
                                        disabled={isSubmittingAnswer}
                                    >
                                        <span>{isSubmittingAnswer ? 'Po kontrolloj...' : 'Kontrollo'}</span>
                                    </button>
                                    
                                    <div className="navigation-buttons-modern">
                                        <button
                                            type="button"
                                            className="nav-btn-modern prev"
                                            onClick={() => {
                                                if (currentExerciseIndex > 0) {
                                                    setCurrentExerciseIndex(currentExerciseIndex - 1)
                                                    setMessage('U kthyet në ushtrimin e mëparshëm! 👈')
                                                }
                                            }}
                                            disabled={currentExerciseIndex === 0}
                                        >
                                            ← E mëparshme
                                        </button>
                                        
                                        <button
                                            type="button"
                                            className="nav-btn-modern next"
                                            onClick={() => {
                                                if (currentExerciseIndex < exercises.length - 1) {
                                                    setCurrentExerciseIndex(currentExerciseIndex + 1)
                                                    setMessage('Kaluat në ushtrimin tjetër! 👉')
                                                }
                                            }}
                                            disabled={currentExerciseIndex === exercises.length - 1}
                                        >
                                            Tjetri →
                                        </button>
                                    </div>

                                    {exercises[currentExerciseIndex].category === 'listen_write' && (
                                        <button
                                            type="button"
                                            className="hint-btn-modern"
                                            onClick={() => showPronunciationHint()}
                                        >
                                            💡 Këshillë Shqiptimi
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                        
                        {/* AI Practice Section - ULTRA ADVANCED VERSION */}
                        {userId && selectedLevel && (
                            <LazyErrorBoundary label="ushtrimeve me AI">
                                <Suspense fallback={
                                    <div className="section-loading page-loading page-loading--inline" role="status" aria-live="polite" aria-busy="true">
                                        <div className="page-loading-inner">
                                            <div className="page-loading-spinner" aria-hidden="true"></div>
                                            <p className="page-loading-title">Duke ngarkuar</p>
                                            <p className="page-loading-subtitle">Ushtrimet me AI</p>
                                        </div>
                                    </div>
                                }>
                                    <AdvancedAIPractice
                                        userId={userId}
                                        levelId={selectedLevel.id}
                                        onGenerateRequest={async () => {
                                            return await generateAdvancedPractice({
                                                user_id: userId,
                                                level_id: selectedLevel.id,
                                                count: 5,
                                                difficulty: 'adaptive'
                                            })
                                        }}
                                    />
                                </Suspense>
                            </LazyErrorBoundary>
                        )}
                    </div>
                ) : null}
            </div>
        </div>
    )
}

export default App
