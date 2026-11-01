-- 003: Security hardening (BG-01)
-- Run after 001_initial_schema.sql and 002_workflow.sql. Safe to re-run.
--
-- The FastAPI backend uses the service-role key, which bypasses RLS, for every write. Browsers only hold the public
-- anon key plus a user session, so through PostgREST they should be able to read their own workspace and nothing else.
-- Before this migration, the "same_org_all" policies let any signed-in user insert, update or delete workflow rows
-- (content, findings, approvals, sources...) and forge audit-log entries directly, bypassing every API check, and
-- "profiles_self_manage" let users change their own role or workspace.

-- Role of the signed-in user, read without RLS (like get_auth_user_org_id) so policies on profiles don't query
-- profiles under RLS themselves.
create or replace function public.get_auth_user_role()
returns text as $$
    select role from public.profiles where id = auth.uid() limit 1;
$$ language sql stable security definer set search_path = public;

-- Profiles: users may still update their own row, but never their role or workspace.
drop policy if exists "profiles_self_manage" on public.profiles;
create policy "profiles_self_manage" on public.profiles
    for update
    using (id = auth.uid())
    with check (
        id = auth.uid()
        and role = public.get_auth_user_role()
        and org_id = public.get_auth_user_org_id()
    );

-- Tenant tables: read-only for browser clients. All writes go through the API.
drop policy if exists "sources_same_org_all" on public.sources;
drop policy if exists "sources_admin_write" on public.sources;  -- 002: admins could write sources directly
drop policy if exists "sources_same_org_read" on public.sources;
create policy "sources_same_org_read" on public.sources
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "source_chunks_same_org_all" on public.source_chunks;
drop policy if exists "source_chunks_same_org_read" on public.source_chunks;
create policy "source_chunks_same_org_read" on public.source_chunks
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "rules_same_org_all" on public.rules;
drop policy if exists "rules_same_org_read" on public.rules;
create policy "rules_same_org_read" on public.rules
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "content_items_same_org_all" on public.content_items;
drop policy if exists "content_items_same_org_read" on public.content_items;
create policy "content_items_same_org_read" on public.content_items
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "content_versions_same_org_all" on public.content_versions;
drop policy if exists "content_versions_same_org_read" on public.content_versions;
create policy "content_versions_same_org_read" on public.content_versions
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "findings_same_org_all" on public.findings;
drop policy if exists "findings_same_org_read" on public.findings;
create policy "findings_same_org_read" on public.findings
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "comments_same_org_all" on public.comments;
drop policy if exists "comments_same_org_read" on public.comments;
create policy "comments_same_org_read" on public.comments
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "review_runs_same_org_all" on public.review_runs;
drop policy if exists "review_runs_same_org_read" on public.review_runs;
create policy "review_runs_same_org_read" on public.review_runs
    for select using (org_id = public.get_auth_user_org_id());

drop policy if exists "approvals_same_org_all" on public.approvals;
drop policy if exists "approvals_same_org_read" on public.approvals;
create policy "approvals_same_org_read" on public.approvals
    for select using (org_id = public.get_auth_user_org_id());

-- Audit log: browsers can read it but no longer insert (only the API writes audit entries).
drop policy if exists "audit_log_same_org_insert" on public.audit_log;
drop policy if exists "audit_log_same_org_read" on public.audit_log;
create policy "audit_log_same_org_read" on public.audit_log
    for select using (org_id = public.get_auth_user_org_id());
