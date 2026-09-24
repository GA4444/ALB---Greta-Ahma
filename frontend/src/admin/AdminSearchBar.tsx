import { useId } from 'react'

type AdminSearchBarProps = {
	value: string
	onChange: (value: string) => void
	placeholder: string
	ariaLabel?: string
	className?: string
}

/**
 * Unified admin search field — same look/behavior across Admin Dashboard lists.
 */
export default function AdminSearchBar({
	value,
	onChange,
	placeholder,
	ariaLabel,
	className = '',
}: AdminSearchBarProps) {
	const inputId = useId()
	const hasValue = value.trim().length > 0

	return (
		<div className={`admin-search ${className}`.trim()}>
			<label className="admin-search-label" htmlFor={inputId}>
				<span className="admin-search-icon" aria-hidden="true">
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
						<circle cx="11" cy="11" r="7" />
						<path d="M20 20l-3.5-3.5" />
					</svg>
				</span>
				<span className="visually-hidden">{ariaLabel || placeholder}</span>
			</label>
			<input
				id={inputId}
				type="search"
				className="admin-search-input"
				value={value}
				placeholder={placeholder}
				aria-label={ariaLabel || placeholder}
				autoComplete="off"
				spellCheck={false}
				onChange={(e) => onChange(e.target.value)}
			/>
			{hasValue && (
				<button
					type="button"
					className="admin-search-clear"
					aria-label="Pastro kërkimin"
					onClick={() => onChange('')}
				>
					×
				</button>
			)}
		</div>
	)
}
