const LEADERBOARD_TITLE = 'Vendi yt në renditje'

interface AppHeaderProps {
	userStats: {
		experience: number
		nextLevelExp: number
		level: number
		totalPoints: number
		streakDays: number
	}
	selectedClass: unknown
	selectedCourse: unknown
	onBackToClasses: () => void
	onBackToCourses: () => void
	onLogout: () => void
	onShowProfile: () => void
	onShowLeaderboard: () => void
	onShowLevelInfo: () => void
}

export function AppHeader({
	userStats,
	selectedClass,
	selectedCourse,
	onBackToClasses,
	onBackToCourses,
	onLogout,
	onShowProfile,
	onShowLeaderboard,
	onShowLevelInfo,
}: AppHeaderProps) {
	const progress = userStats.nextLevelExp
		? Math.min(100, Math.max(0, (userStats.experience / userStats.nextLevelExp) * 100))
		: 0

	return (
		<header className="header">
			<div className="header-content">
				<div className="header-main">
					<div className="header-logo">
						<span className="header-emoji">🇦🇱</span>
						<h1>AlbLingo</h1>
					</div>
					<nav className="header-navigation" aria-label="Navigimi kryesor">
						<button
							className={`nav-btn ${!selectedClass ? 'active' : ''}`}
							onClick={onBackToClasses}
						>
							🏠 Shtëpia
						</button>
						{selectedClass && (
							<button className="nav-btn" onClick={onBackToClasses}>
								← Kthehu te Klasat
							</button>
						)}
						{selectedCourse && (
							<button className="nav-btn" onClick={onBackToCourses}>
								← Kthehu te Kurset
							</button>
						)}
					</nav>
				</div>

				<div className="header-account">
					<div className="header-progress-summary">
						<div
							className="user-progress"
							role="progressbar"
							aria-label="Progresi drejt nivelit tjetër"
							aria-valuemin={0}
							aria-valuemax={100}
							aria-valuenow={Math.round(progress)}
						>
							<div className="user-progress-fill" style={{ width: `${progress}%` }} />
						</div>

						<div className="user-stats">
							<button
								type="button"
								className="stat-item clickable-stat"
								onClick={onShowLevelInfo}
								title="Kliko për detaje"
							>
								<span className="stat-icon">⭐</span>
								<span className="stat-value">Niveli {userStats.level}</span>
							</button>
							<div className="stat-item">
								<span className="stat-icon">🏆</span>
								<span className="stat-value">{userStats.totalPoints} pikë</span>
							</div>
							<div className="stat-item">
								<span className="stat-icon">🔥</span>
								<span className="stat-value">{userStats.streakDays} ditë</span>
							</div>
						</div>
					</div>

					<div className="header-actions">
						<button className="profile-btn" onClick={onShowProfile}>👤 Profili</button>
						<button
							className="leaderboard-btn"
							onClick={onShowLeaderboard}
							title={LEADERBOARD_TITLE}
						>
							🏆 {LEADERBOARD_TITLE}
						</button>
						<button className="logout-btn" onClick={onLogout}>Dil</button>
					</div>
				</div>
			</div>
		</header>
	)
}

export function AppFooter() {
	return (
		<footer className="footer">
			<div className="footer-content">
				<div className="footer-section">
					<h4>🇦🇱 AlbLingo</h4>
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
