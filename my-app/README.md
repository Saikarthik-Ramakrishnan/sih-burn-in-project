# Dashboard

React + Vite front end for the screening results. It polls `/api/v1/health/ready`, uploads a CSV to `/api/v1/screen`, and renders each part's measured values, batch comparison, forecast with its interval, explanation and recommendation.

```bash
cd my-app
npm install
npm run dev        # http://localhost:5173, expects the backend on :8000
```

Which response fields to bind and how to display them: [docs/dashboardAdapterFieldDictionary.md](docs/dashboardAdapterFieldDictionary.md). Build a production bundle with `npm run build`; the backend serves `my-app/dist` when it exists.
