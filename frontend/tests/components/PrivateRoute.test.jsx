import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import PrivateRoute from '../../src/components/PrivateRoute'

// Mock useAuth hook
const mockAuthContext = {
  isAuthenticated: true,
  loading: false
}

vi.mock('../../../offy-front/src/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

describe('PrivateRoute Component', () => {
  it('renders element when user is authenticated', () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.loading = false

    render(
      <BrowserRouter>
        <PrivateRoute element={<div>Protected Content</div>} />
      </BrowserRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('shows loading state while checking authentication', () => {
    mockAuthContext.isAuthenticated = false
    mockAuthContext.loading = true

    render(
      <BrowserRouter>
        <PrivateRoute element={<div>Protected Content</div>} />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('redirects to signin when user is not authenticated', () => {
    mockAuthContext.isAuthenticated = false
    mockAuthContext.loading = false

    render(
      <BrowserRouter>
        <PrivateRoute element={<div>Protected Content</div>} />
      </BrowserRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    // The Navigate component will redirect, so protected content won't render
  })
})
