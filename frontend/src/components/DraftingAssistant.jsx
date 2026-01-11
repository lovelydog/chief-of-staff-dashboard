import { useState } from 'react'
import { checkStyle } from '../services/api'

/**
 * Drafting Assistant component
 * Checks text against communication style guidelines
 */
export default function DraftingAssistant() {
    const [text, setText] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    async function handleCheck() {
        if (!text.trim()) return

        try {
            setLoading(true)
            setError(null)
            const response = await checkStyle(text)
            setResult(response)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    function handleClear() {
        setText('')
        setResult(null)
        setError(null)
    }

    function getScoreColor(score) {
        if (score >= 85) return 'text-emerald-400'
        if (score >= 70) return 'text-blue-400'
        if (score >= 50) return 'text-amber-400'
        return 'text-rose-400'
    }

    function getScoreRingColor(score) {
        if (score >= 85) return 'score-high'
        if (score >= 70) return 'bg-blue-500/20 text-blue-400 ring-2 ring-blue-500/50'
        if (score >= 50) return 'score-medium'
        return 'score-low'
    }

    function getSeverityColor(severity) {
        switch (severity) {
            case 'high': return 'bg-rose-500/20 text-rose-400 border-rose-500/30'
            case 'medium': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
            case 'low': return 'bg-slate-600/20 text-slate-400 border-slate-500/30'
            default: return 'bg-slate-600/20 text-slate-400 border-slate-500/30'
        }
    }

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">✍️ Drafting Assistant</h1>
                <p className="text-slate-400">Verify your message aligns with your communication style</p>
            </div>

            <div className="grid grid-cols-2 gap-6">
                {/* Input Section */}
                <div className="card">
                    <h2 className="text-lg font-semibold text-white mb-4">Your Draft</h2>
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste your message, email, or brain dump here...

Example:
Sorry to bother you, but I wanted to touch base about the project. We've made some progress and things are going well. I think we should circle back on this later when we have more information."
                        className="textarea h-80"
                    />
                    <div className="flex gap-3 mt-4">
                        <button
                            onClick={handleCheck}
                            disabled={loading || !text.trim()}
                            className="btn-primary flex-1 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <span className="animate-spin">⏳</span>
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    🔍 Analyze Style
                                </>
                            )}
                        </button>
                        <button
                            onClick={handleClear}
                            className="btn-secondary"
                        >
                            Clear
                        </button>
                    </div>
                </div>

                {/* Results Section */}
                <div className="space-y-6">
                    {error && (
                        <div className="card bg-rose-500/10 border-rose-500/30">
                            <p className="text-rose-400">Error: {error}</p>
                        </div>
                    )}

                    {result && (
                        <div className="animate-slide-up space-y-6">
                            {/* Score Card */}
                            <div className="card">
                                <div className="flex items-center gap-6">
                                    <div className={`w-20 h-20 rounded-full flex items-center justify-center font-bold text-2xl ${getScoreRingColor(result.score)}`}>
                                        {result.score}
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-white mb-1">Style Score</h3>
                                        <p className="text-slate-400">{result.summary}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Issues List */}
                            {result.issues && result.issues.length > 0 ? (
                                <div className="card">
                                    <h3 className="text-lg font-semibold text-white mb-4">
                                        Issues Found ({result.issues.length})
                                    </h3>
                                    <div className="space-y-4">
                                        {result.issues.map((issue, index) => (
                                            <div
                                                key={index}
                                                className={`p-4 rounded-lg border ${getSeverityColor(issue.severity)} animate-slide-up`}
                                                style={{ animationDelay: `${index * 100}ms` }}
                                            >
                                                <div className="flex items-start justify-between mb-2">
                                                    <span className="text-xs font-medium uppercase tracking-wider">
                                                        {issue.category}
                                                    </span>
                                                    <span className={`badge ${issue.severity === 'high' ? 'badge-low' :
                                                            issue.severity === 'medium' ? 'badge-medium' :
                                                                'bg-slate-600/30 text-slate-400 border border-slate-500/30'
                                                        }`}>
                                                        {issue.severity}
                                                    </span>
                                                </div>
                                                <p className="text-white mb-2">{issue.issue}</p>
                                                <p className="text-sm text-slate-400">
                                                    💡 {issue.suggestion}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : result && (
                                <div className="card bg-emerald-500/10 border-emerald-500/30">
                                    <div className="flex items-center gap-3">
                                        <span className="text-3xl">✅</span>
                                        <div>
                                            <h3 className="text-lg font-semibold text-emerald-400">Perfect!</h3>
                                            <p className="text-slate-400">No issues found. Your message follows the style guide well.</p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Style Reference */}
                            <div className="card">
                                <h3 className="text-lg font-semibold text-white mb-4">📋 Quick Reference</h3>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <p className="text-slate-500 uppercase text-xs mb-2">Do ✓</p>
                                        <ul className="space-y-1 text-slate-300">
                                            <li>• Lead with the conclusion (BLUF)</li>
                                            <li>• Include specific metrics</li>
                                            <li>• Add clear action items</li>
                                            <li>• Use active voice</li>
                                        </ul>
                                    </div>
                                    <div>
                                        <p className="text-slate-500 uppercase text-xs mb-2">Don't ✗</p>
                                        <ul className="space-y-1 text-slate-300">
                                            <li>• Start with "Sorry to bother..."</li>
                                            <li>• Use vague terms like "significant"</li>
                                            <li>• Over-apologize</li>
                                            <li>• Bury the main point</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {!result && !error && (
                        <div className="card text-center py-16">
                            <div className="text-5xl mb-4">📝</div>
                            <h3 className="text-lg font-semibold text-white mb-2">Ready to Analyze</h3>
                            <p className="text-slate-400 max-w-xs mx-auto">
                                Paste your draft on the left and click "Analyze Style" to check it against your communication guidelines.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
