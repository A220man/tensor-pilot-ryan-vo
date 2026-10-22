import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

beforeEach(() => {
  vi.resetAllMocks()
})

describe('App', () => {
  it('shows loading state initially', () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise(() => {})))
    render(<App />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('displays health data when fetch succeeds', async () => {
    const mockHealth = { status: 'healthy', service: 'tensor-pilot-ryan-vo' }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockHealth),
    }))

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Backend Status:')).toBeInTheDocument()
      expect(screen.getByText('healthy (tensor-pilot-ryan-vo)')).toBeInTheDocument()
    })
  })

  it('displays error when fetch fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })
})