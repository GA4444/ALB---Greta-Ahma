interface UserReportData {
	user_info?: {
		username: string
		email: string
	}
	metrics: {
		totalExercises: number
		completedExercises: number
		averageScore: number
		totalTimeMinutes: number
		currentStreak: number
		longestStreak: number
		achievements: number
		level: string
	}
	strengths: Array<{ area: string; score: number; exercises: number }>
	weaknesses: Array<{ area: string; score: number; exercises: number }>
	learningStyle: {
		preferredTime: string
		averageSessionLength: string
		studyFrequency: string
		bestPerformanceDay: string
		completionRate: number
	}
	recommendations: string[]
	categoryPerformance?: Array<{
		category: string
		completed: number
		total: number
		percentage: number
	}>
	generatedAt?: string
	dataSource?: string
}

/** AlbLingo brand teal #1F6F8B */
const BRAND = {
	primary: [31, 111, 139] as [number, number, number],
	sky: [74, 159, 212] as [number, number, number],
	success: [91, 189, 108] as [number, number, number],
	warning: [217, 119, 6] as [number, number, number],
	text: [30, 41, 59] as [number, number, number],
	muted: [100, 116, 139] as [number, number, number],
	border: [226, 232, 240] as [number, number, number],
	bg: [248, 250, 252] as [number, number, number],
	white: [255, 255, 255] as [number, number, number],
}

function formatTimeSpent(totalMinutes: number): string {
	const hours = Math.floor(totalMinutes / 60)
	const minutes = totalMinutes % 60
	if (hours <= 0) return `${minutes} min`
	return `${hours}h ${minutes}min`
}

async function loadAlbLingoLogoDataUrl(): Promise<string | null> {
	try {
		const response = await fetch('/alblingo.png')
		if (!response.ok) return null
		const blob = await response.blob()
		return await new Promise((resolve, reject) => {
			const reader = new FileReader()
			reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : null)
			reader.onerror = () => reject(reader.error)
			reader.readAsDataURL(blob)
		})
	} catch {
		return null
	}
}

