# Product Requirements Document: VeloBid Frontend Rebuild

## 1. Executive Summary

VeloBid will rebuild its current vanilla JavaScript single-page application as a modern React 19 and TypeScript frontend while preserving the existing FastAPI backend, Docker deployment model, and complete product feature set. The rebuild is intended to improve maintainability, frontend velocity, UI consistency, mobile behavior, and the quality of the AI agent chat experience without disrupting the working production application.

The current application is stable and functional. It supports login, project management, bid generation, AI chat, document viewing, blueprint analysis, bid versioning, settings, line item tables, and residential estimates. However, the frontend is implemented as an inline vanilla JavaScript SPA served from FastAPI static files. As the product surface grows, that structure increases the cost of change, makes regression control harder, and limits the ability to deliver a polished ChatGPT/Gemini-style assistant experience.

The target frontend will be a componentized React application using Vite, TypeScript, Tailwind CSS, and shadcn/ui. The AI chat sidebar will be implemented using either CopilotKit or assistant-ui, selected during implementation after validating compatibility with VeloBid's existing `/api/v1/agent/chat` SSE stream, chat history APIs, speech controls, markdown tables, and project-scoped sessions.

The backend will remain unchanged for the rebuild. All existing `/api/v1/*` routes will continue to serve the product, and the new frontend will integrate through typed API clients, route-level data loading, and a development proxy. Production will continue to be served from the FastAPI container, with the React build output mounted or copied into the backend static directory.

## 2. Current State Assessment

### 2.1 Application Overview

VeloBid currently consists of:

| Area | Current State |
|---|---|
| Backend | FastAPI Python application |
| Frontend | Vanilla JavaScript SPA, inline/application script style |
| Static serving | FastAPI serves files at `/static/*`; root `/` loads the SPA |
| Container | Docker container running on port `8000` |
| Deployment | Tailscale Funnel at `https://velobid.tailfceaca.ts.net/` |
| API namespace | All product APIs are under `/api/v1/*` |
| API docs | Swagger at `/docs`, ReDoc at `/redoc`, OpenAPI at `/openapi.json` |

### 2.2 Current Frontend Capabilities

The current SPA includes the following verified capabilities:

| Capability | Current Behavior |
|---|---|
| Authentication | Bidder selection, user ID, password, login against `/api/v1/auth/login` |
| Project dashboard | Grid cards, archive/unarchive, active/archive filtering |
| Agent chat sidebar | Project-scoped sessions, resizable sidebar, SSE streaming, localStorage session mapping |
| Speech features | Speech-to-text microphone button and text-to-speech playback per message |
| Bid preview and generation | HVAC bid preview and generated bid workflows |
| Document viewer | Sidebar tree navigation for blueprints and PDFs |
| Bid versioning | Version diff and restore |
| Blueprint vision analysis | AI-powered blueprint upload and analysis |
| Line item tables | Tabular line items with sorting |
| Settings | Application/user settings surface |
| Residential estimates | Residential estimating workflow |
| Responsive behavior | Mobile breakpoints at `768px` and `480px` |
| Markdown rendering | Styled markdown tables with sparkline-style enhancements |

### 2.3 QA Findings Relevant to Rebuild

The QA audit found no critical issues. API pass rate was 76%, with all identified failures classified as low severity, false positives, or design choices.

Key findings to preserve in the rebuild:

| Finding | Product Requirement |
|---|---|
| SPA loads successfully at `/` | The React app must continue to be reachable at `/` in production |
| Static assets are served at `/static/*` | React production assets must align with existing static path conventions |
| CORS is correctly configured | Development should use either Vite proxy or existing CORS behavior |
| `/api/v1/agent/chat` returns HTTP 200 with SSE error event for invalid payloads | Chat client must handle stream-level error events, not only HTTP errors |
| All 36 OpenAPI routes are active | The rebuild must not require backend route changes |

### 2.4 Constraints

- FastAPI backend remains as-is for the frontend rebuild.
- All existing `/api/v1/*` routes must stay available.
- Docker remains the production runtime.
- The current production app must remain usable during migration.
- Feature parity is required before replacing the current SPA.
- Mobile behavior at `768px` and `480px` must be preserved or improved.

## 3. Goals & Success Criteria

### 3.1 Product Goals

1. Replace the vanilla JavaScript SPA with a maintainable React 19 application.
2. Preserve all existing VeloBid workflows with no functional regression.
3. Deliver a modern AI chat experience comparable to ChatGPT and Gemini.
4. Standardize UI composition using shadcn/ui primitives.
5. Improve frontend type safety, testability, and long-term delivery velocity.
6. Keep backend APIs, deployment topology, and Docker runtime stable.
7. Improve mobile usability across dashboard, chat, document viewing, tables, and settings.

### 3.2 Why Move to React and shadcn/ui

The current frontend has outgrown a vanilla JS SPA structure. React and shadcn/ui address the core product and engineering needs:

