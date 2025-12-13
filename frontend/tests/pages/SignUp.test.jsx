import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SignUp from '../../src/pages/SignUp'

const mockNavigate = vi.fn()
const mockSignUp = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => ({
    signUp: mockSignUp
  })
}))

describe('SignUp Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign up form with all elements', () => {
    render(
      <BrowserRouter>
        <SignUp />
      </BrowserRouter>
    )

    expect(screen.getByText('Create Account')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
    expect(screen.getByText(/Already have an account\?/)).toBeInTheDocument()
  })

  it('updates input values when user types', async () => {
    const user = userEvent.setup()
    
    render(
      <BrowserRouter>
        <SignUp />
      </BrowserRouter>
    )

    const usernameInput = screen.getByPlaceholderText('Username')
    const emailInput = screen.getByPlaceholderText('Email')
    const passwordInput = screen.getByPlaceholderText('Password')

    await user.type(usernameInput, 'newuser')
    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')

    expect(usernameInput).toHaveValue('newuser')
    expect(emailInput).toHaveValue('newuser@example.com')
    expect(passwordInput).toHaveValue('password123')
  })

  it('calls signUp and navigates on successful submission', async () => {
    const user = userEvent.setup()
    mockSignUp.mockResolvedValueOnce({ username: 'newuser' })

    render(
      <BrowserRouter>
        <SignUp />
      </BrowserRouter>
    )

    await user.type(screen.getByPlaceholderText('Username'), 'newuser')
    await user.type(screen.getByPlaceholderText('Email'), 'newuser@example.com')
    await user.type(screen.getByPlaceholderText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'password123'
      })
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on failed sign up', async () => {
    const user = userEvent.setup()
    mockSignUp.mockRejectedValueOnce({ message: 'Email already in use' })

    render(
      <BrowserRouter>
        <SignUp />
      </BrowserRouter>
    )

    await user.type(screen.getByPlaceholderText('Username'), 'existinguser')
    await user.type(screen.getByPlaceholderText('Email'), 'existing@example.com')
    await user.type(screen.getByPlaceholderText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText('Email already in use')).toBeInTheDocument()
    })
  })

  it('has a link to sign in page', () => {
    render(
      <BrowserRouter>
        <SignUp />
      </BrowserRouter>
    )

    const signInLink = screen.getByRole('link', { name: /sign in/i })
    expect(signInLink).toBeInTheDocument()
    expect(signInLink).toHaveAttribute('href', '/signin')
  })
})
