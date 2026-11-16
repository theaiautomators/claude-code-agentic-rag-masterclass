# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

## Modules

### [-] Module 1: App Shell + Observability

**Plan 1 — Supabase + Schema + RLS** (`.agent/plans/1.supabase-auth-setup.md`)
- [x] Root `.gitignore`
- [x] Supabase CLI as npm dev dependency (`npm run supabase -- <cmd>`), `supabase init` + `start`
- [x] Chat schema migration (`threads`, `messages`, indexes)
- [x] Row-Level Security (8 per-user policies; message writes also require thread ownership)
- [x] Auth config (email signup on, confirmations off, `site_url` = http://localhost:5173)

**Plan 2 — Backend chat API** (`.agent/plans/2.backend-chat-api.md`)
- [ ] Not started

**Plan 3 — Frontend chat UI** (`.agent/plans/3.frontend-chat-ui.md`)
- [ ] Not started