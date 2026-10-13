# Sprite Stash

Kylie & Jerry's shared Fortnite Sprite tracker (Chapter 7 Season 4). Sprite names and images from fortnite.gg.

- `template.html` is the source of the page. Run `python3 build.py` after editing it.
- `docs/` is what GitHub Pages serves. `docs/config.js` holds the Supabase URL and anon key.
- `supabase.sql` creates the table and its access rules. `supabase-import.sql` copies over marks from the old claude.ai version.
