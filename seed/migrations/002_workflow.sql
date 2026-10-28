-- ==============================================================================
-- BrandGuard 002: workflow, citations, review runs, approvals
-- Run after 001_initial_schema.sql. Idempotent.
-- ==============================================================================

-- Sources: human-readable citation code and extracted text
alter table public.sources add column if not exists code text;
alter table public.sources add column if not exists body text;
alter table public.sources drop constraint if exists sources_source_type_check;
alter table public.sources add constraint sources_source_type_check
    check (source_type in ('guideline', 'terminology', 'claim_library', 'regulatory', 'asset', 'other'));
create unique index if not exists idx_sources_org_code on public.sources(org_id, code);

-- Full-text fallback for retrieval when embeddings are unavailable
alter table public.source_chunks add column if not exists tsv tsvector
    generated always as (to_tsvector('english', content)) stored;
create index if not exists idx_source_chunks_tsv on public.source_chunks using gin (tsv);

-- Content items and versions
alter table public.content_items add column if not exists channel text not null default 'instagram_post'
    check (channel in ('instagram_post', 'website_page', 'influencer_post', 'press_release', 'email'));
alter table public.content_items add column if not exists ai_generated boolean not null default false;
alter table public.content_items add column if not exists current_version int not null default 1;
alter table public.content_versions add column if not exists alt_text text;
alter table public.content_versions add column if not exists note text;
create unique index if not exists idx_content_versions_item_no
    on public.content_versions(content_item_id, version_number);

-- Review runs
create table if not exists public.review_runs (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    content_item_id uuid not null references public.content_items(id) on delete cascade,
    content_version_id uuid not null references public.content_versions(id) on delete cascade,
    version_number int not null,
    layer_a_ms int default 0,
    layer_b_ms int default 0,
    used_fallback boolean default false,
    model text,
    created_at timestamptz default now() not null
);
create index if not exists idx_review_runs_org_id on public.review_runs(org_id);

-- Findings: YAML rule ids are text, citations are shown as codes
alter table public.findings drop constraint if exists findings_rule_id_fkey;
alter table public.findings alter column rule_id type text using rule_id::text;
alter table public.findings add column if not exists run_id uuid references public.review_runs(id) on delete cascade;
alter table public.findings add column if not exists source_codes text[] default array[]::text[];
alter table public.findings add column if not exists span_text text;
alter table public.findings add column if not exists decision_text text;
alter table public.findings add column if not exists replacement text;
alter table public.findings add column if not exists decided_at timestamptz;

-- Approvals (one row per workflow transition)
create table if not exists public.approvals (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    content_item_id uuid not null references public.content_items(id) on delete cascade,
    version_number int not null,
    actor_id uuid references auth.users(id) on delete set null,
    role text,
    action text not null check (action in ('submit', 'approve', 'request_changes', 'escalate', 'reject')),
    reason text,
    override boolean default false,
    created_at timestamptz default now() not null
);
create index if not exists idx_approvals_org_id on public.approvals(org_id);

alter table public.review_runs enable row level security;
alter table public.approvals enable row level security;
drop policy if exists "review_runs_same_org_all" on public.review_runs;
create policy "review_runs_same_org_all" on public.review_runs
    for all using (org_id = public.get_auth_user_org_id());
drop policy if exists "approvals_same_org_all" on public.approvals;
create policy "approvals_same_org_all" on public.approvals
    for all using (org_id = public.get_auth_user_org_id());

-- Role enforcement in the database: only creators/admins write content, only
-- admins write sources, nobody but the backend (service role) writes approvals.
drop policy if exists "sources_same_org_all" on public.sources;
drop policy if exists "sources_same_org_read" on public.sources;
create policy "sources_same_org_read" on public.sources
    for select using (org_id = public.get_auth_user_org_id());
drop policy if exists "sources_admin_write" on public.sources;
create policy "sources_admin_write" on public.sources
    for all using (
        org_id = public.get_auth_user_org_id()
        and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
    );
drop policy if exists "approvals_same_org_all" on public.approvals;
drop policy if exists "approvals_same_org_read" on public.approvals;
create policy "approvals_same_org_read" on public.approvals
    for select using (org_id = public.get_auth_user_org_id());

-- Storage: scope objects to the caller's org folder (path = <org_id>/...)
drop policy if exists "sources_bucket_authenticated_access" on storage.objects;
drop policy if exists "sources_bucket_org_access" on storage.objects;
create policy "sources_bucket_org_access" on storage.objects
    for all using (
        bucket_id = 'sources' and (storage.foldername(name))[1] = public.get_auth_user_org_id()::text
    );
drop policy if exists "submissions_bucket_authenticated_access" on storage.objects;
drop policy if exists "submissions_bucket_org_access" on storage.objects;
create policy "submissions_bucket_org_access" on storage.objects
    for all using (
        bucket_id = 'submissions' and (storage.foldername(name))[1] = public.get_auth_user_org_id()::text
    );
