import { lazy, Suspense, useState } from 'react'
import LazyErrorBoundary from './components/LazyErrorBoundary'
import './ChatbotFloating.css'

const AdvancedChatbot = lazy(() => import('./AdvancedChatbot'))

interface ChatbotFloatingProps {
	userId?: string
	context?: {
		current_level?: string
		current_exercise?: string
		recent_mistakes?: string[]
	}
}

export default function ChatbotFloating({ userId, context }: ChatbotFloatingProps) {
	const [isOpen, setIsOpen] = useState(false)
	const [hasUnread, setHasUnread] = useState(false)

	const handleToggle = () => {
		setIsOpen((open) => {
			if (!open) setHasUnread(false)
			return !open
		})
	}

	const handleClose = () => setIsOpen(false)

	return (
		<>
			<button
				type="button"
				className={`chatbot-float-btn ${isOpen ? 'active' : ''}`}
				onClick={handleToggle}
				aria-label={isOpen ? 'Mbyll bashkëbiseduesin' : 'Hap bashkëbiseduesin AI'}
				aria-expanded={isOpen}
				aria-controls="chatbot-floating-panel"
			>
				{isOpen ? '✕' : '💬'}
				{!isOpen && hasUnread && <span className="unread-badge" />}
				{!isOpen && <span className="chatbot-label">AI</span>}
			</button>

			{isOpen && (
				<div
					className="chatbot-modal-overlay"
					role="presentation"
					onClick={handleClose}
				>
					<div
						id="chatbot-floating-panel"
						className="chatbot-floating-panel"
						role="dialog"
						aria-modal="true"
						aria-label="Bashkëbiseduesi AI"
						onClick={(event) => event.stopPropagation()}
					>
						<LazyErrorBoundary label="bashkëbiseduesit">
							<Suspense fallback={<div className="chatbot-panel-loading">Duke hapur bashkëbiseduesin…</div>}>
								<AdvancedChatbot
									userId={userId}
									context={context}
									onClose={handleClose}
								/>
							</Suspense>
						</LazyErrorBoundary>
					</div>
				</div>
			)}
		</>
	)
}
