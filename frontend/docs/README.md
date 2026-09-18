# Frontend Engineering Documentation: Current Progress & Architecture

> **Application**: `CardioRecourse Clinician Dashboard & Patient Portal`  
> **Status**: Milestone C0 / Initial Scaffold & Tooling Operational  
> **Framework**: React 19 + TypeScript on Vite 8  
> **Location**: [`frontend/`](file:///d:/CodeSplash/Axiora/frontend/)  

---

## 1. What Has Been Implemented So Far

The frontend client infrastructure has been bootstrapped with a modern React + TypeScript single-page application (SPA) architecture.

### 1.1 Development & Build System
- **Vite 8 Build Tooling**: Fast hot module replacement (HMR), tree-shaking, and ES module bundling.
- **TypeScript 5.x / 6.x Setup**:
  - `tsconfig.json`: Root project configuration.
  - `tsconfig.app.json`: Strict typing rules for client application code.
  - `tsconfig.node.json`: Tooling configurations for Vite and build scripts.
- **ESLint 10**: Configured via `eslint.config.js` with `react-hooks` and `react-refresh` plugins for strict UI quality enforcement.

### 1.2 Development Proxy Configuration ([`frontend/vite.config.ts`](file:///d:/CodeSplash/Axiora/frontend/vite.config.ts))
The local development server is configured on port `5173` with an active reverse proxy targeting the FastAPI backend:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```
- **Benefit**: Any request sent to `/api/...` in the frontend is automatically proxied to `http://127.0.0.1:8000/...`, completely bypassing browser Cross-Origin Resource Sharing (CORS) friction and simplifying network code.

### 1.3 Production-Grade Dependencies Installed ([`frontend/package.json`](file:///d:/CodeSplash/Axiora/frontend/package.json))
- **`recharts` (^3.10.1)**: SVG charting engine selected for rendering the bidirectional SHAP attribution waterfall charts and feature contribution graphs.
- **`lucide-react` (^1.47.0)**: Modern medical and diagnostic icon pack for clinical badges, risk indicators, and action buttons.
- **`axios` (^1.20.0)**: Robust Promise-based HTTP client for talking to backend REST endpoints.
- **`clsx` (^2.1.1) & `tailwind-merge` (^3.7.0)**: Utility libraries for dynamic, conditional CSS class management.
- **`react` & `react-dom` (^19.2.8)**: Modern React runtime.

### 1.4 Codebase Structure
```
frontend/
├── vite.config.ts          # Vite configuration with /api reverse proxy
├── package.json            # Pinned dependencies and scripts (dev, build, lint)
├── tsconfig*.json          # TypeScript compilation settings
├── eslint.config.js        # Linting rules
├── index.html              # HTML5 root shell
├── public/                 # Static assets (favicons, SVGs)
├── docs/                   # Frontend technical documentation
└── src/
    ├── main.tsx            # React root DOM mounting point
    ├── App.tsx             # Main application container
    ├── App.css             # Component-level styles
    ├── index.css           # Global reset and typography styles
    └── assets/             # Branding and vector assets
```

---

## 2. Immediate Next Steps & Planned Architecture

The frontend will be built out according to the wireframes and specifications in [ARCHITECTURE.md](file:///d:/CodeSplash/Axiora/ARCHITECTURE.md) and [TASK_BOARD.md](file:///d:/CodeSplash/Axiora/TASK_BOARD.md):

```
┌─────────────────────────────────────────────────────────────┐
│                 CardioRecourse Clinician UX                 │
├──────────────────────────────┬──────────────────────────────┤
│ Left Panel: Input & Control  │ Right Panel: Diagnostic View │
├──────────────────────────────┼──────────────────────────────┤
│ 1. Demo Persona Selector     │ 3. Animated Risk Gauge       │
│    (Arthur, Sunethra, Dinesh)│    (Green / Amber / Red)     │
│                              │                              │
│ 2. 15-Biomarker Input Form   │ 4. SHAP Waterfall Chart      │
│    - Range validation        │    (Bidirectional SVG)       │
│    - Unit normalization      │                              │
│    - Live recalculation      │ 5. Side-by-Side DiCE Cards   │
│                              │    (Plan A vs. Plan B)       │
├──────────────────────────────┴──────────────────────────────┤
│ 6. Action Bar: Generate Printable Patient Action Plan (PDF) │
└─────────────────────────────────────────────────────────────┘
```

1. **Task C1 & C2 (Design System & Layout)**: Build the clinical layout using glassmorphism cards and clinical status color tokens (Low: `#10B981`, Amber: `#F59E0B`, High: `#EF4444`).
2. **Task C3 & C4 (Form & Persona Loader)**: Connect the 15-feature input form with client-side range boundaries and 1-click loading for the 3 clinical test personas.
3. **Task C5 (API Client)**: Implement `frontend/src/api/client.ts` consuming `/api/predict`, `/api/explain`, `/api/recourse`, and composite `/api/assess`.
4. **Task C6 & C7 (Visualization Widgets)**: Build the circular cardiovascular risk gauge and Recharts-powered SHAP attribution waterfall chart.
5. **Task C8 & C9 (Recourse & Reporting)**: Render side-by-side DiCE intervention cards with delta badges and the 1-page printable Patient Action Plan (`window.print()` formatted for A4).

---

## 3. How to Run & Verify the Frontend

### Start Development Server:
```powershell
# In a terminal within frontend directory
cd frontend
npm run dev
```
The application will launch on:  
👉 **`http://localhost:5173`**

### Typecheck & Production Build Verification:
```powershell
# From frontend directory
npm run build
```
This runs `tsc -b` to guarantee zero TypeScript errors and compiles the production bundle into `frontend/dist/`.
