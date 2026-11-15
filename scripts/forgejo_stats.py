#!/usr/bin/env python3
"""Render contributions-2d.svg: a GitHub-style calendar, GitHub + Forgejo combined.

GitHub counts come from the public contributions page (no token needed).
Forgejo counts come from commits authored by you on your own, non-migrated
repos. Repos migrated or mirrored from GitHub are skipped, so GitHub's import
history does not get counted twice.

Usage: FORGEJO_TOKEN=... python3 scripts/forgejo_stats.py contributions-2d.svg
       python3 scripts/forgejo_stats.py --selftest
"""
import json
import math
import os
import re
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

BASE = os.environ.get("FORGEJO_URL", "https://forgejo.mateuszkorniak.pl").rstrip("/")
TOKEN = os.environ.get("FORGEJO_TOKEN", "")
GH_USER = os.environ.get("GITHUB_USER", "ZiQu-dev")
PAGE = 50
EXTRA_NAMES = {"Mateusz Korniak"}  # commit author names that also count as you
LEVELS = ["#18181b", "#3b2a6b", "#5b3fb0", "#8b6cf0", "#c4b5fd"]
TEAL = ["#18181b", "#134e4a", "#0f766e", "#14b8a6", "#5eead4"]  # Forgejo accent


def api(path):
    req = urllib.request.Request(f"{BASE}/api/v1{path}", headers={"Authorization": f"token {TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def paged(path):
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        items = api(f"{path}{sep}limit={PAGE}&page={page}")
        yield from items
        if len(items) < PAGE:
            return
        page += 1


IGNORE = {x.strip() for x in os.environ.get("IGNORE_REPOS", "").split(",") if x.strip()}  # "name" or "owner/name"


def is_counted_repo(repo):
    # shortcut: migrated repos are detected via original_url/mirror flags only, a manual "fork" of GitHub code would still count, upgrade if that bites
    return (not repo.get("mirror") and not repo.get("original_url") and not repo.get("empty")
            and repo["full_name"] not in IGNORE and repo["name"] not in IGNORE)


def is_me(commit, login):
    author = commit.get("author") or {}
    name = commit["commit"]["author"]["name"]
    return author.get("login") == login or name in EXTRA_NAMES | {login}


GH_TOKEN = os.environ.get("GH_TOKEN", "")
GQL_CALENDAR = ("query($login: String!) { user(login: $login) { contributionsCollection { "
                "contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }")


GQL_RANGE = ("query($login: String!, $from: DateTime!, $to: DateTime!) { user(login: $login) { contributionsCollection(from: $from, to: $to) { "
             "contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }")


def github_daily(user, token="", start=None, end=None):
    """Per-day counts for [start, end] (default: last year). With a token: GraphQL, includes private
    contribution counts (no repo names). Without: GitHub's public calendar page, public activity only."""
    if token:
        variables = {"login": user}
        query = GQL_CALENDAR
        if start and end:
            query = GQL_RANGE
            variables |= {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"}
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "forgejo-stats"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return parse_graphql_calendar(json.load(r))
    qs = f"?from={start}&to={end}" if start and end else ""
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions{qs}",
                                 headers={"User-Agent": "forgejo-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return parse_github_calendar(r.read().decode("utf-8"))


def parse_graphql_calendar(body):
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def parse_github_calendar(html):
    days = {}
    for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})" id="(contribution-day-component-\d+-\d+)"', html):
        day, cell = m.groups()
        tip = re.search(rf'for="{cell}"[^>]*>([^<]*)', html)
        count = re.match(r"(\d+) contributions? on", tip.group(1)) if tip else None
        days[day] = int(count.group(1)) if count else 0
    return days


def forgejo_repos():
    """Your repos plus every org repo you can read, minus migrated/mirrored ones. Logs both lists."""
    every = list(paged("/user/repos"))
    for r in every:
        if not is_counted_repo(r):
            ignored = r["full_name"] in IGNORE or r["name"] in IGNORE
            print(f"skipped {r['full_name']}: ignored={ignored} mirror={r.get('mirror')} original_url={r.get('original_url') or '-'}")
    return [r for r in every if is_counted_repo(r)]


def collect_forgejo(repos, login, since):
    def my_commit_dates(r):
        path = f"/repos/{r['full_name']}/commits?stat=false&files=false&verification=false&since={since}"
        return [c["commit"]["author"]["date"][:10] for c in paged(path) if is_me(c, login)]

    daily = Counter()
    with ThreadPoolExecutor(8) as ex:
        for r, dates in zip(repos, ex.map(my_commit_dates, repos)):
            print(f"counted {r['full_name']}: {len(dates)} of your commits")
            daily.update(dates)
    return daily


def forgejo_languages(repos):
    totals = Counter()
    with ThreadPoolExecutor(8) as ex:
        for langs in ex.map(lambda r: api(f"/repos/{r['full_name']}/languages"), repos):
            totals.update(langs)
    return totals


def calendar_days(today):
    """53 Sunday-aligned weeks ending today, as (date, row, col) with Sunday as row 0."""
    row_today = (today.weekday() + 1) % 7
    start = today - timedelta(days=52 * 7 + row_today)
    out = []
    for i in range((today - start).days + 1):
        d = start + timedelta(days=i)
        out.append((d, (d.weekday() + 1) % 7, i // 7))
    return out


def render_calendar(gh, fg, today):
    cell, gap, left, top = 11, 3, 36, 84
    days = calendar_days(today)
    totals = {d.isoformat(): gh.get(d.isoformat(), 0) + fg.get(d.isoformat(), 0) for d, _, _ in days}
    peak = max([1, *totals.values()])
    width = left + 53 * (cell + gap) + 10
    height = top + 7 * (cell + gap) + 36
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" font-family="monospace">',
        f'<rect width="{width}" height="{height}" rx="10" fill="#09090b" stroke="#27272a"/>',
        f'<text x="{left}" y="34" fill="#e4e4e7" font-size="13">Contributions, last year: GitHub + Forgejo</text>',
    ]
    seen_months = set()
    for d, row, col in days:
        key = d.strftime("%Y-%m")
        if d.day <= 7 and key not in seen_months and row == 0:
            seen_months.add(key)
            out.append(f'<text x="{left + col * (cell + gap)}" y="{top - 8}" fill="#71717a" font-size="9">{d.strftime("%b")}</text>')
        k = d.isoformat()
        t = totals[k]
        lvl = 0 if t == 0 else min(4, math.ceil(4 * t / peak))
        x, y = left + col * (cell + gap), top + row * (cell + gap)
        tip = f"{k}: GitHub {gh.get(k, 0)}, Forgejo {fg.get(k, 0)}"
        out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{LEVELS[lvl]}"><title>{tip}</title></rect>')
        if fg.get(k, 0) > 0:
            out.append(f'<circle cx="{x + cell - 2.5}" cy="{y + 2.5}" r="2" fill="#5eead4"/>')
    legend_y = top + 7 * (cell + gap) + 18
    out.append(f'<text x="{left}" y="{legend_y}" fill="#71717a" font-size="10">less</text>')
    for i, c in enumerate(LEVELS):
        out.append(f'<rect x="{left + 34 + i * 14}" y="{legend_y - 9}" width="11" height="11" rx="2" fill="{c}"/>')
    out.append(f'<text x="{left + 34 + 5 * 14 + 4}" y="{legend_y}" fill="#71717a" font-size="10">more   teal dot = Forgejo</text>')
    out.append("</svg>")
    return "\n".join(out)


def shade(hex_color, f):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{min(255, int(v * f)):02x}" for v in (r, g, b))


def render_isometric(gh, fg, today, _panel=False):
    """Isometric 3D version: flat tile per day, bar height = combined count."""
    k, pad, maxh = 6, 16, 36  # small scale so three yearly panels fit side by side on a README
    days = calendar_days(today)
    tot = {d.isoformat(): gh.get(d.isoformat(), 0) + fg.get(d.isoformat(), 0) for d, _, _ in days}
    peak = max([1, *tot.values()])
    hd = 0 if _panel else 34  # header band for the title
    ox, oy = 7 * k + pad, maxh + 44 + hd
    width, height = 60 * k + 2 * pad, oy + 30 * k + pad + 30

    def p(c, r, z):
        return (ox + (c - r) * k, oy + (c + r) * k / 2 - z)

    def poly(pts, fill):
        coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        return f'<polygon points="{coords}" fill="{fill}" stroke="#09090b" stroke-width="0.5"/>'

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" font-family="monospace">']
    if not _panel:
        out.append(f'<rect width="{width}" height="{height}" rx="10" fill="#09090b" stroke="#27272a"/>')
        out.append(f'<text x="{pad}" y="32" fill="#e4e4e7" font-size="13">Contributions calendar: GitHub + Forgejo</text>')
    for d, row, col in sorted(days, key=lambda t: t[1] + t[2]):
        key = d.isoformat()
        t = tot[key]
        lvl = 0 if t == 0 else min(4, math.ceil(4 * t / peak))
        h = 0 if t == 0 else 6 + (maxh - 6) * t / peak
        forgejo_led = fg.get(key, 0) > 0 and fg.get(key, 0) >= gh.get(key, 0)
        top = (TEAL if forgejo_led else LEVELS)[lvl]
        if h > 0:
            out.append(poly([p(col + 1, row, 0), p(col + 1, row + 1, 0), p(col + 1, row + 1, h), p(col + 1, row, h)], shade(top, 0.6)))
            out.append(poly([p(col, row + 1, 0), p(col + 1, row + 1, 0), p(col + 1, row + 1, h), p(col, row + 1, h)], shade(top, 0.8)))
        out.append(poly([p(col, row, h), p(col + 1, row, h), p(col + 1, row + 1, h), p(col, row + 1, h)], top))
    if not _panel:  # the row puts totals in its own left column instead
        legend = f"GitHub {sum(gh.values())} · Forgejo {sum(fg.values())} · last year · teal top = mostly Forgejo"
        out.append(f'<text x="{pad}" y="{height - 14}" fill="#71717a" font-size="10">{legend}</text>')
    out.append("</svg>")
    return "\n".join(out)


YEARS = 2  # 3D panels stacked in depth, newest in front


def render_isometric_row(panels):
    """One shared header; yearly panels stacked in depth: newest in front, older ones behind and above."""
    parts = [render_isometric(gh, fg, end, _panel=True) for end, gh, fg in panels]
    w = int(re.search(r'width="(\d+)"', parts[0]).group(1))
    ph = int(re.search(r'height="(\d+)"', parts[0]).group(1))
    top, pad, step, n = 76, 40, 64, len(parts)  # step = how far each older year sits above the one in front
    lbl = 180  # left column for date labels and totals, so they never sit on the bars
    grid_top = 36 + 44  # same as render_isometric's oy for a panel (maxh + 44)
    W, H = pad + lbl + w + pad, top + ph + (n - 1) * step + pad
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="monospace">',
           f'<rect width="{W}" height="{H}" rx="10" fill="#09090b" stroke="#27272a"/>',
           f'<text x="{pad}" y="32" fill="#e4e4e7" font-size="13">Contributions, last {n} years: GitHub + Forgejo</text>']
    for k in reversed(range(n)):  # draw the oldest first so newer panels cover the back ones
        end, part = panels[k][0], parts[k]
        y = top + (n - 1 - k) * step
        first = calendar_days(end)[0][0]
        out.append(part.replace('<svg xmlns="http://www.w3.org/2000/svg"', f'<svg x="{pad + lbl}" y="{y}"', 1))
        g, f = sum(panels[k][1].values()), sum(panels[k][2].values())
        out.append(f'<text x="{pad}" y="{y + grid_top}" fill="#e4e4e7" font-size="11">{first.strftime("%b %Y")} \u2013 {end.strftime("%b %Y")}</text>')
        out.append(f'<text x="{pad}" y="{y + grid_top + 16}" fill="#71717a" font-size="10">GitHub {g} · Forgejo {f}</text>')
    out.append("</svg>")
    return "\n".join(out)


def github_languages(user):
    """Bytes per language across your public, non-fork repos. Public data only, no token."""
    repos = json.load(urllib.request.urlopen(f"https://api.github.com/users/{user}/repos?per_page=100", timeout=30))
    totals = Counter()
    with ThreadPoolExecutor(8) as ex:
        for langs in ex.map(lambda r: json.load(urllib.request.urlopen(r["languages_url"], timeout=30)),
                            [r for r in repos if not r["fork"]]):
            totals.update(langs)
    return totals


def streaks(counts, today):
    """(current, longest) streaks in days, from a {iso_date: count} mapping."""
    active = {d for d, n in counts.items() if n > 0}
    day, current = today, 0
    if day.isoformat() not in active:
        day -= timedelta(days=1)  # today not yet active: streak still counts from yesterday
    while day.isoformat() in active:
        current += 1
        day -= timedelta(days=1)
    longest = run = 0
    for d, _, _ in calendar_days(today):
        run = run + 1 if d.isoformat() in active else 0
        longest = max(longest, run)
    return current, longest


LANG_COLORS = ["#a78bfa", "#c4b5fd", "#8b5cf6", "#d4d4d8", "#a1a1aa", "#71717a"]


def render_stats_card(gh, fg, langs, today):
    total = {k: gh.get(k, 0) + fg.get(k, 0) for k in set(gh) | set(fg)}
    cur, longest = streaks(total, today)
    active = sum(1 for n in total.values() if n > 0)
    top = langs.most_common(6)
    lang_sum = sum(b for _, b in top) or 1
    w, h = 860, 260
    ff = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
    mono = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="{ff}">',
        '<defs><linearGradient id="nm" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fafafa"/><stop offset="1" stop-color="#71717a"/></linearGradient>'
        '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>'
        '<clipPath id="c"><rect width="860" height="260" rx="16"/></clipPath></defs>',
        f'<rect width="{w}" height="{h}" rx="16" fill="#050507"/>',
        '<g clip-path="url(#c)"><circle cx="760" cy="40" r="110" fill="#a78bfa" opacity="0.22" filter="url(#soft)"/></g>',
        '<rect x="16.5" y="16.5" width="827" height="227" rx="12" fill="#09090b" fill-opacity="0.85" stroke="#27272a"/>',
        '<line x1="430.5" y1="44" x2="430.5" y2="216" stroke="#27272a"/>',
        f'<g font-family="{mono}" font-size="12" letter-spacing="1" fill="#a78bfa">'
        '<text x="48" y="52">~/Activity</text><text x="470" y="52">~/Languages</text></g>',
        f'<text x="48" y="108" fill="url(#nm)" font-size="42" font-weight="700">{sum(total.values()):,}</text>',
        f'<text x="48" y="128" fill="#71717a" font-size="12" font-family="{mono}">contributions, last year</text>',
    ]
    stats = [("GitHub / Forgejo", f"{sum(gh.values()):,} / {sum(fg.values()):,}"),
             ("Active days", f"{active}"),
             ("Current streak", f"{cur} d"),
             ("Longest streak", f"{longest} d")]
    for i, (label, value) in enumerate(stats):
        y = 160 + i * 24
        out.append(f'<text x="48" y="{y}" fill="#71717a" font-size="12" font-family="{mono}">{label}</text>')
        out.append(f'<text x="390" y="{y}" fill="#e4e4e7" font-size="13" text-anchor="end" font-weight="600" font-family="{mono}">{value}</text>')
    for i, (name, bytes_) in enumerate(top):
        y = 76 + i * 28
        pct = bytes_ / lang_sum
        out.append(f'<text x="470" y="{y + 11}" fill="#e4e4e7" font-size="12" font-family="{mono}">{name}</text>')
        out.append(f'<rect x="580" y="{y + 2}" width="180" height="8" rx="4" fill="#27272a"/>')
        out.append(f'<rect x="580" y="{y + 2}" width="{max(180 * pct, 8):.1f}" height="8" rx="4" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        out.append(f'<text x="812" y="{y + 11}" fill="#71717a" font-size="11" font-family="{mono}" text-anchor="end">{pct:.0%}</text>')
    out.append("</svg>")
    return "\n".join(out)


def selftest():
    html = ('<td data-date="2026-03-14" id="contribution-day-component-0-0" data-level="2"></td>'
            '<tool-tip for="contribution-day-component-0-0">5 contributions on March 14th.</tool-tip>'
            '<td data-date="2026-03-15" id="contribution-day-component-0-1" data-level="0"></td>'
            '<tool-tip for="contribution-day-component-0-1">No contributions on March 15th.</tool-tip>')
    assert parse_github_calendar(html) == {"2026-03-14": 5, "2026-03-15": 0}
    gql = {"data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": [
        {"contributionDays": [{"date": "2026-03-14", "contributionCount": 7}]}]}}}}}
    assert parse_graphql_calendar(gql) == {"2026-03-14": 7}
    ok = {"full_name": "Org/secret-repo", "name": "secret-repo", "mirror": False, "original_url": "", "empty": False}
    assert is_counted_repo(ok)
    assert not is_counted_repo({**ok, "mirror": True})
    assert not is_counted_repo({**ok, "original_url": "https://github.com/x/y"})
    assert not is_counted_repo({**ok, "empty": True})
    IGNORE.update({"secret-repo", "Org/other"})
    assert not is_counted_repo(ok)  # ignored by bare name
    assert not is_counted_repo({**ok, "full_name": "Org/other", "name": "other"})  # ignored by owner/name
    assert is_counted_repo({**ok, "full_name": "Org/fine", "name": "fine"})
    IGNORE.clear()
    days = calendar_days(date(2026, 11, 8))
    assert len(days) >= 365 and days[0][0].weekday() == 6 and days[-1][0] == date(2026, 11, 8)
    svg = render_calendar({"2026-11-08": 3}, {"2026-11-08": 2}, date(2026, 11, 8))
    assert svg.startswith("<svg") and svg.endswith("</svg>") and "GitHub 3, Forgejo 2" in svg
    t = date(2026, 11, 8)
    assert streaks({"2026-11-06": 1, "2026-11-07": 1, "2026-11-08": 1}, t) == (3, 3)
    assert streaks({"2026-11-06": 1, "2026-11-07": 1}, t) == (2, 2)  # today empty: counts from yesterday
    assert streaks({"2026-11-01": 1, "2026-11-03": 1, "2026-11-04": 1}, t) == (0, 2)
    card = render_stats_card({"2026-11-08": 3}, {}, Counter({"Python": 3, "Go": 1}), t)
    assert "Languages" in card and "75%" in card
    mixed = render_stats_card({"2026-11-08": 1}, {"2026-11-07": 1}, Counter(), t)  # one GitHub-only day, one Forgejo-only day
    assert ">2</text>" in mixed  # Active days counts both sources


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        print("selftest ok")
        sys.exit(0)
    if not TOKEN:
        sys.exit("FORGEJO_TOKEN is not set")
    today = datetime.now(timezone.utc).date()
    login = api("/user")["login"]
    repos = forgejo_repos()
    # one 365-day window per year, newest first; the 2D calendar and stats card use windows[0]
    ends = [today - timedelta(days=365 * i) for i in range(YEARS)]
    starts = [e - timedelta(days=364) for e in ends]
    fg_all = collect_forgejo(repos, login, starts[-1].isoformat())
    panels = []  # (end, gh, fg) per window
    for s, e in zip(starts, ends):
        gh = github_daily(GH_USER, GH_TOKEN, s.isoformat(), e.isoformat())
        fg = {k: v for k, v in fg_all.items() if s.isoformat() <= k <= e.isoformat()}
        panels.append((e, gh, fg))
    _, gh, fg = panels[0]
    langs = github_languages(GH_USER) + forgejo_languages(repos)
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    for name, svg in (("contributions-2d.svg", render_calendar(gh, fg, today)),
                      ("contributions-3d.svg", render_isometric_row(panels)),
                      ("stats-card.svg", render_stats_card(gh, fg, langs, today))):
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            f.write(svg)
    print(f"wrote 2d+3d to {outdir}: GitHub {sum(gh.values())}, Forgejo {sum(fg.values())}")
