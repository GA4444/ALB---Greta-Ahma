import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

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
}

export async function exportUserReportToPDF(
	username: string,
	email: string,
	reportData: UserReportData
): Promise<void> {
	try {
		// Create PDF with better settings
		const pdf = new jsPDF({
			orientation: 'p',
			unit: 'mm',
			format: 'a4',
			compress: true
		})
		
		const pageWidth = pdf.internal.pageSize.getWidth()
		const pageHeight = pdf.internal.pageSize.getHeight()
		const margin = 20  // Increased margin
		const contentWidth = pageWidth - 2 * margin
		let yPosition = margin

		// Colors (matching platform) - RGB format for better rendering
		const colors = {
			primaryBlue: [74, 159, 212],
			successGreen: [91, 189, 108],
			warningOrange: [255, 150, 0],
			accentYellow: [255, 200, 0],
			textDark: [30, 41, 59],
			textLight: [100, 116, 139],
			bgLight: [248, 250, 252],
			border: [226, 232, 240],
			white: [255, 255, 255]
		}

		// Helper functions
		const addText = (
			text: string,
			x: number,
			y: number,
			maxWidth: number,
			fontSize: number = 10,
			color: number[] = colors.textDark,
			isBold: boolean = false
		): number => {
			pdf.setFontSize(fontSize)
			pdf.setFont('helvetica', isBold ? 'bold' : 'normal')
			pdf.setTextColor(color[0], color[1], color[2])
			
			const lines = pdf.splitTextToSize(text, maxWidth)
			pdf.text(lines, x, y)
			
			return y + (lines.length * fontSize * 0.4) // Better line height
		}

		const addSectionTitle = (title: string, y: number, sectionNumber: string = ''): number => {
			pdf.setFontSize(16)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
			const displayTitle = sectionNumber ? `${sectionNumber}. ${title}` : title
			pdf.text(displayTitle, margin, y)
			
			// Underline
			pdf.setDrawColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
			pdf.setLineWidth(0.8)
			pdf.line(margin, y + 2, margin + 60, y + 2)
			
			return y + 10
		}

		// Enhanced Header with gradient effect
		const headerHeight = 55
		
		// Gradient background (simulated with layers)
		pdf.setFillColor(74, 159, 212)
		pdf.rect(0, 0, pageWidth, headerHeight, 'F')
		pdf.setFillColor(64, 139, 192)
		pdf.rect(0, headerHeight - 10, pageWidth, 10, 'F')
		
		// Decorative corner elements
		pdf.setFillColor(colors.white[0], colors.white[1], colors.white[2])
		pdf.setGState(new pdf.GState({ opacity: 0.1 }))
		pdf.circle(pageWidth - 20, 20, 30, 'F')
		pdf.circle(-10, headerHeight - 10, 25, 'F')
		pdf.setGState(new pdf.GState({ opacity: 1 }))
		
		// Logo circle with AL text
		pdf.setFillColor(colors.white[0], colors.white[1], colors.white[2])
		pdf.circle(30, 27, 14, 'F')
		pdf.setDrawColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
		pdf.setLineWidth(1)
		pdf.circle(30, 27, 14, 'S')
		
		// "AL" text instead of flag emoji
		pdf.setFontSize(16)
		pdf.setFont('helvetica', 'bold')
		pdf.setTextColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
		pdf.text('AL', 30, 30, { align: 'center' })

		// Title
		pdf.setFontSize(26)
		pdf.setFont('helvetica', 'bold')
		pdf.setTextColor(colors.white[0], colors.white[1], colors.white[2])
		pdf.text('RAPORTI I PËRDORUESIT', 50, 20)
		
		// Subtitle line
		pdf.setFontSize(10)
		pdf.setFont('helvetica', 'normal')
		pdf.text('Analizë e Detajuar e Performancës', 50, 28)

		// Username & Email with better styling
		pdf.setFontSize(15)
		pdf.setFont('helvetica', 'bold')
		pdf.text(username, 50, 38)
		
		pdf.setFontSize(10)
		pdf.setFont('helvetica', 'normal')
		pdf.text('Email: ' + (email || 'Jo i specifikuar'), 50, 45)

		// Date in a box
		const currentDate = new Date().toLocaleDateString('sq-AL', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		})
		
		const dateBoxWidth = 50
		pdf.setFillColor(colors.white[0], colors.white[1], colors.white[2])
		pdf.setGState(new pdf.GState({ opacity: 0.9 }))
		pdf.roundedRect(pageWidth - margin - dateBoxWidth, 12, dateBoxWidth, 18, 2, 2, 'F')
		pdf.setGState(new pdf.GState({ opacity: 1 }))
		
		pdf.setFontSize(8)
		pdf.setFont('helvetica', 'normal')
		pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
		pdf.text('DATA E RAPORTIT', pageWidth - margin - dateBoxWidth / 2, 18, { align: 'center' })
		pdf.setFontSize(9)
		pdf.setFont('helvetica', 'bold')
		pdf.text(currentDate, pageWidth - margin - dateBoxWidth / 2, 26, { align: 'center' })

		yPosition = headerHeight + 20

		// ==========================================
		// SECTION 1: KEY METRICS
		// ==========================================
		yPosition = addSectionTitle('METRIKS KRYESORE', yPosition, '1')

		// Metrics Grid (2x3) with enhanced design
		const metrics = [
			{ icon: 'U', label: 'Ushtrime Totale', value: reportData.metrics.totalExercises, color: colors.primaryBlue },
			{ icon: '✓', label: 'Përfunduar', value: reportData.metrics.completedExercises, color: colors.successGreen },
			{ icon: '%', label: 'Pikë Mesatare', value: `${reportData.metrics.averageScore}%`, color: colors.accentYellow },
			{ icon: 'T', label: 'Kohë Totale', value: `${Math.round(reportData.metrics.totalTimeMinutes / 60)}h`, color: colors.warningOrange },
			{ icon: 'S', label: 'Vargu aktual', value: `${reportData.metrics.currentStreak}`, color: [239, 68, 68] },
			{ icon: 'A', label: 'Arritje', value: reportData.metrics.achievements, color: [168, 85, 247] }
		]

		const boxWidth = (contentWidth - 12) / 3
		const boxHeight = 28
		let metricX = margin
		let metricY = yPosition

		metrics.forEach((metric, index) => {
			// Shadow effect
			pdf.setFillColor(0, 0, 0)
			pdf.setGState(new pdf.GState({ opacity: 0.05 }))
			pdf.roundedRect(metricX + 1, metricY + 1, boxWidth, boxHeight, 3, 3, 'F')
			pdf.setGState(new pdf.GState({ opacity: 1 }))
			
			// Main box with gradient simulation
			pdf.setFillColor(colors.white[0], colors.white[1], colors.white[2])
			pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2])
			pdf.setLineWidth(0.5)
			pdf.roundedRect(metricX, metricY, boxWidth, boxHeight, 3, 3, 'FD')
			
			// Colored accent bar
			pdf.setFillColor(metric.color[0], metric.color[1], metric.color[2])
			pdf.roundedRect(metricX, metricY, boxWidth, 4, 3, 3, 'F')

			// Icon background circle
			pdf.setFillColor(colors.bgLight[0], colors.bgLight[1], colors.bgLight[2])
			pdf.circle(metricX + 8, metricY + 15, 6, 'F')
			
			// Icon
			pdf.setFontSize(14)
			pdf.text(metric.icon, metricX + 5, metricY + 18)

			// Value
			pdf.setFontSize(18)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(metric.color[0], metric.color[1], metric.color[2])
			pdf.text(String(metric.value), metricX + 18, metricY + 14)

			// Label
			pdf.setFontSize(7.5)
			pdf.setFont('helvetica', 'normal')
			pdf.setTextColor(colors.textLight[0], colors.textLight[1], colors.textLight[2])
			const labelLines = pdf.splitTextToSize(metric.label, boxWidth - 20)
			pdf.text(labelLines, metricX + 18, metricY + 21)

			// Move to next position
			if ((index + 1) % 3 === 0) {
				metricX = margin
				metricY += boxHeight + 6
			} else {
				metricX += boxWidth + 6
			}
		})

		yPosition = metricY + 12

		// ==========================================
		// SECTION 2: STRENGTHS & WEAKNESSES
		// ==========================================
		if (yPosition > pageHeight - 70) {
			pdf.addPage()
			yPosition = margin + 10
		}

		yPosition = addSectionTitle('ANALIZA E PERFORMANCËS', yPosition, '2')

		// Two-column layout
		const colWidth = (contentWidth - 10) / 2

		// Strengths Column
		const strengthX = margin
		let strengthY = yPosition
		
		// Strengths box
		pdf.setFillColor(240, 253, 244) // Light green
		pdf.setDrawColor(colors.successGreen[0], colors.successGreen[1], colors.successGreen[2])
		pdf.setLineWidth(1.5)
		pdf.roundedRect(strengthX, strengthY, colWidth, 50, 4, 4, 'FD')
		
		strengthY += 8
		pdf.setFontSize(12)
		pdf.setFont('helvetica', 'bold')
		pdf.setTextColor(colors.successGreen[0], colors.successGreen[1], colors.successGreen[2])
		pdf.text('PIKAT E FORTA', strengthX + 5, strengthY)
		strengthY += 8

		reportData.strengths.forEach((strength, idx) => {
			// Badge number
			pdf.setFillColor(colors.successGreen[0], colors.successGreen[1], colors.successGreen[2])
			pdf.circle(strengthX + 8, strengthY - 1, 3, 'F')
			pdf.setFontSize(8)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.white[0], colors.white[1], colors.white[2])
			pdf.text(String(idx + 1), strengthX + 8, strengthY + 0.5, { align: 'center' })
			
			// Text
			pdf.setFontSize(9.5)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
			pdf.text(strength.area, strengthX + 14, strengthY)
			
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(8.5)
			pdf.setTextColor(colors.textLight[0], colors.textLight[1], colors.textLight[2])
			pdf.text(`${strength.score}% • ${strength.exercises} ushtrime`, strengthX + 14, strengthY + 4.5)
			
			strengthY += 10
		})

		// Weaknesses Column
		const weaknessX = margin + colWidth + 10
		let weaknessY = yPosition
		
		// Weaknesses box
		pdf.setFillColor(255, 247, 237) // Light orange
		pdf.setDrawColor(colors.warningOrange[0], colors.warningOrange[1], colors.warningOrange[2])
		pdf.setLineWidth(1.5)
		pdf.roundedRect(weaknessX, weaknessY, colWidth, 50, 4, 4, 'FD')
		
		weaknessY += 8
		pdf.setFontSize(12)
		pdf.setFont('helvetica', 'bold')
		pdf.setTextColor(colors.warningOrange[0], colors.warningOrange[1], colors.warningOrange[2])
		pdf.text('PIKAT E DOBËTA', weaknessX + 5, weaknessY)
		weaknessY += 8

		reportData.weaknesses.forEach((weakness, idx) => {
			// Badge number
			pdf.setFillColor(colors.warningOrange[0], colors.warningOrange[1], colors.warningOrange[2])
			pdf.circle(weaknessX + 8, weaknessY - 1, 3, 'F')
			pdf.setFontSize(8)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.white[0], colors.white[1], colors.white[2])
			pdf.text(String(idx + 1), weaknessX + 8, weaknessY + 0.5, { align: 'center' })
			
			// Text
			pdf.setFontSize(9.5)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
			pdf.text(weakness.area, weaknessX + 14, weaknessY)
			
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(8.5)
			pdf.setTextColor(colors.textLight[0], colors.textLight[1], colors.textLight[2])
			pdf.text(`${weakness.score}% • ${weakness.exercises} ushtrime`, weaknessX + 14, weaknessY + 4.5)
			
			weaknessY += 10
		})

		yPosition = yPosition + 50 + 15

		// ==========================================
		// SECTION 3: LEARNING STYLE
		// ==========================================
		if (yPosition > pageHeight - 80) {
			pdf.addPage()
			yPosition = margin + 10
		}

		yPosition = addSectionTitle('STILI I MËSIMIT & PREFERENCAT', yPosition, '3')

		const learningData = [
			{ icon: '•', label: 'Koha e Preferuar', value: reportData.learningStyle.preferredTime, color: [147, 51, 234] },
			{ icon: '•', label: 'Gjatësia Mesatare', value: reportData.learningStyle.averageSessionLength, color: [59, 130, 246] },
			{ icon: '•', label: 'Frekuenca', value: reportData.learningStyle.studyFrequency, color: [16, 185, 129] },
			{ icon: '•', label: 'Dita më e Mirë', value: reportData.learningStyle.bestPerformanceDay, color: [245, 158, 11] },
			{ icon: '•', label: 'Shkalla e Përfundimit', value: `${reportData.learningStyle.completionRate}%`, color: [239, 68, 68] }
		]

		learningData.forEach((item, idx) => {
			// Alternating background
			if (idx % 2 === 0) {
				pdf.setFillColor(colors.bgLight[0], colors.bgLight[1], colors.bgLight[2])
			} else {
				pdf.setFillColor(colors.white[0], colors.white[1], colors.white[2])
			}
			pdf.setDrawColor(colors.border[0], colors.border[1], colors.border[2])
			pdf.setLineWidth(0.3)
			pdf.roundedRect(margin, yPosition, contentWidth, 12, 2, 2, 'FD')
			
			// Colored left border
			pdf.setFillColor(item.color[0], item.color[1], item.color[2])
			pdf.roundedRect(margin, yPosition, 3, 12, 2, 2, 'F')

			// Icon with background
			pdf.setFillColor(item.color[0], item.color[1], item.color[2])
			pdf.setGState(new pdf.GState({ opacity: 0.15 }))
			pdf.circle(margin + 9, yPosition + 6, 5, 'F')
			pdf.setGState(new pdf.GState({ opacity: 1 }))
			
			pdf.setFontSize(11)
			pdf.text(item.icon, margin + 6.5, yPosition + 8.5)

			// Label
			pdf.setFontSize(9.5)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
			pdf.text(item.label, margin + 18, yPosition + 7.5)

			// Value
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(9)
			pdf.setTextColor(item.color[0], item.color[1], item.color[2])
			pdf.text(item.value, margin + contentWidth - 5, yPosition + 7.5, { align: 'right' })

			yPosition += 13
		})

		yPosition += 10

		// ==========================================
		// SECTION 4: RECOMMENDATIONS
		// ==========================================
		if (yPosition > pageHeight - 90) {
			pdf.addPage()
			yPosition = margin + 10
		}

		yPosition = addSectionTitle('REKOMANDIME TË PERSONALIZUARA', yPosition, '4')

		reportData.recommendations.forEach((rec, index) => {
			// Check if we need a new page
			if (yPosition > pageHeight - 35) {
				pdf.addPage()
				yPosition = margin + 10
			}

			// Recommendation box with shadow
			const boxHeight = Math.ceil(rec.length / 70) * 5 + 10
			
			// Shadow
			pdf.setFillColor(0, 0, 0)
			pdf.setGState(new pdf.GState({ opacity: 0.05 }))
			pdf.roundedRect(margin + 1, yPosition + 1, contentWidth, boxHeight, 3, 3, 'F')
			pdf.setGState(new pdf.GState({ opacity: 1 }))
			
			// Main box
			pdf.setFillColor(255, 251, 235) // Light yellow
			pdf.setDrawColor(colors.accentYellow[0], colors.accentYellow[1], colors.accentYellow[2])
			pdf.setLineWidth(0.8)
			pdf.roundedRect(margin, yPosition, contentWidth, boxHeight, 3, 3, 'FD')
			
			// Number badge with gradient effect
			const badgeX = margin + 8
			const badgeY = yPosition + boxHeight / 2
			
			// Outer circle (shadow)
			pdf.setFillColor(colors.accentYellow[0] - 30, colors.accentYellow[1] - 30, colors.accentYellow[2] - 30)
			pdf.circle(badgeX, badgeY, 4.5, 'F')
			
			// Inner circle
			pdf.setFillColor(colors.accentYellow[0], colors.accentYellow[1], colors.accentYellow[2])
			pdf.circle(badgeX, badgeY, 4, 'F')
			
			// Number
			pdf.setFontSize(10)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.white[0], colors.white[1], colors.white[2])
			pdf.text(String(index + 1), badgeX, badgeY + 1, { align: 'center' })

			// Priority indicator (if first 2 recommendations)
			if (index < 2) {
				pdf.setFontSize(7)
				pdf.setFont('helvetica', 'bold')
				pdf.setTextColor(colors.accentYellow[0], colors.accentYellow[1], colors.accentYellow[2])
				pdf.text('PRIORITET I LARTË', margin + 16, yPosition + 5)
			}

			// Recommendation text
			pdf.setFontSize(9.5)
			pdf.setFont('helvetica', 'normal')
			pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
			const recLines = pdf.splitTextToSize(rec, contentWidth - 28)
			pdf.text(recLines, margin + 16, yPosition + (index < 2 ? 10 : 7))

			yPosition += boxHeight + 5
		})

		yPosition += 8

		// ==========================================
		// SECTION 5: SUMMARY
		// ==========================================
		if (yPosition > pageHeight - 80) {
			pdf.addPage()
			yPosition = margin + 10
		}

		yPosition = addSectionTitle('PËRMBLEDHJE E PLOTË', yPosition, '5')

		// Enhanced summary box with gradient
		const summaryHeight = 62
		
		// Shadow
		pdf.setFillColor(0, 0, 0)
		pdf.setGState(new pdf.GState({ opacity: 0.08 }))
		pdf.roundedRect(margin + 2, yPosition + 2, contentWidth, summaryHeight, 5, 5, 'F')
		pdf.setGState(new pdf.GState({ opacity: 1 }))
		
		// Gradient background (simulated)
		pdf.setFillColor(236, 253, 245) // Very light green
		pdf.roundedRect(margin, yPosition, contentWidth, summaryHeight, 5, 5, 'F')
		
		pdf.setFillColor(240, 253, 244) // Light green
		pdf.roundedRect(margin, yPosition, contentWidth, 8, 5, 5, 'F')
		
		// Border
		pdf.setDrawColor(colors.successGreen[0], colors.successGreen[1], colors.successGreen[2])
		pdf.setLineWidth(1.5)
		pdf.roundedRect(margin, yPosition, contentWidth, summaryHeight, 5, 5, 'S')

		// Header
		pdf.setFontSize(11)
		pdf.setFont('helvetica', 'bold')
		pdf.setTextColor(colors.successGreen[0], colors.successGreen[1], colors.successGreen[2])
		pdf.text('GJENDJA E PËRGJITHSHME', margin + contentWidth / 2, yPosition + 6, { align: 'center' })

		yPosition += 14

		const summaryItems = [
			{ icon: '•', label: 'Niveli Aktual', value: reportData.metrics.level, color: [147, 51, 234] },
			{ icon: '•', label: 'Progres', value: `${reportData.metrics.totalExercises} ushtrime (${Math.round((reportData.metrics.completedExercises / reportData.metrics.totalExercises) * 100)}% të përfunduara)`, color: colors.primaryBlue },
			{ icon: '•', label: 'Kohë Totale', value: `${Math.round(reportData.metrics.totalTimeMinutes / 60)}h ${reportData.metrics.totalTimeMinutes % 60}min`, color: colors.warningOrange },
			{ icon: '•', label: 'Rekordi i vargut', value: `${reportData.metrics.longestStreak} ditë`, color: [239, 68, 68] },
			{ icon: '•', label: 'Fusha më e Fortë', value: `${reportData.strengths[0]?.area} (${reportData.strengths[0]?.score}%)`, color: colors.successGreen },
			{ icon: '•', label: 'Për Përmirësim', value: `${reportData.weaknesses[0]?.area} (${reportData.weaknesses[0]?.score}%)`, color: colors.warningOrange }
		]

		summaryItems.forEach((item, idx) => {
			const itemY = yPosition + (idx * 9)
			
			// Icon
			pdf.setFontSize(10)
			pdf.text(item.icon, margin + 5, itemY)
			
			// Label
			pdf.setFontSize(9)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.textDark[0], colors.textDark[1], colors.textDark[2])
			pdf.text(item.label + ':', margin + 13, itemY)
			
			// Value with color
			pdf.setFont('helvetica', 'normal')
			pdf.setTextColor(item.color[0], item.color[1], item.color[2])
			const valueText = pdf.splitTextToSize(item.value, contentWidth - 55)
			pdf.text(valueText, margin + 48, itemY)
		})

		yPosition += summaryHeight + 5

		// ==========================================
		// FOOTER - Enhanced for all pages
		// ==========================================
		const totalPages = pdf.getNumberOfPages()
		
		for (let i = 1; i <= totalPages; i++) {
			pdf.setPage(i)
			
			const footerY = pageHeight - 18
			
			// Footer background
			pdf.setFillColor(colors.bgLight[0], colors.bgLight[1], colors.bgLight[2])
			pdf.rect(0, footerY - 2, pageWidth, 18, 'F')
			
			// Top border line with gradient effect
			pdf.setDrawColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
			pdf.setLineWidth(1)
			pdf.line(margin, footerY, pageWidth - margin, footerY)
			
			// Left side - Logo and branding
			pdf.setFontSize(7)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
			pdf.text('AlbLingo', margin, footerY + 6)
			
			pdf.setFont('helvetica', 'normal')
			pdf.setFontSize(6.5)
			pdf.setTextColor(colors.textLight[0], colors.textLight[1], colors.textLight[2])
			pdf.text('Platformë Edukative për Gjuhën Shqipe', margin, footerY + 10)
			
			// Center - Generation date
			pdf.setFontSize(7)
			pdf.setFont('helvetica', 'normal')
			pdf.setTextColor(colors.textLight[0], colors.textLight[1], colors.textLight[2])
			pdf.text(`Gjeneruar: ${currentDate}`, pageWidth / 2, footerY + 8, { align: 'center' })
			
			// Right side - Page number with style
			pdf.setFillColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
			pdf.setGState(new pdf.GState({ opacity: 0.1 }))
			pdf.circle(pageWidth - margin - 10, footerY + 8, 8, 'F')
			pdf.setGState(new pdf.GState({ opacity: 1 }))
			
			pdf.setFontSize(8)
			pdf.setFont('helvetica', 'bold')
			pdf.setTextColor(colors.primaryBlue[0], colors.primaryBlue[1], colors.primaryBlue[2])
			pdf.text(`${i}`, pageWidth - margin - 10, footerY + 9, { align: 'center' })
			
			pdf.setFontSize(6)
			pdf.setFont('helvetica', 'normal')
			pdf.text(`nga ${totalPages}`, pageWidth - margin - 10, footerY + 12, { align: 'center' })
			
			// Confidentiality notice (on last page only)
			if (i === totalPages) {
				pdf.setFontSize(6)
				pdf.setFont('helvetica', 'italic')
				pdf.setTextColor(colors.textLight[0], colors.textLight[1], colors.textLight[2])
				pdf.text('© 2026 AlbLingo • Dokument Konfidencial', pageWidth / 2, pageHeight - 5, { align: 'center' })
			}
		}

		// Save the PDF
		const fileName = `Raport_${username.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`
		pdf.save(fileName)

		console.log('PDF u gjenerua me sukses:', fileName)
	} catch (error) {
		console.error('Gabim në gjenerimin e PDF:', error)
		throw error
	}
}

