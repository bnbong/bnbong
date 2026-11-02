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

import math
import os
import random
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets")

FONT_STACK = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Pretendard', "
    "'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif"
)
MONO_STACK = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
# Myeongjo-style headings (VastHorizon brand). Korean serif faces come before the
# Gothic fallback so Hangul stays serif wherever a Myeongjo font is installed.
SERIF_STACK = (
    "'Noto Serif KR', 'AppleMyungjo', 'Apple Myungjo', 'Nanum Myeongjo', 'Batang', "
    "'Apple SD Gothic Neo', Georgia, 'Times New Roman', serif"
)
# Latin-only headings ("JunHyeok Lee", section titles): a Latin serif first so the
# browser never picks the Latin glyphs of a Korean Gothic face.
LATIN_SERIF_STACK = "Georgia, 'Times New Roman', 'Noto Serif', 'Noto Serif KR', 'AppleMyungjo', serif"

# Design tokens: same code, two palettes, both drawn from the VastHorizon brand
#   navy #272B61 · blue violet #5960A1 · lavender #8C68AC · teal mist #63A9C9
#   apricot ribbon #F3DAD5 · paper #FFF9F3
# dark = night sky, light = paper. Accents a1..a4 are the only icon/chip colors:
#   a1 navy/blue violet, a2 lavender, a3 apricot (point), a4 teal.
# "<key>_text" variants are used when an accent colors text (contrast on paper).
THEMES = {
    "light": {
        "bg": "#FFF9F3",
        "bg2": "#FFFFFF",
        "tint": "#F2EAF5",
        "sky1": "#FFF9F3",
        "sky2": "#F8F0F4",
        "sky3": "#EFE6F4",
        "fog": "#63A9C9",
        "fog_alpha": "0.10",
        "haze": "#8C68AC",
        "haze_alpha": "0.12",
        "border": "#E6DCEB",
        "grid": "#8C68AC",
        "line": "#8C68AC",
        "line_alpha": "0.40",
        "text": "#272B61",
        "muted": "#5960A1",
        "kicker": "#8C68AC",
        "handle": "#5960A1",
        "a1": "#272B61",
        "a2": "#8C68AC",
        "a3": "#E0907A",
        "a3_text": "#B8664C",
        "a4": "#3D88AB",
        "on_accent": "#FFF9F3",
        "tile1": "#272B61",
        "tile2": "#8C68AC",
        "wave1": "#8C68AC",
        "wave2": "#63A9C9",
        "wave_alpha1": "0.14",
        "wave_alpha2": "0.24",
        "node_fill": "#FFF9F3",
        "panel": "#FFFFFF",
        "panel_alpha": "0.72",
        "panel_stroke": "#8C68AC",
        "panel_stroke_alpha": "0.28",
        "ribbon": "#F3DAD5",
        "ribbon_text": "#272B61",
        "ribbon_point": "#C97B62",
        "star": "#272B61",
        "star_point": "#E0907A",
        "star_dust": "#5960A1",
        "star_dust_alpha": "0.30",
        "betelgeuse": "#E07446",
        "rigel": "#3D88AB",
        "chip_alpha": "0.10",
        "chip_stroke_alpha": "0.40",
        "grid_alpha": "0.45",
    },
    "dark": {
        "bg": "#272B61",
        "bg2": "#2F3470",
        "tint": "#3A3F80",
        "sky1": "#272B61",
        "sky2": "#5960A1",
        "sky3": "#8C68AC",
        "fog": "#63A9C9",
        "fog_alpha": "0.38",
        "haze": "#B98AD6",
        "haze_alpha": "0.30",
        "border": "#5960A1",
        "grid": "#D9CFF0",
        "line": "#E4DCF5",
        "line_alpha": "0.42",
        "text": "#FFF9F3",
        "muted": "#D6CBEC",
        "kicker": "#F7C9B8",
        "handle": "#DCCFF2",
        "a1": "#AEB3EC",
        "a2": "#D2B3EC",
        "a3": "#F7C9B8",
        "a4": "#8FD0EA",
        "on_accent": "#FFF9F3",
        "tile1": "#5960A1",
        "tile2": "#8C68AC",
        "wave1": "#5960A1",
        "wave2": "#8C68AC",
        "wave_alpha1": "0.55",
        "wave_alpha2": "0.9",
        "node_fill": "#272B61",
        "panel": "#272B61",
        "panel_alpha": "0.55",
        "panel_stroke": "#E4DCF5",
        "panel_stroke_alpha": "0.22",
        "ribbon": "#F3DAD5",
        "ribbon_text": "#272B61",
        "ribbon_point": "#C97B62",
        "star": "#FFF9F3",
        "star_point": "#F7C9B8",
        "star_dust": "#FFF9F3",
        "star_dust_alpha": "0.55",
        "betelgeuse": "#FFAE85",
        "rigel": "#DCEBFF",
        "chip_alpha": "0.16",
        "chip_stroke_alpha": "0.45",
        "grid_alpha": "0.55",
    },
}


