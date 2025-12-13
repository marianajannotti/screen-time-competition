import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SignIn from '../../src/pages/SignIn'

const mockNavigate = vi.fn()
const mockSignIn = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    signIn: mockSignIn
  })
}))

describe('SignIn Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign in form with all elements', () => {
    render(
      <BrowserRouter>
        <SignIn />
      </BrowserRouter>
    )

    expect(screen.getByText('Welcome back')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Email or username')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByText(/Need an account\?/)).toBeInTheDocument()
  })

  it('updates input values when user types', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <SignIn />
      </BrowserRouter>
    )

    const usernameInput = screen.getByPlaceholderText('Email or username')
    const passwordInput = screen.getByPlaceholderText('Password')

    await user.type(usernameInput, 'testuser')
    await user.type(passwordInput, 'password123')

    expect(usernameInput).toHaveValue('testuser')
    expect(passwordInput).toHaveValue('password123')
  })

  it('calls signIn and navigates on successful submission', async () => {
    const user = userEvent.setup()
    mockSignIn.mockResolvedValueOnce({ username: 'testuser' })

    render(
      <BrowserRouter>
        <SignIn />
      </BrowserRouter>
    )

    await user.type(screen.getByPlaceholderText('Email or username'), 'testuser')
    await user.type(screen.getByPlaceholderText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith({
        emailOrUsername: 'testuser',
        password: 'password123'
      })
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on failed sign in', async () => {
    const user = userEvent.setup()
    mockSignIn.mockRejectedValueOnce({ message: 'Invalid credentials' })

    render(
      <BrowserRouter>
        <SignIn />
      </BrowserRouter>
    )

    await user.type(screen.getByPlaceholderText('Email or username'), 'wronguser')
    await user.type(screen.getByPlaceholderText('Password'), 'wrongpass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('has a link to sign up page', () => {
    render(
      <BrowserRouter>
        <SignIn />
      </BrowserRouter>
    )

    const signUpLink = screen.getByRole('link', { name: /sign up/i })
    expect(signUpLink).toBeInTheDocument()
    expect(signUpLink).toHaveAttribute('href', '/signup')
  })
})