| Need | React + shadcn/ui Benefit |
|---|---|
| Large feature surface | Component boundaries make features easier to isolate and evolve |
| Complex state | React hooks and route-level state patterns reduce ad hoc DOM manipulation |
| Reusable UI | shadcn/ui provides accessible, composable primitives for forms, cards, dialogs, tables, tabs, sheets, and navigation |
| Chat experience | React ecosystem supports dedicated AI chat libraries and streaming UI patterns |
| Maintainability | TypeScript contracts reduce runtime ambiguity across API integrations |
| Mobile responsiveness | Tailwind and component composition make breakpoint behavior explicit |
| Visual consistency | A shared design system reduces one-off styles and interaction drift |

### 3.3 Success Criteria

The rebuild will be considered successful when:

| Category | Success Criteria |
|---|---|
| Feature parity | Every current feature listed in this PRD is implemented in the React app |
| API compatibility | The frontend uses existing FastAPI routes without requiring backend breaking changes |
| Chat quality | Chat supports streaming, markdown, suggestions, message actions, STT, TTS, and project-scoped sessions |
| Responsiveness | Dashboard, chat, tables, document viewer, and dialogs work at desktop, tablet, and mobile breakpoints |
| Performance | Initial dashboard route loads quickly under normal production data; route-level code splitting is used where appropriate |
| Reliability | Login, dashboard, bid generation, chat streaming, document viewing, version restore, file upload, and settings pass regression QA |
| Deployment | Docker image serves the built React app and FastAPI backend on port `8000` |
| Maintainability | Feature code is organized by domain with typed API clients and reusable UI components |

## 4. Tech Stack Decision

### 4.1 Selected Stack

| Layer | Decision | Rationale |
|---|---|---|
| UI framework | React 19 | Modern component model, stable ecosystem, strong fit for complex SPA workflows, good support for streaming and interactive chat |
| Language | TypeScript | API contract safety, safer refactors, better editor support, clearer component props and domain models |
| Build tool | Vite | Fast local development, simple React setup, optimized production builds, straightforward proxy configuration |
| Styling | Tailwind CSS | Utility-first styling aligns with shadcn/ui, supports responsive constraints, reduces global CSS drift |
| Component system | shadcn/ui | Accessible primitives, source-owned components, strong fit for forms, tables, cards, sheets, dialogs, tabs, menus, toasts |
| Chat UI | CopilotKit or assistant-ui | Purpose-built assistant experience with streaming messages, modern layout patterns, actions, suggestions, and extensibility |
| Routing | React Router | Stable client-side route model for dashboard, projects, documents, settings, auth, and estimates |
| Data fetching | TanStack Query | Cache management, retries, loading states, mutation flows, and invalidation for API-backed UI |
| Forms | React Hook Form + Zod | Works directly with shadcn forms, supports typed validation and structured error display |
| Icons | lucide-react | Native fit with shadcn/ui and consistent action iconography |
| Markdown | react-markdown + remark-gfm | Required for assistant output, bid tables, markdown tables, and code blocks |
| Testing | Vitest, React Testing Library, Playwright | Unit, integration, and end-to-end coverage for high-risk workflows |

### 4.2 Chat Framework Decision

The rebuild should evaluate CopilotKit and assistant-ui in a short implementation spike before locking the final chat library.

| Option | Strengths | Risks / Validation Needed |
|---|---|---|
| CopilotKit | Larger ecosystem, AI app patterns, strong assistant integration concepts, approximately 30k GitHub stars in source research | Must validate clean adapter support for VeloBid's custom SSE endpoint and project-scoped chat sessions |
| assistant-ui | Chat-first UI primitives, strong fit for ChatGPT-like layout, approximately 10k GitHub stars in source research | Must validate STT/TTS controls, artifact/table rendering, and SSE adapter complexity |

Recommendation: start with assistant-ui if the priority is a polished standalone chat sidebar; choose CopilotKit if deeper in-app agent actions and future copilot workflows are prioritized. The implementation must expose a small VeloBid chat adapter either way so the product is not tightly coupled to library internals.

### 4.3 Theme Direction

The React UI must use VeloBid's existing blue palette:

| Token | Value | Usage |
|---|---|---|
| Primary | `#0b57d0` | Primary buttons, active route state, key actions |
| Dark | `#1a365d` | Headers, emphasis text, navigation accents |
| Background | shadcn neutral base | Application shell, content surfaces |
| Destructive | shadcn destructive token | Delete file, archive confirmation, irreversible actions |

Tailwind theme tokens should be defined in `src/styles/globals.css` and `tailwind.config.ts` using shadcn-compatible CSS variables.

## 5. Feature Inventory

### 5.1 Feature-to-Component Map

