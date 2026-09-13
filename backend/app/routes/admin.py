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


# The pixel mascot, served by the web container at /favicon.svg and shared with
# HoneyDrop.tsx rather than inlined again — the inline copy had already drifted
# (its eyes were a row taller than the site's). Same origin in prod, where Caddy
# routes /api/* here and everything else to the web image, and in dev through
# Vite's /api proxy. 33x39 is the art's 11x13 at an exact 3x scale, so every
# pixel-art cell lands on a whole pixel.
_LOGO = '<img src="/favicon.svg" width="33" height="39" alt="">'

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
/* Same bob as the React header logo (index.css's .animate-bob). */
header img { animation: bob 3.4s ease-in-out infinite; }
@keyframes bob { 0%, 100% { transform: translateY(0) }
                 50% { transform: translateY(-7px) } }
h2 { font-size: 1.15rem; margin: 2.6rem 0 .9rem; }
.stats { display: flex; flex-wrap: wrap; gap: .7rem; }
.stat { flex: 1 1 8rem; background: var(--n-100); border: 1px solid var(--divider);
        border-radius: 16px; padding: .85rem 1.1rem;
        box-shadow: 0 1px 2px rgba(46, 43, 37, 0.14); }
.stat b { display: block; font-family: var(--heading); font-weight: 400;
          font-size: 1.85rem; line-height: 1.1; color: var(--a-700); }
.stat span { font-size: 12.5px; color: var(--n-700); }
.card { background: var(--n-100); border: 1px solid var(--divider);
        border-radius: 16px; overflow: auto; max-height: 26rem;
        box-shadow: 0 1px 2px rgba(46, 43, 37, 0.14); }
table { border-collapse: collapse; width: 100%; min-width: 30rem; }
th, td { text-align: left; padding: .55rem .9rem;
         border-bottom: 1px solid var(--divider); }
th { font-size: 11.5px; text-transform: uppercase; letter-spacing: .06em;
     color: var(--n-700); font-weight: 700; background: var(--surface);
     position: sticky; top: 0; z-index: 1;
     /* border-collapse drops a sticky cell's own border on scroll, so the
        header's underline is an inset shadow instead. */
     border-bottom: 0; box-shadow: inset 0 -1px 0 var(--divider); }
td { font-size: 14px; font-variant-numeric: tabular-nums; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--n-200); }
td:first-child { color: var(--sage-700); font-weight: 600; }
.muted { display: inline-block; background: var(--a-100); border-radius: 999px;
         border: 1px solid var(--a-200); padding: 0 .55rem;
         font-size: 12px; color: var(--a-700); }
p.muted { background: none; border: 0; color: var(--n-500); padding: .9rem; }
::selection { background: var(--a-200); }

/* Honey backdrop. Absolute at the document's top, so it scrolls away with the
   page; z-index -1 paints above the body background but under every in-flow
   element, so the drips run behind the cards. The layer is one viewport tall,
   so the bottom fade dissolves falling drops instead of clipping them at a
   hard line once the page is scrolled. */
