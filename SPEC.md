# SPEC.md — Boston AI Platform: Senior Python/FastAPI Engineer

**Job:** [Upwork ~022044637134162079839](https://www.upwork.com/jobs/~022044637134162079839)
**Budget:** $15–35/hr | **Duration:** 1–3 months (possibly 3–6 months) | **Type:** Ongoing project
**Client:** Boston AI Life Sciences Startup
**Trial:** $100–150 flat paid trial to fix a specific bug
**Hours:** 15–20 hrs/week (to start), async-friendly
**GitHub:** https://github.com/9KMan/JOB-20260416120132-d80f67

---

## 1. Project Overview

**Product:** AI platform for life sciences commercial teams — Python/FastAPI backend, Supabase/PostgreSQL, React/TypeScript frontend. Already built and running in production.
**Goal:** Ship reliable improvements over 3–6 months via scoped tickets with clear acceptance criteria.
**Team:** Async-first, weekly sync calls, fast feedback loops, no politics.

---

## 2. Technical Stack

| Layer       | Technology |
|-------------|------------|
| Backend     | Python 3.11+, FastAPI, asyncio |
| Database    | PostgreSQL (JSONB), Supabase |
| Frontend    | React, TypeScript |
| Auth        | OAuth2 (Google, GitHub), JWT |
| SMS/Comms   | Twilio (webhooks, outbound, session threading) |
| AI/Observability | Langfuse, LiteLLM |
| Deployment  | Docker, Docker Compose |
| Infra       | AWS (EC2, RDS) |

---

## 3. Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React FE   │────▶│  FastAPI     │────▶│  PostgreSQL  │
│  (TypeScript)│◀────│  (Python)    │◀────│  + Supabase  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Twilio      │     │  Langfuse    │
                     │  SMS/Voice   │     │  LiteLLM     │
                     └──────────────┘     └──────────────┘
```

---

## 4. Core Work Areas

### 4.1 Debugging & Integration Fixes
- Fix service integration issues (services not talking correctly)
- Debug data flow issues (code looks right, runtime behavior is wrong)
- Query database to verify runtime state vs expected state
- Add structured logging to trace request flows
- Write integration tests for repaired flows

### 4.2 Database & Migrations
- Write PostgreSQL migrations with proper up/down
- Verify database state post-migration
- Query JSONB fields for debugging
- Optimize slow queries (EXPLAIN ANALYZE)
- Data integrity validation scripts

### 4.3 REST API Development
- Build and harden REST endpoints per OpenAPI spec
- Input validation with Pydantic
- Error handling with proper HTTP status codes
- Rate limiting and pagination
- JWT authentication on all protected routes
- Webhook endpoints for third-party integrations

### 4.4 OAuth & Third-Party Integrations
- Wire OAuth2 flows (Google, GitHub)
- Implement token refresh flows
- Third-party API integrations (Twilio, OpenAI, etc.)
- Webhook receivers for Twilio SMS/Voice

### 4.5 Twilio SMS Integration
- Inbound SMS webhooks (receive SMS, parse, route)
- Outbound SMS (send via Twilio API)
- Session threading (group messages by conversation)
- Voice webhook handling
- Error handling and retry logic for SMS delivery

### 4.6 Frontend (Occasional)
- React/TypeScript component work
- API integration in frontend
- Bug fixes in existing UI

---

## 5. Database Schema (Key Tables)

### Users
```sql
id UUID PRIMARY KEY,
email TEXT UNIQUE NOT NULL,
name TEXT,
oauth_provider TEXT,
oauth_id TEXT,
created_at TIMESTAMPTZ DEFAULT now()
```

### Organizations
```sql
id UUID PRIMARY KEY,
name TEXT,
owner_id UUID REFERENCES users(id),
settings JSONB DEFAULT '{}',
created_at TIMESTAMPTZ DEFAULT now()
```

### AI Conversations
```sql
id UUID PRIMARY KEY,
org_id UUID REFERENCES organizations(id),
user_id UUID REFERENCES users(id),
title TEXT,
model TEXT,
system_prompt TEXT,
created_at TIMESTAMPTZ DEFAULT now()
```

### Messages
```sql
id UUID PRIMARY KEY,
conversation_id UUID REFERENCES ai_conversations(id),
role TEXT CHECK (role IN ('user', 'assistant', 'system')),
content JSONB,
tokens_used INTEGER,
latency_ms INTEGER,
created_at TIMESTAMPTZ DEFAULT now()
```

### SMS Sessions
```sql
id UUID PRIMARY KEY,
external_sid TEXT UNIQUE,
from_number TEXT,
to_number TEXT,
status TEXT,
started_at TIMESTAMPTZ,
ended_at TIMESTAMPTZ
```

### SMS Messages
```sql
id UUID PRIMARY KEY,
session_id UUID REFERENCES sms_sessions(id),
direction TEXT CHECK (direction IN ('inbound', 'outbound')),
body TEXT,
twilio_sid TEXT UNIQUE,
created_at TIMESTAMPTZ DEFAULT now()
```

---

## 6. API Endpoints

### Auth
- `GET /api/auth/oauth/:provider` — Initiate OAuth flow
- `GET /api/auth/oauth/:provider/callback` — OAuth callback
- `POST /api/auth/refresh` — Refresh JWT
- `GET /api/auth/me` — Current user

### AI Chat
- `GET /api/conversations` — List user's conversations
- `POST /api/conversations` — Create new
- `GET /api/conversations/:id` — Get with messages
- `POST /api/conversations/:id/messages` — Send message (streaming)
- `DELETE /api/conversations/:id`

### Database Migrations
- `POST /api/admin/migrations` — Run migration (with rollback plan)
- `GET /api/admin/migrations/status` — Check migration state

### Twilio SMS
- `POST /api/webhooks/twilio/sms` — Inbound SMS webhook
- `POST /api/webhooks/twilio/voice` — Inbound voice webhook
- `GET /api/sms/sessions` — List SMS sessions
- `GET /api/sms/sessions/:id/messages` — Session messages
- `POST /api/sms/send` — Send outbound SMS

### Admin
- `GET /api/admin/users` — List users
- `GET /api/admin/usage` — Platform usage stats
- `GET /api/admin/health` — System health

---

## 7. Debugging Process

### For each bug ticket:
1. Reproduce locally — get exact error
2. Query database to verify data state
3. Add debug logging to trace execution path
4. Identify root cause
5. Implement fix
6. Write test to prevent regression
7. Verify fix in staging
8. Document in PR description

### Example debugging commands:
```bash
# Check migration status
alembic history | head -20
alembic current

# Debug runtime data
psql $DATABASE_URL -c "SELECT * FROM users WHERE id = '...';"
psql $DATABASE_URL -c "SELECT * FROM messages WHERE conversation_id = '...' ORDER BY created_at;"

# Check API logs
docker compose logs api --tail=100 | grep "conversation_id"
```

---

## 8. Git/PR Workflow

### Per ticket:
1. Create branch: `feat/TICKET-id-description`
2. Write tests first (TDD)
3. Implement fix
4. Run: `pytest && alembic history && docker compose build`
5. Open PR with:
   - Summary of what changed
   - How you verified it works
   - Screenshots if UI change
   - Migration commands if DB change
6. Get review + merge

### Commit message format:
```
<TYPE>: <short description>

<what changed>
<why it was changed>
<how you tested it>

Fixes: TICKET-id
```

---

## 9. Trial Task Checklist

Before full engagement, complete paid trial ($100–150):
- [ ] Fix assigned bug from detailed ticket
- [ ] Document debugging process (what you tried, what worked)
- [ ] Submit PR with explanation
- [ ] Verify fix runs in production-like environment

---

## 10. Milestones

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1–2  | Debug existing integration issues | 3+ bugs fixed, documented |
| 3–4  | Twilio SMS integration | Inbound/outbound working, session threading |
| 5–6  | API hardening + OAuth | All endpoints secured, OAuth complete |
| 7–8  | Feature delivery per tickets | 4+ features shipped from backlog |

---

## 11. Risk Factors

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Complex existing codebase | High | Budget extra time, ask questions in tickets |
| Supabase quirks | Medium | Reference Supabase docs, check RPC functions |
| Twilio webhook reliability | Medium | Webhook retry logic, verify delivery |
| Data migration failures | Medium | Always have rollback, test on copy first |

---

## 12. Nice-to-Have (Bonus)

- Langfuse / LiteLLM integration for AI observability
- WebRTC for real-time audio streaming
- Additional OAuth providers (Microsoft, Slack)
