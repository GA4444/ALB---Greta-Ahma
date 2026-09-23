import BrandLogo from './BrandLogo'
import './WelcomeLanding.css'

type WelcomeLandingProps = {
	onRegister?: () => void
	onLogin?: () => void
	onRegisterClick?: () => void
	onLoginClick?: () => void
}

export default function WelcomeLanding({
	onRegister,
	onLogin,
	onRegisterClick,
	onLoginClick,
}: WelcomeLandingProps) {
	const handleRegister = onRegister ?? onRegisterClick ?? (() => {})
	const handleLogin = onLogin ?? onLoginClick ?? (() => {})

	return (
		<div className="welcome-landing">
			<header className="welcome-header">
				<div className="welcome-brand">
					<BrandLogo size={12} className="welcome-brand-mark" />
					<span className="welcome-brand-name">ALBLingo</span>
				</div>
				<div className="welcome-lang" aria-label="Gjuha e faqes">
					<span className="welcome-lang-label">Gjuha e faqes:</span>
					<span className="welcome-lang-value">Shqip</span>
				</div>
			</header>

			<main className="welcome-main">
				<div className="welcome-visual" aria-hidden="true">
					<div className="welcome-scene">
						<div className="welcome-blob welcome-blob-a" />
						<div className="welcome-blob welcome-blob-b" />
						<div className="welcome-blob welcome-blob-c" />
						<div className="welcome-mascot">
							<BrandLogo size={100} className="welcome-mascot-logo" decorative />
						</div>
						<span className="welcome-float welcome-float-abc">Abc</span>
					</div>
				</div>

				<div className="welcome-copy">
					<h1 className="welcome-title">Mirë se erdhe në ALBLingo</h1>
					<p className="welcome-subtitle">Mëso drejtshkrimin në mënyrë argëtuese</p>
					<div className="welcome-actions">
						<button type="button" className="welcome-btn welcome-btn-primary" onClick={handleRegister}>
							Regjistrohu
						</button>
						<button type="button" className="welcome-btn welcome-btn-secondary" onClick={handleLogin}>
							Hyr
						</button>
					</div>
				</div>
			</main>
		</div>
	)
}
