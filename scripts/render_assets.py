#!/usr/bin/env python3
"""Render light/dark SVG assets for the bnbong GitHub profile README.

Usage:
    python3 scripts/render_assets.py

Writes (overwrites) every asset into ./assets relative to the repository root:
    hero_{light,dark}.svg, journey_{light,dark}.svg, stack_{light,dark}.svg,
    section_{about,projects,stack,blog,stats}_{light,dark}.svg,
    footer_{light,dark}.svg

Pure Python (stdlib only). The SVGs are self-contained: no external fonts,
images or scripts, so they render inside GitHub's <img> sandbox. Use them in
README.md through <picture> with prefers-color-scheme sources.
"""

from __future__ import annotations

import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets")

FONT_STACK = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Pretendard', "
    "'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif"
)
MONO_STACK = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

# Design tokens: same code, two palettes.
THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "bg2": "#F8FAFC",
        "tint": "#EEF2FF",
        "border": "#E2E8F0",
        "grid": "#CBD5E1",
        "text": "#0F172A",
        "muted": "#64748B",
        "a1": "#2563EB",
        "a2": "#7C3AED",
        "a3": "#F59E0B",
        "on_accent": "#FFFFFF",
        "chip_alpha": "0.08",
        "chip_stroke_alpha": "0.30",
        "grid_alpha": "0.45",
    },
    "dark": {
        "bg": "#0D1117",
        "bg2": "#161B22",
        "tint": "#151B2E",
        "border": "#30363D",
        "grid": "#30363D",
        "text": "#E6EDF3",
        "muted": "#8B949E",
        "a1": "#60A5FA",
        "a2": "#A78BFA",
        "a3": "#FBBF24",
        "on_accent": "#0D1117",
        "chip_alpha": "0.12",
        "chip_stroke_alpha": "0.38",
        "grid_alpha": "0.55",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def text_width(text: str, size: float, bold: bool = False) -> float:
    """Rough, deliberately generous width estimate (no font metrics available)."""
    width = 0.0
    for ch in text:
        if ord(ch) >= 0x1100:  # Hangul / CJK: ~1em
            width += 1.0
        elif ch in "il.,:;|!'·":
            width += 0.32
        elif ch == " ":
            width += 0.3
        elif ch.isupper() or ch in "mwMW@&":
            width += 0.70
        else:
            width += 0.56
    return width * size * (1.06 if bold else 1.0)


def svg_doc(w: int, h: int, title: str, body: str, defs: str = "", css: str = "") -> str:
    style = (
        f"text{{font-family:{FONT_STACK};}}"
        f".mono{{font-family:{MONO_STACK};}}"
        f"{css}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">\n'
        f"<title>{esc(title)}</title>\n"
        f"<style>{style}</style>\n"
        f"<defs>{defs}</defs>\n"
        f"{body}\n</svg>\n"
    )


def card_bg(w: int, h: int, t: dict, fill: str | None = None) -> str:
    return (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" '
        f'fill="{fill or t["bg"]}" stroke="{t["border"]}"/>'
    )


def clip_round(cid: str, w: int, h: int) -> str:
    return f'<clipPath id="{cid}"><rect width="{w}" height="{h}" rx="16"/></clipPath>'


# 24x24 stroke icons (drawn with plain paths, no external resources)
ICONS = {
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "shield": '<path d="M12 2.5l8 3v6c0 5-3.4 8.6-8 10.5-4.6-1.9-8-5.5-8-10.5v-6z"/>'
    '<path d="M12 8l1.2 2.5 2.7.4-2 1.9.5 2.7-2.4-1.3-2.4 1.3.5-2.7-2-1.9 2.7-.4z"/>',
    "server": '<rect x="3.5" y="3.5" width="17" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="17" height="7" rx="1.5"/>'
    '<path d="M7.5 7h.01M7.5 17h.01M11 7h5M11 17h5"/>',
    "cloud": '<path d="M7 19h10.5a4.5 4.5 0 0 0 .6-8.96A6.5 6.5 0 0 0 5.6 9.3 4.9 4.9 0 0 0 7 19z"/>',
    "data": '<ellipse cx="12" cy="5.5" rx="8" ry="3"/><path d="M4 5.5v13c0 1.7 3.6 3 8 3s8-1.3 8-3v-13"/>'
    '<path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "grad": '<path d="M2 9.5L12 4.5l10 5-10 5z"/><path d="M6 11.5v5c0 1.4 2.7 3 6 3s6-1.6 6-3v-5"/><path d="M22 9.5v5.5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    "rocket": '<path d="M12 2.5c3.5 2 5.5 5.8 5.5 10l-2.5 3.5H9l-2.5-3.5c0-4.2 2-8 5.5-10z"/>'
    '<circle cx="12" cy="10" r="2"/><path d="M9 16l-2.5 4M15 16l2.5 4M12 18v3.5"/>',
    "layers": '<path d="M12 3l9 4.5-9 4.5-9-4.5z"/><path d="M3 12l9 4.5 9-4.5"/><path d="M3 16.5l9 4.5 9-4.5"/>',
    "pen": '<path d="M4 20h4L19.5 8.5a2.1 2.1 0 0 0-4-4L4 16z"/><path d="M13.5 6.5l4 4"/><path d="M12 20h8"/>',
    "chart": '<path d="M3.5 20.5h17"/><rect x="5" y="11" width="3" height="7" rx="0.8"/>'
    '<rect x="10.5" y="6" width="3" height="12" rx="0.8"/><rect x="16" y="13.5" width="3" height="4.5" rx="0.8"/>',
}


def icon(name: str, cx: float, cy: float, size: float, color: str, sw: float = 2.0) -> str:
    s = size / 24.0
    return (
        f'<g transform="translate({cx - size / 2:.1f} {cy - size / 2:.1f}) scale({s:.3f})" '
        f'fill="none" stroke="{color}" stroke-width="{sw / s * s:.2f}" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>'
    )


def accent_gradient(gid: str, t: dict, x2: str = "1", y2: str = "1") -> str:
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{t["a1"]}"/><stop offset="1" stop-color="{t["a2"]}"/>'
        f"</linearGradient>"
    )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------


