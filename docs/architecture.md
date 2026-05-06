# VeloBid Architecture

```mermaid
graph TB
  subgraph Browser["🌐 Browser"]
    SPA["React 19 SPA<br/>Vite + shadcn/ui + assistant-ui"]
  end

  subgraph Docker["🐳 Docker Container (velobid)"]
    subgraph Frontend["📦 Frontend (served statically)"]
      Pages["Pages<br/>ProjectsPage / SettingsPage / LoginPage<br/>ProjectDetailPage / ResidentialEstimatesPage"]
      Chat["Chat<br/>ChatProvider / chat-store<br/>ChatPanel / assistant-ui"]
      API_Services["API Service Layer<br/>src/api/services/"]
      API_Client["API Client<br/>apiFetch&lt;T&gt; / ApiError<br/>queryClient (TanStack Query)"]
      Types["Shared Types<br/>src/types/ (bids, blueprint, vision, files)"]
    end

    subgraph Backend["⚙️ FastAPI Backend (Python)"]
      Routers["Routers<br/>projects / bids / settings / auth<br/>chat / files / blueprints / residential"]
      Services["Services<br/>Business Logic Layer"]
      BidEngine["Bid Engine<br/>PDF Generation / Pricing<br/>Line Items / Validation"]
    end

    subgraph Config["📁 Config & Data"]
      Projects_Config["config/projects/<br/>Project JSON definitions"]
      Bidders_Config["config/bidders/<br/>Bidder company profiles"]
      Bid_Projects["bid_projects/<br/>Generated bid files"]
    end
  end

  subgraph External["☁️ External"]
    OpenCode["OpenCode Go API<br/>deepseek-v4-flash / kimi-k2.6"]
    XAI["xAI Grok Vision<br/>Blueprint analysis"]
    Tailscale["Tailscale Funnel<br/>velobid.tailfceaca.ts.net:443"]
  end

  %% Frontend flows
  SPA --> Pages
  SPA --> Chat
  Pages --> API_Services
  Chat --> API_Services
  API_Services --> API_Client
  API_Services --> Types

  %% API call flows
  API_Client -.->|GET/POST/PATCH /api/v1/*| Routers
  Chat -.->|POST /api/v1/agent/chat + SSE| Routers

  %% Backend flows
  Routers --> Services
  Services --> BidEngine
  Services --> Config
  BidEngine --> Config

  %% Docker mounts
  Frontend -.->|volume: api/static| Docker
  Config -.->|volumes| Docker

  %% External flows
  Routers -.->|Agent chat| OpenCode
  Routers -.->|Blueprint vision| XAI
  Tailscale -.->|funnel port 8000| Docker

  %% Styling
  classDef frontend fill:#7c3aed,color:#fff,stroke:none
  classDef backend fill:#0369a1,color:#fff,stroke:none
  classDef config fill:#545454,color:#fff,stroke:none
  classDef external fill:#333,color:#fff,stroke:none,stroke-dasharray:4

  class SPA,Pages,Chat,API_Services,API_Client,Typ es frontend
  class Routers,Services,BidEngine backend
  class Projects_Config,Bidders_Config,Bid_Projects config
  class OpenCode,XAI,Tailscale external
```

## Data Flow

```
User Action → Page Component → API Service (typed) → apiFetch<T> → /api/v1/* → FastAPI Router
                                                                                        ↓
User sees ← Page updates ← Promise<T> ← apiFetch parses JSON ← JSON response ← Service / Engine
```

## Key Patterns

- **All API calls** go through `apiFetch<T>` which auto-prepends `/api/v1` and throws typed errors
- **SSE streaming** for agent chat bypasses `apiFetch` (returns raw `Response` for reader)
- **TanStack Query** configured at the root for caching (30s stale, 1 retry)
- **Shared types** in `src/types/` match Pydantic schemas on the backend
- **No inline types in pages** — everything imported from services or types barrel
