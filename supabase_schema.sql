-- MARG-AI — Supabase schema
--
-- This file is the version-controlled source of truth for the Supabase project
-- referenced in index.html (SUPABASE_URL / SUPABASE_ANON_KEY near the top of <head>).
-- It was written by reading the live schema directly from the project (ap-south-1 /
-- Mumbai, project ref mpfzxbvpndextzgiqpmo) — it matches what's actually deployed,
-- not an aspirational design. Keep this file and the live database in sync: any
-- schema change made through the Supabase dashboard or `apply_migration` should be
-- reflected back here in the same commit.
--
-- Safe to re-run: every statement is idempotent (IF NOT EXISTS / CREATE OR REPLACE).

-- ============================================================================
-- usage_events — anonymous, insert-only product analytics.
--
-- Logged from the client via trackEvent() (see index.html). Each row is tied only
-- to a random per-browser id (anon_id), never to a name, email or other identifying
-- detail — see the in-app Privacy Policy. There is deliberately no SELECT/UPDATE/
-- DELETE policy for the public/anon role: the client can only ever insert new rows,
-- never read, edit or remove existing ones. Only service-role access (dashboard,
-- SQL editor, or a future admin-only backend) can query this table.
-- ============================================================================

create table if not exists public.usage_events (
    id         uuid primary key default gen_random_uuid(),
    anon_id    text not null,
    event_name text not null,
    meta       jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_usage_events_created_at on public.usage_events using btree (created_at);
create index if not exists idx_usage_events_event_name on public.usage_events using btree (event_name);
create index if not exists idx_usage_events_anon_id on public.usage_events using btree (anon_id);

alter table public.usage_events enable row level security;

-- Anyone (including the anonymous/public client role) may INSERT a row, as long as
-- anon_id and event_name are both non-empty and no longer than 64 characters — this
-- bounds what a malicious client could stuff into the table, without needing any
-- server-side validation layer. No SELECT/UPDATE/DELETE policy exists for this role
-- by design, so the client genuinely cannot read back analytics data, even its own.
drop policy if exists "anyone can log an event" on public.usage_events;
create policy "anyone can log an event"
    on public.usage_events
    for insert
    to public
    with check (
        char_length(anon_id) >= 1 and char_length(anon_id) <= 64
        and char_length(event_name) >= 1 and char_length(event_name) <= 64
    );

-- Useful ad-hoc queries (run these in the Supabase SQL editor, not from the client —
-- there's no policy allowing the client to read this table):
--
--   -- events per day
--   select date_trunc('day', created_at) as day, count(*)
--   from usage_events group by 1 order by 1 desc;
--
--   -- most common events
--   select event_name, count(*) from usage_events group by 1 order by 2 desc;

-- ============================================================================
-- Not yet built: the "decision room" feature referenced in index.html's Supabase
-- comment (a shared space for a student + parent to plan together) has no tables
-- here because it was never implemented — only commented as an intended future
-- use of this Supabase project. When/if that's built, its schema (likely a `rooms`
-- table + membership + RLS scoped to room participants, probably with Realtime
-- enabled) belongs in this file alongside usage_events, not as a separate file.
-- ============================================================================
