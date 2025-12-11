# Frontend Tests

This directory will contain frontend tests for the React application.

## Test Types

### Component Tests
Test individual React components in isolation using Vitest or Jest.

Example:
```javascript
// tests/frontend/components/Dashboard.test.jsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../../../offy-front/src/pages/Dashboard';

describe('Dashboard Component', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });
});
```

### Integration Tests
Test component interactions and API integration.

### End-to-End Tests
Test complete user workflows using Playwright or Cypress.

## Setup (Future)

```bash
# Install testing dependencies
cd offy-front
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom

# Run frontend tests
npm test
```

## Test Organization

```
tests/frontend/
├── components/     # Component unit tests
├── integration/    # Component interaction tests
└── e2e/           # End-to-end user workflow tests
```
