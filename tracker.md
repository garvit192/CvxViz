# ✅ CvxViz Project Tracker

## Week 1: Solver & API Base
- [✅] **Implement solve_lp()** – Add LP/QP support using cvxpy
- [✅] **Write unit tests** – Include edge cases and standard forms
- [✅] **Create FastAPI backend** – Initial /solve endpoint
- [ ] **Deploy demo API** – Initial deployment on AWS EB

## Week 2: Config & Versioning
- [ ] **Restructure app layout** – Split into app/, api/v1/, solver/
- [ ] **Environment config** – Use pydantic-settings or dotenv
- [ ] **Add API token auth** – Basic bearer or key-based auth
- [ ] **Enable CORS** – Allow secure frontend requests

## Week 3: Async & Performance
- [ ] **Async endpoints** – Convert to async FastAPI handlers
- [ ] **Add rate limiting** – Prevent abuse (in-memory or Redis)
- [ ] **Test concurrency** – Run stress tests

## Week 4: Logging & Monitoring
- [ ] **Structured logging** – Use loguru or logging
- [ ] **Error middleware** – Unified error format
- [ ] **AWS CloudWatch** – Log collection from EB or agent

## Week 5: Docker & CI/CD
- [ ] **Dockerfile** – Multi-stage build w/ Uvicorn+Gunicorn
- [ ] **CI pipeline** – Tests + build image on PR
- [ ] **CD to EB/ECS** – Deploy on merge to main

## Week 6: Caching & Documentation
- [ ] **Add caching** – Use lru_cache or Redis
- [ ] **Profile endpoint** – Latency analysis
- [ ] **Write README** – Docs + diagrams
- [ ] **API docs** – OpenAPI schema & usage guide