| Current Feature | New Route / Area | New React Component(s) | shadcn / Library Usage | API Integration |
|---|---|---|---|---|
| Login | `/login` | `LoginPage`, `LoginForm`, `BidderSelect` | `Form`, `Card`, `Input`, `Select`, `Button`, `Alert` | `POST /api/v1/auth/login`, `GET /api/v1/bidders`, `GET /api/v1/auth/me` |
| Project dashboard grid | `/projects` | `ProjectsPage`, `ProjectGrid`, `ProjectCard`, `ProjectFilters` | `Card`, `Badge`, `Button`, `Tabs`, `DropdownMenu`, `Skeleton` | `GET /api/v1/projects`, `GET /api/v1/projects/with-pricing`, project archive/unarchive endpoints |
| Archive/unarchive projects | `/projects` | `ProjectArchiveAction`, `ArchiveConfirmDialog` | `AlertDialog`, `DropdownMenuItem`, `Toast` | project archive/unarchive endpoints |
| Agent chat sidebar | App shell / project pages | `AgentChatSidebar`, `ChatPanel`, `ChatMessageList`, `ChatComposer`, `ChatSuggestions` | CopilotKit or assistant-ui, `ResizablePanel`, `Button`, `Tooltip`, `ScrollArea` | `POST /api/v1/agent/chat`, session/message endpoints |
| Chat history | Project pages | `ChatSessionProvider`, `ChatHistoryList` | Chat library primitives, `ScrollArea`, `Skeleton` | session and message endpoints |
| STT microphone | Chat composer | `SpeechToTextButton` | `Button`, `Tooltip`, Web Speech API wrapper | Browser Web Speech API; no backend required unless existing route exists |
| TTS playback | Chat messages | `TextToSpeechButton` | `Button`, `Tooltip` | Browser SpeechSynthesis API |
| Markdown tables and sparklines | Chat messages / bid preview | `MarkdownRenderer`, `SparklineCell` | `react-markdown`, `remark-gfm`, custom table components | Consumes assistant and bid markdown payloads |
| Bid preview | `/projects/:projectId/bids/preview` or project detail tab | `BidPreviewPanel`, `BidPreviewToolbar` | `Card`, `Tabs`, `Button`, `ScrollArea` | bid preview endpoint |
| Bid generation | Project detail | `GenerateBidButton`, `BidGenerationDialog`, `BidGenerationStatus` | `Dialog`, `Progress`, `Button`, `Toast` | bid generate endpoint |
| Bid view/download | Project detail / bid route | `BidViewer`, `BidDownloadButton` | `Sheet`, `Button`, `DropdownMenu` | bid view/download endpoints |
| Bid tables | Project detail / bid preview | `BidTable`, `LineItemsTable`, `SortableHeader` | `Table`, `Checkbox`, `DropdownMenu`, `Badge` | bid preview/view endpoints, line item payloads |
| Document viewer | `/projects/:projectId/documents` | `DocumentViewerPage`, `DocumentTree`, `DocumentSheet`, `DocumentFrame` | `Sheet`, `ResizablePanel`, `ScrollArea`, custom `iframe` | blueprints list/get endpoints, files list/delete endpoints |
| Sidebar tree navigation | Document viewer | `DocumentTree`, `TreeNode`, `BlueprintNode`, `PdfNode` | `ScrollArea`, `Collapsible`, `Button` | `GET /api/v1/files/list`, blueprint list endpoints |
| Blueprint Vision | `/projects/:projectId/blueprints/analyze` or dialog from documents | `BlueprintVisionDialog`, `BlueprintUploadDropzone`, `VisionResultPanel` | `Dialog`, `Form`, `Input`, `Progress`, `Card`, `Textarea` | blueprint upload/list/get endpoints, vision analyze endpoint |
| File upload | Documents / blueprint vision | `FileUploadDropzone`, `UploadProgressList` | `Card`, `Input`, `Progress`, `Toast` | blueprint upload endpoint |
| File delete | Documents | `DeleteFileDialog`, `FileActionsMenu` | `AlertDialog`, `DropdownMenu`, `Toast` | file delete endpoint |
| Version management | Project detail / bid route | `BidVersionsPanel`, `VersionDiffDialog`, `RestoreVersionButton` | `Tabs`, `Table`, `Dialog`, `AlertDialog`, `Badge` | version diff and restore endpoints |
| Settings | `/settings` | `SettingsPage`, `SettingsTabs`, `ProfileSettingsForm`, `SystemSettingsForm` | `Form`, `Tabs`, `Card`, `Switch`, `Input`, `Textarea` | `GET /api/v1/settings`, settings update endpoint if available |
| Bidders management | `/settings/bidders` or settings tab | `BiddersTable`, `BidderFormDialog` | `Table`, `Dialog`, `Form`, `Button` | bidders CRUD endpoints |
| Users management | `/settings/users` or settings tab | `UsersTable`, `UserFormDialog`, `SetPasswordDialog` | `Table`, `Dialog`, `Form`, `AlertDialog` | users CRUD endpoints, `POST /api/v1/auth/set-password` |
| Trades list | Settings or bid workflow | `TradeSelect`, `TradesTable` | `Select`, `Table`, `Badge` | `GET /api/v1/trades` |
| Residential estimates | `/residential` | `ResidentialEstimatesPage`, `ResidentialEstimateForm`, `ResidentialResultsPanel` | `Form`, `Card`, `Tabs`, `Table` | residential estimates endpoints |
| Health/meta display | Admin/debug area | `SystemStatusCard` | `Card`, `Badge` | `GET /api/v1/health`, `GET /api/v1/meta` |
| Mobile responsiveness | Global | `AppShell`, `MobileNav`, `ChatDrawer`, `ResponsiveProjectGrid` | `Sheet`, `Drawer` if added, `Button`, Tailwind breakpoints | All feature APIs |