def acc_text(t: dict, key: str) -> str:
    """Accent color to use for text (darker variant on paper when defined)."""
    return t.get(f"{key}_text", t[key])


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
        f".serif{{font-family:{SERIF_STACK};}}"
        f".serif-latin{{font-family:{LATIN_SERIF_STACK};}}"
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


def accent_gradient(gid: str, t: dict, x2: str = "1", y2: str = "1", k1: str = "a1", k2: str = "a2") -> str:
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{t[k1]}"/><stop offset="1" stop-color="{t[k2]}"/>'
        f"</linearGradient>"
    )


def sky_defs(prefix: str, t: dict, x2: str = "1", y2: str = "0.35") -> str:
    """Night-sky (dark) / paper (light) gradient plus teal-mist and lavender-haze glows."""
    return (
        f'<linearGradient id="{prefix}sky" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{t["sky1"]}"/><stop offset="0.55" stop-color="{t["sky2"]}"/>'
        f'<stop offset="1" stop-color="{t["sky3"]}"/></linearGradient>'
        f'<radialGradient id="{prefix}fog" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["fog"]}" stop-opacity="{t["fog_alpha"]}"/>'
        f'<stop offset="1" stop-color="{t["fog"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="{prefix}haze" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["haze"]}" stop-opacity="{t["haze_alpha"]}"/>'
        f'<stop offset="1" stop-color="{t["haze"]}" stop-opacity="0"/></radialGradient>'
    )


def sparkle(cx: float, cy: float, r: float, color: str, extra: str = "", inner: str = "") -> str:
    """Four-pointed star (the brand's filled apricot star)."""
    k = r * 0.22
    d = (
        f"M{cx:.1f} {cy - r:.1f}Q{cx + k:.1f} {cy - k:.1f} {cx + r:.1f} {cy:.1f}"
        f"Q{cx + k:.1f} {cy + k:.1f} {cx:.1f} {cy + r:.1f}"
        f"Q{cx - k:.1f} {cy + k:.1f} {cx - r:.1f} {cy:.1f}"
        f"Q{cx - k:.1f} {cy - k:.1f} {cx:.1f} {cy - r:.1f}Z"
    )
    return f'<path d="{d}" fill="{color}"{extra}>{inner}</path>'


def dotted_ring(cx: float, cy: float, r: float, t: dict, opacity: float = 0.7) -> str:
    """Empty dashed circle: a celestial object not met yet."""
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{t["line"]}" '
        f'stroke-width="1" stroke-dasharray="2 2.4" opacity="{opacity}"/>'
    )


def star_dust(rng: random.Random, n: int, x0: float, y0: float, x1: float, y1: float, t: dict) -> str:
    out = []
    base = float(t["star_dust_alpha"])
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.choice((0.7, 0.9, 1.1, 1.4))
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" opacity="{base * rng.uniform(0.45, 1):.2f}"/>')
    return f'<g fill="{t["star_dust"]}">{"".join(out)}</g>'


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