def render_hero(t: dict) -> str:
    w, h = 1200, 320
    defs = (
        clip_round("hc", w, h)
        + f'<linearGradient id="hbg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg2"]}"/><stop offset="1" stop-color="{t["tint"]}"/></linearGradient>'
        + accent_gradient("hacc", t, "1", "0")
        + f'<radialGradient id="glow1" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["a1"]}" stop-opacity="0.22"/>'
        f'<stop offset="1" stop-color="{t["a1"]}" stop-opacity="0"/></radialGradient>'
        + f'<radialGradient id="glow2" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["a2"]}" stop-opacity="0.20"/>'
        f'<stop offset="1" stop-color="{t["a2"]}" stop-opacity="0"/></radialGradient>'
        + f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M40 0H0V40" fill="none" stroke="{t["grid"]}" stroke-width="0.6" opacity="{t["grid_alpha"]}"/></pattern>'
        + f'<linearGradient id="gfade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0.15"/><stop offset="0.55" stop-color="#fff" stop-opacity="0.6"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
        + f'<mask id="gmask"><rect width="{w}" height="{h}" fill="url(#gfade)"/></mask>'
    )

    # Constellation on the right side
    stars = [
        (790, 92), (858, 62), (930, 110), (1010, 74), (1086, 128),
        (1132, 66), (884, 190), (968, 226), (1052, 206), (1120, 252), (820, 262),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (3, 5), (2, 6), (6, 7), (7, 8), (8, 4), (8, 9), (6, 10)]
    lines = "".join(
        f'<line x1="{stars[a][0]}" y1="{stars[a][1]}" x2="{stars[b][0]}" y2="{stars[b][1]}"/>'
        for a, b in edges
    )
    dots = []
    twinkle = {2: ("3.6s", "0s"), 5: ("4.2s", "1.2s"), 8: ("3.2s", "2.1s")}
    for i, (x, y) in enumerate(stars):
        color = t["a2"] if i % 3 == 1 else (t["a3"] if i in (5, 9) else t["a1"])
        r = 4.2 if i in twinkle else 2.8
        anim = ""
        if i in twinkle:
            dur, begin = twinkle[i]
            anim = (
                f'<animate attributeName="opacity" values="1;0.25;1" dur="{dur}" begin="{begin}" '
                f'repeatCount="indefinite"/>'
            )
            dots.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{color}" opacity="0.15"/>')
        dots.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}">{anim}</circle>')

    name = "JunHyeok Lee"
    name_size = 64
    name_w = text_width(name, name_size, bold=True)
    underline_w = 140  # fixed: real glyph widths are unknown
    del name_w

    body = f"""{card_bg(w, h, t)}
<g clip-path="url(#hc)">
  <rect width="{w}" height="{h}" fill="url(#hbg)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)" mask="url(#gmask)"/>
  <circle cx="1040" cy="60" r="220" fill="url(#glow2)"/>
  <circle cx="160" cy="300" r="240" fill="url(#glow1)"/>
  <g stroke="{t["muted"]}" stroke-width="1" opacity="0.45">{lines}</g>
  <g>{"".join(dots)}</g>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>
<g transform="translate(72 0)">
  <text x="0" y="76" class="mono" font-size="15" fill="{t["a1"]}" letter-spacing="2">HELLO, WORLD — I'M</text>
  <text x="-3" y="150" font-size="{name_size}" font-weight="800" fill="{t["text"]}" letter-spacing="-1">{esc(name)}</text>
  <rect x="0" y="168" width="{underline_w:.0f}" height="5" rx="2.5" fill="url(#hacc)">
    <animate attributeName="width" from="0" to="{underline_w:.0f}" dur="1.4s" begin="0.2s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/>
  </rect>
  <text x="0" y="208" class="mono" font-size="20" font-weight="600" fill="{t["a2"]}">@bnbong</text>
  <text x="0" y="246" font-size="22" font-weight="600" fill="{t["text"]}">Cloud · DevOps · Backend Developer</text>
  <text x="0" y="280" font-size="18" fill="{t["muted"]}">삶을 윤택하게 만드는 개발자</text>
</g>"""
    return svg_doc(w, h, "JunHyeok Lee (bnbong) - Cloud, DevOps, Backend Developer", body, defs)