### 5.2 Feature Parity Requirements

The React application must preserve:

- Bidder + user + password login flow.
- Project cards, active/archive filtering, archive/unarchive actions.
- Project-scoped agent chat sessions.
- SSE streaming chat responses.
- STT input and TTS message playback.
- Markdown rendering, including markdown tables and bid-related structured output.
- Bid preview, bid generation, bid view, and bid download.
- Document tree navigation and embedded document viewing.
- Blueprint upload and vision analysis.
- Bid version diff and restore.
- Line item table sorting.
- Settings, bidder management, user management, and password management.
- Residential estimates.
- Mobile layouts at `768px` and `480px`.

## 6. Architecture Plan

### 6.1 Frontend Architecture

The React app will be a Vite application under a new frontend directory:

```text
/tmp/prd-workspace/frontend
```

The app will be organized around domain features, shared UI primitives, API clients, and route-level pages. Route pages should compose feature components and delegate API access to typed hooks.

Primary frontend layers:

| Layer | Responsibility |
|---|---|
| `src/app` | App bootstrap, providers, router, shell |
| `src/pages` | Route-level screens |
| `src/features` | Domain-specific components, hooks, and state |
| `src/components/ui` | shadcn/ui generated primitives |
| `src/components/shared` | App-specific reusable components |
| `src/lib/api` | Typed API client, SSE client, endpoint wrappers |
| `src/types` | Shared TypeScript types matching backend payloads |
| `src/styles` | Tailwind and shadcn theme setup |

### 6.2 Backend Integration

The FastAPI backend remains the source of truth for authentication, projects, bids, files, blueprints, versions, chat, and settings.

Development integration:

```ts
// frontend/vite.config.ts
server: {
  proxy: {
    "/api": "http://localhost:8000",
    "/docs": "http://localhost:8000",
    "/redoc": "http://localhost:8000",
    "/openapi.json": "http://localhost:8000"
  }
}
```

Production integration:

- Vite builds static assets into `frontend/dist`.
- Docker build copies `frontend/dist` into the backend static directory.
- FastAPI serves the React `index.html` at `/`.
- Static assets continue to be served from `/static/*` or an agreed equivalent configured in FastAPI.
- API calls use same-origin relative URLs such as `/api/v1/projects`.

### 6.3 CORS and Credentials

The QA report confirms CORS currently echoes the request origin and supports credentials. The frontend should:

- Use same-origin relative URLs in production.
- Use Vite proxy in local development where possible.
- Set `credentials: "include"` on API requests if backend auth depends on cookies.
- Preserve token/session behavior if the current app stores auth state in localStorage.

The implementation must confirm the current auth persistence mechanism before coding the auth provider.

### 6.4 API Client Pattern

Create a central fetch wrapper:

```ts
// src/lib/api/client.ts
export async function apiFetch<T>(
  path: string,
  options?: ApiRequestOptions
): Promise<T>
```

Requirements:

- Prefix all product requests with `/api/v1`.
- Parse JSON responses.
- Surface structured validation errors from HTTP `422`.
- Support file/blob responses for downloads.
- Support multipart uploads for blueprints and documents.
- Attach auth credentials consistently.
- Provide cancellation via `AbortSignal`.

Create a separate SSE adapter:

```ts
// src/lib/api/chatStream.ts
export function streamAgentChat(request: AgentChatRequest): AsyncIterable<AgentChatEvent>
```

SSE requirements:

- Use `POST /api/v1/agent/chat`.
- Accept project/session context and message history in the backend-compatible payload.
- Handle HTTP errors.
- Handle stream-level events of type `error`.
- Yield token/message deltas as they arrive.
- Support cancellation when users stop generation, change projects, or close chat.

### 6.5 Build Pipeline

Local development:

1. Run FastAPI backend on `localhost:8000`.
2. Run Vite frontend on `localhost:5173`.
3. Vite proxies `/api/*` to FastAPI.

Production build:

1. Install frontend dependencies.
2. Run `npm run build`.
3. Copy `frontend/dist` to backend static output.
4. Build Docker image.
5. Serve FastAPI and React app from port `8000`.

### 6.6 Docker Integration

The existing Docker runtime must remain. The Dockerfile should be updated to include a Node build stage only if the frontend lives in the same repository/image.

Expected multi-stage shape:

```dockerfile
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.12-slim AS app
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
COPY --from=frontend-build /app/frontend/dist ./static
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Final paths must be adjusted to match the actual backend module and static directory.

## 7. Component Tree

```text
App
├── AppProviders
│   ├── QueryClientProvider
│   ├── AuthProvider
│   ├── ThemeProvider
│   ├── TooltipProvider
│   └── Toaster
├── RouterProvider
│   ├── PublicLayout
│   │   └── LoginPage
│   │       └── LoginForm
│   │           ├── BidderSelect
│   │           ├── UserIdInput
│   │           └── PasswordInput
│   └── AuthenticatedLayout
│       ├── AppShell
│       │   ├── TopNav
│       │   ├── MobileNav
│       │   ├── MainContent
│       │   └── AgentChatSidebar
│       │       ├── ChatHeader
│       │       ├── ChatSessionMenu
│       │       ├── ChatMessageList
│       │       │   └── ChatMessage
│       │       │       ├── MarkdownRenderer
│       │       │       ├── SparklineTable
│       │       │       └── TextToSpeechButton
│       │       ├── ChatSuggestions
│       │       └── ChatComposer
│       │           ├── SpeechToTextButton
│       │           ├── MessageInput
│       │           └── SendButton
│       ├── ProjectsPage
│       │   ├── ProjectFilters
│       │   ├── ProjectGrid
│       │   │   └── ProjectCard
│       │   └── ArchiveConfirmDialog
│       ├── ProjectDetailPage
│       │   ├── ProjectHeader
│       │   ├── ProjectTabs
│       │   │   ├── BidPreviewPanel
│       │   │   ├── LineItemsTable
│       │   │   ├── BidVersionsPanel
│       │   │   └── ProjectFilesPanel
│       │   └── GenerateBidDialog
│       ├── DocumentViewerPage
│       │   ├── DocumentTree
│       │   ├── DocumentToolbar
│       │   ├── DocumentFrame
│       │   └── DocumentSheet
│       ├── BlueprintVisionPage
│       │   ├── BlueprintUploadDropzone
│       │   ├── VisionAnalysisForm
│       │   └── VisionResultPanel
│       ├── ResidentialEstimatesPage
│       │   ├── ResidentialEstimateForm
│       │   └── ResidentialResultsPanel
│       └── SettingsPage
│           └── SettingsTabs
│               ├── ProfileSettingsForm
│               ├── SystemSettingsForm
│               ├── BiddersTable
│               ├── UsersTable
│               └── TradesTable
```

## 8. API Integration Map

API route names are based on the current OpenAPI route inventory and QA report. Exact request and response schemas must be generated or manually typed from `/openapi.json` before implementation.

### 8.1 System and Settings

| Endpoint | Method | Consumer Component(s) | Expected Use |
|---|---|---|---|
| `/api/v1/health` | GET | `SystemStatusCard` | Display backend health in admin/debug settings |
| `/api/v1/meta` | GET | `AppBootstrap`, `SystemStatusCard` | Read app metadata/version if exposed |
| `/api/v1/settings` | GET | `SettingsPage`, `SystemSettingsForm` | Load application settings |
| `/api/v1/settings` or configured update route | PUT/PATCH/POST | `SystemSettingsForm` | Persist changed settings if supported |

### 8.2 Authentication

| Endpoint | Method | Consumer Component(s) | Contract Notes |
|---|---|---|---|
| `/api/v1/auth/login` | POST | `LoginForm`, `AuthProvider` | Payload includes bidder, user ID, and password fields matching backend schema |
| `/api/v1/auth/me` | GET | `AuthProvider`, `AuthenticatedLayout` | Validates current session/user |
| `/api/v1/auth/set-password` | POST | `SetPasswordDialog`, `UsersTable` | Used by settings/admin user management |

### 8.3 Bidders and Users

| Endpoint Group | Method(s) | Consumer Component(s) | Expected Use |
|---|---|---|---|
| `/api/v1/bidders` | GET | `LoginForm`, `BiddersTable`, `BidderSelect` | List bidders for login and admin screens |
| `/api/v1/bidders/*` | POST/PUT/PATCH/DELETE | `BidderFormDialog`, `BiddersTable` | Create, update, delete bidders |
| `/api/v1/users/*` | GET/POST/PUT/PATCH/DELETE | `UsersTable`, `UserFormDialog` | User administration |

### 8.4 Projects and Trades

| Endpoint | Method | Consumer Component(s) | Expected Use |
|---|---|---|---|
| `/api/v1/projects` | GET | `ProjectsPage`, `ProjectGrid` | Load dashboard projects |
| `/api/v1/projects/with-pricing` | GET | `ProjectsPage`, `ProjectCard`, `BidPreviewPanel` | Load projects with pricing summary where available |
| `/api/v1/projects` | POST | `ProjectCreateDialog` if implemented | Create project if current backend supports it |
| `/api/v1/projects/{projectId}` | GET/PUT/PATCH/DELETE | `ProjectDetailPage`, `ProjectHeader` | Read/update/delete project details |
| project archive endpoint | POST/PATCH | `ProjectArchiveAction` | Archive project |
| project unarchive endpoint | POST/PATCH | `ProjectArchiveAction` | Restore archived project |
| `/api/v1/trades` | GET | `TradeSelect`, `TradesTable`, bid workflows | Load trade options, including HVAC |

### 8.5 Bids and Line Items

| Endpoint Group | Method(s) | Consumer Component(s) | Expected Use |
|---|---|---|---|
| bid preview endpoint | POST/GET | `BidPreviewPanel`, `BidTable` | Preview bid data before generation |
| bid generate endpoint | POST | `GenerateBidButton`, `BidGenerationDialog` | Generate HVAC bid |
| bid view endpoint | GET | `BidViewer`, `BidPreviewPanel` | Display generated bid |
| bid download endpoint | GET | `BidDownloadButton` | Download generated bid document/blob |
| line item payloads from bid endpoints | GET/POST | `LineItemsTable` | Display sortable line items |

### 8.6 Chat Sessions, Messages, and Agent Streaming

| Endpoint | Method | Consumer Component(s) | Contract Notes |
|---|---|---|---|
| `/api/v1/session` or sessions group | POST/GET | `ChatSessionProvider`, `ChatSessionMenu` | Create/list project-scoped chat sessions |
| messages group | GET/POST | `ChatMessageList`, `ChatSessionProvider` | Load and persist chat history |
| `/api/v1/agent/chat` | POST SSE | `AgentChatSidebar`, `ChatPanel`, `ChatComposer` | Streams assistant response events; may return HTTP 200 with stream-level error event |
| `/api/v1/ai/refine` | POST | `BidPreviewPanel`, `ChatPanel`, `RefineBidAction` | Refine AI/bid output |

Agent chat request contract must include:

- Current user message.
- Prior messages or session ID, depending on backend schema.
- Project ID when chat is project-scoped.
- Bid/document context when available.
- Trade context where applicable.

Agent chat response contract must support:

- Incremental text deltas.
- Final assistant message.
- Error events.
- Optional structured artifacts, tables, or metadata if currently emitted.

### 8.7 Files, Blueprints, and Document Viewer

| Endpoint Group | Method(s) | Consumer Component(s) | Expected Use |
|---|---|---|---|
| `/api/v1/files/list` | GET | `DocumentTree`, `ProjectFilesPanel` | List available files |
| file delete endpoint | DELETE | `DeleteFileDialog`, `FileActionsMenu` | Delete file |
| blueprint upload endpoint | POST multipart | `BlueprintUploadDropzone` | Upload blueprint/PDF/image files |
| blueprint list endpoint | GET | `DocumentTree`, `BlueprintVisionPage` | List blueprints |
| blueprint get endpoint | GET | `DocumentFrame`, `DocumentSheet` | Render selected blueprint/PDF in iframe |
| `/api/v1/vision/analyze` | POST | `BlueprintVisionDialog`, `VisionResultPanel` | Run AI blueprint analysis |

### 8.8 Versions

| Endpoint Group | Method(s) | Consumer Component(s) | Expected Use |
|---|---|---|---|
| versions list endpoint | GET | `BidVersionsPanel` | List bid versions |
| versions diff endpoint | GET/POST | `VersionDiffDialog` | Compare two versions |
| versions restore endpoint | POST | `RestoreVersionButton` | Restore selected version |

### 8.9 Residential Estimates

| Endpoint Group | Method(s) | Consumer Component(s) | Expected Use |
|---|---|---|---|
| residential estimates endpoint | GET/POST | `ResidentialEstimatesPage`, `ResidentialEstimateForm`, `ResidentialResultsPanel` | Create and view residential estimates |

## 9. Route Design

React Router will provide route-level ownership and layout separation.

| Route | Component | Access | Purpose |
|---|---|---|---|
| `/login` | `LoginPage` | Public | Bidder/user/password login |
| `/` | Redirect | Authenticated | Redirect to `/projects` |
| `/projects` | `ProjectsPage` | Authenticated | Project dashboard grid |
| `/projects/:projectId` | `ProjectDetailPage` | Authenticated | Project summary, bid tabs, files, versions |
| `/projects/:projectId/bids` | `ProjectBidsPage` or project tab | Authenticated | Bid preview, generation, view, download |
| `/projects/:projectId/documents` | `DocumentViewerPage` | Authenticated | Document tree and iframe viewer |
| `/projects/:projectId/blueprints` | `BlueprintsPage` | Authenticated | Blueprint list and upload |
| `/projects/:projectId/blueprints/analyze` | `BlueprintVisionPage` | Authenticated | AI blueprint vision analysis |
| `/residential` | `ResidentialEstimatesPage` | Authenticated | Residential estimate workflow |
| `/settings` | `SettingsPage` | Authenticated | Settings overview |
| `/settings/profile` | `SettingsPage` tab route | Authenticated | Current user/profile settings |
| `/settings/bidders` | `SettingsPage` tab route | Authenticated/admin | Bidder management |
| `/settings/users` | `SettingsPage` tab route | Authenticated/admin | User management |
| `/settings/trades` | `SettingsPage` tab route | Authenticated/admin | Trades reference |
| `*` | `NotFoundPage` | Any | Unknown route fallback |

Route behavior:

- Authenticated routes must check `/api/v1/auth/me` or equivalent persisted auth state.
- Project routes must validate `projectId` and show a not-found state if missing.
- The chat sidebar should persist across authenticated routes.
- On mobile, the chat sidebar should become a sheet/drawer launched from the app shell.
- Route transitions must not interrupt an active chat stream unless the selected project context changes.

## 10. Migration Strategy

### 10.1 Migration Principles

- Preserve the running vanilla SPA until the React app reaches feature parity.
- Do not modify backend route contracts during the frontend rebuild unless a separate backend change is explicitly approved.
- Build React against the live FastAPI API surface from day one.
- Migrate by vertical slices to reduce regression risk.
- Use feature flags or alternate static route serving if both frontends need to coexist temporarily.

### 10.2 Phased Plan

#### Phase 1: Foundation

- Create `frontend/` Vite React 19 TypeScript app.
- Install Tailwind CSS, shadcn/ui, lucide-react, React Router, TanStack Query, React Hook Form, Zod, markdown libraries, and test tooling.
- Configure Vite proxy to FastAPI.
- Define VeloBid theme tokens.
- Create `AppProviders`, `AuthProvider`, `apiFetch`, and route skeletons.
- Generate or manually define initial TypeScript API types from `/openapi.json`.

Exit criteria:

- React app runs locally.
- `/login` and authenticated shell render.
- API health/meta/settings queries work through proxy.

#### Phase 2: Authentication and Dashboard

- Implement login flow.
- Implement project dashboard grid.
- Implement active/archive filters.
- Implement archive/unarchive actions.
- Add loading, empty, error, and unauthorized states.

Exit criteria:

- Users can log in and see the same project set as the current SPA.
- Archive workflows match existing behavior.

#### Phase 3: Project Detail, Bids, and Tables

- Implement project detail route.
- Implement bid preview and generation flows.
- Implement bid view/download.
- Implement line item tables with sorting.
- Implement bid version list, diff, and restore.

Exit criteria:

- HVAC bid workflows match the current SPA.
- Generated bid artifacts can be viewed and downloaded.
- Version restore is confirmed by regression testing.

#### Phase 4: Chat Sidebar

- Complete CopilotKit vs assistant-ui spike.
- Implement VeloBid chat adapter for `/api/v1/agent/chat`.
- Implement project-scoped sessions and message history.
- Implement streaming, stop generation, retry, suggestions, markdown rendering, tables, STT, and TTS.
- Preserve localStorage mapping if backend session model requires it.

Exit criteria:

- Chat feels materially more modern than the current sidebar.
- Streaming works with real backend SSE events.
- Stream-level error events are displayed gracefully.

#### Phase 5: Documents and Blueprint Vision

- Implement document viewer route.
- Implement sidebar tree navigation.
- Implement custom iframe viewer.
- Implement blueprint upload.
- Implement vision analysis dialog/page and results rendering.
- Implement file delete with confirmation.

Exit criteria:

- Users can browse and inspect blueprints/PDFs.
- AI blueprint analysis matches current functionality.

#### Phase 6: Settings, Users, Bidders, Residential

- Implement settings tabs.
- Implement bidder and user management.
- Implement password set/reset flow.
- Implement trades reference UI.
- Implement residential estimates.

Exit criteria:

- Administrative and estimating workflows match existing SPA.

#### Phase 7: Production Cutover

- Add frontend build stage to Docker.
- Serve React app from FastAPI.
- Confirm `/`, `/static/*`, `/docs`, `/redoc`, and `/openapi.json` remain available.
- Run full regression suite against Docker container.
- Deploy behind Tailscale Funnel.
- Keep rollback path to previous static SPA until post-cutover validation is complete.

Exit criteria:

- Production Docker image serves the React app on port `8000`.
- No critical regressions in login, dashboard, chat, bids, documents, blueprint vision, versions, settings, or residential estimates.

### 10.3 Rollback Strategy

Before replacing the vanilla SPA:

- Keep the current static SPA files in source control or a tagged Docker image.
- Build the React app into a separate static directory until cutover.
- Use a simple environment variable or FastAPI static configuration switch if parallel serving is needed.
- Maintain ability to redeploy the previous image if production validation fails.

## 11. File / Directory Structure

Proposed structure:

```text
/tmp/prd-workspace
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── ...
│   └── static/
│       └── ...
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── components.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── app/
│   │   │   ├── App.tsx
│   │   │   ├── AppProviders.tsx
│   │   │   ├── router.tsx
│   │   │   └── routes.ts
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── form.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── sheet.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   └── tabs.tsx
│   │   │   └── shared/
│   │   │       ├── AppShell.tsx
│   │   │       ├── EmptyState.tsx
│   │   │       ├── ErrorState.tsx
│   │   │       ├── LoadingState.tsx
│   │   │       └── MarkdownRenderer.tsx
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── api.ts
│   │   │   │   ├── AuthProvider.tsx
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── types.ts
│   │   │   ├── projects/
│   │   │   │   ├── api.ts
│   │   │   │   ├── ProjectCard.tsx
│   │   │   │   ├── ProjectFilters.tsx
│   │   │   │   ├── ProjectGrid.tsx
│   │   │   │   └── types.ts
│   │   │   ├── chat/
│   │   │   │   ├── api.ts
│   │   │   │   ├── chatStream.ts
│   │   │   │   ├── AgentChatSidebar.tsx
│   │   │   │   ├── ChatComposer.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatMessageList.tsx
│   │   │   │   ├── SpeechToTextButton.tsx
│   │   │   │   ├── TextToSpeechButton.tsx
│   │   │   │   └── types.ts
│   │   │   ├── bids/
│   │   │   │   ├── api.ts
│   │   │   │   ├── BidPreviewPanel.tsx
│   │   │   │   ├── BidTable.tsx
│   │   │   │   ├── GenerateBidDialog.tsx
│   │   │   │   ├── LineItemsTable.tsx
│   │   │   │   └── types.ts
│   │   │   ├── documents/
│   │   │   │   ├── api.ts
│   │   │   │   ├── DocumentFrame.tsx
│   │   │   │   ├── DocumentSheet.tsx
│   │   │   │   ├── DocumentTree.tsx
│   │   │   │   └── types.ts
│   │   │   ├── blueprints/
│   │   │   │   ├── api.ts
│   │   │   │   ├── BlueprintUploadDropzone.tsx
│   │   │   │   ├── BlueprintVisionDialog.tsx
│   │   │   │   ├── VisionResultPanel.tsx
│   │   │   │   └── types.ts
│   │   │   ├── versions/
│   │   │   │   ├── api.ts
│   │   │   │   ├── BidVersionsPanel.tsx
│   │   │   │   ├── RestoreVersionButton.tsx
│   │   │   │   └── VersionDiffDialog.tsx
│   │   │   ├── settings/
│   │   │   │   ├── api.ts
│   │   │   │   ├── BiddersTable.tsx
│   │   │   │   ├── SettingsTabs.tsx
│   │   │   │   ├── SystemSettingsForm.tsx
│   │   │   │   ├── UsersTable.tsx
│   │   │   │   └── types.ts
│   │   │   └── residential/
│   │   │       ├── api.ts
│   │   │       ├── ResidentialEstimateForm.tsx
│   │   │       ├── ResidentialEstimatesPage.tsx
│   │   │       └── types.ts
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── client.ts
│   │   │   │   ├── errors.ts
│   │   │   │   └── queryClient.ts
│   │   │   ├── storage/
│   │   │   │   └── chatSessionStorage.ts
│   │   │   └── utils.ts
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── ProjectsPage.tsx
│   │   │   ├── ProjectDetailPage.tsx
│   │   │   ├── DocumentViewerPage.tsx
│   │   │   ├── BlueprintVisionPage.tsx
│   │   │   ├── ResidentialEstimatesPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   ├── styles/
│   │   │   └── globals.css
│   │   └── types/
│   │       ├── api.ts
│   │       ├── bid.ts
│   │       ├── chat.ts
│   │       ├── project.ts
│   │       └── user.ts
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── README.md
├── Dockerfile
├── context.md
├── qa-report.md
├── chat-ui-research.md
└── PRD.md
```

If the actual backend currently lives at repository root rather than `backend/`, the frontend structure remains valid and Docker/static paths should be adapted to the existing backend layout.

## 12. Open Questions

### 12.1 Backend Contracts

1. What are the exact request and response schemas for all 36 `/api/v1/*` routes?
2. Should TypeScript types be generated from `/openapi.json`, or manually maintained in `src/types`?
3. What exact project archive/unarchive route paths and methods are exposed?
4. What exact bid preview/generate/view/download route paths and payloads are exposed?
5. What exact version diff and restore route paths and payloads are exposed?
6. What exact residential estimate route paths and payloads are exposed?

### 12.2 Authentication

1. Does the current login flow return a cookie, bearer token, user object, or session identifier?
2. Where is auth state currently persisted: cookie, localStorage, sessionStorage, or memory?
3. Are there role distinctions between regular users, bidders, and admins?
4. Which settings routes require elevated permissions?

### 12.3 Chat

1. Should the implementation choose CopilotKit or assistant-ui as the final chat UI foundation?
2. What is the exact SSE event schema emitted by `/api/v1/agent/chat`?
3. Are chat sessions fully backend-persisted, or does the frontend need to preserve localStorage session mapping?
4. Are suggested prompts generated by the backend, hardcoded per context, or inferred in the frontend?
5. Should chat support artifacts as first-class panels for bid tables, documents, or generated estimates?
6. Should stream-level errors continue to be shown inside the chat transcript, or should they use toast/error banners?

### 12.4 Documents and Blueprints

1. Which file types must the document iframe support: PDF, image, generated HTML, or other document formats?
2. Are blueprint uploads project-scoped, bidder-scoped, or global?
3. What file size limits and accepted MIME types should the upload UI enforce?
4. Should blueprint vision analysis be a route, a dialog, or both?

### 12.5 Product Behavior

1. Should `/projects/:projectId` become the main workspace route, with documents, bids, versions, and chat as tabs?
2. Should residential estimates be standalone or project-linked?
3. Should archived projects be hidden by default as in the current SPA?
4. Should bid generation be blocking, backgrounded, or stream progress updates if the backend supports it?

### 12.6 Deployment

1. What is the current backend static directory path inside the Docker image?
2. Should React assets continue to be served under `/static/*`, or should Vite's default `/assets/*` be supported?
3. Is there a need to serve both vanilla and React frontends during a beta period?
4. What rollback mechanism should be used in production: image tag rollback, static path switch, or feature flag?

### 12.7 QA and Release

1. What existing manual QA scripts should be converted into Playwright tests?
2. Which workflows are mandatory release blockers?
3. What fixture data is available for deterministic bid, blueprint, and residential estimate testing?
4. Should accessibility testing be part of the release gate?
5. Should visual regression screenshots be captured for desktop, `768px`, and `480px` breakpoints?

