# Dashboard

React + Vite front end for the screening results, dark "obsidian-amber" theme. It polls `/api/v1/health/ready`, screens a CSV through `POST /api/v1/screen` (optional outcome file for the 168 h reveal), and shows the overview, component grid, fault topology, per-part inspector, chamber view and export.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to the backend on :8000
```

The "Sample Data" button fetches the backend's `sample.csv` and screens it live. When the backend is unreachable the app falls back to `src/lib/demoData.js`, a 64-part subset of a genuine v2 response regenerated with `python scripts/build_frontend_fixtures.py`. Metadata the CSV does not supply (board position, tester channel) renders as N/A; nothing is invented on the client.

`npm run build` writes `dist/`; the backend serves it when `SIH_FRONTEND_DIST_DIR` points there.
