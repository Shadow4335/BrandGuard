-- ==============================================================================
-- BrandGuard Initial Schema Migration
-- Designed for Supabase SQL Editor execution in one paste
-- ==============================================================================

-- 1. Enable Required Extensions
create extension if not exists "uuid-ossp";
create extension if not exists vector;

-- 2. Organizations Table
create table if not exists public.organisations (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    created_at timestamptz default now() not null,
    updated_at timestamptz default now() not null
);

-- 3. Profiles Table (extends auth.users with tenant isolation & role)
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    org_id uuid not null references public.organisations(id) on delete cascade,
    role text not null check (role in ('admin', 'creator', 'manager', 'reviewer')),
    email text,
    full_name text,
    created_at timestamptz default now() not null,
    updated_at timestamptz default now() not null
);

-- 4. Sources Table (brand guidelines, claims, regulatory, asset libraries)
create table if not exists public.sources (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    title text not null,
    source_type text not null default 'guideline' check (source_type in ('guideline', 'claim_library', 'regulatory', 'asset', 'other')),
    file_path text,
    metadata jsonb default '{}'::jsonb not null,
    created_at timestamptz default now() not null,
    updated_at timestamptz default now() not null
);

-- 5. Source Chunks Table (vector embeddings for Layer B retrieval)
create table if not exists public.source_chunks (
    id uuid primary key default gen_random_uuid(),
    source_id uuid not null references public.sources(id) on delete cascade,
    org_id uuid not null references public.organisations(id) on delete cascade,
    content text not null,
    embedding vector(768),
    chunk_index int default 0 not null,
    metadata jsonb default '{}'::jsonb not null,
    created_at timestamptz default now() not null
);

-- HNSW Vector Index for efficient cosine similarity queries
create index if not exists idx_source_chunks_embedding
    on public.source_chunks
    using hnsw (embedding vector_cosine_ops);

-- 6. Rules Table (Layer A regex, rapidfuzz, prohibited terms)
create table if not exists public.rules (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    name text not null,
    description text,
    category text not null check (category in ('tone', 'terminology', 'messaging', 'claim', 'disclosure', 'visual', 'accessibility')),
    severity text not null check (severity in ('high', 'medium', 'low')),
    pattern text not null,
    rule_type text not null default 'regex',
    is_active boolean default true not null,
    metadata jsonb default '{}'::jsonb not null,
    created_at timestamptz default now() not null,
    updated_at timestamptz default now() not null
);

-- 7. Content Items Table (governed marketing materials)
create table if not exists public.content_items (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    title text not null,
    status text not null default 'draft' check (status in ('draft', 'checked', 'changes_requested', 'pending_manager', 'escalated', 'approved', 'rejected')),
    creator_id uuid references auth.users(id) on delete set null,
    created_at timestamptz default now() not null,
    updated_at timestamptz default now() not null
);

-- 8. Content Versions Table
create table if not exists public.content_versions (
    id uuid primary key default gen_random_uuid(),
    content_item_id uuid not null references public.content_items(id) on delete cascade,
    org_id uuid not null references public.organisations(id) on delete cascade,
    version_number int default 1 not null,
    file_type text default 'text/plain' not null,
    raw_text text,
    file_path text,
    created_by uuid references auth.users(id) on delete set null,
    created_at timestamptz default now() not null
);

-- 9. Findings Table (core contract for Layer A & Layer B findings)
create table if not exists public.findings (
    id uuid primary key default gen_random_uuid(),
    content_version_id uuid not null references public.content_versions(id) on delete cascade,
    org_id uuid not null references public.organisations(id) on delete cascade,
    layer text not null check (layer in ('A', 'B')),
    category text not null check (category in ('tone', 'terminology', 'messaging', 'claim', 'disclosure', 'visual', 'accessibility')),
    rule_id uuid references public.rules(id) on delete set null,
    source_ids uuid[] default array[]::uuid[],
    span jsonb,
    region jsonb,
    issue text not null,
    why_flagged text not null,
    suggested_fix text not null,
    severity text not null check (severity in ('high', 'medium', 'low')),
    confidence text not null check (confidence in ('high', 'medium', 'low')),
    status text not null default 'open' check (status in ('open', 'accepted', 'edited', 'rejected')),
    decided_by uuid references auth.users(id) on delete set null,
    decision_reason text,
    created_at timestamptz default now() not null
);

-- 10. Comments Table
create table if not exists public.comments (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    finding_id uuid references public.findings(id) on delete cascade,
    content_version_id uuid not null references public.content_versions(id) on delete cascade,
    author_id uuid not null references auth.users(id) on delete cascade,
    text text not null,
    created_at timestamptz default now() not null
);

-- 11. Audit Log Table (Append-only governance trail)
create table if not exists public.audit_log (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organisations(id) on delete cascade,
    event_type text not null,
    actor_id uuid references auth.users(id) on delete set null,
    target_type text not null,
    target_id uuid,
    details jsonb default '{}'::jsonb not null,
    created_at timestamptz default now() not null
);

