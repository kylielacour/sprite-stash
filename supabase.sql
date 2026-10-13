-- Sprite Stash: run this once in Supabase → SQL Editor → New query.

create table if not exists public.sprite_marks (
  sprite_id  integer     not null,
  person     text        not null check (person in ('k', 'j')),
  owned      boolean     not null default false,
  mastered   boolean     not null default false,
  updated_at timestamptz not null default now(),
  primary key (sprite_id, person)
);

-- Only signed-in users (you and Jerry) can read or change marks.
alter table public.sprite_marks enable row level security;

drop policy if exists "signed-in read"   on public.sprite_marks;
drop policy if exists "signed-in insert" on public.sprite_marks;
drop policy if exists "signed-in update" on public.sprite_marks;

create policy "signed-in read"   on public.sprite_marks for select to authenticated using (true);
create policy "signed-in insert" on public.sprite_marks for insert to authenticated with check (true);
create policy "signed-in update" on public.sprite_marks for update to authenticated using (true) with check (true);

-- Live updates between your two phones.
alter publication supabase_realtime add table public.sprite_marks;
