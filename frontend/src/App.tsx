// Updated: 2026-01-05 18:21 - Fixed cls.courses iteration bug
import { useState, useEffect } from 'react'
import type { ChangeEvent } from 'react'
import type { CourseOut, LevelOut, ExerciseOut, ProgressOut, ClassData, AIPracticeExercise, AICoachResponse, UserAchievementsResponse, StreakData, DailyChallenge, SRSStatsResponse } from './api'
import { getClasses, getClassCourses, getCourseLevels, getLevelExercises, submitAnswer, fetchUserOverview, login, register, getAIRecommendations, getAdaptiveDifficulty, getLearningPath, getProgressInsights, getLeaderboard, getUserRank, getPublicStats, fetchAIPersonalizedPractice, fetchAICoach, analyzeOCR, getUserAchievements, getUserStreak, getDailyChallenge, getSRSStats, getUserProfile, updateUserProfile, type LeaderboardEntry, generateAdvancedPractice, browseCorpus, browseCorpusDocument, generatePedagogicalFeedback, getAdaptiveNextItem } from './api'
import type { CorpusDocument } from './api'
import AdminDashboard from './AdminDashboard'
import AdvancedAIPractice from './AdvancedAIPractice'
import ChatbotFloating from './ChatbotFloating'
import './App.css'
import './mobile-refinements.css'

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

