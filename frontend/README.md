# Vakil Vision frontend

React UI for the FastAPI contract upload and analysis endpoints.

## Run locally

```powershell
npm install
npm run dev
```

Vite proxies `/contracts` and `/analysis` to the FastAPI Cloud app by default. To use a local API instead, copy `.env.example` to `.env.local` and set `VITE_API_PROXY_TARGET=http://127.0.0.1:8000`.

## Build for FastAPI Cloud

```powershell
npm run build
```

The FastAPI app serves `frontend/dist` at `/`. Build it before deploying the repository with `fastapi deploy`.