export async function exportUserReportToPDF(
	username: string,
	email: string,
	reportData: UserReportData
): Promise<void> {
	try {
		const [{ default: jsPDF }, logoDataUrl] = await Promise.all([
			import('jspdf'),
			loadAlbLingoLogoDataUrl(),
		])
		const pdf = new jsPDF({
			orientation: 'p',
			unit: 'mm',
			format: 'a4',
			compress: true,
		})

		const pageWidth = pdf.internal.pageSize.getWidth()
		const pageHeight = pdf.internal.pageSize.getHeight()
		const margin = 16
		const contentWidth = pageWidth - 2 * margin
		const footerReserve = 24
		let y = margin

		const currentDate = new Date().toLocaleDateString('sq-AL', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
		})

		const drawLogo = (x: number, cy: number, size: number) => {
			if (!logoDataUrl) return false
			try {
				pdf.addImage(logoDataUrl, 'PNG', x, cy - size / 2, size, size)
				return true
			} catch {
				return false
			}
		}

		const ensureSpace = (needed: number) => {
			if (y + needed > pageHeight - footerReserve) {
				pdf.addPage()
				y = margin + 8
			}
		}

		const sectionTitle = (title: string) => {
			ensureSpace(16)
			pdf.setFont('helvetica', 'bold')
			pdf.setFontSize(11)
			pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.text(title, margin, y)
			y += 2.2
			pdf.setDrawColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.setLineWidth(0.7)
			pdf.line(margin, y, margin + 36, y)
			pdf.setDrawColor(BRAND.border[0], BRAND.border[1], BRAND.border[2])
			pdf.setLineWidth(0.3)
			pdf.line(margin + 36, y, pageWidth - margin, y)
			y += 8
		}

		const wrapText = (text: string, maxW: number, fontSize: number) => {
			pdf.setFontSize(fontSize)
			return pdf.splitTextToSize(text, maxW) as string[]
		}

		// ── Header with real ALBLingo logo ──
		const headerH = 46
		pdf.setFillColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
		pdf.rect(0, 0, pageWidth, headerH, 'F')
		pdf.setFillColor(BRAND.sky[0], BRAND.sky[1], BRAND.sky[2])
		pdf.rect(0, headerH - 3, pageWidth, 3, 'F')

		const logoSize = 22
		const logoX = margin
		const logoCY = 21
		pdf.setFillColor(BRAND.white[0], BRAND.white[1], BRAND.white[2])
		pdf.roundedRect(logoX - 1.5, logoCY - logoSize / 2 - 1.5, logoSize + 3, logoSize + 3, 3, 3, 'F')
		const hasLogo = drawLogo(logoX, logoCY, logoSize)
		if (!hasLogo) {
			pdf.setFont('helvetica', 'bold')
			pdf.setFontSize(10)
			pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.text('AL', logoX + logoSize / 2, logoCY + 1.5, { align: 'center' })
		}

		const textX = logoX + logoSize + 8
		pdf.setFont('helvetica', 'bold')
		pdf.setFontSize(10)
		pdf.setTextColor(BRAND.white[0], BRAND.white[1], BRAND.white[2])
		pdf.text('ALBLingo', textX, 14)

		pdf.setFontSize(15)
		pdf.text('Raporti i Progresit', textX, 24)

		pdf.setFont('helvetica', 'normal')
		pdf.setFontSize(8.5)
		pdf.text('Platformë edukative për gjuhën shqipe', textX, 32)

		pdf.setFontSize(8)
		pdf.text(`Gjeneruar: ${currentDate}`, pageWidth - margin, 18, { align: 'right' })
		pdf.setFont('helvetica', 'normal')
		pdf.text('Educational Progress Report', pageWidth - margin, 26, { align: 'right' })

		y = headerH + 12

		// ── User information ──
		sectionTitle('Informacioni i përdoruesit')
		pdf.setFillColor(BRAND.bg[0], BRAND.bg[1], BRAND.bg[2])
		pdf.setDrawColor(BRAND.border[0], BRAND.border[1], BRAND.border[2])
		pdf.setLineWidth(0.4)
		pdf.roundedRect(margin, y, contentWidth, 22, 2, 2, 'FD')

		pdf.setFont('helvetica', 'bold')
		pdf.setFontSize(11)
		pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
		pdf.text(username || '—', margin + 6, y + 9)

		pdf.setFont('helvetica', 'normal')
		pdf.setFontSize(9)
		pdf.setTextColor(BRAND.muted[0], BRAND.muted[1], BRAND.muted[2])
		pdf.text(email || 'Email jo i specifikuar', margin + 6, y + 16)

		pdf.setFont('helvetica', 'bold')
		pdf.setFontSize(9)
		pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
		pdf.text(`Niveli: ${reportData.metrics.level}`, pageWidth - margin - 6, y + 12, { align: 'right' })
		y += 28

		// ── Overall Progress ──
		sectionTitle('Progresi i përgjithshëm')
		const metrics = [
			{ label: 'Ushtrime', value: String(reportData.metrics.totalExercises) },
			{ label: 'Saktësi', value: `${reportData.metrics.averageScore}%` },
			{ label: 'Të sakta', value: String(reportData.metrics.completedExercises) },
			{ label: 'Kohë', value: formatTimeSpent(reportData.metrics.totalTimeMinutes) },
			{ label: 'Ditë radhazi', value: String(reportData.metrics.currentStreak) },
			{ label: 'Rekord', value: String(reportData.metrics.longestStreak) },
		]

		const cols = 3
		const gap = 4
		const boxW = (contentWidth - gap * (cols - 1)) / cols
		const boxH = 20

		metrics.forEach((m, i) => {
			const col = i % cols
			const row = Math.floor(i / cols)
			if (col === 0) ensureSpace(boxH + 6)
			const x = margin + col * (boxW + gap)
			const by = y + row * (boxH + gap)

			pdf.setFillColor(BRAND.white[0], BRAND.white[1], BRAND.white[2])
			pdf.setDrawColor(BRAND.border[0], BRAND.border[1], BRAND.border[2])
			pdf.setLineWidth(0.4)
			pdf.roundedRect(x, by, boxW, boxH, 2, 2, 'FD')
			pdf.setFillColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.rect(x, by, 2.2, boxH, 'F')

			pdf.setFont('helvetica', 'bold')
			pdf.setFontSize(13)
			pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.text(m.value, x + 6, by + 9)

			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(7.5)
			pdf.setTextColor(BRAND.muted[0], BRAND.muted[1], BRAND.muted[2])
			pdf.text(m.label, x + 6, by + 15)
		})
		y += Math.ceil(metrics.length / cols) * (boxH + gap) + 4

		// ── Learning Performance (categories) ──
		const categories = reportData.categoryPerformance || []
		if (categories.length > 0) {
			sectionTitle('Performanca në mësim')
			ensureSpace(14)
			// Table header
			pdf.setFillColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.roundedRect(margin, y, contentWidth, 8, 1, 1, 'F')
			pdf.setFont('helvetica', 'bold')
			pdf.setFontSize(8)
			pdf.setTextColor(BRAND.white[0], BRAND.white[1], BRAND.white[2])
			pdf.text('Kategoria', margin + 3, y + 5.5)
			pdf.text('Të sakta', margin + contentWidth * 0.48, y + 5.5)
			pdf.text('Totali', margin + contentWidth * 0.66, y + 5.5)
			pdf.text('Saktësi', margin + contentWidth * 0.84, y + 5.5)
			y += 9

			categories.forEach((cat, idx) => {
				ensureSpace(10)
				if (idx % 2 === 0) {
					pdf.setFillColor(BRAND.bg[0], BRAND.bg[1], BRAND.bg[2])
					pdf.rect(margin, y - 4, contentWidth, 9, 'F')
				}
				pdf.setFont('helvetica', 'normal')
				pdf.setFontSize(8)
				pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
				const nameLines = wrapText(String(cat.category || ''), contentWidth * 0.42, 8)
				pdf.text(nameLines[0] || '—', margin + 3, y + 1.5)
				pdf.text(String(cat.completed ?? 0), margin + contentWidth * 0.48, y + 1.5)
				pdf.text(String(cat.total ?? 0), margin + contentWidth * 0.66, y + 1.5)
				pdf.setFont('helvetica', 'bold')
				pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
				pdf.text(`${cat.percentage ?? 0}%`, margin + contentWidth * 0.84, y + 1.5)
				y += 9
			})
			y += 4
		}

		// ── Strengths ──
		sectionTitle('Pikat e forta')
		if (!reportData.strengths?.length) {
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(9)
			pdf.setTextColor(BRAND.muted[0], BRAND.muted[1], BRAND.muted[2])
			pdf.text('Nuk ka ende të dhëna të mjaftueshme.', margin, y)
			y += 10
		} else {
			reportData.strengths.forEach((s, i) => {
				ensureSpace(12)
				pdf.setFillColor(240, 253, 244)
				pdf.setDrawColor(BRAND.success[0], BRAND.success[1], BRAND.success[2])
				pdf.setLineWidth(0.5)
				pdf.roundedRect(margin, y, contentWidth, 11, 2, 2, 'FD')
				pdf.setFont('helvetica', 'bold')
				pdf.setFontSize(9)
				pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
				pdf.text(`${i + 1}. ${s.area}`, margin + 4, y + 7)
				pdf.setFont('helvetica', 'normal')
				pdf.setTextColor(BRAND.success[0], BRAND.success[1], BRAND.success[2])
				pdf.text(`${s.score}%  ·  ${s.exercises} ushtrime`, pageWidth - margin - 4, y + 7, { align: 'right' })
				y += 13
			})
		}

		// ── Areas for Improvement ──
		sectionTitle('Fushat për përmirësim')
		if (!reportData.weaknesses?.length) {
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(9)
			pdf.setTextColor(BRAND.muted[0], BRAND.muted[1], BRAND.muted[2])
			pdf.text('Nuk është identifikuar ende ndonjë fushë e dobët.', margin, y)
			y += 10
		} else {
			reportData.weaknesses.forEach((w, i) => {
				ensureSpace(12)
				pdf.setFillColor(255, 247, 237)
				pdf.setDrawColor(BRAND.warning[0], BRAND.warning[1], BRAND.warning[2])
				pdf.setLineWidth(0.5)
				pdf.roundedRect(margin, y, contentWidth, 11, 2, 2, 'FD')
				pdf.setFont('helvetica', 'bold')
				pdf.setFontSize(9)
				pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
				pdf.text(`${i + 1}. ${w.area}`, margin + 4, y + 7)
				pdf.setFont('helvetica', 'normal')
				pdf.setTextColor(BRAND.warning[0], BRAND.warning[1], BRAND.warning[2])
				pdf.text(`${w.score}%  ·  ${w.exercises} ushtrime`, pageWidth - margin - 4, y + 7, { align: 'right' })
				y += 13
			})
		}

		// ── Learning preferences (existing data) ──
		sectionTitle('Stili i mësimit')
		const styleRows = [
			['Koha e preferuar', reportData.learningStyle.preferredTime],
			['Gjatësia mesatare', reportData.learningStyle.averageSessionLength],
			['Frekuenca', reportData.learningStyle.studyFrequency],
			['Dita më e mirë', reportData.learningStyle.bestPerformanceDay],
			['Shkalla e përfundimit', `${reportData.learningStyle.completionRate}%`],
		]
		styleRows.forEach(([label, value], idx) => {
			ensureSpace(10)
			if (idx % 2 === 0) {
				pdf.setFillColor(BRAND.bg[0], BRAND.bg[1], BRAND.bg[2])
				pdf.rect(margin, y - 3.5, contentWidth, 9, 'F')
			}
			pdf.setFont('helvetica', 'bold')
			pdf.setFontSize(8.5)
			pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
			pdf.text(label, margin + 3, y + 2)
			pdf.setFont('helvetica', 'normal')
			pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			const valLines = wrapText(String(value || '—'), contentWidth * 0.48, 8.5)
			pdf.text(valLines[0], pageWidth - margin - 3, y + 2, { align: 'right' })
			y += 9
		})
		y += 4

		// ── Recommendations ──
		sectionTitle('Rekomandime')
		const recs = reportData.recommendations || []
		if (!recs.length) {
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(9)
			pdf.setTextColor(BRAND.muted[0], BRAND.muted[1], BRAND.muted[2])
			pdf.text('Nuk ka rekomandime për momentin.', margin, y)
			y += 10
		} else {
			recs.forEach((rec, i) => {
				const lines = wrapText(rec, contentWidth - 14, 9)
				const boxH = Math.max(12, lines.length * 4.2 + 6)
				ensureSpace(boxH + 4)
				pdf.setFillColor(BRAND.bg[0], BRAND.bg[1], BRAND.bg[2])
				pdf.setDrawColor(BRAND.border[0], BRAND.border[1], BRAND.border[2])
				pdf.setLineWidth(0.4)
				pdf.roundedRect(margin, y, contentWidth, boxH, 2, 2, 'FD')
				pdf.setFillColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
				pdf.circle(margin + 6, y + boxH / 2, 3.2, 'F')
				pdf.setFont('helvetica', 'bold')
				pdf.setFontSize(8)
				pdf.setTextColor(BRAND.white[0], BRAND.white[1], BRAND.white[2])
				pdf.text(String(i + 1), margin + 6, y + boxH / 2 + 1, { align: 'center' })
				pdf.setFont('helvetica', 'normal')
				pdf.setFontSize(9)
				pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
				pdf.text(lines, margin + 12, y + 5.5)
				y += boxH + 4
			})
		}

		// ── Summary ──
		sectionTitle('Përmbledhje')
		const accuracyPct =
			reportData.metrics.totalExercises > 0
				? Math.round(
						(reportData.metrics.completedExercises / reportData.metrics.totalExercises) * 100
					)
				: 0
		const summaryLines = [
			`Niveli aktual: ${reportData.metrics.level}`,
			`Ushtrime totale: ${reportData.metrics.totalExercises} (${accuracyPct}% të sakta)`,
			`Koha totale: ${formatTimeSpent(reportData.metrics.totalTimeMinutes)}`,
			`Numri më i madh i ditëve radhazi: ${reportData.metrics.longestStreak} ditë`,
			`Më i fortë në: ${
				reportData.strengths[0]
					? `${reportData.strengths[0].area} (${reportData.strengths[0].score}%)`
					: 'Nuk ka ende të dhëna të mjaftueshme'
			}`,
			`Duhet të përmirësojë: ${
				reportData.weaknesses[0]
					? `${reportData.weaknesses[0].area} (${reportData.weaknesses[0].score}%)`
					: 'Nuk është identifikuar ende'
			}`,
		]
		ensureSpace(summaryLines.length * 7 + 8)
		pdf.setFillColor(236, 253, 245)
		pdf.setDrawColor(BRAND.success[0], BRAND.success[1], BRAND.success[2])
		pdf.setLineWidth(0.6)
		const sumH = summaryLines.length * 6.5 + 8
		pdf.roundedRect(margin, y, contentWidth, sumH, 2, 2, 'FD')
		let sy = y + 7
		summaryLines.forEach((line) => {
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(9)
			pdf.setTextColor(BRAND.text[0], BRAND.text[1], BRAND.text[2])
			pdf.text(line, margin + 5, sy)
			sy += 6.5
		})

		// ── Footer on every page (with logo) ──
		const totalPages = pdf.getNumberOfPages()
		for (let i = 1; i <= totalPages; i++) {
			pdf.setPage(i)
			const fy = pageHeight - 12
			pdf.setDrawColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.setLineWidth(0.45)
			pdf.line(margin, fy - 6, pageWidth - margin, fy - 6)

			const footerLogoSize = 7
			const footerLogoDrawn = drawLogo(margin, fy - 0.5, footerLogoSize)
			const brandX = footerLogoDrawn ? margin + footerLogoSize + 2.5 : margin

			pdf.setFont('helvetica', 'bold')
			pdf.setFontSize(7.5)
			pdf.setTextColor(BRAND.primary[0], BRAND.primary[1], BRAND.primary[2])
			pdf.text('ALBLingo', brandX, fy)

			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(7)
			pdf.setTextColor(BRAND.muted[0], BRAND.muted[1], BRAND.muted[2])
			pdf.text(`Gjeneruar: ${currentDate}`, pageWidth / 2, fy, { align: 'center' })
			pdf.text(`Faqe ${i} / ${totalPages}`, pageWidth - margin, fy, { align: 'right' })
		}

		const safeName = (username || 'user').replace(/[^\w\-]+/g, '_').slice(0, 40)
		const fileName = `AlbLingo_Raport_${safeName}_${new Date().toISOString().split('T')[0]}.pdf`
		pdf.save(fileName)
	} catch (error) {
		console.error('Gabim në gjenerimin e PDF:', error)
		throw error
	}
}

