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
import type { AdminPeriodStats, AdminStats } from '../api'

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
	periodStats: AdminPeriodStats | null
	periodLoading?: boolean
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
const colors = ['#1F6F8B', '#5BBD6C', '#FFC800', '#FF9600', '#4A9FD4', '#64748b']

function ChartCard({ title, children, half = false }: {
	title: string
	children: React.ReactNode
	half?: boolean
}) {
	return (
		<div className={`chart-card${half ? ' chart-card-half' : ''}`}>
			<h3 className="chart-title">{title}</h3>
			<div className="chart-body">{children}</div>
		</div>
	)
}

function StandardTooltip() {
	return <Tooltip contentStyle={tooltipStyle} />
}

function EmptyPeriodNote() {
	return (
		<p className="report-empty" style={{ margin: '0.75rem 0 0' }}>
			Nuk ka aktivitet në këtë periudhë. Statistikat rifreskohen nga database në kohë reale.
		</p>
	)
}

function PeriodSummaryCards({ periodStats }: { periodStats: AdminPeriodStats }) {
	const s = periodStats.summary
	const cards = [
		['Përdorues aktivë', s.active_users],
		['Përpjekje', s.total_attempts],
		['Saktësi', `${s.avg_score}%`],
		['Kohë (min)', s.time_spent_minutes],
	] as const
	return (
		<div className="stats-grid" style={{ marginBottom: '1rem' }}>
			{cards.map(([label, value]) => (
				<div className="stat-card" key={label}>
					<div className="stat-value">{value}</div>
					<div className="stat-label">{label}</div>
				</div>
			))}
		</div>
	)
}

function StatsCharts({
	stats,
	timeRange,
	periodStats,
}: Pick<AdminChartsProps, 'stats' | 'timeRange' | 'periodStats'>) {
	const summary = [
		{ name: 'Përdorues', value: stats.total_users, fill: colors[0] },
		{ name: 'Klasa', value: stats.total_classes, fill: colors[1] },
		{ name: 'Kurse', value: stats.total_courses, fill: colors[2] },
		{ name: 'Nivele', value: stats.total_levels, fill: colors[3] },
		{ name: 'Ushtrime', value: stats.total_exercises, fill: colors[4] },
		{ name: 'Përpjekje', value: stats.total_attempts, fill: colors[5] },
	]
	const content = summary.slice(1, 5)

	return (
		<div className="charts-container admin-charts">
			<section className="charts-section" aria-label="Përmbledhje">
				<div className="charts-grid charts-grid--full">
					<ChartCard title="Përmbledhje e platformës (të gjitha kohët)">
						<ResponsiveContainer width="100%" height="100%">
							<BarChart data={summary} margin={{ top: 16, right: 16, left: 8, bottom: 8 }}>
								<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
								<XAxis dataKey="name" tick={axisTick} />
								<YAxis tick={axisTick} />
								<StandardTooltip />
								<Bar dataKey="value" radius={[8, 8, 0, 0]} />
							</BarChart>
						</ResponsiveContainer>
					</ChartCard>
				</div>

				<div className="charts-row">
					<ChartCard title="Shpërndarja e përmbajtjes" half>
						<ResponsiveContainer width="100%" height="100%">
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

					<ChartCard title="Periudha e zgjedhur (live)" half>
						{periodStats ? (
							<div style={{ padding: '0.5rem 0.25rem', color: '#334155', fontSize: '0.95rem', lineHeight: 1.6 }}>
								<p style={{ margin: '0 0 0.5rem' }}>
									<strong>Burimi:</strong> {periodStats.data_source} (real-time)
								</p>
								<p style={{ margin: '0 0 0.5rem' }}>
									<strong>Nga:</strong> {new Date(periodStats.period_start).toLocaleString('sq-AL')}
								</p>
								<p style={{ margin: '0 0 0.5rem' }}>
									<strong>Deri:</strong> {new Date(periodStats.period_end).toLocaleString('sq-AL')}
								</p>
								<p style={{ margin: 0 }}>
									<strong>Gjeneruar:</strong> {new Date(periodStats.generated_at).toLocaleString('sq-AL')}
								</p>
							</div>
						) : (
							<EmptyPeriodNote />
						)}
					</ChartCard>
				</div>
			</section>

			<section className="scientific-section">
				<h2 className="section-title">
					Analiza sipas periudhës — {timeRange === 'weekly' ? 'Javore' : timeRange === 'monthly' ? 'Mujore' : 'Vjetore'}
				</h2>
				{periodStats && <PeriodSummaryCards periodStats={periodStats} />}
				{timeRange === 'weekly' && <WeeklyCharts periodStats={periodStats} />}
				{timeRange === 'monthly' && <MonthlyCharts periodStats={periodStats} />}
				{timeRange === 'yearly' && <YearlyCharts periodStats={periodStats} />}
			</section>
		</div>
	)
}

