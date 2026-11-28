import { useState, useEffect } from 'react'

interface ChildProgressEntry {
  id: string
  child_id: string
  concept_id: string
  state: 'not_started' | 'learning' | 'known' | 'evidence_assessed'
  started_at: string | null
  completed_at: string | null
  updated_at: string
}

interface ChildProfile {
  child_id: string
  child_name: string
}

interface ProgressStats {
  total_concepts: number
  by_state: Record<string, number>
  by_subject: Record<string, number>
}

const STATE_COLORS: Record<string, string> = {
  not_started: '#6b7280',
  learning: '#f59e0b',
  known: '#10b981',
  evidence_assessed: '#3b82f6',
}

const STATE_LABELS: Record<string, string> = {
  not_started: 'Not Started',
  learning: 'Learning',
  known: 'Known',
  evidence_assessed: 'Evidence Assessed',
}

interface ChildProgressProps {
  initialChildId?: string
}

export function ChildProgress({ initialChildId }: ChildProgressProps) {
  const [childId, setChildId] = useState<string>(initialChildId || 'child-1')
  const [profiles, setProfiles] = useState<ChildProfile[]>([])
  const [entries, setEntries] = useState<ChildProgressEntry[]>([])
  const [stats, setStats] = useState<ProgressStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'all' | 'known' | 'hidden' | 'dim'>('all')
  const [filterState, setFilterState] = useState<'all' | 'not_started' | 'learning' | 'known' | 'evidence_assessed'>('all')
  const [filterSubject, setFilterSubject] = useState<string | null>(null)
  const [filterConcept, setFilterConcept] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [childId])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [progressResp, conceptsResp] = await Promise.all([
        fetch(`/api/v1/child-progress/?child_id=${childId}`),
        fetch('/api/v1/concepts/'),
      ])

      if (!progressResp.ok || !conceptsResp.ok) {
        throw new Error('Failed to load data')
      }

      const progressData = await progressResp.json()
      const conceptsData = await conceptsResp.json()

      const entriesWithInfo = progressData.map((p: any) => {
        const concept = conceptsData.concepts.find((c: any) => c.id === p.concept_id)
        const stateColor = STATE_COLORS[p.state] || '#6b7280'
        const stateLabel = STATE_LABELS[p.state] || p.state
        const subjectDisplay = concept 
          ? `${concept.subject_id ? 'Subject ' + concept.subject_id : 'No Subject'}: ${concept.name}`
          : 'Unknown'
        return {
          ...p,
          concept_name: concept ? concept.name : 'Unknown concept',
          subject_display: subjectDisplay,
          state_color: stateColor,
          state_label: stateLabel,
        }
      })

      setEntries(entriesWithInfo)
      setProfiles(
        [...new Set(entriesWithInfo.map((e: any) => ({ child_id: e.child_id, child_name: `Child ${e.child_id}` })))]
      )

      const byState: Record<string, number> = { not_started: 0, learning: 0, known: 0, evidence_assessed: 0 }
      const bySubject: Record<string, number> = {}
      for (const e of entriesWithInfo) {
        byState[e.state] = (byState[e.state] || 0) + 1
        const subj = e.subject_display
        bySubject[subj] = (bySubject[subj] || 0) + 1
      }

      setStats({
        total_concepts: entriesWithInfo.length,
        by_state: byState,
        by_subject: bySubject,
      })
    } catch (e: any) {
      setError(e.message || 'Failed to load progress data')
    } finally {
      setLoading(false)
    }
  }

  async function updateState(newState: string) {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`/api/v1/child-progress/${entries[0]?.id}/update?state=${newState}`, {
        method: 'POST',
      })
      if (!resp.ok) {
        const err = await resp.text()
        throw new Error(err || 'Failed to update state')
      }
      const updated = await resp.json()
      
      setEntries(entries.map((e: any) =>
        e.id === updated.id ? { ...e, state: updated.state, started_at: updated.started_at, completed_at: updated.completed_at, updated_at: updated.updated_at } : e
      )
      )
      
      loadData()
    } catch (e: any) {
      setError(e.message || 'Failed to update state')
    } finally {
      setLoading(false)
    }
  }

  async function deleteEntry(id: string) {
    if (!confirm('Delete this progress entry?')) return
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`/api/v1/child-progress/${id}`, { method: 'DELETE' })
      if (!resp.ok) {
        const err = await resp.text()
        throw new Error(err || 'Failed to delete entry')
      }
      setEntries(entries.filter((e: any) => e.id !== id))
      setStats({
        total_concepts: entries.filter((e: any) => e.id !== id).length,
        by_state: { not_started: 0, learning: 0, known: 0, evidence_assessed: 0 },
        by_subject: {},
      })
    } catch (e: any) {
      setError(e.message || 'Failed to delete entry')
    } finally {
      setLoading(false)
    }
  }

  const displayEntries = entries.filter((e: any) => {
    if (filterState !== 'all' && e.state !== filterState) return false
    if (filterConcept && e.concept_id !== filterConcept) return false
    if (mode === 'known' && e.state !== 'known') return false
    return true
  })

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h2>Child Learning Progress Tracker</h2>
      
      <div style={{ marginBottom: '1.5rem', padding: '0.5rem', backgroundColor: '#f0f4f8', borderRadius: '6px' }}>
        <strong>Child Profile:</strong> 
        <select 
          value={childId} 
          onChange={(e) => setChildId(e.target.value)}
          style={{ padding: '0.25rem 0.5rem', marginLeft: '0.5rem' }}
        >
          {profiles.map((p: any) => (
            <option key={p.child_id} value={p.child_id}>{p.child_name}</option>
          ))}
        </select>
      </div>

      {stats && (
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <div style={{ backgroundColor: '#e2e8f0', padding: '0.5rem', borderRadius: '4px' }}>
              <small>Total Concepts</small>
              <div style={{ fontSize: 1.5, fontWeight: 'bold' }}>{stats.total_concepts}</div>
            </div>
            <div style={{ backgroundColor: '#e2e8f0', padding: '0.5rem', borderRadius: '4px' }}>
              <small>Not Started</small>
              <div style={{ color: '#6b7280', fontSize: 1.5, fontWeight: 'bold' }}>{stats.by_state.not_started}</div>
            </div>
            <div style={{ backgroundColor: '#e2e8f0', padding: '0.5rem', borderRadius: '4px' }}>
              <small>Learning</small>
              <div style={{ color: '#f59e0b', fontSize: 1.5, fontWeight: 'bold' }}>{stats.by_state.learning}</div>
            </div>
            <div style={{ backgroundColor: '#e2e8f0', padding: '0.5rem', borderRadius: '4px' }}>
              <small>Known</small>
              <div style={{ color: '#10b981', fontSize: 1.5, fontWeight: 'bold' }}>{stats.by_state.known}</div>
            </div>
            <div style={{ backgroundColor: '#e2e8f0', padding: '0.5rem', borderRadius: '4px' }}>
              <small>Evidence Assessed</small>
              <div style={{ color: '#3b82f6', fontSize: 1.5, fontWeight: 'bold' }}>{stats.by_state.evidence_assessed}</div>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '1.5rem', backgroundColor: '#f0f4f8', padding: '0.5rem', borderRadius: '6px' }}>
        <strong>View Mode:</strong> 
        <button
          onClick={() => setMode('all')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.25rem', 
            border: mode === 'all' ? '1px solid #3b82f6' : 'none',
            background: mode === 'all' ? '#3b82f6' : 'transparent',
            color: mode === 'all' ? 'white' : '#333',
          }}
        >
          All
        </button>
        <button
          onClick={() => setMode('known')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.25rem', 
            border: mode === 'known' ? '1px solid #10b981' : 'none',
            background: mode === 'known' ? '#10b981' : 'transparent',
            color: mode === 'known' ? 'white' : '#333',
          }}
        >
          Known Only
        </button>
        <button
          onClick={() => setMode('hidden')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.25rem', 
            border: mode === 'hidden' ? '1px solid #6b7280' : 'none',
            background: mode === 'hidden' ? '#6b7280' : 'transparent',
            color: mode === 'hidden' ? 'white' : '#333',
          }}
        >
          Hide
        </button>
        <button
          onClick={() => setMode('dim')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.25rem', 
            border: mode === 'dim' ? '1px solid #f59e0b' : 'none',
            background: mode === 'dim' ? '#f59e0b' : 'transparent',
            color: mode === 'dim' ? 'white' : '#333',
          }}
        >
          Dim
        </button>
      </div>

      <div style={{ marginBottom: '1.5rem', backgroundColor: '#f0f4f8', padding: '0.5rem', borderRadius: '6px' }}>
        <strong>State Filter:</strong> 
        <button
          onClick={() => setFilterState('all')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.1rem', 
            border: filterState === 'all' ? '1px solid #3b82f6' : 'none',
            background: filterState === 'all' ? '#3b82f6' : 'transparent',
            color: filterState === 'all' ? 'white' : '#333',
          }}
        >
          All
        </button>
        <button
          onClick={() => setFilterState('not_started')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.1rem', 
            border: filterState === 'not_started' ? '1px solid #6b7280' : 'none',
            background: filterState === 'not_started' ? '#6b7280' : 'transparent',
            color: filterState === 'not_started' ? 'white' : '#333',
          }}
        >
          Not Started
        </button>
        <button
          onClick={() => setFilterState('learning')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.1rem', 
            border: filterState === 'learning' ? '1px solid #f59e0b' : 'none',
            background: filterState === 'learning' ? '#f59e0b' : 'transparent',
            color: filterState === 'learning' ? 'white' : '#333',
          }}
        >
          Learning
        </button>
        <button
          onClick={() => setFilterState('known')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.1rem', 
            border: filterState === 'known' ? '1px solid #10b981' : 'none',
            background: filterState === 'known' ? '#10b981' : 'transparent',
            color: filterState === 'known' ? 'white' : '#333',
          }}
        >
          Known
        </button>
        <button
          onClick={() => setFilterState('evidence_assessed')}
          style={{ 
            padding: '0.25rem 0.5rem', 
            marginRight: '0.1rem', 
            border: filterState === 'evidence_assessed' ? '1px solid #3b82f6' : 'none',
            background: filterState === 'evidence_assessed' ? '#3b82f6' : 'transparent',
            color: filterState === 'evidence_assessed' ? 'white' : '#333',
          }}
        >
          Evidence Assessed
        </button>
      </div>

      <div style={{ marginBottom: '1.5rem', backgroundColor: '#f0f4f8', padding: '0.5rem', borderRadius: '6px' }}>
        <strong>Subject Filter:</strong> 
        <select
          onChange={(e) => setFilterSubject(e.target.value || null)}
          style={{ padding: '0.25rem 0.5rem', marginLeft: '0.5rem' }}
        >
          <option value="">All Subjects</option>
          {['Math', 'Science', 'Language', 'History'].map((s: string) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: '1.5rem', backgroundColor: '#f0f4f8', padding: '0.5rem', borderRadius: '6px' }}>
        <strong>Concept Filter:</strong> 
        <select
          onChange={(e) => setFilterConcept(e.target.value || null)}
          style={{ padding: '0.25rem 0.5rem', marginLeft: '0.5rem' }}
        >
          <option value="">All Concepts</option>
        </select>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>Loading...</div>
      ) : error ? (
        <div style={{ color: '#dc3545', marginTop: '2rem' }}>Error: {error}</div>
      ) : entries.length === 0 ? (
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>No progress entries found.</div>
      ) : (
        <div style={{ 
          marginTop: '1rem', 
          maxHeight: '500px', 
          overflowY: 'auto', 
          backgroundColor: '#f8f9fa', 
          borderRadius: '6px',
          padding: '1rem'
        }}>
          {displayEntries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              No entries match the current filters.
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
              {displayEntries.map((e: any) => (
                <div
                  key={e.id}
                  style={{ 
                    backgroundColor: '#fff', 
                    padding: '1rem', 
                    borderRadius: '6px', 
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)', 
                    borderLeft: `4px solid ${e.state_color}`,
                    ...(mode === 'dim' && { opacity: 0.7 }),
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 'bold', color: e.state_color }}>{e.concept_name}</span>
                    <span style={{ fontSize: 0.875, color: '#666' }>{e.subject_display}</span>
                  </div>
                  
                  <div style={{ marginBottom: '0.5rem' }}>
                    <span style={{ 
                      display: 'inline-block', 
                      padding: '0.1rem 0.4rem', 
                      borderRadius: '3px', 
                      fontSize: 0.75, 
                      color: '#fff',
                      backgroundColor: e.state_color
                    }}>
                      {e.state_label}
                    </span>
                  </div>
                  
                  <div style={{ fontSize: 0.875, color: '#666' }}>
                    Updated: {new Date(e.updated_at).toLocaleString()}
                  </div>
                  
                  <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem' }}>
                    <button
                      onClick={() => updateState('not_started')}
                      style={{
                        flex: 1,
                        padding: '0.2rem',
                        borderRadius: '4px',
                        border: 'none',
                        fontSize: 0.75,
                        color: '#fff',
                        backgroundColor: '#6b7280',
                        cursor: 'pointer',
                      }}
                    >
                      Not Started
                    </button>
                    <button
                      onClick={() => updateState('learning')}
                      style={{
                        flex: 1,
                        padding: '0.2rem',
                        borderRadius: '4px',
                        border: 'none',
                        fontSize: 0.75,
                        color: '#fff',
                        backgroundColor: '#f59e0b',
                        cursor: 'pointer',
                      }}
                    >
                      Learning
                    </button>
                    <button
                      onClick={() => updateState('known')}
                      style={{
                        flex: 1,
                        padding: '0.2rem',
                        borderRadius: '4px',
                        border: 'none',
                        fontSize: 0.75,
                        color: '#fff',
                        backgroundColor: '#10b981',
                        cursor: 'pointer',
                      }}
                    >
                      Known
                    </button>
                    <button
                      onClick={() => updateState('evidence_assessed')}
                      style={{
                        flex: 1,
                        padding: '0.2rem',
                        borderRadius: '4px',
                        border: 'none',
                        fontSize: 0.75,
                        color: '#fff',
                        backgroundColor: '#3b82f6',
                        cursor: 'pointer',
                      }}
                    >
                      Evidence Assessed
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0', backgroundColor: '#f0f4f8', borderRadius: '0 0 6px 6px' }}>
        <button
          onClick={() => {
            window.location.href = `/api/v1/child-progress/?create=1&child_id=${childId}`
          }}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            border: 'none',
            fontSize: '0.875rem',
            color: '#fff',
            backgroundColor: '#3b82f6',
            cursor: 'pointer',
          }}
        >
          New Progress Entry
        </button>
      </div>
    </div>
  )
}
