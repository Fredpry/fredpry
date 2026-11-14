"""Generate the animated SVGs used in README.md.

Run:  python scripts/build_assets.py
Writes assets/hero-{light,dark}.svg and assets/demo-{light,dark}.svg.

Colours follow the FP personal brand: orange #DD7333, graphite #1A1613,
warm white #F6F2ED, muted #6B6259.
"""
from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

ORANGE = "#DD7333"

THEMES = {
    "light": {
        "bg": "#F6F2ED",
        "card_line": "#E7DFD5",
        "ink": "#1A1613",
        "muted": "#6B6259",
        "dots": "#E2D8CC",
        "orange": ORANGE,
        "orange_soft": "#F3C8A8",
        # materials: (top, left/+y face, right/+x face, seam)
        "ground": ("#ECE3D8", "#D9CBBB", "#C9B8A5", "#DCD0C2"),
        "wall": ("#FFFDFA", "#F1EAE1", "#E1D5C7", "#D8CCBE"),
        "band": ("#EE9A62", ORANGE, "#B85A22", "#C4652B"),
        "roof": ("#4A413A", "#2E2722", "#1F1A16", "#1A1613"),
        "core": ("#6B6259", "#4A413A", "#36302A", "#2E2823"),
        "silo": ("#F1A877", "#DD7333", "#B85A22", "#C4652B"),
        "silo_cap": ("#FFFDFA", "#F1EAE1", "#E1D5C7", "#D8CCBE"),
        "leaf": ("#E58A4E", "#C9622A", "#A44C1C", "#A9521F"),
        "leaf2": ("#D9A066", "#BF8550", "#9C6A3C", "#A47243"),
        "trunk": ("#7A5A44", "#634633", "#4E3626", "#4E3626"),
        "belt": ("#5A504A", "#433B35", "#332C27", "#2A2420"),
        "doc": ("#FFFFFF", "#EFE8E0", "#DDD2C5", "#CFC2B3"),
        "smoke": "#CFC3B6",
        "window": "#2E2722",
        "window_lit": "#F7B27E",
    },
    "dark": {
        "bg": "#1A1613",
        "card_line": "#3A322C",
        "ink": "#F6F2ED",
        "muted": "#A89E94",
        "dots": "#2C2520",
        "orange": "#E8854A",
        "orange_soft": "#5A3A26",
        "ground": ("#3A322C", "#2A241F", "#221D19", "#2F2823"),
        "wall": ("#E9E1D7", "#CFC4B7", "#B3A797", "#A99C8C"),
        "band": ("#F09A60", "#DD7333", "#B85A22", "#C4652B"),
        "roof": ("#5A5048", "#3F3731", "#2E2823", "#26201C"),
        "core": ("#4A413A", "#36302A", "#28221E", "#1F1A16"),
        "silo": ("#F1A877", "#DD7333", "#B85A22", "#C4652B"),
        "silo_cap": ("#E9E1D7", "#CFC4B7", "#B3A797", "#A99C8C"),
        "leaf": ("#E58A4E", "#C9622A", "#A44C1C", "#A9521F"),
        "leaf2": ("#C99560", "#AB7848", "#8A5E35", "#8F623A"),
        "trunk": ("#7A5A44", "#634633", "#4E3626", "#4E3626"),
        "belt": ("#5F5650", "#48403A", "#38312C", "#2E2823"),
        "doc": ("#FFFFFF", "#E9E1D7", "#CFC4B7", "#B3A797"),
        "smoke": "#6B6259",
        "window": "#221D19",
        "window_lit": "#FFB57D",
    },
}

SERIF = "'Instrument Serif', Georgia, 'Times New Roman', serif"
SANS = "Sora, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def f(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# --------------------------------------------------------------------------
# Isometric voxel engine
# --------------------------------------------------------------------------
class Iso:
    def __init__(self, s: float, ox: float, oy: float):
        self.s = s
        self.c = s * math.cos(math.radians(30))
        self.ox = ox
        self.oy = oy

    def p(self, x: float, y: float, z: float) -> tuple[float, float]:
        return (self.ox + (x - y) * self.c, self.oy + (x + y) * self.s / 2 - z * self.s)

    def poly(self, pts) -> str:
        return "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts) + "Z"

    def faces(self, x, y, z, w=1.0, d=1.0, h=1.0):
        P = self.p
        top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]
        right = [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)]
        left = [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)]
        return top, left, right


