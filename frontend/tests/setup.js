import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock localStorage
beforeEach(() => {
  const localStorageMock = (() => {
    let store = {}
    return {
      getItem: (key) => store[key] || null,
      setItem: (key, value) => {
        store[key] = value.toString()
      },
      removeItem: (key) => {
        delete store[key]
      },
      clear: () => {
        store = {}
      }
    }
  })()
  
  global.localStorage = localStorageMock
})

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_API_BASE: 'http://localhost:5001'
  }
}))
