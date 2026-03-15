# Don'ts

## Supabase

**Never run `supabase db reset`** unless you intentionally want to wipe all data and start fresh.
- Drops all tables, auth users, storage files
- Browser sessions become invalid (JWT tokens no longer match any user)
- You'll need to sign up again and re-ingest all documents

**Never run `supabase stop --no-backup`** — removes Docker volumes, permanently deletes all data.

### Safe alternative for applying new migrations

```bash
npx supabase migration up
```

Applies only new migration files without touching existing data.
