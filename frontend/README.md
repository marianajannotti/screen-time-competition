# Offy — Frontend (React + Vite)

This repository is a minimal React + Vite skeleton for the Offy screen-time app. It includes a mock API layer, authentication context, and example pages (Sign In, Sign Up, Dashboard, Profile, Add Screen Time).

## Prerequisites

- Node.js (v16+ recommended)
- npm (or yarn / pnpm) available in your PATH

This project was developed and tested on Windows (PowerShell). All command examples below use PowerShell syntax.

## Install dependencies

From the frontend directory run:

```powershell
# install runtime/dev deps from package.json
npm install

# install router used by the app (not added automatically)
npm install react-router-dom
```

Note: `react-router-dom` is required by the router introduced in this skeleton. If you prefer a different package manager, use the equivalent commands.

## Run development server

Start the Vite dev server:

```powershell
npm run dev
```

Open the address shown in the terminal (usually http://localhost:5173).

## Build and preview

Build for production:

```powershell
npm run build
```

Preview the production build locally:

```powershell
npm run preview
```

## Quick usage notes

- Demo user: A demo user is created in the mock DB stored in `localStorage`.
	- Username: `demo`
	- Email: `demo@example.com`
	- Password: (mocked — no password validation in the mock API)

- Pages available:
	- `/signin` — Sign in
	- `/signup` — Sign up
	- `/dashboard` — Protected: your dashboard and mock leaderboard
	- `/profile` — Protected: view/edit mock profile
	- `/add` — Protected: add screen time

## WebApp Features

- Log and track total screen time
- Set daily and weekly goals for reduced phone usage
- Earn streaks and rewards (badges) for meeting goals consistently
- Create personalized challenges with friends (e.g., who spends the least time on Instagram in a week or who has the lowest total screen time in a month)
- Compete on a leaderboard to see who is winning by staying off their phones
- Add friends and form groups to compete or compare progress
- Recover password (password reset flow)

## Mock API

All backend-like calls are in `src/api/mockApi.js`. Functions return Promises and persist a tiny in-memory DB to `localStorage` so that your actions survive reloads.

To swap the mock API for real endpoints, replace the exported functions in `src/api/mockApi.js` with network calls (fetch/axios). The `AuthContext` calls only these functions, so changing them keeps the rest of the app unchanged.

Example: replace `signIn()` implementation with a POST to your server:

```js
// pseudo-code
export async function signIn({ emailOrUsername, password }) {
	const res = await fetch('/api/auth/signin', { method: 'POST', body: JSON.stringify({ emailOrUsername, password }) })
	return res.json()
}
```

## Troubleshooting

- If you see "Module not found: react-router-dom": ensure you ran `npm install react-router-dom`.
- If `localStorage` data needs resetting during development, open the browser devtools and remove the key `offy_mock_db_v1` and `offy_user` from Storage.

## Files of interest

- `src/api/mockApi.js` — mock API layer (single place to change for real APIs)
- `src/contexts/AuthContext.jsx` — authentication provider used by pages
- `src/AppRouter.jsx` — router + route definitions
- `src/pages/*` — page components (SignIn, SignUp, Dashboard, Profile, AddScreenTime)