.honey { position: absolute; inset: 0; width: 100%; height: 100%; z-index: -1;
         pointer-events: none; opacity: .72;
         -webkit-mask-image: linear-gradient(#000 70%, transparent);
         mask-image: linear-gradient(#000 70%, transparent); }
.strand { transform-box: fill-box; transform-origin: 50% 0;
          animation: strand var(--t) var(--d) infinite; }
.bulb { transform-box: fill-box; transform-origin: 50% 50%;
        transform: translateY(var(--l));
        animation: bulb var(--t) var(--d) infinite; }
/* One cycle: the strand stretches from the pool while the bulb swells at its
   tip (0-50%), the neck thins and creeps a little further (50-56%), then it
   snaps: the thread recoils fast and beads up while the bulb free-falls
   (56-61%), the stub sinks slowly back into the pool (61-76%), and everything
   sits hidden inside the pool until the next cycle. The recoil MUST start fast
   and decelerate — an ease-in here reads as the thread freezing mid-air. */
@keyframes strand {
  0%   { transform: scale(1, 0);
         animation-timing-function: cubic-bezier(.55, 0, .85, .4); }
  50%  { transform: scale(1, 1); animation-timing-function: ease-in; }
  56%  { transform: scale(.7, 1.08);
         animation-timing-function: cubic-bezier(.1, .9, .2, 1); }
  61%  { transform: scale(.95, .3); animation-timing-function: ease-in-out; }
  76%, 100% { transform: scale(1, 0); }
}
@keyframes bulb {
  0%   { transform: translateY(0) scale(.5);
         animation-timing-function: cubic-bezier(.55, 0, .85, .4); }
  50%  { transform: translateY(var(--l)) scale(1); animation-timing-function: ease-in; }
  56%  { transform: translateY(calc(var(--l) * 1.08)) scale(1);
         animation-timing-function: cubic-bezier(.4, 0, .9, .6); }
  /* step-end: snap back into the pool while off-screen, never mid-frame. */
  86%  { transform: translateY(110vh) scale(1); animation-timing-function: step-end; }
  100% { transform: translateY(0) scale(.5); }
}
@media (prefers-reduced-motion: reduce) {
  .strand, .bulb, header img { animation: none; }
}
"""


def _drip(x: int, y: int, w: int, r: int, length: int, cycle: int, delay: int) -> str:
    # x in vw and y in px put the group inside a pool lobe; the bulb rests there
    # at half size, merged into the pool by the goo filter until it emerges.
    return (
        f'<g style="transform:translate({x}vw,{y}px);'
        f'--l:{length}px;--t:{cycle}s;--d:{delay}s">'
        f'<rect class="strand" x="{-w / 2}" width="{w}" height="{length}"/>'
        f'<circle class="bulb" r="{r}"/></g>'
    )


# (x vw, y px, strand width, bulb radius, drop length, cycle s, delay s). Each x
# sits under a lobe of the pool path below; negative delays desync the loops.
_DRIPS = [
    (13, 78, 18, 14, 360, 15, -6),
    (31, 72, 12, 9, 200, 12, -2),
    (50, 84, 22, 17, 440, 18, -11),
    (70, 64, 11, 8, 150, 11, -5),
    (88, 80, 15, 12, 300, 14, -9),
]

# Pool edge in a 1000x100 box stretched to the viewport (preserveAspectRatio
# none), so the lobes land at the same vw fractions as _DRIPS' x values. Lobe
# spacing, depth and handle lengths are deliberately uneven — evenly spaced
# equal sags read as a scallop border, not poured honey.
_POOL = (
    "M0 0H1000V56C985 56 975 68 960 68C948 68 940 46 925 46C905 46 900 94 880 94"
    "C850 94 838 60 812 60C792 60 785 40 770 40C738 40 728 78 700 78"
    "C675 78 668 48 655 48C640 48 632 54 620 54C606 54 600 50 590 50"
    "C570 50 562 66 545 66C530 66 520 98 500 98C470 98 462 42 445 42"
    "C428 42 420 58 405 58C392 58 386 46 375 46C350 46 332 86 310 86"
    "C288 86 278 40 262 40C250 40 240 42 230 42C216 42 210 64 200 64"
    "C175 64 155 92 130 92C110 92 100 44 85 44C68 44 60 72 45 72"
    "C22 72 12 52 0 52Z"
)

# ponytail: the goo filter covers the whole viewport, so every frame blurs a
# full-screen layer. Fine on an admin page; if it ever janks, shrink the filter
# region to the pool band and move the falling bulb out of the filtered group.
_HONEY = (
    '<svg class="honey" aria-hidden="true"><defs>'
    '<linearGradient id="hg" x2="0" y2="1">'
    '<stop offset="0" stop-color="#f7cf5c"/><stop offset="1" stop-color="#e1932a"/>'
    "</linearGradient>"
    # Classic goo: blur, then crush the alpha so blobs fuse into one skin. The
    # same blur, offset and tinted terracotta, doubles as the drop shadow.
    '<filter id="goo" filterUnits="userSpaceOnUse" x="0" y="-10%" width="100%" '
    'height="120%" color-interpolation-filters="sRGB">'
    # 6/18/-7 rather than the usual 7/19/-9: the alpha crush eats anything
    # thinner than ~7px, and a necking strand has to stay visible at 70% width.
    '<feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b"/>'
    '<feColorMatrix in="b" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 18 -7" '
    'result="goo"/>'
    '<feOffset in="b" dy="5" result="o"/>'
    '<feFlood flood-color="#8c491a" flood-opacity=".35"/>'
    '<feComposite in2="o" operator="in" result="sh"/>'
    '<feMerge><feMergeNode in="sh"/><feMergeNode in="goo"/></feMerge>'
    "</filter></defs>"
    '<g filter="url(#goo)" fill="url(#hg)">'
    '<svg width="100%" height="100" viewBox="0 0 1000 100" '
    f'preserveAspectRatio="none"><path d="{_POOL}"/></svg>'
    + "".join(_drip(*d) for d in _DRIPS)
    + "</g></svg>"
)


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
{_HONEY}
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