# ---------------------------------------------------------------------------
# Journey timeline
# ---------------------------------------------------------------------------

JOURNEY = [
    ("music", "2020–2021", "GiftMusic", ["백엔드 개발"]),
    ("shield", "2021.04–2023.01", "공군 825기", ["정보체계관리병", "병장 만기전역"]),
    ("server", "2023–2024", "K-Buddy", ["백엔드 & DevOps"]),
    ("cloud", "2024.07–08", "Kakao Enterprise", ["IaaS 기술 기획 인턴"]),
    ("data", "2026.07–", "SSAFY 16기", ["데이터 트랙 (대전)"]),
    ("grad", "2026.08", "한양대학교 ERICA", ["컴퓨터학부 졸업"]),
]
CURRENT_INDEX = 4  # node that gets the subtle "now" pulse


def render_journey(t: dict) -> str:
    w, h = 1200, 264
    n = len(JOURNEY)
    margin = 110
    step = (w - 2 * margin) / (n - 1)  # 196px per column
    line_y = 104
    defs = clip_round("jc", w, h) + accent_gradient("jline", t, "1", "0") + accent_gradient("jnode", t)
    accents = [t["a1"], t["a2"], t["a1"], t["a2"], t["a3"], t["a1"]]

    parts = [card_bg(w, h, t)]
    parts.append(
        f'<text x="32" y="42" class="mono" font-size="13" fill="{t["muted"]}" letter-spacing="2">JOURNEY</text>'
        f'<text x="{w - 32}" y="42" class="mono" font-size="13" fill="{t["muted"]}" text-anchor="end" letter-spacing="1">2020 → NOW</text>'
    )
    # base line + gradient progress line
    parts.append(
        f'<line x1="{margin}" y1="{line_y}" x2="{w - margin}" y2="{line_y}" stroke="{t["border"]}" stroke-width="4" stroke-linecap="round"/>'
        f'<line x1="{margin}" y1="{line_y}" x2="{w - margin}" y2="{line_y}" stroke="url(#jline)" stroke-width="3" '
        f'stroke-linecap="round" stroke-dasharray="2 10" opacity="0.9">'
        f'<animate attributeName="stroke-dashoffset" from="24" to="0" dur="2.4s" repeatCount="indefinite"/></line>'
    )
    for i, (ic, period, title, subs) in enumerate(JOURNEY):
        cx = margin + i * step
        acc = accents[i]
        # sanity: keep text inside its column
        for s, size, bold in [(period, 13, True), (title, 16, True)] + [(x, 13, False) for x in subs]:
            assert text_width(s, size, bold) < step - 8, f"journey text too wide: {s}"
        pulse = ""
        if i == CURRENT_INDEX:
            pulse = (
                f'<circle cx="{cx:.0f}" cy="{line_y}" r="30" fill="none" stroke="{acc}" stroke-width="2">'
                f'<animate attributeName="r" values="30;40" dur="2.6s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.6;0" dur="2.6s" repeatCount="indefinite"/></circle>'
            )
        parts.append(
            f"<g>{pulse}"
            f'<circle cx="{cx:.0f}" cy="{line_y}" r="30" fill="{t["bg"]}" stroke="{acc}" stroke-width="2.5"/>'
            f'<circle cx="{cx:.0f}" cy="{line_y}" r="23" fill="{acc}" opacity="0.14"/>'
            f'{icon(ic, cx, line_y, 26, acc, 2.0)}'
            f'<text x="{cx:.0f}" y="166" text-anchor="middle" class="mono" font-size="13" font-weight="700" fill="{acc}">{esc(period)}</text>'
            f'<text x="{cx:.0f}" y="193" text-anchor="middle" font-size="16" font-weight="700" fill="{t["text"]}">{esc(title)}</text>'
            + "".join(
                f'<text x="{cx:.0f}" y="{216 + k * 20}" text-anchor="middle" font-size="13" fill="{t["muted"]}">{esc(s)}</text>'
                for k, s in enumerate(subs)
            )
            + "</g>"
        )
    return svg_doc(w, h, "Journey timeline of JunHyeok Lee from 2020 to now", "\n".join(parts), defs)


