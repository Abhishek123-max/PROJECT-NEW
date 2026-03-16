Hotel Management Front‑end (DineFlow)

## Getting Started

1. Install deps: `npm install`
2. Run dev server: `npm run dev`
3. Open http://localhost:3000

Project layout

- `src/app/page.tsx`: Welcome page with links
- `src/app/login/page.tsx`: Staff login
- `src/app/super-admin/login/page.tsx`: Super Admin login
- `src/app/onboarding/page.tsx`: Client onboarding form
- `src/app/globals.css`: Theme tokens and utilities (card, input, btn-primary)

Design tokens

- Primary: `#6A39FF`
- Radii: `16px / 12px / 8px`
- Background uses soft purple radial gradient per mockups

Next steps

- Wire inputs to form state and validation
- Hook up API routes for auth/onboarding
