import { useState } from 'react'
import Layout from './components/Layout'
import CalendarAudit from './components/CalendarAudit'
import DailyBriefing from './components/DailyBriefing'
import DraftingAssistant from './components/DraftingAssistant'
import Settings from './components/Settings'

function App() {
    const [activeView, setActiveView] = useState('briefing')

    const renderView = () => {
        switch (activeView) {
            case 'audit':
                return <CalendarAudit />
            case 'briefing':
                return <DailyBriefing />
            case 'drafting':
                return <DraftingAssistant />
            case 'settings':
                return <Settings />
            default:
                return <DailyBriefing />
        }
    }

    return (
        <Layout activeView={activeView} onViewChange={setActiveView}>
            {renderView()}
        </Layout>
    )
}

export default App
