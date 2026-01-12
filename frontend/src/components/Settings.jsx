import { useState, useEffect } from 'react'

/**
 * Settings component for managing calendar connections
 */
export default function Settings() {
    const [googleConnected, setGoogleConnected] = useState(false)
    const [appleConnected, setAppleConnected] = useState(false)
    const [appleId, setAppleId] = useState('')
    const [appPassword, setAppPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState(null)

    useEffect(() => {
        // Check URL params for OAuth callback
        const params = new URLSearchParams(window.location.search)
        if (params.get('google_connected') === 'true') {
            const token = params.get('token')
            if (token) {
                localStorage.setItem('google_token', token)
                setGoogleConnected(true)
                setMessage({ type: 'success', text: 'Google Calendar connected!' })
                // Clean URL
                window.history.replaceState({}, '', '/')
            }
        }
        if (params.get('error')) {
            setMessage({ type: 'error', text: params.get('error') })
            window.history.replaceState({}, '', '/')
        }

        // Check stored tokens
        if (localStorage.getItem('google_token')) {
            setGoogleConnected(true)
        }
        if (localStorage.getItem('apple_connected')) {
            setAppleConnected(true)
        }
    }, [])

    const connectGoogle = () => {
        window.location.href = '/api/auth/google'
    }

    const disconnectGoogle = () => {
        localStorage.removeItem('google_token')
        setGoogleConnected(false)
        setMessage({ type: 'success', text: 'Google Calendar disconnected' })
    }

    const connectApple = async () => {
        if (!appleId || !appPassword) {
            setMessage({ type: 'error', text: 'Please enter your Apple ID and app-specific password' })
            return
        }

        setLoading(true)
        try {
            const response = await fetch('/api/calendar/apple', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ apple_id: appleId, app_password: appPassword })
            })

            const data = await response.json()

            if (response.ok && data.connected) {
                localStorage.setItem('apple_connected', 'true')
                localStorage.setItem('apple_id', appleId)
                // Note: In production, NEVER store password in localStorage
                // Use a backend session or encrypted storage
                setAppleConnected(true)
                setMessage({ type: 'success', text: `Apple Calendar connected! Found ${data.events.length} events.` })
                setAppPassword('')
            } else {
                setMessage({ type: 'error', text: data.error || 'Failed to connect' })
            }
        } catch (err) {
            setMessage({ type: 'error', text: err.message })
        } finally {
            setLoading(false)
        }
    }

    const disconnectApple = () => {
        localStorage.removeItem('apple_connected')
        localStorage.removeItem('apple_id')
        setAppleConnected(false)
        setAppleId('')
        setMessage({ type: 'success', text: 'Apple Calendar disconnected' })
    }

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">⚙️ Settings</h1>
                <p className="text-slate-400">Connect your calendars to sync real events</p>
            </div>

            {/* Message Toast */}
            {message && (
                <div className={`mb-6 p-4 rounded-lg border animate-slide-up ${message.type === 'success'
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                    }`}>
                    {message.text}
                    <button
                        onClick={() => setMessage(null)}
                        className="float-right text-current opacity-50 hover:opacity-100"
                    >
                        ✕
                    </button>
                </div>
            )}

            <div className="grid grid-cols-2 gap-6">
                {/* Google Calendar */}
                <div className="card">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center">
                            <svg className="w-8 h-8" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Google Calendar</h2>
                            <p className="text-sm text-slate-400">Connect via OAuth</p>
                        </div>
                    </div>

                    {googleConnected ? (
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-emerald-400">
                                <span>✓</span> Connected
                            </div>
                            <button onClick={disconnectGoogle} className="btn-secondary w-full">
                                Disconnect
                            </button>
                        </div>
                    ) : (
                        <button onClick={connectGoogle} className="btn-primary w-full">
                            Connect Google Calendar
                        </button>
                    )}
                </div>

                {/* Apple Calendar */}
                <div className="card">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-orange-400 flex items-center justify-center text-white text-2xl font-bold">

                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Apple Calendar</h2>
                            <p className="text-sm text-slate-400">Connect via iCloud</p>
                        </div>
                    </div>

                    {appleConnected ? (
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-emerald-400">
                                <span>✓</span> Connected as {localStorage.getItem('apple_id')}
                            </div>
                            <button onClick={disconnectApple} className="btn-secondary w-full">
                                Disconnect
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <input
                                type="email"
                                placeholder="Apple ID (email)"
                                value={appleId}
                                onChange={(e) => setAppleId(e.target.value)}
                                className="input"
                            />
                            <input
                                type="password"
                                placeholder="App-specific password"
                                value={appPassword}
                                onChange={(e) => setAppPassword(e.target.value)}
                                className="input"
                            />
                            <p className="text-xs text-slate-500">
                                Generate an app-specific password at{' '}
                                <a
                                    href="https://appleid.apple.com/account/manage"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-400 hover:underline"
                                >
                                    appleid.apple.com
                                </a>
                            </p>
                            <button
                                onClick={connectApple}
                                disabled={loading}
                                className="btn-primary w-full"
                            >
                                {loading ? 'Connecting...' : 'Connect Apple Calendar'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Microsoft Outlook (Disabled) */}
                <div className="card opacity-50">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white text-xl font-bold">
                            O
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Microsoft Outlook</h2>
                            <p className="text-sm text-slate-400">Enterprise accounts</p>
                        </div>
                    </div>
                    <p className="text-sm text-slate-500 mb-3">
                        Requires Azure AD admin consent. Contact your IT admin.
                    </p>
                    <button disabled className="btn-secondary w-full opacity-50 cursor-not-allowed">
                        Not Available
                    </button>
                </div>

                {/* Instructions */}
                <div className="card bg-slate-800/50">
                    <h3 className="text-lg font-semibold text-white mb-3">📋 Setup Instructions</h3>
                    <div className="space-y-3 text-sm text-slate-400">
                        <div>
                            <p className="font-medium text-slate-300">Google Calendar:</p>
                            <p>Click "Connect" and authorize access. That's it!</p>
                        </div>
                        <div>
                            <p className="font-medium text-slate-300">Apple Calendar:</p>
                            <ol className="list-decimal list-inside space-y-1">
                                <li>Go to appleid.apple.com</li>
                                <li>Sign in → Security → App-Specific Passwords</li>
                                <li>Generate a new password for "Chief of Staff"</li>
                                <li>Enter your Apple ID and the generated password above</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