# Orion, J2000 (RA hours, RA minutes, Dec degrees), size class 1 = brightest.
ORION = {
    "Betelgeuse": (5, 55.2, 7.41, 1),
    "Rigel": (5, 14.5, -8.20, 1),
    "Bellatrix": (5, 25.1, 6.35, 2),
    "Alnilam": (5, 36.2, -1.20, 2),
    "Alnitak": (5, 40.8, -1.94, 2),
    "Mintaka": (5, 32.0, -0.30, 3),
    "Saiph": (5, 47.8, -9.67, 3),
    "Meissa": (5, 35.1, 9.93, 3),
}
ORION_NEBULA = (5, 35.3, -5.39)  # M42, below the belt
ORION_EDGES = [
    ("Meissa", "Betelgeuse"), ("Meissa", "Bellatrix"),
    ("Betelgeuse", "Alnitak"), ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"), ("Alnilam", "Alnitak"),
    ("Alnitak", "Saiph"), ("Mintaka", "Rigel"), ("Rigel", "Saiph"),
]
ORION_APRICOT = {"Bellatrix", "Mintaka", "Alnilam", "Alnitak"}
ORION_TWINKLE = {"Betelgeuse": ("3.8s", "0s"), "Rigel": ("4.4s", "1.3s"), "Alnilam": ("3.2s", "2.2s")}


def orion_projector(box: tuple[float, float, float, float]):
    """Return f(ra_h, ra_m, dec) -> (x, y) fitting Orion into box=(x0, y0, w, h).

    Sky as seen from the ground: RA grows to the left, Dec grows upward. RA is
    converted to degrees (1 min = 15') and scaled by cos(mean Dec) so both axes
    share one angular scale; then one uniform px/deg factor fits the box.
    """
    pts = list(ORION.values())
    dec0 = math.radians(sum(p[2] for p in pts) / len(pts))

    def ang(ra_h: float, ra_m: float, dec: float) -> tuple[float, float]:
        ra_deg = (ra_h * 60 + ra_m) * 0.25
        return -ra_deg * math.cos(dec0), -dec

    raw = [ang(*p[:3]) for p in pts]
    minx, maxx = min(p[0] for p in raw), max(p[0] for p in raw)
    miny, maxy = min(p[1] for p in raw), max(p[1] for p in raw)
    x0, y0, bw, bh = box
    scale = min(bw / (maxx - minx), bh / (maxy - miny))
    ox = x0 + (bw - (maxx - minx) * scale) / 2
    oy = y0 + (bh - (maxy - miny) * scale) / 2

    def project(ra_h: float, ra_m: float, dec: float) -> tuple[float, float]:
        ax, ay = ang(ra_h, ra_m, dec)
        return ox + (ax - minx) * scale, oy + (ay - miny) * scale

    return project