class Voxels:
    """Unit cubes with hidden-face culling, drawn in painter's order."""

    def __init__(self):
        self.cells: dict[tuple[int, int, int], str] = {}

    def add(self, x, y, z, mat):
        self.cells[(x, y, z)] = mat

    def box(self, x0, y0, z0, w, d, h, mat):
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + d):
                for z in range(z0, z0 + h):
                    self.add(x, y, z, mat)

    def render(self, iso: Iso, theme: dict, drop: bool = True) -> list[str]:
        out = []
        for (x, y, z) in sorted(self.cells, key=lambda k: (k[0] + k[1] + k[2], k[2])):
            mat = self.cells[(x, y, z)]
            top_c, left_c, right_c, seam = theme[mat]
            top, left, right = iso.faces(x, y, z)
            parts = []
            if (x, y, z + 1) not in self.cells:
                parts.append((top, top_c))
            if (x, y + 1, z) not in self.cells:
                parts.append((left, left_c))
            if (x + 1, y, z) not in self.cells:
                parts.append((right, right_c))
            if not parts:
                continue
            cls = f' class="b z{min(z, 9)}"' if drop else ""
            paths = "".join(
                f'<path d="{iso.poly(pts)}" fill="{col}"/>' for pts, col in parts
            )
            out.append(f'<g{cls} stroke="{seam}">{paths}</g>')
        return out


def cube_svg(iso: Iso, x, y, z, w, d, h, mat_cols, seam, extra=""):
    top, left, right = iso.faces(x, y, z, w, d, h)
    t, l, r = mat_cols
    return (
        f'<g stroke="{seam}" stroke-width="0.6"{extra}>'
        f'<path d="{iso.poly(left)}" fill="{l}"/>'
        f'<path d="{iso.poly(right)}" fill="{r}"/>'
        f'<path d="{iso.poly(top)}" fill="{t}"/></g>'
    )


# --------------------------------------------------------------------------
# SMIL helpers
# --------------------------------------------------------------------------
def kt(times, total):
    return ";".join(f"{min(max(t / total, 0), 1):.4f}".rstrip("0").rstrip(".") or "0" for t in times)


def opacity_anim(total, show, hide, fade=0.35, start_visible=False):
    """Opacity 0 -> 1 at `show`, back to 0 at `hide` (seconds within loop)."""
    if start_visible:
        times = [0, hide, hide + fade, total]
        vals = [1, 1, 0, 0]
    else:
        times = [0, show, show + fade, hide, hide + fade, total]
        vals = [0, 0, 1, 1, 0, 0]
    return (
        f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" '
        f'values="{";".join(map(str, vals))}" keyTimes="{kt(times, total)}"/>'
    )


def typing_anims(total, n, cell, start, per_char, erase_at, x0=None, cursor=False):
    """Discrete width animation for a clip rect revealing `n` monospace cells."""
    times, widths = [0.0], [0.0]
    t = start
    times.append(t)
    widths.append(0.0)
    for k in range(1, n + 1):
        t += per_char
        times.append(t)
        widths.append(k * cell)
    times.append(erase_at)
    widths.append(n * cell)
    times.append(erase_at + 0.01)
    widths.append(0.0)
    times.append(total)
    widths.append(0.0)
    # keyTimes must be strictly increasing for discrete mode to be safe
    clean_t, clean_w = [], []
    for tt, ww in zip(times, widths):
        if clean_t and tt <= clean_t[-1]:
            tt = clean_t[-1] + 0.001
        clean_t.append(tt)
        clean_w.append(ww)
    keys = ";".join(f"{min(tt / total, 1):.5f}" for tt in clean_t)
    keys = keys.rsplit(";", 1)[0] + ";1"
    vals = ";".join(f(w) for w in clean_w)
    width_anim = (
        f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" '
        f'calcMode="discrete" values="{vals}" keyTimes="{keys}"/>'
    )
    if not cursor:
        return width_anim, ""
    xs = ";".join(f(x0 + w) for w in clean_w)
    x_anim = (
        f'<animate attributeName="x" dur="{total}s" repeatCount="indefinite" '
        f'calcMode="discrete" values="{xs}" keyTimes="{keys}"/>'
    )
    return width_anim, x_anim


# --------------------------------------------------------------------------
# Hero: voxel factory inside an on-prem perimeter
# --------------------------------------------------------------------------
W, H = 1200, 440

TAGLINES = [
    "private AI that never leaves your plant",
    "source-grounded answers, full audit trail",
    "on-prem or private cloud · Poland & DACH",
    "knowledge transfer first, code second",
]