-- 12. Create Tenant & Entity Indexes
create index if not exists idx_profiles_org_id on public.profiles(org_id);
create index if not exists idx_sources_org_id on public.sources(org_id);
create index if not exists idx_source_chunks_org_id on public.source_chunks(org_id);
create index if not exists idx_rules_org_id on public.rules(org_id);
create index if not exists idx_content_items_org_id on public.content_items(org_id);
create index if not exists idx_content_versions_org_id on public.content_versions(org_id);
create index if not exists idx_findings_org_id on public.findings(org_id);
create index if not exists idx_findings_version on public.findings(content_version_id);
create index if not exists idx_comments_org_id on public.comments(org_id);
create index if not exists idx_audit_log_org_id on public.audit_log(org_id);

-- 13. Append-Only Trigger for audit_log (Hard Rule 5)
create or replace function public.reject_audit_log_modification()
returns trigger as $$
begin
    raise exception 'audit_log is append-only: UPDATE and DELETE operations are forbidden.';
end;
$$ language plpgsql;

drop trigger if exists trg_audit_log_immutable on public.audit_log;
create trigger trg_audit_log_immutable
    before update or delete on public.audit_log
    for each row
    execute function public.reject_audit_log_modification();

-- 14. Helper Function for Current User Org ID
create or replace function public.get_auth_user_org_id()
returns uuid as $$
    select org_id from public.profiles where id = auth.uid() limit 1;
$$ language sql stable security definer;

-- 15. Enable Row-Level Security (RLS) on All Tables
alter table public.organisations enable row level security;
alter table public.profiles enable row level security;
alter table public.sources enable row level security;
alter table public.source_chunks enable row level security;
alter table public.rules enable row level security;
alter table public.content_items enable row level security;
alter table public.content_versions enable row level security;
alter table public.findings enable row level security;
alter table public.comments enable row level security;
alter table public.audit_log enable row level security;

-- 16. RLS Policies (Tenant Isolation)
-- Organisations
drop policy if exists "organisations_same_org_read" on public.organisations;
create policy "organisations_same_org_read" on public.organisations
    for select using (id = public.get_auth_user_org_id());

-- Profiles
drop policy if exists "profiles_same_org_read" on public.profiles;
create policy "profiles_same_org_read" on public.profiles
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "profiles_self_manage" on public.profiles;
create policy "profiles_self_manage" on public.profiles
    for update using (id = auth.uid());

-- Sources
drop policy if exists "sources_same_org_all" on public.sources;
create policy "sources_same_org_all" on public.sources
    for all using (org_id = public.get_auth_user_org_id());

-- Source Chunks
drop policy if exists "source_chunks_same_org_all" on public.source_chunks;
create policy "source_chunks_same_org_all" on public.source_chunks
    for all using (org_id = public.get_auth_user_org_id());

-- Rules
drop policy if exists "rules_same_org_all" on public.rules;
create policy "rules_same_org_all" on public.rules
    for all using (org_id = public.get_auth_user_org_id());

-- Content Items
drop policy if exists "content_items_same_org_all" on public.content_items;
create policy "content_items_same_org_all" on public.content_items
    for all using (org_id = public.get_auth_user_org_id());

-- Content Versions
drop policy if exists "content_versions_same_org_all" on public.content_versions;
create policy "content_versions_same_org_all" on public.content_versions
    for all using (org_id = public.get_auth_user_org_id());

-- Findings
drop policy if exists "findings_same_org_all" on public.findings;
create policy "findings_same_org_all" on public.findings
    for all using (org_id = public.get_auth_user_org_id());

-- Comments
drop policy if exists "comments_same_org_all" on public.comments;
create policy "comments_same_org_all" on public.comments
    for all using (org_id = public.get_auth_user_org_id());

-- Audit Log: Select & Insert Only (No Update/Delete)
drop policy if exists "audit_log_same_org_read" on public.audit_log;
create policy "audit_log_same_org_read" on public.audit_log
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "audit_log_same_org_insert" on public.audit_log;
create policy "audit_log_same_org_insert" on public.audit_log
    for insert with check (org_id = public.get_auth_user_org_id());

-- 17. Vector Similarity Search Function (RPC)
create or replace function public.match_chunks(
    query_embedding vector(768),
    org_id uuid,
    source_types text[] default null,
    k int default 5
)
returns table (
    id uuid,
    source_id uuid,
    org_id uuid,
    content text,
    metadata jsonb,
    similarity float
)
language plpgsql
security definer
as $$
begin
    return query
    select
        sc.id,
        sc.source_id,
        sc.org_id,
        sc.content,
        sc.metadata,
        (1 - (sc.embedding <=> query_embedding))::float as similarity
    from public.source_chunks sc
    join public.sources s on s.id = sc.source_id
    where sc.org_id = match_chunks.org_id
      and (
          match_chunks.source_types is null
          or cardinality(match_chunks.source_types) = 0
          or s.source_type = any(match_chunks.source_types)
      )
    order by sc.embedding <=> query_embedding
    limit k;
end;
$$;

-- 18. Storage Buckets & Policies (sources and submissions)
insert into storage.buckets (id, name, public)
values ('sources', 'sources', false), ('submissions', 'submissions', false)
on conflict (id) do nothing;

-- Storage policies for authenticated users
drop policy if exists "sources_bucket_authenticated_access" on storage.objects;
create policy "sources_bucket_authenticated_access" on storage.objects
    for all using (
        bucket_id = 'sources' and auth.role() = 'authenticated'
    );

drop policy if exists "submissions_bucket_authenticated_access" on storage.objects;
create policy "submissions_bucket_authenticated_access" on storage.objects
    for all using (
        bucket_id = 'submissions' and auth.role() = 'authenticated'
    );
