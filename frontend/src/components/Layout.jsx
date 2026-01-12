/**
 * Main layout component with navigation sidebar
 */
export default function Layout({ children, activeView, onViewChange }) {
    const navItems = [
        { id: 'briefing', label: 'Daily Briefing', icon: '📊' },
        { id: 'audit', label: 'Calendar Audit', icon: '🔍' },
        { id: 'drafting', label: 'Drafting Assistant', icon: '✍️' },
        { id: 'settings', label: 'Settings', icon: '⚙️' },
    ]

    return (
        <div className="min-h-screen flex">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
                {/* Logo/Header */}
                <div className="p-6 border-b border-slate-700">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <span className="text-2xl">🎯</span>
                        <span>Chief of Staff</span>
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">Executive Dashboard</p>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-2">
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onViewChange(item.id)}
                            className={`w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 transition-all duration-200 ${activeView === item.id
                                ? 'bg-blue-500/20 text-blue-400 border-l-2 border-blue-500'
                                : 'text-slate-400 hover:text-white hover:bg-slate-700'
                                }`}
                        >
                            <span className="text-xl">{item.icon}</span>
                            <span className="font-medium">{item.label}</span>
                        </button>
                    ))}
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-slate-700">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                            CTO
                        </div>
                        <div>
                            <p className="text-sm font-medium text-white">Chief Technology Officer</p>
                            <p className="text-xs text-slate-400">TechVentures Inc.</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-auto">
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    )
}