function App() {
    // Authentication state - clear invalid values
    const [userId, setUserId] = useState<string | null>(() => {
        try {
            const stored = localStorage.getItem('user_id')
            if (stored && stored !== 'null' && stored !== 'undefined' && stored.trim() !== '') {
                return stored
            }
            return null
        } catch (error) {
            console.error('Error reading userId from localStorage:', error)
            return null
        }
    })
    const [isAdmin, setIsAdmin] = useState<boolean>(() => {
        try {
            return localStorage.getItem('is_admin') === 'true'
        } catch (error) {
            return false
        }
    })
    const [auth, setAuth] = useState({ username: '', password: '' })
    
    // Clear invalid userId from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem('user_id')
            if (stored && (stored === 'null' || stored === 'undefined' || stored.trim() === '')) {
                localStorage.removeItem('user_id')
                localStorage.removeItem('is_admin')
                localStorage.removeItem('username')
                setUserId(null)
                setIsAdmin(false)
            }
        } catch (error) {
            console.error('Error clearing localStorage:', error)
        }
    }, [])

    // Data state
    const [classes, setClasses] = useState<ClassData[]>([])
    const [selectedClass, setSelectedClass] = useState<ClassData | null>(null)
    const [selectedCourse, setSelectedCourse] = useState<CourseOut | null>(null)
    const [selectedLevel, setSelectedLevel] = useState<LevelOut | null>(null)
    const [exercises, setExercises] = useState<ExerciseOut[]>([])
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0)
    
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
    const [showAuth, setShowAuth] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

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
        email: '',
        age: '',
        date_of_birth: '',
        address: '',
        phone_number: ''
    })
    const [profileLoading, setProfileLoading] = useState(false)
    const [profileError, setProfileError] = useState<string | null>(null)

    // Enhanced user registration state
    const [registrationData, setRegistrationData] = useState({
        username: '',
        email: '',
        age: '',
        password: '',
        confirmPassword: ''
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
            }, 500) // 500ms delay

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
            }, 1000) // 1s delay

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
    const CACHE_DURATION = 30000 // 30 seconds

    const fetchClasses = async (forceRefresh = false) => {
        // Return cached data if available and not expired
        if (!forceRefresh && classesCache && (Date.now() - classesCache.timestamp < CACHE_DURATION)) {
            console.log('[Cache] Using cached classes data')
            setClasses(classesCache.data)
            setIsLoading(false)
            return
        }

        try {
            console.log('[Fetch] Fetching classes from API')
            const classesData = await getClasses(userId || undefined)
            setClasses(classesData)
            
            // Update cache immediately with basic class data
            setClassesCache({ data: classesData, timestamp: Date.now() })
            
            // Load levels for all classes in background (lazy)
            // This is done with lower priority to not block the UI
            setTimeout(() => {
                Promise.all(
                    classesData.map(async (classData: ClassData) => {
                        try {
                            const courses = await getClassCourses(classData.id, userId || '1')
                            const coursesWithLevels = await Promise.all(
                                courses.map(async (course: CourseOut) => {
                                    try {
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
                    setClassesCache({ data: classesWithLevels, timestamp: Date.now() })
                }).catch(error => {
                    console.error('Error loading levels for classes:', error)
                })
            }, 100) // Small delay to prioritize main UI
            
            setIsLoading(false)
        } catch (error) {
            console.error('Error fetching classes:', error)
            setIsLoading(false)
        }
    }

    const fetchUserStats = async () => {
        if (userId) {
            try {
                const overview = await fetchUserOverview(userId)
                if (overview) {
                    setUserStats({
                        totalPoints: overview.total_points,
                        totalStars: overview.total_stars,
                        streakDays: Math.floor(overview.total_points / 50), // Calculate streak based on points
                        level: Math.floor(overview.total_points / 100) + 1,
                        experience: overview.total_points % 100,
                        nextLevelExp: 100
                    })
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
        
        try {
            // Fetch courses for this class
            const coursesData = await getClassCourses(classData.id, userId!)
            setClassCourses(coursesData)
            
            // Load levels for all courses in this class to enable global numbering
            const coursesWithLevels = await Promise.all(
                coursesData.map(async (course: CourseOut) => {
                    try {
                        const levels = await getCourseLevels(course.id)
                        return { ...course, levels }
                    } catch (error) {
                        console.error(`Error fetching levels for course ${course.id}:`, error)
                        return { ...course, levels: [] }
                    }
                })
            )
            
            // Update classCourses with levels
            setClassCourses(coursesWithLevels)
            
            // Also update the classes array to include levels for this class
            setClasses(prevClasses => prevClasses.map(cls => {
                if (cls.id === classData.id) {
                    return { ...cls, courses: coursesWithLevels }
                }
                return cls
            }))
        } catch (error) {
            console.error('Error fetching class courses:', error)
            setClassCourses([])
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
            // Fetch levels for this course
            const levelsData = await getCourseLevels(course.id)
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
        if (!selectedLevel || !exercises[currentExerciseIndex]) return

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
            // Trim the answer to remove any leading/trailing whitespace
            const trimmedAnswer = answer.trim()
            console.log('[DEBUG] Submitting answer:', {
                exerciseId: exercises[currentIndex].id,
                userId: userId,
                response: trimmedAnswer
            })
            
            const result = await submitAnswer(exercises[currentIndex].id, { user_id: userId!, response: trimmedAnswer })
            
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
                        setMessage('🎉 Kurs i përfunduar! Zgjidhni kursin që dëshironi! 🚀')
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
                        setMessage('Urime! Ju keni përfunduar të gjitha ushtrimet! Kthehu tek kurset për të vazhduar! 🏆🎉')
                        setSelectedLevel(null)
                        setSelectedCourse(null)
                        setExercises([])
                        setCurrentExerciseIndex(0)
                        // Refresh classes after level is completed
                        if (userId) {
                            fetchClasses()
                        }
                    }
                }, 1500) // Wait 1.5 seconds before moving to next question
            } else {
                console.log('[DEBUG] Incorrect answer')
                setMessage(`Përgjigja e pasaktë. Provo përsëri! 💪`)
                const correctAnswer = result.correct_answer || inferExerciseAnswer(currentExercises[currentIndex])
                if (correctAnswer) {
                    try {
                        const feedback = await generatePedagogicalFeedback({
                            student_answer: trimmedAnswer,
                            correct_answer: correctAnswer,
                            grade: selectedClass?.order_index || 3,
                        })
                        setChildFeedback(feedback)
                    } catch (feedbackError) {
                        console.error('Child feedback error:', feedbackError)
                        setChildFeedback(null)
                    }
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

    // If not logged in, show authentication
    const shouldShowAuth = !userId || userId === 'null' || userId === 'undefined' || (typeof userId === 'string' && userId.trim() === '')
    
    // Always show auth form if no valid userId
    if (shouldShowAuth) {
        return (
            <div className="app" style={{ minHeight: '100vh', width: '100%', position: 'relative', backgroundColor: '#f0f0f0' }}>
                <div className="auth-container" style={{ display: 'flex', minHeight: '100vh', width: '100%', position: 'fixed', top: 0, left: 0, zIndex: 9999, backgroundColor: 'transparent' }}>
                    <div className="auth-card" style={{ display: 'block', visibility: 'visible', opacity: 1, position: 'relative', zIndex: 10, backgroundColor: 'white', padding: '2rem', borderRadius: '1rem', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                        <div className="auth-header">
                            <div className="auth-logo">🇦🇱</div>
                            <h2>Mirësevini në AlbLingo!</h2>
                            <p>Fillo udhëtimin tënd për të mësuar drejtshkrimin e gjuhës shqipe</p>
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
                                    placeholder="Përdoruesi"
                                    value={auth.username}
                                    onChange={(e) => setAuth({ ...auth, username: e.target.value })}
                                />
                                <input
                                    className="auth-input"
                                    placeholder="Fjalëkalimi"
                                    type="password"
                                    value={auth.password}
                                    onChange={(e) => setAuth({ ...auth, password: e.target.value })}
                                />

                                <button
                                    className="auth-submit"
                                    onClick={async () => {
                                        const username = auth.username?.trim()
                                        const password = auth.password
                                        if (!username || !password) {
                                            setMessage('Plotëso përdoruesin dhe fjalëkalimin! ❌')
                                            return
                                        }
                                        try {
                                            setMessage('Duke u lidhur... 🔄')
                                            const res = await login(username, password)
                                            setUserId(String(res.user_id))
                                            setIsAdmin(res.is_admin || false)
                                            setMessage('Mirësevini! 👋')
                                            localStorage.setItem('username', res.username)
                                            localStorage.setItem('user_id', String(res.user_id))
                                            localStorage.setItem('is_admin', String(res.is_admin || false))
                                        } catch (e: any) {
                                            const status = e?.response?.status
                                            const detail = e?.response?.data?.detail || e?.message
                                            if (status === 401) {
                                                setMessage('Kredencialet e pasakta. Provo përsëri! ❌')
                                            } else if (e?.code === 'ECONNREFUSED' || e?.code === 'ECONNABORTED' || e?.message?.includes('timeout') || e?.message?.includes('Network') || !e?.response) {
                                                setMessage('Serveri po zgjohet (mund të zgjasë deri në 1 minutë). Të lutem prit pak dhe provo përsëri. ⏳')
                                            } else {
                                                setMessage(detail || 'Gabim në lidhje. Provo përsëri! ❌')
                                            }
                                        }
                                    }}
                                >
                                    Hyr
                                </button>
                            </div>
                        ) : (
                            // Enhanced Registration Form
                            <div className="auth-form enhanced-registration">
                                <div className="form-row single-column">
                                    <input
                                        className="auth-input"
                                        placeholder="Përdoruesi *"
                                        value={registrationData.username}
                                        onChange={(e) => setRegistrationData({...registrationData, username: e.target.value})}
                                    />
                                </div>

                                <div className="form-row single-column">
                                    <input
                                        className="auth-input"
                                        type="email"
                                        placeholder="Email *"
                                        value={registrationData.email}
                                        onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                                    />
                                </div>

                                <div className="form-row single-column">
                                    <input
                                        className="auth-input"
                                        type="number"
                                        placeholder="Mosha (opsionale)"
                                        value={registrationData.age}
                                        onChange={(e) => setRegistrationData({...registrationData, age: e.target.value})}
                                    />
                                </div>

                                <div className="form-row single-column">
                                    <input
                                        className="auth-input"
                                        type="password"
                                        placeholder="Fjalëkalimi *"
                                        value={registrationData.password}
                                        onChange={(e) => setRegistrationData({...registrationData, password: e.target.value})}
                                    />
                                </div>

                                <div className="form-row single-column">
                                    <input
                                        className="auth-input"
                                        type="password"
                                        placeholder="Konfirmo fjalëkalimin *"
                                        value={registrationData.confirmPassword}
                                        onChange={(e) => setRegistrationData({...registrationData, confirmPassword: e.target.value})}
                                    />
                                </div>

                                <button
                                    className="auth-submit"
                                    onClick={async () => {
                                        if (registrationData.password !== registrationData.confirmPassword) {
                                            setMessage('Fjalëkalimet nuk përputhen! ❌')
                                            return
                                        }
                                        
                                        try {
                                            await register(
                                                registrationData.username,
                                                registrationData.email,
                                                registrationData.password,
                                                registrationData.age ? parseInt(registrationData.age) : undefined
                                            )
                                            setMessage('Regjistrimi u krye me sukses! Tani mund të hyni. ✅')
                                            setShowAuth(false)
                                            setRegistrationData({
                                                username: '',
                                                email: '',
                                                age: '',
                                                password: '',
                                                confirmPassword: ''
                                            })
                                        } catch (e: any) {
                                            setMessage('Gabim në regjistrim. Provo përsëri! ❌')
                                        }
                                    }}
                                >
                                    Regjistrohu
                                </button>
                            </div>
                        )}
                        {message && <div className="message">{message}</div>}
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
                    <AdminDashboard 
                        userId={adminUserId} 
                        onLogout={() => {
                            setUserId(null)
                            setIsAdmin(false)
                            localStorage.removeItem('user_id')
                            localStorage.removeItem('is_admin')
                            localStorage.removeItem('username')
                        }}
                    />
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
            <Header
                userStats={userStats}
                selectedClass={selectedClass}
                selectedCourse={selectedCourse}
                onBackToClasses={() => handleClassClick(null)}
                onBackToCourses={() => handleCourseClick(null)}
                onLogout={handleLogout}
                onShowProfile={handleShowProfile}
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
            <ChatbotFloating
                userId={userId || undefined}
                context={selectedLevel ? {
                    current_level: selectedLevel.name,
                    current_exercise: exercises[currentExerciseIndex]?.prompt,
                } : undefined}
            />

                {showProfile && (
                    <div className="profile-overlay" onClick={() => setShowProfile(false)}>
                        <div className="profile-card enhanced-profile-card" onClick={(e) => e.stopPropagation()}>
                            <div className="profile-header">
                                <div className="profile-title">👤 Profili im</div>
                                <button className="profile-close" onClick={() => setShowProfile(false)}>×</button>
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
                                                    {userProfile?.username?.charAt(0).toUpperCase() || '👤'}
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
                                        <h2 className="profile-username">{userProfile?.username || localStorage.getItem('username') || 'Përdorues'}</h2>
                                        <p className="profile-email">{userProfile?.email || 'Nuk është vendosur email'}</p>
                                    </div>
                                </div>

                                {/* Personal Information */}
                                <div className="profile-section-enhanced">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                        <h3 className="profile-section-title">📋 Informacione Personale</h3>
                                        {!isEditingProfile ? (
                                            <button 
                                                className="profile-edit-btn"
                                                onClick={() => setIsEditingProfile(true)}
                                                style={{ 
                                                    padding: '0.5rem 1rem', 
                                                    background: 'var(--color-primary)', 
                                                    color: 'white', 
                                                    border: 'none', 
                                                    borderRadius: '8px', 
                                                    cursor: 'pointer',
                                                    fontSize: '0.9rem'
                                                }}
                                            >
                                                ✏️ Edito
                                            </button>
                                        ) : (
                                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                <button 
                                                    className="profile-save-btn"
                                                    onClick={handleSaveProfile}
                                                    disabled={profileLoading}
                                                    style={{ 
                                                        padding: '0.5rem 1rem', 
                                                        background: 'var(--color-success)', 
                                                        color: 'white', 
                                                        border: 'none', 
                                                        borderRadius: '8px', 
                                                        cursor: profileLoading ? 'not-allowed' : 'pointer',
                                                        fontSize: '0.9rem',
                                                        opacity: profileLoading ? 0.6 : 1
                                                    }}
                                                >
                                                    {profileLoading ? 'Duke ruajtur...' : '💾 Ruaj'}
                                                </button>
                                                <button 
                                                    className="profile-cancel-btn"
                                                    onClick={() => {
                                                        setIsEditingProfile(false)
                                                        setProfileError(null)
                                                        if (userProfile) {
                                                            setProfileFormData({
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
                                                    style={{ 
                                                        padding: '0.5rem 1rem', 
                                                        background: 'var(--color-accent)', 
                                                        color: 'white', 
                                                        border: 'none', 
                                                        borderRadius: '8px', 
                                                        cursor: 'pointer',
                                                        fontSize: '0.9rem'
                                                    }}
                                                >
                                                    ❌ Anulo
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                    {profileError && (
                                        <div style={{ 
                                            padding: '0.75rem', 
                                            background: '#fee', 
                                            color: '#c33', 
                                            borderRadius: '8px', 
                                            marginBottom: '1rem',
                                            fontSize: '0.9rem'
                                        }}>
                                            {profileError}
                                        </div>
                                    )}
                                    <div className="profile-info-grid">
                                        <div className="profile-info-item">
                                            <span className="info-label">👤 Emri i përdoruesit:</span>
                                            <span className="info-value">{userProfile?.username || localStorage.getItem('username') || 'N/A'}</span>
                                        </div>
                                        <div className="profile-info-item">
                                            <span className="info-label">📧 Email:</span>
                                            {isEditingProfile ? (
                                                <input
                                                    type="email"
                                                    value={profileFormData.email}
                                                    onChange={(e) => setProfileFormData({ ...profileFormData, email: e.target.value })}
                                                    style={{
                                                        padding: '0.5rem',
                                                        border: '1px solid #ddd',
                                                        borderRadius: '6px',
                                                        fontSize: '0.95rem',
                                                        width: '100%',
                                                        maxWidth: '300px'
                                                    }}
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
                                                    style={{
                                                        padding: '0.5rem',
                                                        border: '1px solid #ddd',
                                                        borderRadius: '6px',
                                                        fontSize: '0.95rem',
                                                        width: '100%',
                                                        maxWidth: '100px'
                                                    }}
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
                                                    style={{
                                                        padding: '0.5rem',
                                                        border: '1px solid #ddd',
                                                        borderRadius: '6px',
                                                        fontSize: '0.95rem',
                                                        width: '100%',
                                                        maxWidth: '200px'
                                                    }}
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
                                                    style={{
                                                        padding: '0.5rem',
                                                        border: '1px solid #ddd',
                                                        borderRadius: '6px',
                                                        fontSize: '0.95rem',
                                                        width: '100%',
                                                        maxWidth: '300px'
                                                    }}
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
                                                    style={{
                                                        padding: '0.5rem',
                                                        border: '1px solid #ddd',
                                                        borderRadius: '6px',
                                                        fontSize: '0.95rem',
                                                        width: '100%',
                                                        maxWidth: '200px'
                                                    }}
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
                                            <div className="stat-icon-large">⭐</div>
                                            <div className="stat-content">
                                                <div className="stat-label">Niveli</div>
                                                <div className="stat-value-large">{userStats.level}</div>
                                            </div>
                                        </div>
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large">🏆</div>
                                            <div className="stat-content">
                                                <div className="stat-label">Pikë Totale</div>
                                                <div className="stat-value-large">{userStats.totalPoints.toLocaleString()}</div>
                                            </div>
                                        </div>
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large">🔥</div>
                                            <div className="stat-content">
                                                <div className="stat-label">Varg Ditësh</div>
                                                <div className="stat-value-large">{userStats.streakDays}</div>
                                            </div>
                                        </div>
                                        <div className="profile-stat-card">
                                            <div className="stat-icon-large">💫</div>
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
                                            <div className="profile-stat-card" style={{ background: 'var(--bg-tertiary)' }}>
                                                <div className="stat-icon-large">🔥</div>
                                                <div className="stat-content">
                                                    <div className="stat-label">Vargu Aktual</div>
                                                    <div className="stat-value-large">{userStreak.current_streak}</div>
                                                    <div className="stat-sub-label">ditë</div>
                                                </div>
                                            </div>
                                            <div className="profile-stat-card" style={{ background: 'var(--bg-tertiary)' }}>
                                                <div className="stat-icon-large">⭐</div>
                                                <div className="stat-content">
                                                    <div className="stat-label">Vargu Më i Gjatë</div>
                                                    <div className="stat-value-large">{userStreak.longest_streak}</div>
                                                    <div className="stat-sub-label">ditë</div>
                                                </div>
                                            </div>
                                            {userStreak.last_activity_date && (
                                                <div className="profile-stat-card" style={{ background: 'var(--bg-tertiary)' }}>
                                                    <div className="stat-icon-large">📅</div>
                                                    <div className="stat-content">
                                                        <div className="stat-label">Aktiviteti i Fundit</div>
                                                        <div className="stat-value-large" style={{ fontSize: '1rem' }}>
                                                            {new Date(userStreak.last_activity_date).toLocaleDateString('sq-AL')}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        {userStreak.current_streak > 0 && (
                                            <div style={{ 
                                                marginTop: '1rem', 
                                                padding: '1rem', 
                                                background: 'var(--bg-tertiary)', 
                                                borderRadius: '12px',
                                                textAlign: 'center'
                                            }}>
                                                <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
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
                        <div className="profile-card leaderboard-card" onClick={(e) => e.stopPropagation()}>
                            <div className="profile-header">
                                <div className="profile-title">🏆 Pozita jote në tabelën e kampionëve</div>
                                <button className="profile-close" onClick={() => setShowLeaderboard(false)}>×</button>
                            </div>
                            <div className="leaderboard-content">
                                {userRank && (
                                    <div className="user-rank-badge">
                                        <div className="rank-info">
                                            <span className="rank-label">Renditja juaj:</span>
                                            <span className="rank-value">#{userRank.rank}</span>
                                        </div>
                                        <div className="rank-stats">
                                            <span>Nga {userRank.total_users} përdorues</span>
                                            <span>•</span>
                                            <span>Top {userRank.percentile}%</span>
                                        </div>
                                    </div>
                                )}
                                <div className="leaderboard-table">
                                    <div className="leaderboard-header">
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
                                            return (
                                                <div 
                                                    key={entry.user_id} 
                                                    className={`leaderboard-row ${isCurrentUser ? 'current-user' : ''}`}
                                                >
                                                    <div className="lb-col rank-col">
                                                        {entry.rank === 1 && '🥇'}
                                                        {entry.rank === 2 && '🥈'}
                                                        {entry.rank === 3 && '🥉'}
                                                        {entry.rank > 3 && `#${entry.rank}`}
                                                    </div>
                                                    <div className="lb-col user-col">
                                                        <strong>{entry.username}</strong>
                                                        {isCurrentUser && <span className="you-badge">Ti</span>}
                                                    </div>
                                                    <div className="lb-col points-col">{entry.total_points.toLocaleString()}</div>
                                                    <div className="lb-col level-col">⭐ {entry.level}</div>
                                                    <div className="lb-col accuracy-col">{entry.accuracy.toFixed(1)}%</div>
                                                    <div className="lb-col courses-col">{entry.completed_courses}</div>
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
                        <div className="profile-card level-info-card" onClick={(e) => e.stopPropagation()}>
                            <div className="profile-header">
                                <div className="profile-title">⭐ Informacion i Nivelit</div>
                                <button className="profile-close" onClick={() => setShowLevelInfo(false)}>×</button>
                            </div>
                            <div className="level-info-content">
                                <div className="level-summary">
                                    <div className="level-badge-large">
                                        <div className="level-number">{userStats.level}</div>
                                        <div className="level-label">Niveli Aktual</div>
                                    </div>
                                    <div className="level-stats-summary">
                                        <div className="stat-summary-item">
                                            <span className="stat-icon-large">🏆</span>
                                            <div>
                                                <div className="stat-value-large">{userStats.totalPoints}</div>
                                                <div className="stat-label-small">Pikë totale</div>
                                            </div>
                                        </div>
                                        <div className="stat-summary-item">
                                            <span className="stat-icon-large">📚</span>
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
                        <div className="profile-card corpus-browse-card" onClick={(e) => e.stopPropagation()}>
                            <div className="profile-header">
                                <div className="profile-title">📖 Korpusi i Drejtshkrimit</div>
                                <button className="profile-close" onClick={() => { setShowCorpusBrowse(false); setSelectedCorpusDoc(null) }}>×</button>
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
            <Footer />
            {message && <div className="message">{message}</div>}
        </div>
    )
}

// Header Component
function Header({ 
    userStats, 
    selectedClass, 
    selectedCourse, 
    onBackToClasses, 
    onBackToCourses, 
    onLogout,
    onShowProfile,
    onShowLeaderboard,
    onShowLevelInfo,
}: {
    userStats: any
    selectedClass: any
    selectedCourse: any
    onBackToClasses: () => void
    onBackToCourses: () => void
    onLogout: () => void
    onShowProfile: () => void
    onShowLeaderboard: () => void
    onShowLevelInfo: () => void
}) {
    return (
        <header className="header">
            <div className="header-content">
                <div className="header-main">
                    <div className="header-logo">
                        <span className="header-emoji">🇦🇱</span>
                        <h1>AlbLingo</h1>
                    </div>
                    <div className="header-navigation">
                        <button 
                            className={`nav-btn ${!selectedClass ? 'active' : ''}`}
                            onClick={onBackToClasses}
                        >
                            🏠 Shtëpia
                        </button>
                        {selectedClass && (
                            <button 
                                className="nav-btn"
                                onClick={onBackToClasses}
                            >
                                ← Kthehu te Klasat
                            </button>
                        )}
                        {selectedCourse && (
                            <button 
                                className="nav-btn"
                                onClick={onBackToCourses}
                            >
                                ← Kthehu te Kurset
                            </button>
                        )}
                    </div>
                </div>
                
                {/* User Progress Bar */}
                <div className="user-progress">
                    <div 
                        className="user-progress-fill" 
                        style={{ width: `${(userStats.experience / userStats.nextLevelExp) * 100}%` }}
                    ></div>
                </div>
                
                <div className="user-info">
                    <div className="user-stats">
                        <div className="stat-item clickable-stat" onClick={onShowLevelInfo} title="Kliko për detaje">
                            <span className="stat-icon">⭐</span>
                            <span className="stat-value">Niveli {userStats.level}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-icon">🏆</span>
                            <span className="stat-value">{userStats.totalPoints} pikë</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-icon">🔥</span>
                            <span className="stat-value">{userStats.streakDays} ditë</span>
                        </div>
                    </div>

                    <button className="profile-btn" onClick={onShowProfile}>
                        Profili
                    </button>

                    <button className="leaderboard-btn" onClick={onShowLeaderboard}>
                        🏆 Pozita jote në tabelën e kampionëve
                    </button>

                    <button className="logout-btn" onClick={onLogout}>
                        Dil
                    </button>
                </div>
            </div>
        </header>
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
    const classLabel = selectedClass ? `Klasa ${selectedClass.order_index || selectedClass.name}` : 'klasa jote'
    const levelLabel = selectedLevel ? `Niveli ${selectedLevel.order_index}` : 'niveli yt'
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
        if (currentExercise?.category === 'listen_write') return 'Shtyp “Dëgjo”, pastaj shkruaj atë që dëgjove...'
        if (currentExercise?.category === 'synonyms_antonyms') return 'Zgjidh një opsion ose shkruaj përgjigjen...'
        return 'Shkruani përgjigjen tuaj...'
    }
    
    return (
        <div className={`main-content ${selectedLevel ? 'with-ai-panel' : ''}`}>
            {/* Compact Left Sidebar - Navigation Only */}
            <aside className="sidebar sidebar-compact">
                <div className="sidebar-section">
                    <div className="sidebar-section-header compact">
                        <h3>📚 Klasat</h3>
                        <span className="classes-count-badge">{classes.length}</span>
                    </div>
                    <div className="class-list-compact">
                        {isLoading && classes.length === 0 ? (
                            <>
                                {[1, 2, 3].map((i) => (
                                    <div key={`skeleton-${i}`} className="skeleton-item-compact">
                                        <div className="skeleton" style={{width: '28px', height: '28px', borderRadius: '8px'}}></div>
                                        <div className="skeleton" style={{flex: 1, height: '16px'}}></div>
                                    </div>
                                ))}
                            </>
                        ) : classes.map((classData) => {
                            const progress = (classData as any).progress_percent || 0
                            const isSelected = selectedClass?.id === classData.id
                            return (
                                <div
                                    key={classData.id}
                                    className={`class-item-compact ${classData.unlocked ? 'unlocked' : 'locked'} ${isSelected ? 'selected' : ''}`}
                                    onClick={() => onClassClick(classData)}
                                >
                                    <div className="class-item-left">
                                        <span className={`class-num ${isSelected ? 'active' : ''}`}>
                                            {classData.order_index}
                                        </span>
                                        <span className="class-label">{classData.name}</span>
                                    </div>
                                    <div className="class-item-right">
                                        {classData.unlocked ? (
                                            <div className="progress-mini" title={`${Math.round(progress)}%`}>
                                                <div className="progress-mini-fill" style={{ width: `${progress}%` }}></div>
                                            </div>
                                        ) : (
                                            <span className="lock-mini">🔒</span>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* Compact AI Stats */}
                {userId && aiRecommendations && (
                    <div className="sidebar-section">
                        <div className="sidebar-section-header compact">
                            <h3>📊 Statistika AI</h3>
                            <button className="toggle-btn-compact" onClick={onToggleAIInsights}>
                                {showAIInsights ? '−' : '+'}
                            </button>
                        </div>
                        {showAIInsights && (
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
                    </div>
                )}

                {selectedLevel && currentExercise && (
                    <div className="sidebar-section child-ai-sidebar-section">
                        <div className="child-ai-side-card">
                            <div className="child-ai-side-header">
                                <span>🤖</span>
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

                {/* Compact Gamification */}
                {userId && userStreak && (
                    <div className="sidebar-section">
                        <div className="sidebar-section-header compact">
                            <h3>🏆 Progresi</h3>
                            <button className="toggle-btn-compact" onClick={() => setShowGamification(!showGamification)}>
                                {showGamification ? '−' : '+'}
                            </button>
                        </div>
                        <div className="gamification-compact">
                            <div className="streak-compact">
                                <span className="streak-fire">🔥</span>
                                <span className="streak-num">{userStreak.current_streak}</span>
                                <span className="streak-txt">ditë</span>
                            </div>
                            {showGamification && (
                                <>
                                    {dailyChallenge && dailyChallenge.user_progress && (
                                        <div className="challenge-compact">
                                            <div className="challenge-label">🎯 Sfida</div>
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
                                            <span>🏅 {userAchievements.total_achievements} arritje</span>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* OCR Container - positioned under sidebar-compact */}
                {!selectedClass && !selectedCourse && !selectedLevel && (
                    <section className="ocr-main-container ocr-left-positioned">
                    <div className="ocr-header">
                        <div>
                            <h3>📝 Kontrollo Diktimin Tënd!</h3>
                            <p className="ocr-subtitle">
                                Bëj një foto të diktimit tënd dhe ne do ta kontrollojmë së bashku! Do të shohim nëse ka gabime dhe do të mësojmë si t'i rregullojmë. 🎯
                            </p>
                        </div>
                            {ocrLoading ? (
                                <div className="ocr-loading-header">
                                    <div className="ocr-spinner-small"></div>
                                    <span>Po kontrollojmë... ⏳</span>
                                </div>
                            ) : (
                                <button className="ocr-button" onClick={handleOCRSubmit}>
                                    🚀 Kontrollo Diktimin
                                </button>
                            )}
                    </div>

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
                )}
            </aside>

            {/* Main Content Area */}
            <div className="content-area">
                {isLoading ? (
                    <div className="loading">
                        <div className="loading-spinner"></div>
                        <div>Duke ngarkuar... ⏳</div>
                    </div>
                ) : !selectedClass ? (
                    <div className="welcome-screen-modern">
                        {/* Hero Section */}
                        <div className="hero-section-modern">
                            <div className="hero-content-modern">
                                <div className="hero-badge-modern">Platforma e Mësimit</div>
                                <div className="welcome-emoji-modern">🇦🇱</div>
                                <h1 className="hero-title-modern">Mirësevini në AlbLingo!</h1>
                                <p className="hero-description-modern">
                                    Platforma më e avancuar për mësimin e drejtshkrimit të gjuhës shqipe për fëmijë.
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
                                <h3 className="section-title-modern">🌟 Veçoritë e Platformës</h3>
                                <p className="section-subtitle-modern">Teknologji moderne për mësim efektiv</p>
                            </div>
                            
                            <div className="features-grid-modern">
                                <div className="feature-card-modern">
                                    <div className="feature-icon-wrapper">
                                        <div className="feature-icon-modern">🎧</div>
                                    </div>
                                    <h4 className="feature-title-modern">Audio Interaktiv</h4>
                                    <p className="feature-description-modern">Dëgjoni dhe përsëritni me cilësi të lartë audio</p>
                                </div>
                                <div className="feature-card-modern">
                                    <div className="feature-icon-wrapper">
                                        <div className="feature-icon-modern">📊</div>
                                    </div>
                                    <h4 className="feature-title-modern">Progres i Detajuar</h4>
                                    <p className="feature-description-modern">Ndiqni përparimin tuaj me statistika të hollësishme</p>
                                </div>
                                <div className="feature-card-modern">
                                    <div className="feature-icon-wrapper">
                                        <div className="feature-icon-modern">🏆</div>
                                    </div>
                                    <h4 className="feature-title-modern">Sistem Pikësh</h4>
                                    <p className="feature-description-modern">Fitoni pikë, yje dhe nivele për të qenë të motivuar</p>
                                </div>
                                <div className="feature-card-modern">
                                    <div className="feature-icon-wrapper">
                                        <div className="feature-icon-modern">🤖</div>
                                    </div>
                                    <h4 className="feature-title-modern">AI i Personalizuar</h4>
                                    <p className="feature-description-modern">Rekomandime inteligjente bazuar në progresin tuaj</p>
                                </div>
                                <div className="feature-card-modern">
                                    <div className="feature-icon-wrapper">
                                        <div className="feature-icon-modern">📈</div>
                                    </div>
                                    <h4 className="feature-title-modern">Pozita jote në tabelën e kampionëve</h4>
                                    <p className="feature-description-modern">Krahasoni rezultatet me përdorues të tjerë</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : !selectedCourse ? (
                    <div className="course-selection">
                        <div className="course-selection-header">
                            <button className="back-button-modern" onClick={() => onClassClick(null)}>
                                <span className="back-icon">←</span>
                                <span>Kthehu te Klasat</span>
                            </button>
                            <div className="class-header-info">
                                <div className="class-title-section">
                                    <div className="class-badge-large">{selectedClass.name}</div>
                                    <h2 className="class-title">{selectedClass.name} - Nivelet</h2>
                                    <p className="class-subtitle">Zgjidhni nivelin që dëshironi të filloni</p>
                                </div>
                                <div className="class-overall-progress">
                                    <div className="overall-progress-label">
                                        <span>Progresi i Përgjithshëm</span>
                                        <span className="progress-percentage">
                                            {classCourses.length > 0 
                                                ? Math.round((classCourses.filter(c => c.progress?.is_completed).length / classCourses.length) * 100)
                                                : 0}%
                                        </span>
                                    </div>
                                    <div className="overall-progress-bar">
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
                        </div>
                        
                        {/* Show courses for the selected class */}
                        <div className="course-preview-grid-modern">
                            {isLoading && classCourses.length === 0 ? (
                                // Skeleton loading for courses
                                <div className="skeleton-grid">
                                    {[1, 2, 3, 4, 5, 6].map((i) => (
                                        <div key={`skeleton-course-${i}`} className="skeleton-card">
                                            <div className="skeleton skeleton-circle" style={{width: '80px', height: '80px', margin: '0 auto 12px'}}></div>
                                            <div className="skeleton skeleton-title" style={{margin: '0 auto 12px'}}></div>
                                            <div className="skeleton skeleton-text medium" style={{margin: '0 auto 8px'}}></div>
                                            <div className="skeleton skeleton-button" style={{margin: '12px auto 0'}}></div>
                                        </div>
                                    ))}
                                </div>
                            ) : classCourses.map((course, index) => {
                                const progressPercent = course.progress 
                                    ? Math.min(100, (course.progress.completed_exercises / Math.max(1, course.progress.total_exercises)) * 100)
                                    : 0
                                const isCompleted = course.progress?.is_completed || false
                                
                                return (
                                    <div
                                        key={course.id}
                                        className={`course-card-modern ${course.enabled ? 'unlocked' : 'locked'} ${isCompleted ? 'completed' : ''}`}
                                        onClick={() => course.enabled && onCourseClick(course)}
                                    >
                                        <div className="course-card-header">
                                            <div className="course-number-badge">#{index + 1}</div>
                                            <div className="course-icon-wrapper">
                                                <div className="course-icon-modern">
                                                    {course.category === 'listen_write' && '🎧'}
                                                    {course.category === 'word_from_description' && '🧩'}
                                                    {course.category === 'synonyms_antonyms' && '🔁'}
                                                    {course.category === 'albanian_or_loanword' && '🇦🇱'}
                                                    {course.category === 'missing_letter' && '🔠'}
                                                    {course.category === 'wrong_letter' && '❌'}
                                                    {course.category === 'build_word' && '🧱'}
                                                    {course.category === 'number_to_word' && '🔢'}
                                                    {course.category === 'phrases' && '💬'}
                                                    {course.category === 'spelling_punctuation' && '📝'}
                                                    {course.category === 'abstract_concrete' && '🧠'}
                                                    {course.category === 'build_sentence' && '✍️'}
                                                    {course.category === 'vocabulary' && '📚'}
                                                    {course.category === 'spelling' && '✍️'}
                                                    {course.category === 'grammar' && '🔤'}
                                                    {course.category === 'numbers' && '🔢'}
                                                    {course.category === 'punctuation' && '📝'}
                                                </div>
                                                {isCompleted && (
                                                    <div className="completed-checkmark">✓</div>
                                                )}
                                            </div>
                                        </div>
                                        
                                        <div className="course-card-body">
                                            <h4 className="course-name-modern">{course.name}</h4>
                                            
                                            {course.progress && (
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
                                                            <span className="stat-icon-small">📝</span>
                                                            <span>{course.progress.completed_exercises}/{course.progress.total_exercises} ushtrime</span>
                                                        </div>
                                                        {course.progress.accuracy_percentage > 0 && (
                                                            <div className="progress-stat-item">
                                                                <span className="stat-icon-small">🎯</span>
                                                                <span>{course.progress.accuracy_percentage.toFixed(0)}% saktësi</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {!course.progress && course.enabled && (
                                                <div className="course-start-prompt">
                                                    <span className="start-icon">▶</span>
                                                    <span>Kliko për të filluar</span>
                                                </div>
                                            )}
                                        </div>
                                        
                                        <div className="course-card-footer">
                                            {isCompleted ? (
                                                <div className="status-badge completed-badge">
                                                    <span>🏆</span>
                                                    <span>I përfunduar</span>
                                                </div>
                                            ) : course.enabled ? (
                                                <div className="status-badge active-badge">
                                                    <span>✅</span>
                                                    <span>I hapur</span>
                                                </div>
                                            ) : (
                                                <div className="status-badge locked-badge">
                                                    <span>🔒</span>
                                                    <span>I mbyllur</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
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
                                    <p className="course-subtitle-modern">Zgjidhni nivelin për të filluar ushtrimet</p>
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
                                
                                // Format level name as "Niveli X Klasa Y" (each class starts from Niveli 1)
                                // Get class number with fallback
                                const classNumber = selectedClass 
                                    ? (selectedClass.order_index || classes.findIndex(c => c.id === selectedClass.id) + 1 || 1)
                                    : 1
                                const levelDisplayName = selectedClass
                                    ? `Niveli ${level.order_index} Klasa ${classNumber}`
                                    : level.name
                                return (
                                    <div
                                        key={level.id}
                                        className="level-card-modern"
                                        onClick={() => onLevelClick(level)}
                                    >
                                        <div className="level-card-header-modern">
                                            <div className="level-number-circle">{index + 1}</div>
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
                                                <span className="action-text">Kliko për të filluar →</span>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                ) : selectedLevel && exercises.length > 0 ? (
                    <div className="exercise-area-modern">
                        <div className="exercise-header-modern">
                            <button className="back-button-modern" onClick={() => onLevelClick(null)}>
                                <span className="back-icon">←</span>
                                <span>Kthehu te Nivelet</span>
                            </button>
                            <div className="exercise-title-section">
                                <div className="exercise-badge-modern">Ushtrimet</div>
                                <h2 className="exercise-title-modern">
                                    {selectedLevel && selectedClass && selectedCourse
                                        ? (() => {
                                            const classNumber = selectedClass.order_index || classes.findIndex(c => c.id === selectedClass.id) + 1 || 1
                                            return `Niveli ${selectedLevel.order_index} Klasa ${classNumber}`
                                          })()
                                        : selectedLevel?.name || 'Ushtrimet'
                                    }
                                </h2>
                                <p className="exercise-subtitle-modern">
                                    {selectedLevel.description ? selectedLevel.description : (() => {
                                        if (selectedLevel && selectedClass && selectedCourse) {
                                            const classNumber = selectedClass.order_index || classes.findIndex(c => c.id === selectedClass.id) + 1 || 1
                                            return `Përgjigjuni pyetjeve për të përfunduar Niveli ${selectedLevel.order_index} Klasa ${classNumber}`
                                        }
                                        return `Përgjigjuni pyetjeve për të përfunduar ${selectedLevel?.name || 'ushtrimet'}`
                                    })()}
                                </p>
                            </div>
                        </div>
                        
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
                                    <div className="exercise-number-badge-modern">
                                        #{currentExerciseIndex + 1}
                                    </div>
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
                                            // For Class 1, Level 3: first 5 are antonyms, rest are synonyms
                                            const isClass1 = selectedClass?.order_index === 1
                                            const isLevel3 = selectedLevel?.order_index === 3
                                            
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
                                                    className="voice-btn-modern primary"
                                                    onClick={() => playAudio(exercises[currentExerciseIndex].id)}
                                                >
                                                    <span className="voice-icon">🔊</span>
                                                    <span>Dëgjo</span>
                                                </button>
                                                <button
                                                    className="voice-btn-modern secondary"
                                                    onClick={() => startRecording()}
                                                    disabled={isRecording}
                                                >
                                                    <span className="voice-icon">🎤</span>
                                                    <span>{isRecording ? 'Duke regjistruar...' : 'Regjistro'}</span>
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {exercises[currentExerciseIndex].rule && (
                                        <div className="exercise-hint-modern">
                                            <div className="hint-icon">💡</div>
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
                                                        <p className="choices-label-modern">Zgjidhni fjalën e duhur:</p>
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
                                                <span>💡</span>
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
                                        className="submit-btn-modern"
                                        onClick={handleSubmitAnswer}
                                    >
                                        <span>Dërgo Përgjigjen</span>
                                        <span className="submit-icon">✓</span>
                                    </button>
                                    
                                    <div className="navigation-buttons-modern">
                                        <button
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
                        )}
                    </div>
                ) : null}
            </div>
        </div>
    )
}

// Footer Component
function Footer() {
    return (
        <footer className="footer">
            <div className="footer-content">
                <div className="footer-section">
                    <h4>🇦🇱AlbLingo</h4>
                    <p>Platforma e mësimit të gjuhës shqipe për fëmijë</p>
                </div>
                <div className="footer-section">
                    <h4>📚 Burimet</h4>
                    <ul>
                        <li>Klasat</li>
                        <li>Kurset</li>
                        <li>Ushtrimet</li>
                        <li>AI Insights</li>
                    </ul>
                </div>
                <div className="footer-section">
                    <h4>🎯 Objektivat</h4>
                    <ul>
                        <li>Mësimi i gjuhës</li>
                        <li>Përmirësimi i shkrimit</li>
                        <li>Rritja e fjalorit</li>
                        <li>Gramatika e saktë</li>
                    </ul>
                </div>
                <div className="footer-section">
                    <h4>📞 Kontakti</h4>
                    <p>info@alblingo.al</p>
                    <p>+355 XX XXX XXX</p>
                </div>
            </div>
            <div className="footer-bottom">
                <p>&copy; 2025 AlbLingo. Të gjitha të drejtat e rezervuara.</p>
            </div>
        </footer>
    )
}

export default App
