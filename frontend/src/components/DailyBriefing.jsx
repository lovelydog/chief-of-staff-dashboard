import { useState, useEffect } from 'react'
import { getDailyBriefing, getAvailableDates } from '../services/api'

/**
 * Daily Briefing component
 * Shows today's schedule with strategic value scores
 */
export default function DailyBriefing() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [availableDates, setAvailableDates] = useState([])
    const [selectedDate, setSelectedDate] = useState(null)

    useEffect(() => {
        fetchAvailableDates()
    }, [])

    useEffect(() => {
        if (selectedDate) {
            fetchBriefing(selectedDate)
        }
    }, [selectedDate])

    async function fetchAvailableDates() {
        try {
            const result = await getAvailableDates()
            setAvailableDates(result.dates)
            // Default to first available date
            if (result.dates.length > 0) {
                setSelectedDate(result.dates[0])
            }
        } catch (err) {
            setError(err.message)
            setLoading(false)
        }
    }

    async function fetchBriefing(date) {
        try {
            setLoading(true)
            const result = await getDailyBriefing(date)
            setData(result)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        })
    }

    if (loading && !data) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-slate-400 animate-pulse-subtle">Loading your briefing...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="card bg-rose-500/10 border-rose-500/30">
                <p className="text-rose-400">Error: {error}</p>
                <button onClick={() => fetchBriefing(selectedDate)} className="btn-primary mt-4">Retry</button>
            </div>
        )
    }

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="flex items-start justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📊 Daily Briefing</h1>
                    <p className="text-slate-400">Your schedule with strategic value insights</p>
                </div>

                {/* Date Selector */}
                <select
                    value={selectedDate || ''}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="input w-auto"
                >
                    {availableDates.map(date => (
                        <option key={date} value={date}>
                            {formatDate(date)}
                        </option>
                    ))}
                </select>
            </div>

            {data && (
                <>
                    {/* Stats Row */}
                    <div className="grid grid-cols-4 gap-4 mb-8">
                        <div className="card bg-gradient-to-br from-slate-800 to-slate-850">
                            <p className="text-slate-400 text-sm mb-1">Total Meetings</p>
                            <p className="text-3xl font-bold text-white">{data.total_meetings}</p>
                        </div>
                        <div className="card bg-gradient-to-br from-slate-800 to-slate-850">
                            <p className="text-slate-400 text-sm mb-1">Total Hours</p>
                            <p className="text-3xl font-bold text-white">{data.total_hours}h</p>
                        </div>
                        <div className="card bg-gradient-to-br from-slate-800 to-slate-850">
                            <p className="text-slate-400 text-sm mb-1">Strategic Hours</p>
                            <p className="text-3xl font-bold text-emerald-400">{data.strategic_hours}h</p>
                        </div>
                        <div className="card bg-gradient-to-br from-slate-800 to-slate-850">
                            <p className="text-slate-400 text-sm mb-1">Strategic %</p>
                            <div className="flex items-center gap-3">
                                <p className={`text-3xl font-bold ${data.strategic_percentage >= 60 ? 'text-emerald-400' :
                                        data.strategic_percentage >= 40 ? 'text-amber-400' : 'text-rose-400'
                                    }`}>
                                    {data.strategic_percentage}%
                                </p>
                                <div className="flex-1">
                                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all duration-700 ${data.strategic_percentage >= 60 ? 'bg-emerald-500' :
                                                    data.strategic_percentage >= 40 ? 'bg-amber-500' : 'bg-rose-500'
                                                }`}
                                            style={{ width: `${data.strategic_percentage}%` }}
                                        />
                                    </div>
                                    <p className="text-xs text-slate-500 mt-1">Goal: 60%</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Timeline */}
                    <div className="card p-0 overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-700">
                            <h2 className="text-lg font-semibold text-white">📅 {formatDate(data.date)}</h2>
                        </div>

                        <div className="divide-y divide-slate-700">
                            {data.meetings.length === 0 ? (
                                <div className="p-8 text-center">
                                    <p className="text-slate-400">No meetings scheduled for this day.</p>
                                </div>
                            ) : (
                                data.meetings.map((meeting, index) => (
                                    <div
                                        key={meeting.entry.id}
                                        className="p-6 hover:bg-slate-750 transition-colors animate-slide-up"
                                        style={{ animationDelay: `${index * 50}ms` }}
                                    >
                                        <div className="flex items-start gap-6">
                                            {/* Time Column */}
                                            <div className="w-24 flex-shrink-0">
                                                <p className="text-lg font-semibold text-white">{meeting.entry.start_time}</p>
                                                <p className="text-sm text-slate-500">{meeting.entry.duration_minutes} min</p>
                                            </div>

                                            {/* Timeline Dot */}
                                            <div className="relative flex-shrink-0">
                                                <div className={`w-4 h-4 rounded-full ${meeting.strategic_value === 'High' ? 'bg-emerald-500' :
                                                        meeting.strategic_value === 'Medium' ? 'bg-amber-500' : 'bg-rose-500'
                                                    }`} />
                                                {index < data.meetings.length - 1 && (
                                                    <div className="absolute top-4 left-1.5 w-0.5 h-16 bg-slate-700" />
                                                )}
                                            </div>

                                            {/* Meeting Details */}
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-lg font-semibold text-white">{meeting.entry.title}</h3>
                                                    <span className={`badge-${meeting.strategic_value.toLowerCase()}`}>
                                                        {meeting.strategic_value} Value
                                                    </span>
                                                </div>
                                                <p className="text-sm text-slate-400 mb-2">
                                                    {meeting.entry.description}
                                                </p>
                                                <p className="text-sm text-slate-500">
                                                    👤 {meeting.entry.organizer} • 👥 {meeting.entry.attendees.length} attendees
                                                </p>

                                                {/* OKR Tags */}
                                                {meeting.okr_relevance.length > 0 && (
                                                    <div className="flex gap-2 mt-3">
                                                        {meeting.okr_relevance.map((okr, i) => (
                                                            <span key={i} className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">
                                                                🎯 {okr}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}

                                                {/* Flags */}
                                                {meeting.flags.length > 0 && (
                                                    <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                                                        {meeting.flags.map((flag, i) => (
                                                            <p key={i} className="text-sm text-amber-400">
                                                                ⚠️ {flag}
                                                            </p>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Score Ring */}
                                            <div className="flex-shrink-0">
                                                <div className={`score-${meeting.strategic_value.toLowerCase()}`}>
                                                    {meeting.alignment_score}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