function WeeklyCharts({ periodStats }: { periodStats: AdminPeriodStats | null }) {
	const daily = periodStats?.series || []
	const hours = (periodStats?.peak_hours || []).filter((row) => Number(row.aktivitet) > 0)
	const hoursData = hours.length > 0 ? hours : (periodStats?.peak_hours || [])
	const categories = periodStats?.categories || []

	return (
		<>
			<ChartCard title="Statistika javore — aktiviteti ditor (DB live)">
				{daily.length === 0 ? <EmptyPeriodNote /> : (
					<ResponsiveContainer width="100%" height="100%">
						<ComposedChart data={daily}>
							<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
							<XAxis dataKey="ditë" tick={axisTick} />
							<YAxis yAxisId="left" tick={axisTick} />
							<YAxis yAxisId="right" orientation="right" tick={axisTick} />
							<StandardTooltip /><Legend />
							<Bar yAxisId="left" dataKey="përdorues" fill={colors[0]} radius={[8, 8, 0, 0]} name="Përdorues aktivë" />
							<Bar yAxisId="left" dataKey="përpjekje" fill={colors[1]} radius={[8, 8, 0, 0]} name="Përpjekje" />
							<Line yAxisId="right" type="monotone" dataKey="sukseRate" stroke={colors[3]} strokeWidth={3} name="% Suksesi" />
						</ComposedChart>
					</ResponsiveContainer>
				)}
			</ChartCard>
			<div className="charts-row">
				<ChartCard title="Orët më të frekuentuara (javore)" half>
					<ResponsiveContainer width="100%" height="100%">
						<BarChart data={hoursData}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis dataKey="orë" tick={axisTick} />
							<YAxis tick={axisTick} />
							<StandardTooltip />
							<Bar dataKey="aktivitet" fill={colors[4]} radius={[8, 8, 0, 0]} name="Përpjekje" />
						</BarChart>
					</ResponsiveContainer>
				</ChartCard>
				<ChartCard title="Performanca sipas kategorisë (javore)" half>
					{categories.length === 0 ? <EmptyPeriodNote /> : (
						<ResponsiveContainer width="100%" height="100%">
							<RadarChart data={categories.slice(0, 6)}>
								<PolarGrid />
								<PolarAngleAxis dataKey="kategori" tick={axisTick} />
								<PolarRadiusAxis domain={[0, 100]} />
								<Radar name="Saktësi %" dataKey="pikë" stroke={colors[0]} fill={colors[0]} fillOpacity={0.55} />
								<StandardTooltip />
							</RadarChart>
						</ResponsiveContainer>
					)}
				</ChartCard>
			</div>
		</>
	)
}