/**
 * Alternative: Export report by capturing DOM elements as images
 */
export async function exportUserReportWithChartsToPDF(
	modalElement: HTMLElement,
	username: string
): Promise<void> {
	try {
		const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
			import('html2canvas'),
			import('jspdf'),
		])
		const exportBtn = modalElement.querySelector('.export-report-btn') as HTMLElement
		const closeBtn = modalElement.querySelector('.modal-close') as HTMLElement

		if (exportBtn) exportBtn.style.display = 'none'
		if (closeBtn) closeBtn.style.display = 'none'

		await new Promise((resolve) => setTimeout(resolve, 100))

		const canvas = await html2canvas(modalElement, {
			scale: 2,
			useCORS: true,
			logging: false,
			backgroundColor: '#ffffff',
		})

		if (exportBtn) exportBtn.style.display = ''
		if (closeBtn) closeBtn.style.display = ''

		const pdf = new jsPDF('p', 'mm', 'a4')
		const pageWidth = pdf.internal.pageSize.getWidth()
		const pageHeight = pdf.internal.pageSize.getHeight()

		const imgWidth = pageWidth - 20
		const imgHeight = (canvas.height * imgWidth) / canvas.width

		let heightLeft = imgHeight
		let position = 10

		const imgData = canvas.toDataURL('image/png')
		pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
		heightLeft -= pageHeight - 20

		while (heightLeft > 0) {
			position = heightLeft - imgHeight + 10
			pdf.addPage()
			pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
			heightLeft -= pageHeight - 20
		}

		const safeName = (username || 'user').replace(/[^\w\-]+/g, '_').slice(0, 40)
		pdf.save(`AlbLingo_Raport_${safeName}_${new Date().toISOString().split('T')[0]}.pdf`)
	} catch (error) {
		console.error('Gabim në gjenerimin e PDF me grafikë:', error)
		throw error
	}
}
