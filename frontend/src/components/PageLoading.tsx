import BrandLogo from './BrandLogo'

type PageLoadingProps = {
	/** Existing screen-specific line under the title (keep wording unchanged). */
	subtitle?: string
	title?: string
	brand?: string
	/** Compact variant for nested sections / Suspense fallbacks. */
	inline?: boolean
	className?: string
	showProgress?: boolean
}

/**
 * Shared AlbLingo loading UI — same visual as the Home screen loader.
 */
export default function PageLoading({
	subtitle = 'Po përgatitim platformën për ju',
	title = 'Duke ngarkuar',
	brand = 'AlbLingo',
	inline = false,
	className = '',
	showProgress = true,
}: PageLoadingProps) {
	const classes = [
		'loading',
		'page-loading',
		inline ? 'page-loading--inline' : '',
		className,
	]
		.filter(Boolean)
		.join(' ')

	return (
		<div className={classes} role="status" aria-live="polite" aria-busy="true">
			{showProgress && !inline ? (
				<div className="page-loading-progress" aria-hidden="true">
					<span className="page-loading-progress-bar"></span>
				</div>
			) : null}
			<div className="page-loading-inner">
				{inline ? (
					<div className="page-loading-spinner" aria-hidden="true"></div>
				) : (
					<div className="page-loading-mark" aria-hidden="true">
						<BrandLogo size={52} decorative />
					</div>
				)}
				{!inline ? <p className="page-loading-brand">{brand}</p> : null}
				<p className="page-loading-title">{title}</p>
				{subtitle ? <p className="page-loading-subtitle">{subtitle}</p> : null}
			</div>
		</div>
	)
}
