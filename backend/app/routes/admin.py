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
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _stat(label: str, value: Any) -> str:
    return (
        f'<div class="stat"><b>{_cell(value)}</b>'
        f"<span>{html.escape(label)}</span></div>"
    )


_STYLE = """
:root { color-scheme: light dark; }
body { font: 15px/1.5 system-ui, sans-serif; margin: 0; padding: 2rem;
       max-width: 60rem; margin-inline: auto; }
h1 { font-size: 1.4rem; margin: 0 0 1.5rem; }
h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: .06em;
     opacity: .6; margin: 2.5rem 0 .75rem; }
.stats { display: flex; flex-wrap: wrap; gap: .75rem; }
.stat { flex: 1 1 8rem; border: 1px solid currentColor; border-radius: .5rem;
        padding: .75rem 1rem; }
.stat b { display: block; font-size: 1.6rem; }
.stat span { font-size: .8rem; opacity: .6; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid;
         border-color: color-mix(in srgb, currentColor 15%, transparent); }
th { font-size: .75rem; text-transform: uppercase; opacity: .6; }
td { font-variant-numeric: tabular-nums; }
.muted { opacity: .45; }
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
<h1>nectarly admin</h1>

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
