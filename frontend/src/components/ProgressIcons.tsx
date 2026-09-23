type IconProps = { size?: number; className?: string }

export function IconStar({ size = 18, className }: IconProps) {
	return (
		<svg className={className} viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M12 3l2.4 4.9 5.4.8-3.9 3.8.9 5.4L12 15.9 7.2 18l.9-5.4L4.2 8.7l5.4-.8L12 3z" />
		</svg>
	)
}

export function IconTrophy({ size = 18, className }: IconProps) {
	return (
		<svg className={className} viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M8 21h8" />
			<path d="M12 17v4" />
			<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" />
			<path d="M7 6H4a2 2 0 0 0 2 4" />
			<path d="M17 6h3a2 2 0 0 1-2 4" />
		</svg>
	)
}

export function IconFlame({ size = 18, className }: IconProps) {
	return (
		<svg className={className} viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M12 21c4-3.2 6-6.2 6-9.2A4 4 0 0 0 12 8a4 4 0 0 0-6 3.8c0 3 2 6 6 9.2Z" />
			<path d="M10 11.5c.5-1 1.5-1.8 2.5-2" />
		</svg>
	)
}

export function IconBook({ size = 18, className }: IconProps) {
	return (
		<svg className={className} viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
			<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
		</svg>
	)
}

export function IconSparkle({ size = 18, className }: IconProps) {
	return (
		<svg className={className} viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M12 3v4" />
			<path d="M12 17v4" />
			<path d="M3 12h4" />
			<path d="M17 12h4" />
			<path d="M5.6 5.6l2.8 2.8" />
			<path d="M15.6 15.6l2.8 2.8" />
			<path d="M5.6 18.4l2.8-2.8" />
			<path d="M15.6 8.4l2.8-2.8" />
		</svg>
	)
}

export function IconCalendar({ size = 18, className }: IconProps) {
	return (
		<svg className={className} viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M8 2v3" />
			<path d="M16 2v3" />
			<path d="M4 8h16" />
			<path d="M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z" />
		</svg>
	)
}
