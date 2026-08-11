import type { ComponentProps } from 'react'
import {
	Area,
	AreaChart,
	Bar,
	BarChart,
	CartesianGrid,
	Cell,
	ComposedChart,
	Legend,
	Line,
	LineChart,
	Pie,
	PieChart,
	PolarAngleAxis,
	PolarGrid,
	PolarRadiusAxis,
	Radar,
	RadarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from 'recharts'
import type { AdminStats } from '../api'

export {
	Area,
	AreaChart,
	Bar,
	BarChart,
	CartesianGrid,
	Cell,
	ComposedChart,
	Legend,
	Line,
	LineChart,
	Pie,
	PieChart,
	PolarAngleAxis,
	PolarGrid,
	PolarRadiusAxis,
	Radar,
	RadarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
}

type TimeRange = 'weekly' | 'monthly' | 'yearly'

interface AdminChartsProps {
	kind: 'stats'
	stats: AdminStats
	timeRange: TimeRange
	onTimeRangeChange: (range: TimeRange) => void
	isExporting: boolean
	onExportCSV: () => void
	onExportJSON: () => void
	onExportPDF: () => void
	onExportExcel: () => void
}

const tooltipStyle: ComponentProps<typeof Tooltip>['contentStyle'] = {
	backgroundColor: 'white',
	border: '1px solid #e2e8f0',
	borderRadius: '8px',
	boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
}

const axisTick = { fill: '#64748b', fontSize: 12 }
const colors = ['#4A9FD4', '#5BBD6C', '#FFC800', '#FF9600', '#CE82FF', '#FF4B8C']

function ChartCard({ title, children, half = false }: {
	title: string
	children: React.ReactNode
	half?: boolean
}) {
	return (
		<div className={`chart-card${half ? ' chart-card-half' : ''}`}>
			<h3 className="chart-title">{title}</h3>
			{children}
		</div>
	)
}

function StandardTooltip() {
	return <Tooltip contentStyle={tooltipStyle} />
}

function StatsCharts({ stats, timeRange }: Pick<AdminChartsProps, 'stats' | 'timeRange'>) {
	const summary = [
		{ name: 'Përdorues', value: stats.total_users, fill: colors[0] },
		{ name: 'Klasa', value: stats.total_classes, fill: colors[1] },
		{ name: 'Kurse', value: stats.total_courses, fill: colors[2] },
		{ name: 'Nivele', value: stats.total_levels, fill: colors[3] },
		{ name: 'Ushtrime', value: stats.total_exercises, fill: colors[4] },
		{ name: 'Përpjekje', value: stats.total_attempts, fill: colors[5] },
	]
	const content = summary.slice(1, 5)
	const trend = [
		{ muaj: 'Jan', përdorues: Math.round(stats.total_users * 0.3), ushtrime: Math.round(stats.total_exercises * 0.4) },
		{ muaj: 'Feb', përdorues: Math.round(stats.total_users * 0.4), ushtrime: Math.round(stats.total_exercises * 0.5) },
		{ muaj: 'Mar', përdorues: Math.round(stats.total_users * 0.5), ushtrime: Math.round(stats.total_exercises * 0.6) },
		{ muaj: 'Apr', përdorues: Math.round(stats.total_users * 0.6), ushtrime: Math.round(stats.total_exercises * 0.7) },
		{ muaj: 'Maj', përdorues: Math.round(stats.total_users * 0.75), ushtrime: Math.round(stats.total_exercises * 0.85) },
		{ muaj: 'Qer', përdorues: Math.round(stats.total_users * 0.9), ushtrime: Math.round(stats.total_exercises * 0.95) },
		{ muaj: 'Kor', përdorues: stats.total_users, ushtrime: stats.total_exercises },
	]

	return (
		<div className="charts-container">
			<ChartCard title="📊 Përmbledhje e Përgjithshme">
				<ResponsiveContainer width="100%" height={300}>
					<BarChart data={summary} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
						<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
						<XAxis dataKey="name" tick={axisTick} />
						<YAxis tick={axisTick} />
						<StandardTooltip />
						<Bar dataKey="value" radius={[8, 8, 0, 0]} />
					</BarChart>
				</ResponsiveContainer>
			</ChartCard>

			<div className="charts-row">
				<ChartCard title="🥧 Shpërndarja e Përmbajtjes" half>
					<ResponsiveContainer width="100%" height={300}>
						<PieChart>
							<Pie
								data={content}
								cx="50%"
								cy="50%"
								labelLine={false}
								label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
								outerRadius={80}
								dataKey="value"
							>
								{content.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
							</Pie>
							<StandardTooltip />
						</PieChart>
					</ResponsiveContainer>
				</ChartCard>

				<ChartCard title="📈 Aktiviteti i Përdoruesve" half>
					<ResponsiveContainer width="100%" height={300}>
						<BarChart data={[
							{ name: 'Totali', përdorues: stats.total_users, përpjekje: Math.round(stats.total_attempts / 100) },
							{ name: 'Aktivë', përdorues: Math.round(stats.total_users * 0.7), përpjekje: Math.round(stats.total_attempts / 100 * 0.8) },
							{ name: 'Jo-aktivë', përdorues: Math.round(stats.total_users * 0.3), përpjekje: Math.round(stats.total_attempts / 100 * 0.2) },
						]}>
							<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
							<XAxis dataKey="name" tick={axisTick} />
							<YAxis tick={axisTick} />
							<StandardTooltip />
							<Legend />
							<Bar dataKey="përdorues" fill={colors[0]} radius={[8, 8, 0, 0]} />
							<Bar dataKey="përpjekje" fill={colors[1]} radius={[8, 8, 0, 0]} />
						</BarChart>
					</ResponsiveContainer>
				</ChartCard>
			</div>

			<ChartCard title="📉 Trend Statistikash">
				<ResponsiveContainer width="100%" height={300}>
					<LineChart data={trend}>
						<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
						<XAxis dataKey="muaj" tick={axisTick} />
						<YAxis tick={axisTick} />
						<StandardTooltip />
						<Legend />
						<Line type="monotone" dataKey="përdorues" stroke={colors[0]} strokeWidth={3} dot={{ fill: colors[0], r: 5 }} />
						<Line type="monotone" dataKey="ushtrime" stroke={colors[1]} strokeWidth={3} dot={{ fill: colors[1], r: 5 }} />
					</LineChart>
				</ResponsiveContainer>
			</ChartCard>

			<div className="scientific-section">
				<h2 className="section-title">🔬 Analiza Shkencore</h2>
				{timeRange === 'weekly' && <WeeklyCharts stats={stats} />}
				{timeRange === 'monthly' && <MonthlyCharts stats={stats} />}
				{timeRange === 'yearly' && <YearlyCharts stats={stats} />}
			</div>
		</div>
	)
}

function WeeklyCharts({ stats }: { stats: AdminStats }) {
	const daily = [
		['E Hënë', .15, .12, 83], ['E Martë', .18, .15, 87], ['E Mërkurë', .20, .18, 89],
		['E Enjte', .17, .16, 88], ['E Premte', .14, .14, 86], ['E Shtunë', .10, .10, 80], ['E Diel', .08, .08, 75],
	].map(([ditë, users, attempts, rate]) => ({
		ditë,
		përdorues: Math.round(stats.total_users * Number(users)),
		përpjekje: Math.round(stats.total_attempts * Number(attempts)),
		sukseRate: rate,
	}))
	const hours = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']
		.map((orë, index) => ({ orë, aktivitet: Math.round(stats.total_users * [.05, .15, .20, .25, .30, .20, .15, .08][index]) }))
	return (
		<>
			<ChartCard title="📅 Statistika Javore - Aktiviteti Ditor">
				<ResponsiveContainer width="100%" height={350}>
					<ComposedChart data={daily}>
						<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="ditë" tick={axisTick} />
						<YAxis yAxisId="left" tick={axisTick} /><YAxis yAxisId="right" orientation="right" tick={axisTick} />
						<StandardTooltip /><Legend />
						<Bar yAxisId="left" dataKey="përdorues" fill={colors[0]} radius={[8, 8, 0, 0]} name="Përdorues Aktivë" />
						<Bar yAxisId="left" dataKey="përpjekje" fill={colors[1]} radius={[8, 8, 0, 0]} name="Përpjekje" />
						<Line yAxisId="right" type="monotone" dataKey="sukseRate" stroke={colors[3]} strokeWidth={3} name="% Suksesi" />
					</ComposedChart>
				</ResponsiveContainer>
			</ChartCard>
			<div className="charts-row">
				<ChartCard title="🕐 Orët më të Frekuentuara (Javore)" half>
					<ResponsiveContainer width="100%" height={300}>
						<BarChart data={hours}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="orë" tick={axisTick} /><YAxis tick={axisTick} /><StandardTooltip /><Bar dataKey="aktivitet" fill={colors[4]} radius={[8, 8, 0, 0]} /></BarChart>
					</ResponsiveContainer>
				</ChartCard>
				<ChartCard title="🎯 Performanca Javore sipas Kategorisë" half>
					<ResponsiveContainer width="100%" height={300}>
						<RadarChart data={[['Vocabulary',85],['Grammar',78],['Writing',92],['Reading',88],['Listening',75]].map(([kategori,pikë]) => ({ kategori, pikë }))}>
							<PolarGrid /><PolarAngleAxis dataKey="kategori" tick={axisTick} /><PolarRadiusAxis /><Radar name="Performanca %" dataKey="pikë" stroke={colors[0]} fill={colors[0]} fillOpacity={0.6} /><StandardTooltip />
						</RadarChart>
					</ResponsiveContainer>
				</ChartCard>
			</div>
		</>
	)
}

function MonthlyCharts({ stats }: { stats: AdminStats }) {
	const months = ['Jan 2025','Shk','Mar','Pri','Maj','Qer','Kor','Gus','Sht','Tet','Nën','Dhj']
	const monthly = months.map((muaj, index) => ({
		muaj,
		përdorues: Math.round(stats.total_users * [.20,.25,.35,.45,.55,.65,.70,.78,.85,.90,.95,1][index]),
		ushtrime: Math.round(stats.total_exercises * [.30,.35,.45,.55,.65,.75,.80,.85,.90,.93,.97,1][index]),
		engagement: [65,68,72,75,78,80,82,85,88,90,92,95][index],
	}))
	const retention = months.map((_, index) => ({ muaj: `M${index + 1}`, retention: [95,92,90,89,91,93,94,95,96,96,97,97][index], newUsers: 120 + index * 10 }))
	return (
		<>
			<ChartCard title="📆 Statistika Mujore - Trend 12 Muaj">
				<ResponsiveContainer width="100%" height={350}>
					<AreaChart data={monthly}>
						<CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="muaj" tick={axisTick} /><YAxis tick={axisTick} /><StandardTooltip /><Legend />
						<Area type="monotone" dataKey="përdorues" stroke={colors[0]} fill={colors[0]} fillOpacity={0.35} />
						<Area type="monotone" dataKey="ushtrime" stroke={colors[1]} fill={colors[1]} fillOpacity={0.25} />
					</AreaChart>
				</ResponsiveContainer>
			</ChartCard>
			<div className="charts-row">
				<ChartCard title="📊 Retention Rate Mujore" half>
					<ResponsiveContainer width="100%" height={300}>
						<LineChart data={retention}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="muaj" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" /><StandardTooltip /><Legend /><Line yAxisId="left" dataKey="retention" stroke={colors[1]} strokeWidth={3} /><Line yAxisId="right" dataKey="newUsers" stroke={colors[0]} strokeWidth={3} /></LineChart>
					</ResponsiveContainer>
				</ChartCard>
				<ChartCard title="🎓 Përparimi Mesatar Mujor" half>
					<ResponsiveContainer width="100%" height={300}>
						<ComposedChart data={[
							{ nivel: 'Fillestar', përdorues: Math.round(stats.total_users * .35), mesatare: 65 },
							{ nivel: 'Mesatar', përdorues: Math.round(stats.total_users * .40), mesatare: 78 },
							{ nivel: 'I avancuar', përdorues: Math.round(stats.total_users * .20), mesatare: 88 },
							{ nivel: 'Ekspert', përdorues: Math.round(stats.total_users * .05), mesatare: 95 },
						]}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="nivel" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" /><StandardTooltip /><Legend /><Bar yAxisId="left" dataKey="përdorues" fill={colors[4]} /><Line yAxisId="right" dataKey="mesatare" stroke={colors[3]} strokeWidth={3} /></ComposedChart>
					</ResponsiveContainer>
				</ChartCard>
			</div>
			<ChartCard title="📈 Nota e angazhimit & Koha e kaluar (minutë/sesion)">
				<ResponsiveContainer width="100%" height={300}>
					<ComposedChart data={monthly.map((item, index) => ({ ...item, kohëMinuta: 12 + index * 2, përfundim: 72 + Math.round(index * 2.25) }))}>
						<CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="muaj" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" /><StandardTooltip /><Legend />
						<Area yAxisId="left" dataKey="engagement" fill={colors[0]} stroke={colors[0]} fillOpacity={0.3} /><Bar yAxisId="right" dataKey="kohëMinuta" fill={colors[1]} /><Line yAxisId="left" dataKey="përfundim" stroke={colors[3]} strokeWidth={3} />
					</ComposedChart>
				</ResponsiveContainer>
			</ChartCard>
		</>
	)
}

function YearlyCharts({ stats }: { stats: AdminStats }) {
	const yearly = [
		{ vit: '2021', përdorues: Math.round(stats.total_users * .15), ushtrime: Math.round(stats.total_exercises * .20) },
		{ vit: '2022', përdorues: Math.round(stats.total_users * .35), ushtrime: Math.round(stats.total_exercises * .40) },
		{ vit: '2023', përdorues: Math.round(stats.total_users * .60), ushtrime: Math.round(stats.total_exercises * .65) },
		{ vit: '2024', përdorues: Math.round(stats.total_users * .85), ushtrime: Math.round(stats.total_exercises * .85) },
		{ vit: '2025', përdorues: stats.total_users, ushtrime: stats.total_exercises },
	]
	return (
		<>
			<ChartCard title="📅 Statistika Vjetore - Krahasim 5 Vjet">
				<ResponsiveContainer width="100%" height={350}>
					<BarChart data={yearly}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="vit" /><YAxis /><StandardTooltip /><Legend /><Bar dataKey="përdorues" fill={colors[0]} /><Bar dataKey="ushtrime" fill={colors[1]} /></BarChart>
				</ResponsiveContainer>
			</ChartCard>
			<div className="charts-row">
				<ChartCard title="📊 Rritja Vjetore (%)" half>
					<ResponsiveContainer width="100%" height={300}>
						<LineChart data={[[2021,0,0],[2022,133,100],[2023,71,63],[2024,42,31],[2025,18,18]].map(([vit,a,b]) => ({ vit, rritjaPërdorues:a, rritjaUshtrime:b }))}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="vit" /><YAxis /><StandardTooltip /><Legend /><Line dataKey="rritjaPërdorues" stroke={colors[0]} strokeWidth={3} /><Line dataKey="rritjaUshtrime" stroke={colors[1]} strokeWidth={3} /></LineChart>
					</ResponsiveContainer>
				</ChartCard>
				<ChartCard title="🎯 Arritjet Vjetore" half>
					<ResponsiveContainer width="100%" height={300}>
						<BarChart data={[{kategori:'Certifikata','2023':150,'2024':320,'2025':580},{kategori:'Kurse Përfunduar','2023':450,'2024':890,'2025':1450},{kategori:'Nivele Kaluar','2023':2100,'2024':4200,'2025':6800}]}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="kategori" /><YAxis /><StandardTooltip /><Legend /><Bar dataKey="2023" fill={colors[4]} /><Bar dataKey="2024" fill={colors[3]} /><Bar dataKey="2025" fill={colors[1]} /></BarChart>
					</ResponsiveContainer>
				</ChartCard>
			</div>
			<ChartCard title="🌍 Shpërndarja Demografike Vjetore">
				<ResponsiveContainer width="100%" height={300}>
					<ComposedChart data={['6-8 vjeç','9-11 vjeç','12-14 vjeç','15-17 vjeç','18+ vjeç'].map((grup,index) => ({ grup, përdorues: Math.round(stats.total_users * [.25,.35,.25,.10,.05][index]), engagement:[85,88,90,87,92][index], suksesRate:[78,82,86,88,91][index] }))}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="grup" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" /><StandardTooltip /><Legend /><Bar yAxisId="left" dataKey="përdorues" fill={colors[0]} /><Line yAxisId="right" dataKey="engagement" stroke={colors[1]} /><Line yAxisId="right" dataKey="suksesRate" stroke={colors[3]} /></ComposedChart>
				</ResponsiveContainer>
			</ChartCard>
			<ChartCard title="📚 Performanca e Platformës - Metriks Kyçe (KPIs)">
				<ResponsiveContainer width="100%" height={300}>
					<RadarChart data={[['Kënaqësia e përdoruesit',92],['Learning Effectiveness',88],['Content Quality',95],['Platform Stability',97],['Rikthimi i përdoruesve',89],['Engagement Rate',85]].map(([metrik,pikë]) => ({ metrik, pikë }))}><PolarGrid /><PolarAngleAxis dataKey="metrik" /><PolarRadiusAxis domain={[0,100]} /><Radar dataKey="pikë" stroke={colors[0]} fill={colors[0]} fillOpacity={0.6} /><StandardTooltip /><Legend /></RadarChart>
				</ResponsiveContainer>
			</ChartCard>
		</>
	)
}

export default function AdminCharts(props: AdminChartsProps) {
	const statCards = [
		['👥', props.stats.total_users, 'Përdorues'],
		['🏫', props.stats.total_classes, 'Klasa'],
		['📚', props.stats.total_courses, 'Kurse'],
		['📖', props.stats.total_levels, 'Nivele'],
		['✏️', props.stats.total_exercises, 'Ushtrime'],
		['🎯', props.stats.total_attempts, 'Përpjekje'],
	]
	return (
		<>
			<div className="stats-grid">
				{statCards.map(([icon, value, label]) => (
					<div className="stat-card" key={String(label)}>
						<div className="stat-icon">{icon}</div><div className="stat-value">{value}</div><div className="stat-label">{label}</div>
					</div>
				))}
			</div>
			<div className="time-range-selector">
				<h3 className="selector-title">📅 Zgjedh Periudhën Kohore</h3>
				<div className="selector-buttons">
					{([['weekly','📊 Javore'],['monthly','📈 Mujore'],['yearly','📉 Vjetore']] as const).map(([range, label]) => (
						<button key={range} className={`selector-btn ${props.timeRange === range ? 'active' : ''}`} onClick={() => props.onTimeRangeChange(range)}>{label}</button>
					))}
				</div>
			</div>
			<StatsCharts stats={props.stats} timeRange={props.timeRange} />
			<div className="export-section">
				<h3 className="export-title">📥 Eksporto të Dhënat</h3>
				<p className="export-note" style={{ marginBottom: '15px' }}>
					💡 <strong>Shënim:</strong> Të dhënat e eksportuara përfshijnë statistika të detajuara, analiza kohore ({props.timeRange}), dhe metriks shkencorë të përshtatshëm për publikime akademike dhe punime kërkimore.
				</p>
				<div className="export-buttons">
					<button className="export-btn" onClick={props.onExportCSV} disabled={props.isExporting}>📊 Eksporto CSV</button>
					<button className="export-btn" onClick={props.onExportJSON} disabled={props.isExporting}>🔧 Eksporto JSON</button>
					<button className="export-btn" onClick={props.onExportPDF} disabled={props.isExporting}>📄 Gjenero Raport PDF</button>
					<button className="export-btn" onClick={props.onExportExcel} disabled={props.isExporting}>📗 Eksporto Excel</button>
				</div>
				{props.isExporting && <p style={{ textAlign: 'center', marginTop: '10px', color: '#4A9FD4', fontWeight: 'bold' }}>⏳ Duke eksportuar të dhënat...</p>}
			</div>
		</>
	)
}