# ---------------------------------------------------------------------------
# Tech stack bento
# ---------------------------------------------------------------------------

STACK_PANELS = [
    # (title, icon, accent key, x, y, w, h, items)
    ("Languages", "pen", "a1", 24, 24, 340, 150, ["Python", "Java", "C", "JavaScript"]),
    ("Backend", "server", "a2", 24, 190, 340, 150, ["FastAPI", "Spring", "Django", "Flask", "PyTorch"]),
    ("Infra & Observability", "cloud", "a1", 380, 24, 796, 150,
     ["Docker", "Kubernetes", "GitHub Actions", "Jenkins", "AWS", "GCP", "Azure", "OCI",
      "Nginx", "Linux", "Prometheus", "Grafana"]),
    ("Data", "data", "a3", 380, 190, 340, 150,
     ["PostgreSQL", "Redis", "MongoDB", "MySQL", "SQLite", "Elasticsearch"]),
    ("Etc", "layers", "a2", 736, 190, 440, 150,
     ["Git", "GitHub", "Godot", "REST", "WebSocket", "SQLAlchemy", "Terraform", "EFK/ELK"]),
]


def chip_layout(items, inner_w, chip_h=30, gap=8, font=13):
    """Simple flow layout; returns [(x, y, w, label)], total height."""
    out, x, y = [], 0.0, 0.0
    for label in items:
        cw = text_width(label, font) + 28
        if x > 0 and x + cw > inner_w:
            x, y = 0.0, y + chip_h + gap
        out.append((x, y, cw, label))
        x += cw + gap
    return out, y + chip_h


def render_stack(t: dict) -> str:
    w, h = 1200, 364
    defs = clip_round("sc", w, h)
    parts = [card_bg(w, h, t, t["bg"])]
    pad = 20
    for title, ic, akey, px, py, pw, ph, items in STACK_PANELS:
        acc = t[akey]
        parts.append(
            f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="{t["bg2"]}" stroke="{t["border"]}"/>'
            f'<rect x="{px + pad}" y="{py + pad}" width="30" height="30" rx="8" fill="{acc}" opacity="0.14"/>'
            f'{icon(ic, px + pad + 15, py + pad + 15, 18, acc, 2.0)}'
            f'<text x="{px + pad + 42}" y="{py + pad + 21}" font-size="16" font-weight="700" fill="{t["text"]}">{esc(title)}</text>'
            f'<text x="{px + pw - pad}" y="{py + pad + 21}" text-anchor="end" class="mono" font-size="12" fill="{t["muted"]}">{len(items):02d}</text>'
        )
        chips, used_h = chip_layout(items, pw - 2 * pad)
        top = py + pad + 46
        assert top + used_h <= py + ph - 12, f"panel overflow: {title} ({top + used_h} > {py + ph - 12})"
        for cx, cy, cw, label in chips:
            x0, y0 = px + pad + cx, top + cy
            parts.append(
                f'<g><rect x="{x0:.1f}" y="{y0:.1f}" width="{cw:.1f}" height="30" rx="15" '
                f'fill="{acc}" fill-opacity="{t["chip_alpha"]}" stroke="{acc}" stroke-opacity="{t["chip_stroke_alpha"]}"/>'
                f'<circle cx="{x0 + 13:.1f}" cy="{y0 + 15:.1f}" r="3" fill="{acc}"/>'
                f'<text x="{x0 + 22:.1f}" y="{y0 + 20:.1f}" font-size="13" font-weight="500" fill="{t["text"]}">{esc(label)}</text></g>'
            )
    return svg_doc(w, h, "Tech stack of JunHyeok Lee", "\n".join(parts), defs)


