import { useState } from 'react'
import AdvancedChatbot from './AdvancedChatbot'
import './ChatbotFloating.css'

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
			>
				{isOpen ? '✕' : '💬'}
				{!isOpen && hasUnread && <span className="unread-badge"></span>}
				{!isOpen && <span className="chatbot-label">AI</span>}
			</button>

			{/* Chatbot Panel */}
			{isOpen && (
				<div className="chatbot-floating-panel">
					<AdvancedChatbot
						userId={userId}
						context={context}
						onClose={() => setIsOpen(false)}
					/>
				</div>
			)}
		</>
	)
}