def build_world() -> Voxels:
    v = Voxels()
    # main hall with an orange band under the roof
    v.box(1, 1, 0, 8, 5, 3, "wall")
    for x in range(1, 9):
        v.add(x, 5, 2, "band")
    for y in range(1, 6):
        v.add(8, y, 2, "band")
    # sawtooth roof
    for x in range(1, 9):
        for y in range(1, 6):
            v.add(x, y, 3, "roof")
            if (x - 1) % 3 == 0:
                v.add(x, y, 4, "roof")
    # chimney
    for z in range(3, 9):
        v.add(2, 2, z, "band" if z == 7 else "wall")
    # AI core / server hall with a crenellated top
    v.box(11, 3, 0, 4, 4, 3, "core")
    for x in range(11, 15):
        for y in range(3, 7):
            if (x + y) % 2 == 0:
                v.add(x, y, 3, "core")
    # silo (plus-shaped voxel cylinder) behind the core
    plus = [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]
    for z in range(0, 5):
        for dx, dy in plus:
            v.add(11 + dx, dy, z, "silo")
    for dx, dy in plus:
        v.add(11 + dx, dy, 5, "silo_cap")
    # trees: trunk, 2x2 crown, single block on top
    def tree(tx, ty, leaf, tall=False):
        h = 2 if tall else 1
        for z in range(h):
            v.add(tx, ty, z, "trunk")
        for dx in (0, 1):
            for dy in (0, 1):
                v.add(tx + dx - 1, ty + dy - 1, h, leaf)
                if tall:
                    v.add(tx + dx - 1, ty + dy - 1, h + 1, leaf)
        v.add(tx, ty, h + (2 if tall else 1), leaf)

    tree(1, 9, "leaf", tall=True)
    tree(2, 11, "leaf2")
    tree(17, 2, "leaf2", tall=True)
    tree(18, 11, "leaf")
    # crates by the hall
    v.add(9, 6, 0, "silo_cap")
    v.add(10, 6, 0, "band")
    v.add(9, 6, 1, "band")
    return v


