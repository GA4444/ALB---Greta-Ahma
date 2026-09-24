/**
 * Shared client-side search helpers for Admin Dashboard lists.
 * Case-insensitive partial match across selected string fields.
 */

export function normalizeSearchQuery(query: string): string {
	return query.trim().toLowerCase()
}

export function matchesSearchQuery(query: string, ...parts: Array<string | number | boolean | null | undefined>): boolean {
	const q = normalizeSearchQuery(query)
	if (!q) return true
	const haystack = parts
		.filter((part) => part !== null && part !== undefined && part !== '')
		.map((part) => String(part).toLowerCase())
		.join(' ')
	return haystack.includes(q)
}

export function filterBySearch<T>(
	items: T[],
	query: string,
	getParts: (item: T) => Array<string | number | boolean | null | undefined>
): T[] {
	const q = normalizeSearchQuery(query)
	if (!q) return items
	return items.filter((item) => matchesSearchQuery(q, ...getParts(item)))
}
