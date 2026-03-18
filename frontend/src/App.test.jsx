import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

import App from './App'

class MockEventSource {
  constructor(url) {
    this.url = url
    this.listeners = {}
  }

  addEventListener(type, handler) {
    this.listeners[type] = handler
  }

  close() {}
}

describe('ClawSubmit App', () => {
  beforeEach(() => {
    vi.stubGlobal('EventSource', MockEventSource)
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('loads sample content into the chat panel', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Use Sample' }))
    expect(screen.getByTestId('chat-thread')).toHaveTextContent('麻烦报销一下')
  })

  it('parses and applies the summary suggestion', async () => {
    const parsePayload = {
      expense_type: '差旅-打车',
      amount: '86.50',
      date_time: '2026-03-18 21:30',
      from_to: '虹桥 -> 公司',
      project: '龙虾黑客松',
      cost_center: '市场部',
      summary: '',
      summary_suggestion: '龙虾黑客松差旅打车',
      attachment_path: '/samples/invoice.jpg',
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => parsePayload,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ checklist: ['a', 'b'] }),
      })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Use Sample' }))
    fireEvent.click(screen.getByRole('button', { name: 'Parse' }))

    await waitFor(() => expect(screen.getByDisplayValue('差旅-打车')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Apply Suggestion' }))
    expect(screen.getByRole('textbox', { name: '报销摘要' })).toHaveValue('龙虾黑客松差旅打车')
  })
})
