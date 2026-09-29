import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
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
    <main>
      <h1>FreeStack</h1>
      <p>{statusLabel(status)}</p>
    </main>
  )
}
