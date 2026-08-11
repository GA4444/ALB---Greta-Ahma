import { Component, type ErrorInfo, type ReactNode } from 'react'

interface LazyErrorBoundaryProps {
	children: ReactNode
	label?: string
}

interface LazyErrorBoundaryState {
	hasError: boolean
}

export default class LazyErrorBoundary extends Component<
	LazyErrorBoundaryProps,
	LazyErrorBoundaryState
> {
	state: LazyErrorBoundaryState = { hasError: false }

	static getDerivedStateFromError(): LazyErrorBoundaryState {
		return { hasError: true }
	}

	componentDidCatch(error: Error, info: ErrorInfo) {
		console.error(`Gabim gjatë ngarkimit të ${this.props.label || 'komponentit'}:`, error, info)
	}

	private retry = () => {
		window.location.reload()
	}

	render() {
		if (this.state.hasError) {
			return (
				<div className="lazy-error" role="alert">
					<strong>Nuk mundëm ta ngarkojmë këtë pjesë.</strong>
					<span>Kontrolloni lidhjen dhe provoni përsëri.</span>
					<button type="button" onClick={this.retry}>Provo përsëri</button>
				</div>
			)
		}

		return this.props.children
	}
}
