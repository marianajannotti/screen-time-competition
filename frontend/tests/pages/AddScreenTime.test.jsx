import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import AddScreenTime from '../../src/pages/AddScreenTime'

const mockNavigate = vi.fn()
const mockUser = { username: 'testuser', user_id: 'u1' }

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}))

describe('AddScreenTime Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders the add screen time form', () => {
    render(
      <BrowserRouter>
        <AddScreenTime />
      </BrowserRouter>
    )

    expect(screen.getByText('Log Your Screen Time')).toBeInTheDocument()
    expect(screen.getByLabelText('Date')).toBeInTheDocument()
    expect(screen.getByLabelText('App Name')).toBeInTheDocument()
  })

  it('allows user to select date and time', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <AddScreenTime />
      </BrowserRouter>
    )

    const dateInput = screen.getByLabelText('Date')
    await user.clear(dateInput)
    await user.type(dateInput, '2025-12-01')

    expect(dateInput).toHaveValue('2025-12-01')
  })

  it('saves screen time entry to localStorage', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <AddScreenTime />
      </BrowserRouter>
    )

    const appSelect = screen.getByLabelText('App Name')
    const submitButton = screen.getByRole('button', { name: /save/i })

    await user.selectOptions(appSelect, 'YouTube')
    await user.click(submitButton)

    await waitFor(() => {
      const stored = localStorage.getItem('offy_logs_u1')
      expect(stored).toBeTruthy()
      const logs = JSON.parse(stored)
      expect(logs.length).toBeGreaterThan(0)
    })
  })

  it('closes modal when close button is clicked', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <AddScreenTime />
      </BrowserRouter>
    )

    const closeButton = screen.getByRole('button', { name: '✕' })
    await user.click(closeButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('prevents future dates from being submitted', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <AddScreenTime />
      </BrowserRouter>
    )

    const dateInput = screen.getByLabelText('Date')
    const futureDate = new Date()
    futureDate.setDate(futureDate.getDate() + 1)
    const futureDateStr = futureDate.toISOString().slice(0, 10)

    await user.clear(dateInput)
    await user.type(dateInput, futureDateStr)

    const submitButton = screen.getByRole('button', { name: /save/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Date cannot be in the future')).toBeInTheDocument()
    })
  })
})
