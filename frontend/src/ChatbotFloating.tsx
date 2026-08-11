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
		setIsOpen(!isOpen)
		if (!isOpen) {
			setHasUnread(false) // Mark as read when opened
		}
	}

	return (
		<>
			{/* Floating Button */}
			<button
				className={`chatbot-float-btn ${isOpen ? 'active' : ''}`}
				onClick={handleToggle}
				aria-label="Bashkëbiseduesi AI"
				aria-expanded={isOpen}
				aria-controls="chatbot-floating-panel"
			>
				{isOpen ? '✕' : '💬'}
				{!isOpen && hasUnread && <span className="unread-badge"></span>}
				{!isOpen && <span className="chatbot-label">AI</span>}
			</button>

			{/* Chatbot Panel */}
			{isOpen && (
				<div
					id="chatbot-floating-panel"
					className="chatbot-floating-panel"
					role="dialog"
					aria-label="Bashkëbiseduesi AI"
				>
					<LazyErrorBoundary label="bashkëbiseduesit">
						<Suspense fallback={<div className="chatbot-panel-loading">Duke hapur bashkëbiseduesin…</div>}>
							<AdvancedChatbot
								userId={userId}
								context={context}
								onClose={() => setIsOpen(false)}
							/>
						</Suspense>
					</LazyErrorBoundary>
				</div>
			)}
		</>
	)
}
