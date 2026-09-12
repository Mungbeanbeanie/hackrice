import hmac
import html
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app import analytics, config

router = APIRouter()
security = HTTPBasic()


def _auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> None:
    # Fails closed. A missing password must never mean an open dashboard, and
    # the username is ignored on purpose — one shared password, no user list.
    if not config.ADMIN_PASSWORD:
        raise HTTPException(503, "ADMIN_PASSWORD is not set")
    if not hmac.compare_digest(credentials.password, config.ADMIN_PASSWORD):
        raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": "Basic"})


def _cell(value: Any) -> str:
    # Every value on this page passes through here. `query` is raw user input,
    # so skipping the escape would make the admin page a stored-XSS target.
    if value is None:
        return '<span class="muted">anonymous</span>'
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return html.escape(str(value))


def _table(headers: list[str], rows: list[Any]) -> str:
    if not rows:
        return '<p class="muted">Nothing yet.</p>'
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_cell(v)}</td>" for v in row) + "</tr>" for row in rows
    )
    return (
        f'<div class="card"><table><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def _stat(label: str, value: Any) -> str:
    return (
        f'<div class="stat"><b>{_cell(value)}</b>'
        f"<span>{html.escape(label)}</span></div>"
    )


# The pixel mascot from frontend/src/components/HoneyDrop.tsx, inlined. Copied
# rather than shared: this page deliberately has no build step (see
# architecture.md), so it cannot import from the React tree.
_LOGO = (
    '<svg width="34" height="34" viewBox="0 0 11 13" style="image-rendering:pixelated">'
    '<rect x="5" y="0" width="1" height="1" fill="#E87D00"/>'
    '<rect x="4" y="1" width="3" height="1" fill="#F5A623"/>'
    '<rect x="3" y="2" width="5" height="1" fill="#F5A623"/>'
    '<rect x="2" y="3" width="7" height="1" fill="#FFCC02"/>'
    '<rect x="1" y="4" width="9" height="2" fill="#FFCC02"/>'
    '<rect x="1" y="5" width="9" height="3" fill="#FFD740"/>'
    '<rect x="3" y="6" width="2" height="2" fill="#1a0800"/>'
    '<rect x="6" y="6" width="2" height="2" fill="#1a0800"/>'
    '<rect x="1" y="8" width="9" height="1" fill="#FFCC02"/>'
    '<rect x="2" y="9" width="7" height="1" fill="#F5A623"/>'
    '<rect x="3" y="10" width="5" height="1" fill="#F5A623"/>'
    '<rect x="4" y="11" width="3" height="1" fill="#E87D00"/>'
    '<rect x="5" y="12" width="1" height="1" fill="#D06800"/>'
    '<rect x="2" y="3" width="2" height="2" fill="#FFF176" fill-opacity="0.5"/>'
    "</svg>"
)

# Organic design tokens, copied from frontend/src/index.css. Same reason as
# _LOGO — no Tailwind build here, so the ramp is hand-written rather than
# imported. Only the values this page actually uses.
_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Caprasimo&family=Figtree:wght@400;600;700&display=swap');
:root {
  --bg: #f5ead8; --surface: #ebddc5; --text: #201e1d;
  --accent: #c67139; --divider: rgba(32, 30, 29, 0.16);
  --n-100: #f9f4ed; --n-200: #eee7db; --n-500: #a19786; --n-700: #645c50;
  --a-100: #fff2eb; --a-200: #ffe1d0; --a-700: #8c491a;
  --sage-700: #56633f;
  --heading: "Caprasimo", Georgia, serif;
  --body: "Figtree", system-ui, sans-serif;
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--text); font-family: var(--body);
       font-size: 15px; line-height: 1.55; -webkit-font-smoothing: antialiased;
       margin-inline: auto; max-width: 62rem; padding: 2rem 1rem 4rem; }
h1, h2 { font-family: var(--heading); font-weight: 400; letter-spacing: -0.015em; }
header { display: flex; align-items: center; gap: .7rem; margin-bottom: 2rem;
         padding-bottom: 1.2rem; border-bottom: 1px solid var(--divider); }
h1 { font-size: 1.55rem; margin: 0; }
header p { margin: 0; color: var(--n-700); font-size: 13px; }
h2 { font-size: 1.15rem; margin: 2.6rem 0 .9rem; }
.stats { display: flex; flex-wrap: wrap; gap: .7rem; }
.stat { flex: 1 1 8rem; background: var(--n-100); border: 1px solid var(--divider);
        border-radius: 16px; padding: .85rem 1.1rem;
        box-shadow: 0 1px 2px rgba(46, 43, 37, 0.14); }
.stat b { display: block; font-family: var(--heading); font-weight: 400;
          font-size: 1.85rem; line-height: 1.1; color: var(--a-700); }
.stat span { font-size: 12.5px; color: var(--n-700); }
.card { background: var(--n-100); border: 1px solid var(--divider);
        border-radius: 16px; overflow-x: auto;
        box-shadow: 0 1px 2px rgba(46, 43, 37, 0.14); }
table { border-collapse: collapse; width: 100%; min-width: 30rem; }
th, td { text-align: left; padding: .55rem .9rem;
         border-bottom: 1px solid var(--divider); }
th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .06em;
     color: var(--n-700); font-weight: 700; background: var(--surface); }
td { font-size: 14px; font-variant-numeric: tabular-nums; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--n-200); }
td:first-child { color: var(--sage-700); font-weight: 600; }
.muted { display: inline-block; background: var(--a-100); border-radius: 999px;
         border: 1px solid var(--a-200); padding: 0 .55rem;
         font-size: 12px; color: var(--a-700); }
p.muted { background: none; border: 0; color: var(--n-500); padding: .9rem; }
::selection { background: var(--a-200); }
"""


@router.get("/api/admin", response_class=HTMLResponse, dependencies=[Depends(_auth)])
def admin() -> str:
    try:
        s = analytics.admin_stats()
    except Exception as exc:
        # Same convention as routes/search.py and routes/auth.py: a dependency
        # we cannot reach is a 502, not a traceback.
        raise HTTPException(502, f"Stats unavailable: {exc}") from exc

    return f"""<!doctype html>
<meta charset="utf-8"><title>nectarly admin</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{_STYLE}</style>
<header>{_LOGO}<div><h1>nectarly admin</h1>
<p>signups and search activity</p></div></header>

<h2>Accounts</h2>
<div class="stats">
  {_stat("total signups", s["accounts_total"])}
  {_stat("last 24h", s["accounts_24h"])}
</div>

<h2>Searches</h2>
<div class="stats">
  {_stat("total searches", s["searches_total"])}
  {_stat("last 24h", s["searches_24h"])}
  {_stat("signed in", s["searches_signed_in"])}
  {_stat("anonymous", s["searches_anonymous"])}
</div>

<h2>Recent signups</h2>
{_table(["Email", "Joined"], s["recent_accounts"])}

<h2>Top queries</h2>
{_table(["Query", "Searches"], s["top_queries"])}

<h2>Recent searches</h2>
{_table(["When", "Query", "Mode", "Results", "Account"], s["recent_searches"])}
"""