def render_orion(t: dict, box: tuple[float, float, float, float]) -> str:
    project = orion_projector(box)
    pos = {name: project(*v[:3]) for name, v in ORION.items()}
    xs = [p[0] for p in pos.values()]
    cx, cy = (min(xs) + max(xs)) / 2, box[1] + box[3] / 2

    parts = [
        # faint orbit arcs around the figure, as on the VastHorizon cover
        f'<g fill="none" stroke="{t["line"]}" stroke-width="0.8" opacity="0.32">'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="148"/>'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="104" stroke-dasharray="2 4"/></g>'
    ]
    lines = "".join(
        f'<line x1="{pos[a][0]:.1f}" y1="{pos[a][1]:.1f}" x2="{pos[b][0]:.1f}" y2="{pos[b][1]:.1f}"/>'
        for a, b in ORION_EDGES
    )
    parts.append(f'<g stroke="{t["line"]}" stroke-width="1" opacity="{t["line_alpha"]}">{lines}</g>')

    nx, ny = project(*ORION_NEBULA)
    parts.append(dotted_ring(nx, ny, 4.5, t, 0.85))
    # objects not met yet
    for dx, dy, r in ((118, -62, 5), (-112, 30, 4.5), (96, 78, 4)):
        parts.append(dotted_ring(cx + dx, cy + dy, r, t))

    for name, (_, _, _, cls) in ORION.items():
        x, y = pos[name]
        color = t.get(name.lower(), t["star_point"] if name in ORION_APRICOT else t["star"])
        anim = ""
        if name in ORION_TWINKLE:
            dur, begin = ORION_TWINKLE[name]
            anim = (
                f'<animate attributeName="opacity" values="1;0.35;1" dur="{dur}" begin="{begin}" '
                f'repeatCount="indefinite"/>'
            )
        if cls == 1:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{color}" opacity="0.16"/>')
            parts.append(sparkle(x, y, 9, color, inner=anim))
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{color}"/>')
        else:
            r = 3.2 if cls == 2 else 2.4
            if anim:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" opacity="0.16"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}">{anim}</circle>')

    bx, by = pos["Bellatrix"]
    parts.append(
        f'<text x="{bx + 26:.0f}" y="{by - 34:.0f}" class="serif-latin" font-size="13" font-style="italic" '
        f'fill="{t["muted"]}" letter-spacing="4" opacity="0.85">orion</text>'
    )
    return "".join(parts)


def render_hero(t: dict) -> str:
    w, h = 1200, 320
    ribbon_h = 36
    defs = (
        clip_round("hc", w, h)
        + sky_defs("h", t)
        + accent_gradient("hacc", t, "1", "0", "a3", "a2")
    )
    rng = random.Random(20260)
    name = "JunHyeok Lee"
    name_size = 66
    underline_w = 132  # fixed: real glyph widths are unknown
    tagline = "삶을 윤택하게 만드는 개발자"

    body = f"""{card_bg(w, h, t)}
<g clip-path="url(#hc)">
  <rect width="{w}" height="{h}" fill="url(#hsky)"/>
  <circle cx="230" cy="330" r="300" fill="url(#hfog)"/>
  <circle cx="1080" cy="80" r="280" fill="url(#hhaze)"/>
  {star_dust(rng, 54, 12, 10, w - 12, h - ribbon_h - 6, t)}
  {render_orion(t, (800, 24, 380, 248))}
  <rect x="0" y="{h - ribbon_h}" width="{w}" height="{ribbon_h}" fill="{t["ribbon"]}"/>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>
<g transform="translate(72 0)">
  <text x="0" y="66" class="mono" font-size="14" fill="{t["kicker"]}" letter-spacing="2.5">HELLO, WORLD — I'M</text>
  <text x="-3" y="140" class="serif-latin" font-size="{name_size}" font-weight="400" fill="{t["text"]}" letter-spacing="-0.5">{esc(name)}</text>
  <rect x="0" y="160" width="{underline_w:.0f}" height="3" rx="1.5" fill="url(#hacc)">
    <animate attributeName="width" from="0" to="{underline_w:.0f}" dur="1.4s" begin="0.2s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/>
  </rect>
  <text x="0" y="200" class="mono" font-size="19" font-weight="600" fill="{t["handle"]}">@bnbong</text>
  <text x="0" y="240" font-size="22" font-weight="600" fill="{t["text"]}">Cloud · DevOps · Backend Developer</text>
</g>
{sparkle(w - 40 - text_width(tagline, 16) - 0.5 * len(tagline) - 22, h - 18, 6, t["ribbon_point"])}
<text x="{w - 40}" y="{h - 12}" text-anchor="end" class="serif" font-size="16" fill="{t["ribbon_text"]}" letter-spacing="0.5">{esc(tagline)}</text>"""
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
JOURNEY_ACCENTS = ["a2", "a4", "a1", "a2", "a3", "a4"]  # a3 (apricot) = current