function MonthlyCharts({ periodStats }: { periodStats: AdminPeriodStats | null }) {
	const series = periodStats?.series || []
	const categories = periodStats?.categories || []

	return (
		<>
			<ChartCard title="Statistika mujore — javët e fundit (DB live)">
				{series.length === 0 ? <EmptyPeriodNote /> : (
					<ResponsiveContainer width="100%" height="100%">
						<AreaChart data={series}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis dataKey="muaj" tick={axisTick} />
							<YAxis tick={axisTick} />
							<StandardTooltip /><Legend />
							<Area type="monotone" dataKey="përdorues" stroke={colors[0]} fill={colors[0]} fillOpacity={0.35} name="Përdorues aktivë" />
							<Area type="monotone" dataKey="ushtrime" stroke={colors[1]} fill={colors[1]} fillOpacity={0.25} name="Përpjekje" />
						</AreaChart>
					</ResponsiveContainer>
				)}
			</ChartCard>
			<div className="charts-row">
				<ChartCard title="Saktësia dhe koha sipas javës" half>
					{series.length === 0 ? <EmptyPeriodNote /> : (
						<ResponsiveContainer width="100%" height="100%">
							<ComposedChart data={series}>
								<CartesianGrid strokeDasharray="3 3" />
								<XAxis dataKey="muaj" tick={axisTick} />
								<YAxis yAxisId="left" tick={axisTick} />
								<YAxis yAxisId="right" orientation="right" tick={axisTick} />
								<StandardTooltip /><Legend />
								<Bar yAxisId="right" dataKey="time_minutes" fill={colors[1]} name="Minuta" />
								<Line yAxisId="left" type="monotone" dataKey="sukseRate" stroke={colors[3]} strokeWidth={3} name="% Suksesi" />
							</ComposedChart>
						</ResponsiveContainer>
					)}
				</ChartCard>
				<ChartCard title="Kategoritë (30 ditët e fundit)" half>
					{categories.length === 0 ? <EmptyPeriodNote /> : (
						<ResponsiveContainer width="100%" height="100%">
							<BarChart data={categories.slice(0, 8)}>
								<CartesianGrid strokeDasharray="3 3" />
								<XAxis dataKey="kategori" tick={{ ...axisTick, fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
								<YAxis tick={axisTick} domain={[0, 100]} />
								<StandardTooltip />
								<Bar dataKey="pikë" fill={colors[0]} radius={[6, 6, 0, 0]} name="Saktësi %" />
							</BarChart>
						</ResponsiveContainer>
					)}
				</ChartCard>
			</div>
		</>
	)
}

function YearlyCharts({ periodStats }: { periodStats: AdminPeriodStats | null }) {
	const series = periodStats?.series || []
	const categories = periodStats?.categories || []

	const growth = series.map((row, index) => {
		const prev = index > 0 ? Number(series[index - 1].ushtrime || 0) : 0
		const current = Number(row.ushtrime || 0)
		const growthPct = prev > 0 ? Math.round(((current - prev) / prev) * 100) : (current > 0 ? 100 : 0)
		return {
			muaj: row.muaj,
			rritjaPërpjekje: growthPct,
			përdorues: row.përdorues,
			ushtrime: row.ushtrime,
		}
	})

	return (
		<>
			<ChartCard title="Statistika vjetore — 12 muajt e fundit (DB live)">
				{series.length === 0 ? <EmptyPeriodNote /> : (
					<ResponsiveContainer width="100%" height="100%">
						<BarChart data={series}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis dataKey="muaj" tick={{ ...axisTick, fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={70} />
							<YAxis tick={axisTick} />
							<StandardTooltip /><Legend />
							<Bar dataKey="përdorues" fill={colors[0]} name="Përdorues aktivë" />
							<Bar dataKey="ushtrime" fill={colors[1]} name="Përpjekje" />
						</BarChart>
					</ResponsiveContainer>
				)}
			</ChartCard>
			<div className="charts-row">
				<ChartCard title="Ndryshimi mujor i përpjekjeve (%)" half>
					{growth.length === 0 ? <EmptyPeriodNote /> : (
						<ResponsiveContainer width="100%" height="100%">
							<LineChart data={growth}>
								<CartesianGrid strokeDasharray="3 3" />
								<XAxis dataKey="muaj" tick={{ ...axisTick, fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={70} />
								<YAxis tick={axisTick} />
								<StandardTooltip /><Legend />
								<Line type="monotone" dataKey="rritjaPërpjekje" stroke={colors[0]} strokeWidth={3} name="Ndryshimi %" />
							</LineChart>
						</ResponsiveContainer>
					)}
				</ChartCard>
				<ChartCard title="Kategoritë (365 ditët e fundit)" half>
					{categories.length === 0 ? <EmptyPeriodNote /> : (
						<ResponsiveContainer width="100%" height="100%">
							<RadarChart data={categories.slice(0, 6)}>
								<PolarGrid />
								<PolarAngleAxis dataKey="kategori" tick={axisTick} />
								<PolarRadiusAxis domain={[0, 100]} />
								<Radar name="Saktësi %" dataKey="pikë" stroke={colors[0]} fill={colors[0]} fillOpacity={0.55} />
								<StandardTooltip />
							</RadarChart>
						</ResponsiveContainer>
					)}
				</ChartCard>
			</div>
			<ChartCard title="Saktësia dhe koha sipas muajit">
				{series.length === 0 ? <EmptyPeriodNote /> : (
					<ResponsiveContainer width="100%" height="100%">
						<ComposedChart data={series}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis dataKey="muaj" tick={{ ...axisTick, fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={70} />
							<YAxis yAxisId="left" tick={axisTick} />
							<YAxis yAxisId="right" orientation="right" tick={axisTick} />
							<StandardTooltip /><Legend />
							<Bar yAxisId="right" dataKey="time_minutes" fill={colors[1]} name="Minuta" />
							<Line yAxisId="left" type="monotone" dataKey="sukseRate" stroke={colors[3]} strokeWidth={3} name="% Suksesi" />
						</ComposedChart>
					</ResponsiveContainer>
				)}
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
						<div className="stat-icon">{icon}</div>
						<div className="stat-value">{value}</div>
						<div className="stat-label">{label}</div>
					</div>
				))}
			</div>
			<div className="time-range-selector">
				<h3 className="selector-title">Zgjedh periudhën kohore</h3>
				<div className="selector-buttons">
					{([['weekly', 'Javore'], ['monthly', 'Mujore'], ['yearly', 'Vjetore']] as const).map(([range, label]) => (
						<button
							key={range}
							type="button"
							className={`selector-btn ${props.timeRange === range ? 'active' : ''}`}
							onClick={() => props.onTimeRangeChange(range)}
						>
							{label}
						</button>
					))}
				</div>
				{props.periodLoading && (
					<p style={{ textAlign: 'center', marginTop: 10, color: '#1F6F8B', fontWeight: 600 }}>
						Duke ngarkuar statistikat e periudhës nga database…
					</p>
				)}
			</div>
			<StatsCharts stats={props.stats} timeRange={props.timeRange} periodStats={props.periodStats} />
			<div className="export-section">
				<h3 className="export-title">Eksporto të dhënat</h3>
				<p className="export-note" style={{ marginBottom: '15px' }}>
					Eksporti përdor të njëjtat të dhëna live të periudhës ({props.timeRange}) nga database.
				</p>
				<div className="export-buttons">
					<button type="button" className="export-btn" onClick={props.onExportCSV} disabled={props.isExporting}>Eksporto CSV</button>
					<button type="button" className="export-btn" onClick={props.onExportJSON} disabled={props.isExporting}>Eksporto JSON</button>
					<button type="button" className="export-btn" onClick={props.onExportPDF} disabled={props.isExporting}>Gjenero raport PDF</button>
					<button type="button" className="export-btn" onClick={props.onExportExcel} disabled={props.isExporting}>Eksporto Excel</button>
				</div>
				{props.isExporting && (
					<p style={{ textAlign: 'center', marginTop: '10px', color: '#1F6F8B', fontWeight: 'bold' }}>
						Duke eksportuar të dhënat…
					</p>
				)}
			</div>
		</>
	)
}
