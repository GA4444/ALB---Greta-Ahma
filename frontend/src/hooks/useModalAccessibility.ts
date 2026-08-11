import { useEffect, useRef } from 'react'

const FOCUSABLE_SELECTOR = [
	'a[href]',
	'button:not([disabled])',
	'input:not([disabled])',
	'select:not([disabled])',
	'textarea:not([disabled])',
	'[tabindex]:not([tabindex="-1"])',
].join(',')

export function useModalAccessibility<T extends HTMLElement = HTMLDivElement>(
	isOpen: boolean,
	onClose: () => void
) {
	const modalRef = useRef<T>(null)
	const onCloseRef = useRef(onClose)
	onCloseRef.current = onClose

	useEffect(() => {
		if (!isOpen) return

		const previouslyFocused = document.activeElement as HTMLElement | null
		const previousOverflow = document.body.style.overflow
		const modal = modalRef.current

		document.body.style.overflow = 'hidden'
		const focusTimer = window.setTimeout(() => {
			const firstFocusable = modal?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR)
			;(firstFocusable || modal)?.focus()
		}, 0)

		const handleKeyDown = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				event.preventDefault()
				onCloseRef.current()
				return
			}

			if (event.key !== 'Tab' || !modal) return
			const focusable = Array.from(modal.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
			if (!focusable.length) {
				event.preventDefault()
				modal.focus()
				return
			}

			const first = focusable[0]
			const last = focusable[focusable.length - 1]
			if (event.shiftKey && document.activeElement === first) {
				event.preventDefault()
				last.focus()
			} else if (!event.shiftKey && document.activeElement === last) {
				event.preventDefault()
				first.focus()
			}
		}

		document.addEventListener('keydown', handleKeyDown)
		return () => {
			window.clearTimeout(focusTimer)
			document.removeEventListener('keydown', handleKeyDown)
			document.body.style.overflow = previousOverflow
			previouslyFocused?.focus()
		}
	}, [isOpen])

	return modalRef
}