def hero(theme_name: str) -> str:
    th = THEMES[theme_name]
    iso = Iso(16, 0, 0)

    # ground footprint (grid units)
    GX, GY = 19, 12
    left, right = iso.p(0, GY, 0)[0], iso.p(GX, 0, 0)[0]
    top = iso.p(2, 2, 9)[1] - 40  # chimney plus room for smoke
    bottom = iso.p(GX, GY, -0.6)[1]
    # centre the factory in the right panel (x 570..1180, y 20..420)
    iso.ox = 885 - (left + right) / 2
    iso.oy = 222 - (top + bottom) / 2

    out: list[str] = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">'
        f'<title id="t">Fryderyk Pryjma</title>'
        f'<desc id="d">Animated voxel factory inside an on-prem perimeter. Co-founder and CEO of CortexMine, private AI for industry.</desc>'
    )
    out.append(
        "<style>"
        ".b{animation:drop .55s cubic-bezier(.2,.9,.3,1.3) both}"
        + "".join(f".z{z}{{animation-delay:{0.15 + z * 0.16:.2f}s}}" for z in range(10))
        + "@keyframes drop{from{opacity:0;transform:translateY(-26px)}to{opacity:1;transform:none}}"
        ".fade{animation:fadein .8s ease-out both}"
        "@keyframes fadein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
        ".ants{stroke-dasharray:7 6;animation:ants 1.6s linear infinite}"
        "@keyframes ants{to{stroke-dashoffset:-26}}"
        ".blink{animation:blink 1.05s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
        ".win{animation:win 6s ease-in-out infinite}"
        "@keyframes win{0%,100%{opacity:.15}40%,60%{opacity:1}}"
        ".smoke{animation:smoke 4.2s ease-out infinite;opacity:0}"
        "@keyframes smoke{0%{opacity:0;transform:translate(0,0)}15%{opacity:.85}100%{opacity:0;transform:translate(14px,-70px)}}"
        ".led{animation:led 1.4s steps(1) infinite}"
        "@keyframes led{50%{opacity:.2}}"
        "@media (prefers-reduced-motion:reduce){.b,.fade,.ants,.blink,.win,.smoke,.led{animation:none!important;opacity:1}}"
        "</style>"
    )
    out.append(
        "<defs>"
        f'<pattern id="dots-{theme_name}" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="{th["dots"]}"/></pattern>'
        f'<radialGradient id="glow-{theme_name}" cx="50%" cy="55%" r="55%"><stop offset="0" stop-color="{th["orange"]}" stop-opacity=".16"/><stop offset="1" stop-color="{th["orange"]}" stop-opacity="0"/></radialGradient>'
        "</defs>"
    )
    # card
    out.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="26" fill="{th["bg"]}" stroke="{th["card_line"]}" stroke-width="2"/>')
    out.append(f'<rect x="560" y="12" width="628" height="{H - 24}" rx="20" fill="url(#dots-{theme_name})"/>')
    out.append(f'<ellipse cx="880" cy="250" rx="330" ry="190" fill="url(#glow-{theme_name})"/>')

    # ---- left: identity ------------------------------------------------
    sx, sy = 64, 62
    out.append(f'<g class="fade" style="animation-delay:.05s" transform="translate({sx} {sy}) scale(.52)">'
               f'<path d="M36 20 A48 48 0 0 0 36 100" fill="none" stroke="{th["orange"]}" stroke-width="7" stroke-linecap="round"/>'
               f'<path d="M84 20 A48 48 0 0 1 84 100" fill="none" stroke="{th["orange"]}" stroke-width="7" stroke-linecap="round"/>'
               f'<text x="60" y="75" text-anchor="middle" font-family="{SERIF}" font-size="50" fill="{th["ink"]}">fp</text></g>')
    out.append(f'<text class="fade" style="animation-delay:.2s" x="64" y="178" font-family="{SERIF}" font-size="60" fill="{th["ink"]}">Fryderyk Pryjma</text>')
    out.append(f'<text class="fade" style="animation-delay:.35s" x="66" y="214" font-family="{SANS}" font-weight="600" font-size="14" letter-spacing="2.4" fill="{th["orange"]}">CO-FOUNDER &amp; CEO · CORTEXMINE</text>')

    # typing taglines
    fs = 19
    cell = fs * 0.6
    tx, ty = 66, 284
    slot = 5.5
    total = slot * len(TAGLINES)
    out.append(f'<text class="fade" style="animation-delay:.5s" x="{tx}" y="{ty}" font-family="{MONO}" font-size="{fs}" fill="{th["orange"]}">&gt;</text>')
    lx = tx + cell * 2
    for i, line in enumerate(TAGLINES):
        n = len(line)
        start = i * slot + 0.2
        erase = i * slot + slot - 0.35
        wa, xa = typing_anims(total, n, cell, start, 0.045, erase, x0=lx, cursor=True)
        cid = f"tl{i}"
        out.append(f'<clipPath id="{cid}"><rect x="{f(lx)}" y="{ty - fs}" width="0" height="{fs + 8}">{wa}</rect></clipPath>')
        safe = line.replace("&", "&amp;")
        out.append(
            f'<text x="{f(lx)}" y="{ty}" font-family="{MONO}" font-size="{fs}" fill="{th["ink"]}" '
            f'textLength="{f(n * cell)}" lengthAdjust="spacingAndGlyphs" clip-path="url(#{cid})" xml:space="preserve">{safe}</text>'
        )
        # cursor for this line, visible only during its slot
        vis_times = [0, i * slot, i * slot + 0.001, i * slot + slot - 0.001, i * slot + slot, total]
        vis_vals = [0, 0, 1, 1, 0, 0]
        vis = (f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
               f'values="{";".join(map(str, vis_vals))}" keyTimes="{kt(vis_times, total)}"/>')
        out.append(f'<g opacity="0">{vis}<rect class="blink" x="{f(lx)}" y="{ty - fs + 3}" width="{f(cell * 0.9)}" height="{fs + 2}" fill="{th["orange"]}">{xa}</rect></g>')

    # location + mini legend
    out.append(f'<g class="fade" style="animation-delay:.7s" font-family="{SANS}" font-size="14" fill="{th["muted"]}">'
               f'<path transform="translate(66 352)" d="M7 0C3.1 0 0 3 0 6.9 0 12 7 18 7 18s7-6 7-11.1C14 3 10.9 0 7 0zm0 9.5a2.6 2.6 0 1 1 0-5.2 2.6 2.6 0 0 1 0 5.2z" fill="{th["orange"]}"/>'
               f'<text x="90" y="366">Kraków, Poland</text>'
               f'<rect x="210" y="356" width="22" height="2" fill="{th["orange"]}" class="ants" stroke="{th["orange"]}" stroke-width="2"/>'
               f'<text x="242" y="366">on-prem perimeter: nothing leaves</text></g>')

    # ---- right: voxel world ----------------------------------------------
    g = th["ground"]
    # ground slab
    out.append(cube_svg(iso, 0, 0, -0.6, GX, GY, 0.6, g[:3], g[3], ' class="fade"'))
    # tile grid on ground
    lines = []
    for x in range(1, GX):
        a, b = iso.p(x, 0, 0), iso.p(x, GY, 0)
        lines.append(f"M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}")
    for y in range(1, GY):
        a, b = iso.p(0, y, 0), iso.p(GX, y, 0)
        lines.append(f"M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}")
    out.append(f'<path class="fade" d="{"".join(lines)}" stroke="{g[3]}" stroke-width=".8" fill="none"/>')

    # perimeter fence (marching ants)
    inset = 0.35
    fence = [iso.p(inset, inset, 0), iso.p(GX - inset, inset, 0), iso.p(GX - inset, GY - inset, 0), iso.p(inset, GY - inset, 0)]
    out.append(f'<path class="ants" d="{iso.poly(fence)}" fill="none" stroke="{th["orange"]}" stroke-width="2"/>')
    # fence posts
    posts = []
    for t in [i / 8 for i in range(9)]:
        for a, b in [((inset, GY - inset), (GX - inset, GY - inset)), ((GX - inset, inset), (GX - inset, GY - inset))]:
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            p0, p1 = iso.p(x, y, 0), iso.p(x, y, 0.9)
            posts.append(f"M{f(p0[0])} {f(p0[1])}L{f(p1[0])} {f(p1[1])}")
    out.append(f'<path d="{"".join(posts)}" stroke="{th["orange"]}" stroke-width="2.2" stroke-linecap="round" opacity=".85"/>')

    # conveyor belt (hall door -> core door)
    belt_path_grid = [(4.5, 6.0), (4.5, 8.8), (12.5, 8.8), (12.5, 7.0)]
    bt = th["belt"]
    belt_parts = [
        (4.1, 6.0, 0.8, 3.2),
        (4.9, 8.4, 7.2, 0.8),
        (12.1, 7.0, 0.8, 2.2),
    ]
    out.append('<g class="b z1">')
    for (bx, by, bw, bd) in belt_parts:
        out.append(cube_svg(iso, bx, by, 0, bw, bd, 0.3, bt[:3], bt[3]))
    out.append("</g>")

    # static voxels (hall, core, silo, trees)
    world = build_world()
    out.extend(world.render(iso, th))

    # windows on the hall (+y face at y=6, +x face at x=9)
    wins = []
    k = 0
    for x in [1.25, 2.25, 5.25, 6.25, 7.25]:
        q = [iso.p(x, 6, 0.9), iso.p(x + 0.5, 6, 0.9), iso.p(x + 0.5, 6, 1.7), iso.p(x, 6, 1.7)]
        delay = (k * 1.3) % 6
        wins.append(f'<path d="{iso.poly(q)}" fill="{th["window"]}"/><path class="win" style="animation-delay:-{delay:.1f}s" d="{iso.poly(q)}" fill="{th["window_lit"]}"/>')
        k += 1
    for y in [1.25, 2.25, 3.25, 4.25]:
        q = [iso.p(9, y, 0.9), iso.p(9, y + 0.5, 0.9), iso.p(9, y + 0.5, 1.7), iso.p(9, y, 1.7)]
        delay = (k * 1.7) % 6
        wins.append(f'<path d="{iso.poly(q)}" fill="{th["window"]}"/><path class="win" style="animation-delay:-{delay:.1f}s" d="{iso.poly(q)}" fill="{th["window_lit"]}"/>')
        k += 1
    # hall door
    door = [iso.p(3.9, 6, 0), iso.p(5.1, 6, 0), iso.p(5.1, 6, 1.3), iso.p(3.9, 6, 1.3)]
    wins.append(f'<path d="{iso.poly(door)}" fill="{th["window"]}"/>')
    # core door + LEDs
    cdoor = [iso.p(11.9, 7, 0), iso.p(13.1, 7, 0), iso.p(13.1, 7, 1.3), iso.p(11.9, 7, 1.3)]
    wins.append(f'<path d="{iso.poly(cdoor)}" fill="{th["orange"]}" opacity=".9"/>')
    for i in range(4):
        for j in range(3):
            yy = 3.3 + i * 0.9
            zz = 0.6 + j * 0.8
            q = [iso.p(15, yy, zz), iso.p(15, yy + 0.35, zz), iso.p(15, yy + 0.35, zz + 0.25), iso.p(15, yy, zz + 0.25)]
            delay = ((i * 3 + j) * 0.37) % 1.4
            wins.append(f'<path class="led" style="animation-delay:-{delay:.2f}s" d="{iso.poly(q)}" fill="{th["orange"]}"/>')
    out.append(f'<g class="fade" style="animation-delay:1.1s">{"".join(wins)}</g>')

    # documents riding the belt (SMIL motion along the projected path)
    pts = [iso.p(x, y, 0.3) for x, y in belt_path_grid]
    motion = "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts)
    dur = 9
    docs = []
    for i in range(4):
        cube = cube_svg(iso, -0.3, -0.3, 0, 0.6, 0.6, 0.45, th["doc"][:3], th["doc"][3])
        # orange "text line" on the document's top face
        l1 = [iso.p(-0.18, -0.05, 0.46), iso.p(0.18, -0.05, 0.46)]
        l2 = [iso.p(-0.18, 0.1, 0.46), iso.p(0.08, 0.1, 0.46)]
        rel = lambda pts_: "M" + "L".join(f"{f(a - iso.ox)} {f(b - iso.oy)}" for a, b in pts_)
        # cube_svg emits absolute coords; shift them so animateMotion moves the cube
        cube_rel = _shift_paths(cube, -iso.ox, -iso.oy)
        docs.append(
            f'<g opacity="0">'
            f'<animateMotion dur="{dur}s" begin="{-i * dur / 4:.2f}s" repeatCount="indefinite" path="{motion}"/>'
            f'<animate attributeName="opacity" dur="{dur}s" begin="{-i * dur / 4:.2f}s" repeatCount="indefinite" values="0;1;1;0" keyTimes="0;.06;.92;1"/>'
            f'{cube_rel}<path d="{rel(l1)}{rel(l2)}" stroke="{th["orange"]}" stroke-width="1.4" stroke-linecap="round"/></g>'
        )
    out.append(f'<g class="fade" style="animation-delay:1.4s">{"".join(docs)}</g>')

    # smoke puffs from the chimney
    top = iso.p(2.5, 2.5, 9.1)
    puffs = []
    for i in range(4):
        r = 8 + (i % 2) * 3
        puffs.append(
            f'<rect class="smoke" style="animation-delay:{1.6 + i * 1.05:.2f}s" x="{f(top[0] - r / 2)}" y="{f(top[1] - r)}" '
            f'width="{r}" height="{r}" rx="1.5" fill="{th["smoke"]}"/>'
        )
    out.append("".join(puffs))

    # a data packet tries to leave, bounces off the perimeter
    a = iso.p(15.4, 5.0, 0.9)
    b = iso.p(GX - inset - 0.25, 5.0, 0.9)
    pk = _shift_paths(cube_svg(iso, -0.22, -0.22, 0, 0.44, 0.44, 0.44, th["band"][:3], th["band"][3]), -iso.ox, -iso.oy)
    T = 7
    out.append(
        f'<g opacity="0">'
        f'<animateMotion dur="{T}s" repeatCount="indefinite" path="M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}L{f(a[0])} {f(a[1])}" '
        f'keyPoints="0;0;.5;1;1" keyTimes="0;.35;.55;.75;1" calcMode="spline" keySplines="0 0 1 1;.5 0 1 1;0 0 .5 1;0 0 1 1"/>'
        f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="0;.33;.37;.73;.77;1"/>'
        f"{pk}</g>"
    )
    # perimeter flash where the packet hits
    h0 = iso.p(GX - inset, 3.8, 0)
    h1 = iso.p(GX - inset, 6.2, 0)
    h2 = iso.p(GX - inset, 6.2, 1.6)
    h3 = iso.p(GX - inset, 3.8, 1.6)
    out.append(
        f'<path d="{iso.poly([h0, h1, h2, h3])}" fill="{th["orange"]}" opacity="0">'
        f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" values="0;0;.55;0;0" keyTimes="0;.54;.56;.68;1"/></path>'
    )
    lock = iso.p(GX - inset, 5.0, 2.4)
    out.append(
        f'<g opacity="0" transform="translate({f(lock[0])} {f(lock[1])})">'
        f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="0;.54;.57;.7;.76;1"/>'
        f'<rect x="-7" y="-4" width="14" height="11" rx="2" fill="{th["orange"]}"/>'
        f'<path d="M-4.2-4v-3a4.2 4.2 0 0 1 8.4 0v3" fill="none" stroke="{th["orange"]}" stroke-width="2.2"/>'
        f'<circle cx="0" cy="1.5" r="1.6" fill="{th["bg"]}"/></g>'
    )

    out.append("</svg>")
    return "".join(out)


