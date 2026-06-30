# Conductor Observatory — Roadmap

## ✅ Phase 1–2: Foundation
- Project scaffold (pyproject.toml, ruff, mypy, pytest, structlog)
- DuckDB storage layer with migrations (observations, insights, features)
- FastAPI app with `/health`, `/timeline`, `/observations`
- conductor-engine integration (wraps collectors as Capabilities)

## ✅ Phase 3: Collectors
- Fitbit (sleep, HRV, heart rate, activity)
- Calendar (Google Calendar events)
- Spotify (currently playing, recently played)
- Weather (OpenWeatherMap current + forecast)
- Hardcover (reading activity)
- Home Assistant (entity states)
- Shared: HttpClient (retry), OAuth2Client + OAuthTokenStore

## ✅ Phase 4: LLM & Analytics
- LLM client (raw httpx → OpenRouter, no SDK)
- Analytics engine (SQL: period comparison, year-over-year, recurring patterns)
- Insight generator (LLM prompt with current + historical + recurrence context)
- 35 tests, ruff + mypy clean

## ✅ Phase 5: API Extensions
- `GET /analytics/comparison`, `/year-over-year`, `/recurring`, `/recent`
- `GET /insights`, `POST /insights/generate`

## 🔜 Phase 6: Real API Connection
- Vaultwarden credential loader → `.env` injection
- Integration smoke-test (run all enabled collectors against live APIs)
- OAuth token acquisition flow (manual first-time auth for Fitbit, Calendar, Spotify)
- Collector health endpoint (last-run timestamps, errors)

## 🔜 Phase 7: Docker & Deployment
- Multi-arch Dockerfile (amd64 + arm64 for Raspberry Pi 5)
- docker-compose.yml (app + DuckDB volume)
- Environment variable injection via vaultwarden or `.env`
- Healthcheck + restart policy
- Data volume backup strategy

## 🔜 Phase 8: React Dashboard
- App scaffolding (Vite + React + TypeScript + Tailwind)
- **Dashboard** — key metric cards (sleep score, steps, HRV, weather)
- **Charts** — trend lines (sleep over time, steps per day, HRV)
- **Timeline** — scrollable event feed with filters
- **Insights** — LLM-generated insight cards with confidence badges
- **Chat** — natural-language Q&A over observatory data
- **Settings** — enable/disable collectors, set API keys via vaultwarden

## 🔮 Future Ideas

### Infrastructure & Reliability
- GitHub Actions CI (lint + typecheck + test on PR)
- Pre-commit hooks (ruff, mypy)
- Scheduled collector runs via conductor-engine cron/workflow
- Prometheus metrics endpoint (`/metrics` for uptime, collector lag)
- Structured logging review for production readability

### Data & Analytics
- Parquet export for long-term cold storage
- Data pruning (auto-delete observations older than N months)
- Anomaly detection rules (HRV drops 30%, sleep < 5h) → push notification
- Export/import (JSON or Parquet dump/restore)
- SQL-based user-defined dashboards

### User Experience
- Push notifications (Sleep score dropped → iOS/Android alert)
- Multi-user support (shared household observatory)
- OAuth login flow (self-contained, no manual token pasting)
- PWA support (mobile-friendly dashboard)
- Dark mode

### Platform Expansion
- More collectors: GitHub (commit activity), Strava (exercise), Apple Health, Garmin
- Plug-in collector system (external Python packages register collectors)
- Webhook receiver (accept pushes from external services)
- RSS/Atom feed of daily summaries
