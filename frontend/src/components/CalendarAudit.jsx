import { useState, useEffect } from 'react'
import { getCalendarAudit, saveFeedback } from '../services/api'

/**
 * Calendar Audit component - "Ruthless Calendar Audit"
 * Analyzes meetings against OKRs and flags misaligned ones
 */
export default function CalendarAudit() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [filter, setFilter] = useState('all') // all, flagged, high, medium, low
    const [expandedId, setExpandedId] = useState(null)
    const [savingFeedback, setSavingFeedback] = useState(null)

    useEffect(() => {
        fetchData()
    }, [])

    async function fetchData() {
        try {
            setLoading(true)
            const result = await getCalendarAudit()
            setData(result)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    async function handleAction(meetingId, action) {
        try {
            setSavingFeedback(meetingId)
            await saveFeedback(meetingId, action)
            // Update local state to show feedback was saved
            setData(prev => ({
                ...prev,
                meetings: prev.meetings.map(m =>
                    m.entry.id === meetingId
                        ? { ...m, userAction: action }
                        : m
                )
            }))
        } catch (err) {
            console.error('Failed to save feedback:', err)
        } finally {
            setSavingFeedback(null)
        }
    }

    const filteredMeetings = data?.meetings?.filter(meeting => {
        if (filter === 'all') return true
        if (filter === 'flagged') return meeting.flags.length > 0
        return meeting.strategic_value.toLowerCase() === filter
    }) || []

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-slate-400 animate-pulse-subtle">Loading calendar data...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="card bg-rose-500/10 border-rose-500/30">
                <p className="text-rose-400">Error: {error}</p>
                <button onClick={fetchData} className="btn-primary mt-4">Retry</button>
            </div>
        )
    }

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">🔍 Ruthless Calendar Audit</h1>
                <p className="text-slate-400">Analyzing your calendar against your OKRs and priorities</p>
            </div>

            {/* Summary Cards */}
            {data?.summary && (
                <div className="grid grid-cols-4 gap-4 mb-8">
                    <div className="card">
                        <p className="text-slate-400 text-sm mb-1">Total Meetings</p>
                        <p className="text-3xl font-bold text-white">{data.summary.total_meetings}</p>
                    </div>
                    <div className="card">
                        <p className="text-slate-400 text-sm mb-1">High Strategic Value</p>
                        <p className="text-3xl font-bold text-emerald-400">{data.summary.high_strategic_value}</p>
                    </div>
                    <div className="card">
                        <p className="text-slate-400 text-sm mb-1">Needs Attention</p>
                        <p className="text-3xl font-bold text-rose-400">{data.summary.needs_attention}</p>
                    </div>
                    <div className="card">
                        <p className="text-slate-400 text-sm mb-1">Calendar Health</p>
                        <div className="flex items-center gap-2">
                            <p className="text-3xl font-bold text-blue-400">{data.summary.health_score}%</p>
                            <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-blue-500 rounded-full transition-all duration-500"
                                    style={{ width: `${data.summary.health_score}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Filter Tabs */}
            <div className="flex gap-2 mb-6">
                {[
                    { id: 'all', label: 'All Meetings' },
                    { id: 'flagged', label: '⚠️ Flagged' },
                    { id: 'high', label: '🟢 High Value' },
                    { id: 'medium', label: '🟡 Medium' },
                    { id: 'low', label: '🔴 Low Value' },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setFilter(tab.id)}
                        className={`px-4 py-2 rounded-lg font-medium transition-all ${filter === tab.id
                                ? 'bg-blue-500 text-white'
                                : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Meetings List */}
            <div className="space-y-3">
                {filteredMeetings.map((meeting, index) => (
                    <div
                        key={meeting.entry.id}
                        className="card-hover animate-slide-up"
                        style={{ animationDelay: `${index * 50}ms` }}
                    >
                        <div
                            className="flex items-start gap-4 cursor-pointer"
                            onClick={() => setExpandedId(expandedId === meeting.entry.id ? null : meeting.entry.id)}
                        >
                            {/* Score Badge */}
                            <div className={`score-${meeting.strategic_value.toLowerCase()}`}>
                                {meeting.alignment_score}
                            </div>

                            {/* Meeting Info */}
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-1">
                                    <h3 className="font-semibold text-white">{meeting.entry.title}</h3>
                                    <span className={`badge-${meeting.strategic_value.toLowerCase()}`}>
                                        {meeting.strategic_value}
                                    </span>
                                    {meeting.userAction && (
                                        <span className="badge bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                            ✓ {meeting.userAction}
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-slate-400">
                                    {meeting.entry.date} • {meeting.entry.start_time} - {meeting.entry.end_time} • {meeting.entry.duration_minutes} min
                                </p>

                                {/* Flags */}
                                {meeting.flags.length > 0 && (
                                    <div className="mt-2 space-y-1">
                                        {meeting.flags.map((flag, i) => (
                                            <p key={i} className="text-sm text-amber-400 flex items-center gap-2">
                                                <span>⚠️</span> {flag}
                                            </p>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Recommendation */}
                            <div className="text-right">
                                <span className={`px-3 py-1 rounded-lg text-sm font-medium ${meeting.recommendation === 'Keep'
                                        ? 'bg-emerald-500/20 text-emerald-400'
                                        : meeting.recommendation === 'Delegate'
                                            ? 'bg-amber-500/20 text-amber-400'
                                            : 'bg-rose-500/20 text-rose-400'
                                    }`}>
                                    {meeting.recommendation}
                                </span>
                            </div>
                        </div>

                        {/* Expanded Details */}
                        {expandedId === meeting.entry.id && (
                            <div className="mt-4 pt-4 border-t border-slate-700 animate-fade-in">
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <p className="text-xs text-slate-500 uppercase mb-1">Organizer</p>
                                        <p className="text-slate-300">{meeting.entry.organizer}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-500 uppercase mb-1">Attendees</p>
                                        <p className="text-slate-300">{meeting.entry.attendees.join(', ')}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-500 uppercase mb-1">Meeting Type</p>
                                        <p className="text-slate-300">{meeting.entry.meeting_type.replace('_', ' ')}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-500 uppercase mb-1">Description</p>
                                        <p className="text-slate-300">{meeting.entry.description}</p>
                                    </div>
                                </div>

                                {meeting.okr_relevance.length > 0 && (
                                    <div className="mb-4">
                                        <p className="text-xs text-slate-500 uppercase mb-2">OKR Alignment</p>
                                        <div className="flex gap-2 flex-wrap">
                                            {meeting.okr_relevance.map((okr, i) => (
                                                <span key={i} className="badge bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                                    {okr}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Action Buttons */}
                                <div className="flex gap-3">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleAction(meeting.entry.id, 'keep'); }}
                                        disabled={savingFeedback === meeting.entry.id}
                                        className="btn-primary flex items-center gap-2"
                                    >
                                        ✓ Keep
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleAction(meeting.entry.id, 'delegate'); }}
                                        disabled={savingFeedback === meeting.entry.id}
                                        className="btn-secondary flex items-center gap-2"
                                    >
                                        👥 Delegate
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleAction(meeting.entry.id, 'decline'); }}
                                        disabled={savingFeedback === meeting.entry.id}
                                        className="btn-ghost text-rose-400 hover:text-rose-300 flex items-center gap-2"
                                    >
                                        ✕ Decline
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {filteredMeetings.length === 0 && (
                <div className="card text-center py-12">
                    <p className="text-slate-400">No meetings match the current filter.</p>
                </div>
            )}
        </div>
    )
}