def render_journey(t: dict) -> str:
    w, h = 1200, 264
    n = len(JOURNEY)
    margin = 110
    step = (w - 2 * margin) / (n - 1)  # 196px per column
    line_y = 104
    defs = clip_round("jc", w, h) + sky_defs("j", t) + accent_gradient("jline", t, "1", "0", "a2", "a3")

    rng = random.Random(7)
    parts = [
        card_bg(w, h, t),
        f'<g clip-path="url(#jc)"><rect width="{w}" height="{h}" fill="url(#jsky)"/>'
        f'<circle cx="120" cy="270" r="260" fill="url(#jfog)"/>'
        f'<circle cx="1100" cy="20" r="240" fill="url(#jhaze)"/>'
        f'{star_dust(rng, 26, 12, 8, w - 12, h - 8, t)}</g>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>',
        f'<text x="32" y="42" class="mono" font-size="13" fill="{t["muted"]}" letter-spacing="2">JOURNEY</text>'
        f'<text x="{w - 32}" y="42" class="mono" font-size="13" fill="{t["muted"]}" text-anchor="end" letter-spacing="1">2020 → NOW</text>',
        # base line + gradient progress line
        f'<line x1="{margin}" y1="{line_y}" x2="{w - margin}" y2="{line_y}" stroke="{t["line"]}" stroke-opacity="{t["line_alpha"]}" stroke-width="1.5"/>'
        f'<line x1="{margin}" y1="{line_y}" x2="{w - margin}" y2="{line_y}" stroke="url(#jline)" stroke-width="3" '
        f'stroke-linecap="round" stroke-dasharray="2 10" opacity="0.95">'
        f'<animate attributeName="stroke-dashoffset" from="24" to="0" dur="2.4s" repeatCount="indefinite"/></line>',
    ]
    for i, (ic, period, title, subs) in enumerate(JOURNEY):
        cx = margin + i * step
        key = JOURNEY_ACCENTS[i]
        acc = t[key]
        # sanity: keep text inside its column
        for s, size, bold in [(period, 13, True), (title, 16, True)] + [(x, 13, False) for x in subs]:
            assert text_width(s, size, bold) < step - 8, f"journey text too wide: {s}"
        pulse = ""
        if i == CURRENT_INDEX:
            pulse = (
                f'<circle cx="{cx:.0f}" cy="{line_y}" r="30" fill="none" stroke="{t["a3"]}" stroke-width="2">'
                f'<animate attributeName="r" values="30;40" dur="2.6s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.7;0" dur="2.6s" repeatCount="indefinite"/></circle>'
            )
        parts.append(
            f"<g>{pulse}"
            f'<circle cx="{cx:.0f}" cy="{line_y}" r="30" fill="{t["node_fill"]}" stroke="{acc}" stroke-width="2"/>'
            f'<circle cx="{cx:.0f}" cy="{line_y}" r="23" fill="{acc}" opacity="0.16"/>'
            f'{icon(ic, cx, line_y, 26, acc, 2.0)}'
            f'<text x="{cx:.0f}" y="166" text-anchor="middle" class="mono" font-size="13" font-weight="700" fill="{acc_text(t, key)}">{esc(period)}</text>'
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
    ("Infra & Observability", "cloud", "a4", 380, 24, 796, 150,
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
    defs = clip_round("sc", w, h) + sky_defs("s", t)
    rng = random.Random(11)
    parts = [
        card_bg(w, h, t),
        f'<g clip-path="url(#sc)"><rect width="{w}" height="{h}" fill="url(#ssky)"/>'
        f'<circle cx="140" cy="380" r="300" fill="url(#sfog)"/>'
        f'<circle cx="1100" cy="40" r="280" fill="url(#shaze)"/>'
        f'{star_dust(rng, 30, 12, 8, w - 12, h - 8, t)}</g>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>',
    ]
    pad = 20
    for title, ic, akey, px, py, pw, ph, items in STACK_PANELS:
        acc = t[akey]
        parts.append(
            f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="{t["panel"]}" fill-opacity="{t["panel_alpha"]}" '
            f'stroke="{t["panel_stroke"]}" stroke-opacity="{t["panel_stroke_alpha"]}"/>'
            f'<rect x="{px + pad}" y="{py + pad}" width="30" height="30" rx="8" fill="{acc}" opacity="0.18"/>'
            f'{icon(ic, px + pad + 15, py + pad + 15, 18, acc, 2.0)}'
            f'<text x="{px + pad + 42}" y="{py + pad + 21}" class="serif-latin" font-size="17" font-weight="700" fill="{t["text"]}">{esc(title)}</text>'
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
    defs = (
        clip_round("shc", w, h)
        + sky_defs("sh", t, "1", "0")
        + accent_gradient("sic", t, "1", "1", "tile1", "tile2")
        + f'<linearGradient id="sline" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["a3"]}" stop-opacity="0.95"/>'
        f'<stop offset="0.5" stop-color="{t["a2"]}" stop-opacity="0.45"/>'
        f'<stop offset="1" stop-color="{t["a2"]}" stop-opacity="0"/></linearGradient>'
    )
    # Georgia bold runs wider than the sans estimate; err on the generous side.
    line_x = 80 + text_width(title, 25, bold=True) * 1.05 + 18
    body = f"""{card_bg(w, h, t)}
<g clip-path="url(#shc)"><rect width="{w}" height="{h}" fill="url(#shsky)"/></g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>
<rect x="20" y="12" width="40" height="40" rx="11" fill="url(#sic)"/>
{icon(ic, 40, 32, 22, t["on_accent"], 2.2)}
<text x="80" y="41" class="serif-latin" font-size="25" font-weight="700" fill="{t["text"]}">{esc(title)}</text>
{sparkle(line_x, 32, 6.5, t["a3"])}
<path d="M{line_x + 14:.0f} 31.2 L1172 31.7 L1172 32.3 L{line_x + 14:.0f} 32.8 Z" fill="url(#sline)"/>"""
    return svg_doc(w, h, f"Section: {title}", body, defs)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------


def render_footer(t: dict) -> str:
    w, h = 1200, 120
    defs = clip_round("fc", w, h) + sky_defs("f", t, "1", "0") + accent_gradient("fw", t, "1", "0", "wave1", "wave2")
    wave1 = "M0 70 C150 50 300 92 450 74 S750 48 900 70 S1100 88 1200 66 V120 H0 Z"
    wave2 = "M0 84 C180 68 330 104 520 88 S820 66 980 86 S1130 96 1200 82 V120 H0 Z"
    ribbon = "M0 102 C200 96 380 108 600 101 S980 95 1200 103 V120 H0 Z"
    body = f"""{card_bg(w, h, t)}
<g clip-path="url(#fc)">
  <path d="{wave1}" fill="url(#fw)" opacity="{t["wave_alpha1"]}">
    <animateTransform attributeName="transform" type="translate" values="0 0;-18 2;0 0" dur="9s" repeatCount="indefinite"/>
  </path>
  <path d="{wave2}" fill="url(#fw)" opacity="{t["wave_alpha2"]}"/>
  <circle cx="160" cy="120" r="180" fill="url(#ffog)"/>
  <path d="{ribbon}" fill="{t["ribbon"]}"/>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>
<text x="588" y="46" text-anchor="end" class="serif-latin" font-size="16" fill="{t["muted"]}" letter-spacing="0.5">Thanks for visiting</text>
{sparkle(600, 41, 6, acc_text(t, "a3"))}
<text x="612" y="46" class="serif-latin" font-size="16" font-weight="700" fill="{t["text"]}" letter-spacing="0.5">bnbong.com</text>"""
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