def _shift_paths(svg: str, dx: float, dy: float) -> str:
    """Translate every absolute M/L coordinate pair inside path data."""
    import re

    def fix(m):
        d = m.group(1)
        nums = re.findall(r"[ML]|-?\d+(?:\.\d+)?", d)
        res, i = [], 0
        while i < len(nums):
            tok = nums[i]
            if tok in "ML":
                x = float(nums[i + 1]) + dx
                y = float(nums[i + 2]) + dy
                res.append(f"{tok}{f(x)} {f(y)}")
                i += 3
            else:
                i += 1
        return f'd="{"".join(res)}Z"'

    return re.sub(r'd="([^"]+)Z"', fix, svg)


# --------------------------------------------------------------------------
# Demo terminal
# --------------------------------------------------------------------------
def demo(theme_name: str) -> str:
    th = THEMES[theme_name]
    DW, DH = 1200, 400
    fs = 18
    cell = fs * 0.6
    total = 17.0
    hide = 15.6

    if theme_name == "light":
        win_bg, bar_bg, txt, dim = "#FFFDFA", "#F1EAE1", "#1A1613", "#8A8076"
    else:
        win_bg, bar_bg, txt, dim = "#211C18", "#2C2520", "#F6F2ED", "#A89E94"

    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {DW} {DH}" width="{DW}" height="{DH}" role="img" aria-labelledby="dt dd">'
        f'<title id="dt">Illustrative example of a source-grounded answer</title>'
        f'<desc id="dd">A question about bolt torque is answered from internal documents with citations, on-prem, and the answer is written to an audit trail.</desc>'
        "<style>.blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.blink{animation:none}}</style>"
    )
    o.append(f'<rect x="1" y="1" width="{DW - 2}" height="{DH - 2}" rx="22" fill="{win_bg}" stroke="{th["card_line"]}" stroke-width="2"/>')
    o.append(f'<path d="M1 23a22 22 0 0 1 22-22h{DW - 46}a22 22 0 0 1 22 22v25H1z" fill="{bar_bg}"/>')
    for i, col in enumerate([th["orange"], th["muted"], th["card_line"]]):
        o.append(f'<circle cx="{32 + i * 22}" cy="25" r="6.5" fill="{col}"/>')
    o.append(f'<text x="{DW / 2}" y="30" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{dim}">private workspace · plant-01 · on-prem</text>')
    o.append(f'<text x="{DW - 30}" y="30" text-anchor="end" font-family="{SANS}" font-size="12" font-weight="600" letter-spacing="1.5" fill="{th["orange"]}">ILLUSTRATIVE</text>')

    x0 = 48
    y = 100
    lh = 40

    def text(x, yy, s, fill, weight="400", n=None, clip=None, extra=""):
        n = n if n is not None else len(s)
        cp = f' clip-path="url(#{clip})"' if clip else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        return (f'<text x="{f(x)}" y="{yy}" font-family="{MONO}" font-size="{fs}" font-weight="{weight}" fill="{fill}" '
                f'textLength="{f(n * cell)}" lengthAdjust="spacingAndGlyphs" xml:space="preserve"{cp}{extra}>{s}</text>')

    # line 1: question typed
    q = "What torque do we use for M12 bolts on line 3?"
    o.append(text(x0, y, "›", th["orange"], "700"))
    qx = x0 + cell * 2
    wa, xa = typing_anims(total, len(q), cell, 0.5, 0.05, hide, x0=qx, cursor=True)
    o.append(f'<clipPath id="q"><rect x="{f(qx)}" y="{y - fs}" width="0" height="{fs + 8}">{wa}</rect></clipPath>')
    o.append(text(qx, y, q, txt, "600", clip="q"))
    q_done = 0.5 + 0.05 * len(q)
    cur_vis = (f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
               f'values="1;0;0" keyTimes="0;{(q_done + 0.4) / total:.4f};1"/>')
    o.append(f'<g>{cur_vis}<rect class="blink" x="{f(qx)}" y="{y - fs + 3}" width="{f(cell * 0.9)}" height="{fs + 2}" fill="{th["orange"]}">{xa}</rect></g>')

    # line 2: searching with voxel progress
    t2 = q_done + 0.5
    y2 = y + lh + 6
    s2 = "searching 12,481 documents on-prem · nothing leaves the site"
    o.append(f'<g opacity="0">{opacity_anim(total, t2, hide)}{text(qx, y2, s2, dim)}</g>')
    bx = qx + cell * (len(s2) + 2)
    blocks = []
    for i in range(10):
        ti = t2 + 0.25 + i * 0.14
        blocks.append(
            f'<rect x="{f(bx + i * 13)}" y="{y2 - 13}" width="10" height="10" rx="1.5" fill="{th["orange"]}" opacity="0">'
            f'{opacity_anim(total, ti, hide, fade=0.08)}</rect>'
        )
    o.append("".join(blocks))
    t3 = t2 + 0.25 + 10 * 0.14 + 0.4

    # line 3: answer (typed fast)
    y3 = y2 + lh + 14
    ans = "85 Nm, cross pattern, two passes: 60 Nm, then 85 Nm."
    ax = qx
    wa3, _ = typing_anims(total, len(ans), cell, t3, 0.022, hide)
    o.append(f'<clipPath id="a"><rect x="{f(ax)}" y="{y3 - fs}" width="0" height="{fs + 8}">{wa3}</rect></clipPath>')
    o.append(f'<rect x="{x0 - 2}" y="{y3 - fs - 4}" width="4" height="{lh * 3 + 6}" rx="2" fill="{th["orange"]}" opacity="0">{opacity_anim(total, t3, hide)}</rect>')
    o.append(text(ax, y3, ans, txt, "700", clip="a"))
    t4 = t3 + 0.022 * len(ans) + 0.4

    cites = [
        ("[1]", "WI-204 Assembly work instruction, rev. F, p. 7"),
        ("[2]", "QA-17 Torque control audit, March 2026, §4.2"),
    ]
    for i, (tag, src) in enumerate(cites):
        yy = y3 + lh * (i + 1)
        ti = t4 + i * 0.45
        o.append(f'<g opacity="0">{opacity_anim(total, ti, hide)}'
                 f'{text(ax, yy, tag, th["orange"], "700")}{text(ax + cell * 4, yy, src, dim)}</g>')
    t5 = t4 + 2 * 0.45 + 0.5

    # audit line
    y5 = y3 + lh * 3 + 22
    o.append(f'<g opacity="0">{opacity_anim(total, t5, hide)}'
             f'<rect x="{x0 - 6}" y="{y5 - 26}" width="{DW - 2 * x0 + 12}" height="40" rx="10" fill="{th["orange_soft"]}" opacity=".55"/>'
             f'{text(x0 + 8, y5, "✓", th["orange"], "700")}'
             f'{text(x0 + 8 + cell * 2, y5, "access: role=maintenance · answer + sources written to audit trail #A-20431", txt)}</g>')

    o.append("</svg>")
    return "".join(o)


