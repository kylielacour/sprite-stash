-- Your marks copied from the claude.ai version. Run once, after supabase.sql.
insert into public.sprite_marks (sprite_id, person, owned, mastered) values
  (105, 'k', true, true),
  (105, 'j', true, true),
  (108, 'k', true, false),
  (108, 'j', true, true),
  (114, 'k', true, true),
  (114, 'j', true, false),
  (170, 'j', true, false),
  (171, 'j', true, false),
  (172, 'j', true, false),
  (176, 'k', false, false),
  (178, 'k', false, false),
  (185, 'k', true, false),
  (185, 'j', true, false),
  (186, 'k', true, false),
  (187, 'k', true, false),
  (205, 'j', true, true),
  (207, 'k', true, true),
  (207, 'j', true, true),
  (210, 'k', true, false),
  (210, 'j', true, false),
  (245, 'k', true, false)
on conflict (sprite_id, person) do update set owned = excluded.owned, mastered = excluded.mastered;
