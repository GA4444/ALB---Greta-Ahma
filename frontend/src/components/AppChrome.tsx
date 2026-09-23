import BrandLogo from './BrandLogo'
import { IconBook, IconFlame, IconStar, IconTrophy } from './ProgressIcons'

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
	curriculumLabel?: string | null
	onBackToClasses: () => void
	onBackToCourses: () => void
	onLogout: () => void
	onShowProfile: () => void
	onShowLeaderboard: () => void
	onShowLevelInfo: () => void
	profileOpen?: boolean
	leaderboardOpen?: boolean
}

export function AppHeader({
	userStats,
	selectedClass,
	selectedCourse,
	curriculumLabel,
	onBackToClasses,
	onBackToCourses,
	onLogout,
	onShowProfile,
	onShowLeaderboard,
	onShowLevelInfo,
	profileOpen = false,
	leaderboardOpen = false,
}: AppHeaderProps) {
	const progress = userStats.nextLevelExp
		? Math.min(100, Math.max(0, (userStats.experience / userStats.nextLevelExp) * 100))
		: 0

	return (
		<>
			<header className="header app-chrome-header">
				<div className="header-content">
					<div className="header-main">
						<div className="header-logo brand-mark">
							<BrandLogo size={28} className="brand-logo-sm" decorative />
							<h1>AlbLingo</h1>
						</div>
						<nav className="header-navigation" aria-label="Navigimi kryesor">
							<button
								type="button"
								className={`nav-btn nav-btn-home ${!selectedClass ? 'active' : ''}`}
								onClick={onBackToClasses}
							>
								Shtëpia
							</button>
							{selectedClass && (
								<button type="button" className="nav-btn" onClick={onBackToClasses}>
									← Kthehu te Klasat
								</button>
							)}
							{selectedCourse && (
								<button type="button" className="nav-btn" onClick={onBackToCourses}>
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
								aria-label="Progresi yt"
								aria-valuemin={0}
								aria-valuemax={100}
								aria-valuenow={Math.round(progress)}
							>
								<div className="user-progress-fill" style={{ width: `${progress}%` }} />
							</div>

							<div className="user-stats">
								{curriculumLabel && (
									<div className="stat-item curriculum-stat" title="Ku je tani">
										<span className="stat-icon" aria-hidden="true"><IconBook size={14} /></span>
										<span className="stat-value">{curriculumLabel}</span>
									</div>
								)}
								<button
									type="button"
									className="stat-item clickable-stat"
									onClick={onShowLevelInfo}
									title="Pikët e tua"
								>
									<span className="stat-icon" aria-hidden="true"><IconStar size={14} /></span>
									<span className="stat-value">XP {userStats.level}</span>
								</button>
								<div className="stat-item">
									<span className="stat-icon" aria-hidden="true"><IconTrophy size={14} /></span>
									<span className="stat-value">{userStats.totalPoints} pikë</span>
								</div>
								<div className="stat-item">
									<span className="stat-icon" aria-hidden="true"><IconFlame size={14} /></span>
									<span className="stat-value">{userStats.streakDays} ditë</span>
								</div>
							</div>
						</div>

						<div className="header-actions" role="group" aria-label="Llogaria">
							<button type="button" className="profile-btn" onClick={onShowProfile}>Unë</button>
							<button
								type="button"
								className="leaderboard-btn"
								onClick={onShowLeaderboard}
								title={LEADERBOARD_TITLE}
							>
								{LEADERBOARD_TITLE}
							</button>
							<button type="button" className="logout-btn" onClick={onLogout}>Dil</button>
						</div>
					</div>
				</div>

				{/* Compact mobile top strip — fills header width beside logo on phones */}
				<div className="mobile-top-strip" aria-label="Progresi">
					<div className="mobile-top-strip-row">
						<button type="button" className="mobile-top-chip" onClick={onShowLevelInfo} title="Niveli">
							<span className="mobile-top-chip-icon" aria-hidden="true"><IconStar /></span>
							<strong>{userStats.level}</strong>
						</button>
						<div className="mobile-top-chip" title="Pikët">
							<span className="mobile-top-chip-icon" aria-hidden="true"><IconTrophy /></span>
							<strong>{userStats.totalPoints}</strong>
						</div>
						<div className="mobile-top-chip" title="Seria">
							<span className="mobile-top-chip-icon" aria-hidden="true"><IconFlame /></span>
							<strong>{userStats.streakDays}</strong>
						</div>
					</div>
					{curriculumLabel && (
						<div className="mobile-top-chip mobile-top-chip-wide">
							<span className="mobile-top-chip-icon" aria-hidden="true"><IconBook /></span>
							<strong>{curriculumLabel}</strong>
						</div>
					)}
				</div>
			</header>

			<nav className="mobile-bottom-nav" aria-label="Navigimi i telefonit">
				<button
					type="button"
					className={`mobile-tab ${!selectedClass ? 'active' : ''}`}
					onClick={onBackToClasses}
				>
					<span className="mobile-tab-icon" aria-hidden="true">
						<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
							<path d="M3 10.5 12 3l9 7.5" />
							<path d="M5 9.5V21h14V9.5" />
							<path d="M9 21v-7h6v7" />
						</svg>
					</span>
					<span className="mobile-tab-label">Shtëpia</span>
				</button>
				<button
					type="button"
					className={`mobile-tab ${leaderboardOpen ? 'active' : ''}`}
					onClick={onShowLeaderboard}
				>
					<span className="mobile-tab-icon" aria-hidden="true">
						<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
							<path d="M8 21h8" />
							<path d="M12 17v4" />
							<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" />
							<path d="M7 6H4a2 2 0 0 0 2 4" />
							<path d="M17 6h3a2 2 0 0 1-2 4" />
						</svg>
					</span>
					<span className="mobile-tab-label">Renditja</span>
				</button>
				<button
					type="button"
					className={`mobile-tab ${profileOpen ? 'active' : ''}`}
					onClick={onShowProfile}
				>
					<span className="mobile-tab-icon" aria-hidden="true">
						<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
							<circle cx="12" cy="8" r="4" />
							<path d="M4 21a8 8 0 0 1 16 0" />
						</svg>
					</span>
					<span className="mobile-tab-label">Unë</span>
				</button>
				<button
					type="button"
					className="mobile-tab"
					onClick={onLogout}
				>
					<span className="mobile-tab-icon" aria-hidden="true">
						<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
							<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
							<path d="M16 17l5-5-5-5" />
							<path d="M21 12H9" />
						</svg>
					</span>
					<span className="mobile-tab-label">Dil</span>
				</button>
			</nav>
		</>
	)
}

export function AppFooter() {
	return (
		<footer className="footer">
			<div className="footer-shell">
				<div className="footer-content">
					<div className="footer-section footer-section--brand">
						<div className="footer-brand">
							<BrandLogo size={36} className="brand-logo-sm" decorative />
							<h4>AlbLingo</h4>
						</div>
						<p className="footer-tagline">
							Platforma e mësimit të gjuhës shqipe për fëmijë
						</p>
					</div>
					<div className="footer-section">
						<h4>Burimet</h4>
						<ul>
							<li>Klasat</li>
							<li>Kurset</li>
							<li>Ushtrimet</li>
							<li>AI Insights</li>
						</ul>
					</div>
					<div className="footer-section">
						<h4>Objektivat</h4>
						<ul>
							<li>Mësimi i gjuhës</li>
							<li>Përmirësimi i shkrimit</li>
							<li>Rritja e fjalorit</li>
							<li>Gramatika e saktë</li>
						</ul>
					</div>
					<div className="footer-section footer-section--contact">
						<h4>Kontakti</h4>
						<div className="footer-contact">
							<p>info@alblingo.al</p>
							<p>+355 XX XXX XXX</p>
						</div>
					</div>
				</div>
				<div className="footer-bottom">
					<p>&copy; 2025 AlbLingo. Të gjitha të drejtat e rezervuara.</p>
				</div>
			</div>
		</footer>
	)
}