/**
 * Alternative: Export report by capturing DOM elements as images
 * This is more accurate for complex layouts with charts
 */
export async function exportUserReportWithChartsToPDF(
	modalElement: HTMLElement,
	username: string
): Promise<void> {
	try {
		// Hide buttons and non-essential elements
		const exportBtn = modalElement.querySelector('.export-report-btn') as HTMLElement
		const closeBtn = modalElement.querySelector('.modal-close') as HTMLElement
		
		if (exportBtn) exportBtn.style.display = 'none'
		if (closeBtn) closeBtn.style.display = 'none'

		// Wait a bit for styles to apply
		await new Promise(resolve => setTimeout(resolve, 100))

		// Capture the modal content
		const canvas = await html2canvas(modalElement, {
			scale: 2, // Higher quality
			useCORS: true,
			logging: false,
			backgroundColor: '#ffffff'
		})

		// Restore buttons
		if (exportBtn) exportBtn.style.display = ''
		if (closeBtn) closeBtn.style.display = ''

		// Create PDF
		const pdf = new jsPDF('p', 'mm', 'a4')
		const pageWidth = pdf.internal.pageSize.getWidth()
		const pageHeight = pdf.internal.pageSize.getHeight()

		// Calculate dimensions
		const imgWidth = pageWidth - 20 // 10mm margin on each side
		const imgHeight = (canvas.height * imgWidth) / canvas.width

		let heightLeft = imgHeight
		let position = 10 // Top margin

		// Add image data
		const imgData = canvas.toDataURL('image/png')

		// Add first page
		pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
		heightLeft -= pageHeight

		// Add additional pages if needed
		while (heightLeft >= 0) {
			position = heightLeft - imgHeight + 10
			pdf.addPage()
			pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
			heightLeft -= pageHeight
		}

		// Save
		const fileName = `Raport_${username.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`
		pdf.save(fileName)

		console.log('PDF me charts u gjenerua me sukses:', fileName)
	} catch (error) {
		console.error('Gabim në gjenerimin e PDF me charts:', error)
		throw error
	}
}
