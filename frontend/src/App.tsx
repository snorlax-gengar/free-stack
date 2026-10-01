import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import { RequirementForm } from './features/requirement/RequirementForm.tsx'
import './App.css'

type BackendStatus = 'checking' | 'ok' | 'failed'

function statusLabel(status: BackendStatus): string {
  if (status === 'checking') {
    return 'Backend Status: Checking...'
  }
  if (status === 'ok') {
    return 'Backend Status: OK'
  }
  return 'Backend Status: Connection Failed'
}

export default function App() {
  const [status, setStatus] = useState<BackendStatus>('checking')

  useEffect(() => {
    let active = true

    getHealth()
      .then((health) => {
        if (!active) {
          return
        }
        setStatus(health.status === 'ok' ? 'ok' : 'failed')
      })
      .catch(() => {
        if (active) {
          setStatus('failed')
        }
      })

    return () => {
      active = false
    }
  }, [])

  return (
    <main className="shell">
      <header className="header">
        <div>
          <h1 className="brand">FreeStack</h1>
          <p className="tagline">무료/저비용 사이드프로젝트 인프라 추천</p>
        </div>
        <p className="health">{statusLabel(status)}</p>
      </header>
      <RequirementForm />
    </main>
  )
}
