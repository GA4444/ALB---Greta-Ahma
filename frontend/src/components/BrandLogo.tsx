/**
 * Shared brand mark — always use existing /alblingo.svg.
 * Do not invent a new logo.
 */
type BrandLogoProps = {
	size?: number
	className?: string
	alt?: string
	decorative?: boolean
}

const LOGO_SRC = '/alblingo.svg?v=brand'

export default function BrandLogo({
	size = 40,
	className = '',
	alt = 'ALBLingo',
	decorative = false,
}: BrandLogoProps) {
	return (
		<img
			src={LOGO_SRC}
			alt={decorative ? '' : alt}
			width={size}
			height={size}
			className={`brand-logo ${className}`.trim()}
			style={{ width: size, height: size }}
			draggable={false}
			decoding="async"
			aria-hidden={decorative || undefined}
		/>
	)
}
