import { useState, useEffect } from 'react'

interface HealthResponse {
  status: string
  service: string
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (typeof globalThis.fetch === 'undefined') return
    globalThis.fetch('/api/v1/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setHealth(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div style={styles.container}>Loading...</div>
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h1 style={styles.error}>Error</h1>
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <h1>tensor-pilot-ryan-vo</h1>
      <p>AI/ML developer tool for explorable prerequisite taxonomies</p>
      <div style={styles.status}>
        <strong>Backend Status:</strong> {health?.status} ({health?.service})
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '2rem',
    fontFamily: 'system-ui, sans-serif',
  },
  error: {
    color: '#dc3545',
  },
  status: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
}

export default App