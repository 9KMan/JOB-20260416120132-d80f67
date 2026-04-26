# SPEC.md — Senior Python/FastAPI Engineer · AI Platform

**Job:** [Upwork ~022044637134162079839](https://www.upwork.com/jobs/~022044637134162079839)
**Budget:** $15–35/hr | **Duration:** 1–3 months (possibly 3–6 months) | **Hours:** 15–20 hrs/week
**Trial:** $100–150 flat paid trial (fix a bug + document debugging process)
**GitHub:** https://github.com/9KMan/JOB-20260416120132-d80f67

---

## 1. Project Overview

**Client:** Boston AI Life Sciences Startup
**Product:** AI platform for life sciences commercial teams — already built and running.

Existing stack: Python/FastAPI backend, Supabase/PostgreSQL, React/TypeScript frontend.

The job is **ongoing maintenance and feature work**, not greenfield:
- Debug integration issues
- Fix data flow/runtime bugs
- Implement features from handover docs
- Write Postgres migrations
- Build + harden REST APIs
- Wire OAuth + third-party APIs
- Twilio SMS layer (inbound webhooks, outbound, session threading)
- Occasional React/TypeScript frontend work

---

## 2. Technical Stack

| Layer       | Technology |
|-------------|------------|
| Backend     | Python, FastAPI |
| Database    | PostgreSQL (JSONB), Supabase |
| Frontend    | React, TypeScript |
| SMS         | Twilio (SMS + Voice, webhooks) |
| AI/Observability | Langfuse, LiteLLM |
| Real-time   | WebRTC (nice-to-have) |
| Auth        | OAuth integrations |
| Deployment  | Docker |

---

## 3. Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React/TS      │────▶│   FastAPI       │────▶│  Supabase/      │
│   Frontend      │◀────│   Backend       │◀────│  PostgreSQL     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌───────────┐      ┌───────────┐       ┌───────────┐
    │  Twilio   │      │  LLM/AI   │       │  OAuth /  │
    │  SMS/     │      │  Services │       │  3rd Party│
    │  Voice    │      │(Langfuse, │       │  APIs     │
    │  Webhooks │      │ LiteLLM)  │       │           │
    └───────────┘      └───────────┘       └───────────┘
```

---

## 4. Work Areas

### 4.1 Debug Existing Code
- Debug integration issues where services don't talk correctly
- Find and fix data flow issues (code looks right, runtime is wrong)
- Read existing code + query database directly to find root cause
- Clean git/PR workflow with clear commit messages

### 4.2 Database & Migrations
- Write Postgres migrations and verify database state
- Strong JSONB experience required
- Query debugging

### 4.3 REST API Development
- Build new REST API endpoints
- Harden existing endpoints
- OAuth integrations with third-party APIs

### 4.4 Twilio SMS Layer
- Inbound webhooks (receive SMS)
- Outbound messaging
- Session threading (multi-message conversations)
- Twilio Voice (nice-to-have)

### 4.5 Frontend (Occasional)
- React/TypeScript work
- Integrate with backend APIs

### 4.6 AI Integration (Nice-to-Have)
- Langfuse for AI observability
- LiteLLM for model routing
- WebRTC for real-time audio streaming

---

## 5. How They Work

- Clear scoped tickets with acceptance criteria
- PRs with explanation of approach
- Verify work runs correctly in production
- 15–20 hrs/week to start, potential to extend
- Async-friendly with weekly sync calls
- Trial task before longer commitment

---

## 6. Milestones

| Milestone | Deliverable | Est. Time |
|-----------|-------------|-----------|
| M0 — Trial | Fix specific bug + document debugging process | 1–2 days |
| M1 | PR merged, integration issues resolved | 1–2 weeks |
| M2 | Migrations verified, API endpoints hardened | 1–2 weeks |
| M3 | Twilio SMS layer complete | 1–2 weeks |
| M4 | Feature work from handover docs | ongoing |

---

## 7. Risk Factors

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Existing codebase complexity | High | Deep read-first, ask clarifying questions |
| Data flow bugs are subtle | Medium | Write test queries against production-like DB |
| Twilio webhook debugging | Medium | Use ngrok/local dev, detailed logs |
| Scope creep (frontend) | Low | Occasional only, defined per-ticket |

---

## 8. Proposal Deliverables

The PROPOSAL.md and COVER_LETTER.txt must address:
- **Trial answer:** "Most complex existing codebase you've inherited and debugged. What was the bug, how did you find it, what was your process?"
- FastAPI + PostgreSQL depth
- Supabase experience
- Debug process (reading code + querying DB)
- Twilio SMS experience (if any)
- Async Python strength
- Clear written English