# --------------------------------------------------------------------------
# Buttons (theme-neutral: readable on GitHub light and dark)
# --------------------------------------------------------------------------
BUTTONS = {
    # file name: (label, style)
    "btn-site": ("fryderykpryjma.com", "primary"),
    "btn-cortexmine": ("cortexmine.com", "dark"),
    "btn-linkedin": ("LinkedIn", "dark"),
    "btn-rss": ("RSS", "dark"),
}


def button(label: str, style: str) -> str:
    fs = 13
    cw = fs * 0.66  # uppercase + letter spacing
    text_w = len(label) * cw
    pad = 18
    icon = 22 if style == "vote" else 0
    w = round(text_w + pad * 2 + icon)
    h = 36
    if style == "primary":
        fill, stroke, ink = ORANGE, ORANGE, "#FFFFFF"
    elif style == "dark":
        fill, stroke, ink = "#1A1613", "#4A413A", "#F6F2ED"
    else:
        fill, stroke, ink = "#1A1613", ORANGE, "#F6F2ED"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">',
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>',
    ]
    x = pad
    if style == "vote":
        # tiny voxel cube icon
        parts.append(
            f'<g transform="translate({pad - 2} 9)"><path d="M8 0l8 4-8 4-8-4z" fill="#F1A877"/>'
            f'<path d="M0 4l8 4v9l-8-4z" fill="{ORANGE}"/><path d="M16 4l-8 4v9l8-4z" fill="#B85A22"/></g>'
        )
        x += icon
    parts.append(
        f'<text x="{f(x)}" y="23" font-family="{SANS}" font-size="{fs}" font-weight="600" letter-spacing="1.2" '
        f'fill="{ink}" textLength="{f(text_w - 1.2)}" lengthAdjust="spacingAndGlyphs">{label.upper()}</text></svg>'
    )
    return "".join(parts)


def main():
    ASSETS.mkdir(exist_ok=True)
    for name in THEMES:
        (ASSETS / f"hero-{name}.svg").write_text(hero(name), encoding="utf-8")
        (ASSETS / f"demo-{name}.svg").write_text(demo(name), encoding="utf-8")
    for fname, (label, style) in BUTTONS.items():
        (ASSETS / f"{fname}.svg").write_text(button(label, style), encoding="utf-8")
    for p in sorted(ASSETS.glob("*.svg")):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
