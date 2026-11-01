-- Additive, optional multi-workspace support. Existing profiles remain authoritative
-- for their original workspace; no rows or existing policies are removed.
create table if not exists public.workspace_memberships (
  user_id uuid not null references auth.users(id) on delete cascade,
  org_id uuid not null references public.organisations(id) on delete cascade,
  role text not null check (role in ('admin', 'creator', 'manager', 'reviewer')),
  created_at timestamptz not null default now(),
  primary key (user_id, org_id)
);
alter table public.workspace_memberships enable row level security;
-- Membership writes are service-role only; a client can never grant itself access.
grant select on public.workspace_memberships to authenticated;
grant select, insert, update, delete on public.workspace_memberships to service_role;
revoke insert, update, delete on public.workspace_memberships from anon, authenticated;
drop policy if exists "workspace_memberships_self_read" on public.workspace_memberships;
create policy "workspace_memberships_self_read" on public.workspace_memberships
  for select to authenticated using (user_id = auth.uid());

create or replace function public.create_brandguard_workspace(p_user_id uuid, p_name text, p_description text)
returns uuid language plpgsql security invoker set search_path = public as $$
declare new_org uuid;
begin
  -- The API authorizes the caller. This RPC is unavailable to browser roles.
  insert into public.organisations(name) values (p_name) returning id into new_org;
  insert into public.workspace_memberships(user_id, org_id, role)
    values (p_user_id, new_org, 'admin');
  return new_org;
end;
$$;
revoke all on function public.create_brandguard_workspace(uuid, text, text) from public, anon, authenticated;
grant execute on function public.create_brandguard_workspace(uuid, text, text) to service_role;