# ---------------------------------------------------------------------------
# Section headers
# ---------------------------------------------------------------------------

SECTIONS = {
    "about": ("About Me", "user"),
    "projects": ("Featured Projects", "rocket"),
    "stack": ("Tech Stack", "layers"),
    "blog": ("Blog Posts", "pen"),
    "stats": ("Programming Stats", "chart"),
}


def render_section(key: str, t: dict) -> str:
    title, ic = SECTIONS[key]
    w, h = 1200, 64
    defs = accent_gradient("sic", t) + (
        f'<linearGradient id="sline" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["a1"]}" stop-opacity="0.9"/>'
        f'<stop offset="0.5" stop-color="{t["a2"]}" stop-opacity="0.45"/>'
        f'<stop offset="1" stop-color="{t["a2"]}" stop-opacity="0"/></linearGradient>'
    )
    line_x = 80 + 0.85 * text_width(title, 24, bold=True) + 28
    body = f"""{card_bg(w, h, t)}
<rect x="20" y="12" width="40" height="40" rx="11" fill="url(#sic)"/>
{icon(ic, 40, 32, 22, t["on_accent"], 2.2)}
<text x="80" y="41" font-size="24" font-weight="800" fill="{t["text"]}" letter-spacing="-0.3">{esc(title)}</text>
<circle cx="{line_x:.0f}" cy="32" r="3.5" fill="{t["a1"]}"/>
<path d="M{line_x + 12:.0f} 30.5 L1172 31.6 L1172 32.4 L{line_x + 12:.0f} 33.5 Z" fill="url(#sline)"/>"""
    return svg_doc(w, h, f"Section: {title}", body, defs)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------


def render_footer(t: dict) -> str:
    w, h = 1200, 120
    defs = clip_round("fc", w, h) + accent_gradient("fw", t, "1", "0")
    wave1 = "M0 78 C150 58 300 100 450 82 S750 56 900 78 S1100 96 1200 74 V120 H0 Z"
    wave2 = "M0 92 C180 76 330 112 520 96 S820 74 980 94 S1130 104 1200 90 V120 H0 Z"
    body = f"""{card_bg(w, h, t)}
<g clip-path="url(#fc)">
  <path d="{wave1}" fill="url(#fw)" opacity="0.22">
    <animateTransform attributeName="transform" type="translate" values="0 0;-18 2;0 0" dur="9s" repeatCount="indefinite"/>
  </path>
  <path d="{wave2}" fill="url(#fw)" opacity="0.45"/>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>
<text x="600" y="50" text-anchor="middle" font-size="15" fill="{t["muted"]}" letter-spacing="0.5">Thanks for visiting <tspan fill="{t["a1"]}">·</tspan> <tspan fill="{t["text"]}" font-weight="600">bnbong.com</tspan></text>"""
    return svg_doc(w, h, "Thanks for visiting - bnbong.com", body, defs)


# ---------------------------------------------------------------------------


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    outputs = {}
    for mode, t in THEMES.items():
        outputs[f"hero_{mode}.svg"] = render_hero(t)
        outputs[f"journey_{mode}.svg"] = render_journey(t)
        outputs[f"stack_{mode}.svg"] = render_stack(t)
        outputs[f"footer_{mode}.svg"] = render_footer(t)
        for key in SECTIONS:
            outputs[f"section_{key}_{mode}.svg"] = render_section(key, t)
    for name, content in sorted(outputs.items()):
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"wrote assets/{name} ({len(content.encode('utf-8')) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
