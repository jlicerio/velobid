# VeloBid Frontend

React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui frontend for VeloBid.

## Quick Start

```bash
# Start the FastAPI backend on :8000 first, then:
npm run dev
```

The Vite dev server runs at `http://localhost:5173` and proxies `/api/*` to `http://localhost:8000`.

## Build

```bash
npm run build    # outputs to dist/
npm run preview  # preview the production build
```

## Tech Stack

| Layer | Choice |
|-------|--------|
| UI | React 19 |
| Language | TypeScript |
| Build | Vite 8 |
| Styling | Tailwind CSS 3 + CSS variables |
| Components | shadcn/ui (Radix primitives) |
| Routing | React Router 7 |
| Data fetching | TanStack Query 5 |
| Forms | React Hook Form + Zod |
| Icons | lucide-react |
| Markdown | react-markdown + remark-gfm |
| Toasts | sonner |

## Project Structure

```
src/
├── app/              # App bootstrap, providers, router
├── components/
│   ├── ui/           # shadcn/ui primitives
│   ├── shared/       # App-specific reusable components
│   └── chat/         # Chat sidebar components
├── features/         # Domain feature modules (planned)
├── lib/
│   ├── api/          # API client (apiFetch, SSE, query client)
│   ├── chat-store.tsx # Chat state management
│   ├── types.ts      # Chat & SSE types
│   └── utils.ts      # cn() helper
├── pages/            # Route-level page components
├── styles/           # Tailwind + shadcn theme
└── types/            # Domain TypeScript types
```

## Routes

| Route | Page | Access |
|-------|------|--------|
| `/login` | Login | Public |
| `/` | Projects | Authenticated |
| `/projects` | Project Dashboard | Authenticated |
| `/projects/:projectId` | Project Detail | Authenticated |
| `/projects/:projectId/documents` | Document Viewer | Authenticated |
| `/projects/:projectId/blueprints/analyze` | Blueprint Vision | Authenticated |
| `/residential` | Residential Estimates | Authenticated |
| `/settings` | Settings | Authenticated |

## Theme

VeloBid brand colors are defined as CSS variables in `src/styles/globals.css`:

- Primary: `#0b57d0` (hsl 214 89% 43%)
- Dark: `#1a365d`
- Neutral base for backgrounds and surfaces
