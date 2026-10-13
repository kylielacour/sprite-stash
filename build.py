"""Builds both versions of Sprite Stash from template.html.

  index.html       -> the claude.ai artifact (shared data in the artifact db)
  docs/index.html  -> the GitHub Pages site (shared data in Supabase)

Run: python3 build.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
template = (ROOT / "template.html").read_text()
data = (ROOT / "sprites.json").read_text().strip()


def rep(text, old, new):
    assert text.count(old) == 1, f"expected exactly one match for: {old[:60]!r}"
    return text.replace(old, new)


page = template.replace("/*DATA*/[]", data)
(ROOT / "index.html").write_text(page)

# ---- GitHub Pages + Supabase version ----
site = page

site = rep(site, '<link rel="preconnect" href="https://fonts.googleapis.com">',
'''<link rel="preconnect" href="https://fonts.googleapis.com">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#2f3136">
<link rel="icon" href="crown.webp">
<link rel="apple-touch-icon" href="img/182.webp">''')

site = rep(site, "</style>", '''html, body { margin: 0; }
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
img { max-width: 100%; }
[hidden] { display: none !important; }
.login {
  position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; padding: 16px;
  background: color-mix(in srgb, var(--bg) 80%, transparent); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
}
.login form { width: min(360px, 100%); background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
.login h2 { font: 700 24px/1.1 var(--font); letter-spacing: -0.03em; margin: 0; }
.login p { margin: 0; color: var(--muted); font-size: 13px; }
.login input { font: 15px var(--font); color: var(--fg); background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; }
.login button { font: 600 15px/1 var(--font); background: var(--fg); color: var(--bg); border: 0; border-radius: 10px; padding: 12px; cursor: pointer; }
.login .err { color: #ff8a8a; min-height: 1em; }
.signout { background: none; border: 0; color: var(--muted); font: inherit; text-decoration: underline; cursor: pointer; padding: 0; }
</style>''')

site = rep(site, '<span id="status">Connecting…</span>',
'<span id="status">Connecting…</span>\n    <button id="signOut" class="signout" type="button" hidden>Sign out</button>')

site = rep(site, "<main>", '''<div id="login" class="login" hidden>
    <form id="loginForm">
      <h2>Sign in</h2>
      <p>Use the account set up for you in Supabase.</p>
      <input id="email" type="email" autocomplete="username" placeholder="Email" required>
      <input id="password" type="password" autocomplete="current-password" placeholder="Password" required>
      <button type="submit">Sign in</button>
      <p id="loginErr" class="err" aria-live="polite"></p>
    </form>
  </div>

  <main>''')

# Replace the artifact-db save with a Supabase upsert of this person's row.
start = site.index("async function save(patch) {")
end = site.index("function setMe(who) {")
site = site[:start] + '''async function save(patch) {
  const [id, mine] = Object.entries(patch.own)[0];
  const row = { sprite_id: Number(id), person: me, owned: !!mine[me], mastered: !!mine[me + "m"], updated_at: new Date().toISOString() };
  setStatus("Saving…");
  for (let attempt = 0; attempt < 2; attempt++) {
    const { error } = await sb.from("sprite_marks").upsert(row);
    if (!error) { setStatus("Saved"); return; }
    if (error.code === "42501") { canWrite = false; setStatus(NO_EDIT, true); return; }
    await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
  }
  setStatus("Couldn't save that tap. Check your connection and tap it again.", true);
}

''' + site[end:]

site = rep(site, 'const NO_EDIT = "You can look but not edit. Ask Kylie to share it with you as a Contributor.";',
               'const NO_EDIT = "This account can\'t save changes. Check the Supabase table policies.";')

start = site.index("(async () => {\n  const db = window.claude")
end = site.index("</script>", start)
site = site[:start] + '''const sb = window.supabase.createClient(window.SPRITE_STASH.supabaseUrl, window.SPRITE_STASH.supabaseAnonKey);
let channel = null;

function applyRow(r) {
  const cur = own[r.sprite_id] || {};
  own = { ...own, [r.sprite_id]: { ...cur, [r.person]: r.owned, [r.person + "m"]: r.mastered } };
}

async function loadAll() {
  const { data, error } = await sb.from("sprite_marks").select("sprite_id, person, owned, mastered");
  if (error) { setStatus("Couldn't load your sprites. Reload to try again.", true); return false; }
  own = {};
  data.forEach(applyRow);
  render();
  return true;
}

async function connect() {
  stateRef = true;
  document.getElementById("login").hidden = true;
  document.getElementById("signOut").hidden = false;
  setStatus("Syncing…");
  if (!(await loadAll())) return;
  if (channel) sb.removeChannel(channel);
  channel = sb.channel("sprite_marks")
    .on("postgres_changes", { event: "*", schema: "public", table: "sprite_marks" }, p => {
      if (p.new && p.new.sprite_id != null) { applyRow(p.new); render(); }
    })
    .subscribe(status => {
      if (status === "SUBSCRIBED") setStatus("Live");
      else if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") setStatus("Lost the live connection. Reload the page to reconnect.", true);
    });
}

function showLogin() {
  stateRef = null;
  if (channel) { sb.removeChannel(channel); channel = null; }
  own = {};
  render();
  document.getElementById("signOut").hidden = true;
  document.getElementById("login").hidden = false;
  setStatus("Signed out");
}

document.getElementById("loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  const err = document.getElementById("loginErr");
  err.textContent = "";
  const { error } = await sb.auth.signInWithPassword({
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value,
  });
  if (error) { err.textContent = "That email and password didn't match. Try again."; return; }
  connect();
});
document.getElementById("signOut").addEventListener("click", async () => { await sb.auth.signOut(); showLogin(); });

// Refetch when the tab comes back, in case realtime missed something while the phone slept.
document.addEventListener("visibilitychange", () => { if (!document.hidden && stateRef) loadAll(); });

sb.auth.getSession().then(({ data }) => { if (data.session) connect(); else showLogin(); });
''' + site[end:]

site = rep(site, "<script>\n// [id, name",
'''<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>
<script src="config.js"></script>
<script>
// [id, name''')

docs = ROOT / "docs"
docs.mkdir(exist_ok=True)
(docs / "index.html").write_text("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n" + site.replace("</style>", "</style>\n</head>\n<body>", 1) + "\n</body>\n</html>\n")
shutil.copy(ROOT / "crown.webp", docs / "crown.webp")
shutil.copytree(ROOT / "img", docs / "img", dirs_exist_ok=True)
if not (docs / "config.js").exists():
    (docs / "config.js").write_text(
        "// Supabase project settings. The anon key is meant to be public; the table's\n"
        "// row-level security is what keeps strangers out.\n"
        "window.SPRITE_STASH = {\n"
        '  supabaseUrl: "https://YOUR-PROJECT.supabase.co",\n'
        '  supabaseAnonKey: "YOUR-ANON-KEY",\n'
        "};\n")
(docs / ".nojekyll").write_text("")
print("built index.html and docs/")
