"""Profil giriş görselini (tek SVG) ve README.md'yi üretir.

Kullanım:  python3 scripts/build.py

Tek, çerçevesiz, #0d1117 zeminli, animasyonlu bir bant: SCYLLA CHARYBDIS
harfleri gürültüden çözülür, "geçit" yarığı açılıp kapanır, bir satır
karartılmış kayıt titrer. Bütün hareket SVG içindeki CSS ile yapılır (JS yok,
dış kaynak yok). Dosya adı içerik özetini taşır; her değişiklikte yeni ad
oluşur, böylece GitHub önbelleği eski görseli göstermez.
"""

import glob
import hashlib
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://tunalper.github.io/"

W, H = 1200, 280
BG = "#0d1117"
U = 5            # one title pixel
SU = 3           # one small-glyph pixel
SLIT = 7         # the strait between the two dangers
CYCLE = 9.0      # seconds

# display capitals (11x13, 3px stems) - the same drawing as the site
DISPLAY = {
    "S": (11, [511, 1023, 1792, 1792, 1792, 2046, 1023, 7, 7, 7, 7, 2046, 2044]),
    "C": (11, [511, 1023, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 1023, 511]),
    "Y": (11, [1799, 1799, 1799, 1799, 910, 508, 248, 112, 112, 112, 112, 112, 112]),
    "L": (11, [1792, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 1792, 2047, 2047]),
    "A": (11, [508, 1022, 1799, 1799, 1799, 2047, 2047, 1799, 1799, 1799, 1799, 1799, 1799]),
    "H": (11, [1799, 1799, 1799, 1799, 1799, 2047, 2047, 1799, 1799, 1799, 1799, 1799, 1799]),
    "R": (11, [2044, 2046, 1799, 1799, 1799, 2046, 2044, 1820, 1806, 1799, 1799, 1799, 1799]),
    "B": (11, [2044, 2046, 1799, 1799, 1806, 2044, 2046, 1799, 1799, 1799, 1799, 2046, 2044]),
    "D": (11, [2040, 2044, 1806, 1799, 1799, 1799, 1799, 1799, 1799, 1799, 1806, 2044, 2040]),
    "I": (9, [511, 511, 56, 56, 56, 56, 56, 56, 56, 56, 56, 511, 511]),
}
# 6x8 cells of the site's own pixel font
SMALL = {
    "0": [28, 34, 38, 42, 50, 34, 28, 0], "1": [8, 24, 8, 8, 8, 8, 28, 0], "9": [28, 34, 34, 30, 2, 4, 24, 0],
    "6": [12, 16, 32, 60, 34, 34, 28, 0], "8": [28, 34, 34, 28, 34, 34, 28, 0],
    "d": [2, 2, 30, 34, 34, 34, 30, 0], "x": [0, 0, 34, 20, 8, 20, 34, 0],
    "█": [63] * 8, "▓": [63, 42, 63, 42, 63, 42, 63, 42], "░": [42, 0, 42, 0, 42, 0, 42, 0],
    "▶": [32, 48, 56, 60, 56, 48, 32, 0], "⌬": [8, 20, 34, 34, 34, 20, 8, 0],
    "₿": [20, 60, 34, 60, 34, 34, 60, 20], "·": [0, 0, 0, 8, 0, 0, 0, 0],
    "L": [28, 34, 34, 62, 54, 54, 62, 0],   # the lock
    "@": [30, 32, 44, 42, 36, 16, 14, 0],   # the whirlpool
}

# a top-lit gradient, dithered on a 4x4 Bayer grid like the site
BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]
ROWS = [
    ("#ea2250", "#ea2250", 0), ("#ea2250", "#bd173a", .25), ("#bd173a", "#ea2250", .25), ("#bd173a", "#bd173a", 0),
    ("#bd173a", "#8f132e", .5), ("#8f132e", "#bd173a", .25), ("#8f132e", "#8f132e", 0), (None, None, 0),
    ("#8f132e", "#bd173a", .2), ("#8f132e", "#6a0f24", .5), ("#6a0f24", "#6a0f24", 0), ("#6a0f24", "#5c124a", .5), ("#5c124a", "#6a0f24", .25),
]


def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def runs_path(pixels, ox, oy, u):
    """pixels: set of (x, y) -> compact path of horizontal runs."""
    rows = {}
    for x, y in pixels:
        rows.setdefault(y, []).append(x)
    out = []
    for y in sorted(rows):
        xs = sorted(rows[y])
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
                j += 1
            n = j - i + 1
            out.append(f"M{fmt(ox + xs[i] * u)} {fmt(oy + y * u)}h{fmt(n * u)}v{fmt(u)}h-{fmt(n * u)}z")
            i = j + 1
    return "".join(out)


def glyph_pixels(w, rows):
    return {(c, r) for r, v in enumerate(rows) for c in range(w) if v & (1 << (w - 1 - c))}


def build_svg():
    rnd = random.Random(1931)
    title = "SCYLLA CHARYBDIS"
    adv = lambda ch: 6 if ch == " " else DISPLAY[ch][0] + 2  # noqa: E731
    tw = sum(adv(ch) for ch in title) - 2
    ox = round((W - tw * U) / 2)
    oy = 66

    # ------------------------------------------------------------ letters
    letters_top, letters_bot, ghost_px = [], [], set()
    x = 0
    k = 0
    for ch in title:
        if ch == " ":
            x += 6
            continue
        w, rows = DISPLAY[ch]
        px = {(c, r) for c, r in glyph_pixels(w, rows) if r != SLIT}
        lx = ox + x * U
        delay = 0.15 + k * 0.085 + rnd.random() * 0.25
        for half in ("t", "b"):
            sel = (lambda r: r < SLIT) if half == "t" else (lambda r: r > SLIT)
            hp = {(c, r) for c, r in px if sel(r)}
            by_col = {}
            for c, r in hp:
                a, b, m = ROWS[r]
                gx, gy = x + c, r
                col = b if m and (BAYER[(gy & 3) * 4 + (gx & 3)] + .5) / 16 < m else a
                if r < 6 and (r == 0 or (c, r - 1) not in px):
                    col = "#ea2250"  # top rim
                by_col.setdefault(col, set()).add((c, r))
            shade1 = {(c + 1, r + 1) for c, r in hp}
            shade2 = {(c + 2, r + 2) for c, r in hp}
            final = [f'<path fill="#1b0f26" d="{runs_path(shade2, lx, oy, U)}"/>',
                     f'<path fill="#3c0d33" d="{runs_path(shade1, lx, oy, U)}"/>']
            final += [f'<path fill="{col}" d="{runs_path(p, lx, oy, U)}"/>' for col, p in sorted(by_col.items())]
            # noise that slowly agrees with the letter
            noise = []
            for v in range(3):
                agree = 0.35 + v * 0.2
                npx = set()
                for r in range(13):
                    if r == SLIT or not sel(r):
                        continue
                    for c in range(w):
                        if ((c, r) in px and rnd.random() < agree) or rnd.random() < 0.22:
                            npx.add((c, r))
                col = ("#470b1a", "#6a0f24", "#8f132e")[v]
                noise.append(f'<path class="v v{v}" fill="{col}" d="{runs_path(npx, lx, oy, U)}"/>')
            grp = (f'<g class="n" style="animation-delay:{delay:.2f}s">{"".join(noise)}</g>'
                   f'<g class="f" style="animation-delay:{delay:.2f}s">{"".join(final)}</g>')
            (letters_top if half == "t" else letters_bot).append(grp)
        ghost_px |= {(x + c, r) for c, r in px}
        x += w + 2
        k += 1

    gtop = runs_path({(c, r) for c, r in ghost_px if r < SLIT}, ox, oy, U)
    gbot = runs_path({(c, r) for c, r in ghost_px if r > SLIT}, ox, oy, U)

    # --------------------------------------------------------------- rain
    rain = []
    for _ in range(34):
        rx = rnd.uniform(0, W + 120)
        ln = rnd.choice((2, 3, 3, 4))
        col = rnd.choice(("#281436", "#371a49", "#371a49", "#4a1f5e"))
        d = "".join(f"M{fmt(rx - j * 2)} {fmt(j * 4)}h2v4h-2z" for j in range(ln))
        dur = rnd.uniform(0.9, 1.6)
        rain.append(f'<path class="r" fill="{col}" d="{d}" style="animation-duration:{dur:.2f}s;animation-delay:-{rnd.uniform(0, dur):.2f}s"/>')

    # ---------------------------------------------------------- lightning
    bx, by = 96.0, -4.0
    bolt = [(bx, by)]
    while by < 150:
        by += rnd.uniform(10, 20)
        bx += rnd.uniform(-14, 14)
        bolt.append((bx, by))
    bolt_d = "M" + " L".join(f"{fmt(px)} {fmt(py)}" for px, py in bolt)

    # ------------------------------------------------------- the info line
    def small_text(s, x0, y0, col, cls=""):
        out = []
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            rows = SMALL[ch]
            p = {(c, r) for r, v in enumerate(rows) for c in range(6) if v & (1 << (5 - c))}
            out.append(runs_path(p, x0 + i * 6 * SU, y0, SU))
        c = f' class="{cls}"' if cls else ""
        return f'<path{c} fill="{col}" d="{"".join(out)}"/>'

    line_y = 196
    cells = 46
    lx0 = round((W - cells * 6 * SU) / 2)
    info = [
        small_text("▶", lx0, line_y, "#ea2250", "cur"),
        small_text("  ░▓ ████ ▓▓▓▓▓ ███", lx0, line_y, "#470b1a", "red1"),
        small_text("        █   ▓▓   █", lx0, line_y, "#6a0f24", "red2"),
    ]
    hexes = ["0x▓▓▓▓▓▓▓▓▓▓19d6", "0x0000▓▓▓▓▓019d6", "0x000000000019d6"]
    for i, h in enumerate(hexes):
        info.append(small_text(" " * 22 + h, lx0, line_y, "#612676" if i < 2 else "#922fdb", f"hx hx{i}"))
    info.append(small_text(" " * 39 + "L @", lx0, line_y, "#4a1f5e"))
    info.append(small_text(" " * 45 + "₿", lx0, line_y, "#ea2250", "coin"))

    # ---------------------------------------------------------------- css
    css = f"""
.n{{opacity:1;animation:noi {CYCLE}s steps(1) infinite both}}
.f{{opacity:0;animation:fin {CYCLE}s steps(1) infinite both}}
@keyframes fin{{0%,9.9%{{opacity:0}}10%,92.9%{{opacity:1}}93%,100%{{opacity:0}}}}
@keyframes noi{{0%,9.9%{{opacity:1}}10%,92.9%{{opacity:0}}93%,100%{{opacity:1}}}}
.v{{animation:flk .3s steps(1) infinite}}.v1{{animation-delay:-.1s}}.v2{{animation-delay:-.2s}}
@keyframes flk{{0%,32%{{opacity:1}}33%,100%{{opacity:0}}}}
.top{{animation:st {CYCLE}s steps(1) infinite}}.bot{{animation:sb {CYCLE}s steps(1) infinite}}
@keyframes st{{0%,30.9%{{transform:none}}31%,32.4%{{transform:translateX(-{U}px)}}32.5%,63.9%{{transform:none}}64%,65.4%{{transform:translateX({U * 2}px)}}65.5%,100%{{transform:none}}}}
@keyframes sb{{0%,30.9%{{transform:none}}31%,32.4%{{transform:translateX({U}px)}}32.5%,63.9%{{transform:none}}64%,65.4%{{transform:translateX(-{U * 2}px)}}65.5%,100%{{transform:none}}}}
.gh{{opacity:0;animation:gh {CYCLE}s steps(1) infinite}}.g2{{animation-name:gh2}}
@keyframes gh{{0%,30.9%{{opacity:0;transform:none}}31%,32.4%{{opacity:.85;transform:translateX(-{U * 2}px)}}32.5%,63.9%{{opacity:0}}64%,65.4%{{opacity:.85;transform:translateX({U * 3}px)}}65.5%,100%{{opacity:0}}}}
@keyframes gh2{{0%,30.9%{{opacity:0;transform:none}}31%,32.4%{{opacity:.85;transform:translateX({U * 2}px)}}32.5%,63.9%{{opacity:0}}64%,65.4%{{opacity:.85;transform:translateX(-{U * 3}px)}}65.5%,100%{{opacity:0}}}}
.fl{{opacity:0;animation:fl {CYCLE}s steps(1) infinite}}
@keyframes fl{{0%,49.9%{{opacity:0}}50%,50.9%{{opacity:.9}}51%,51.4%{{opacity:.15}}51.5%,52.2%{{opacity:.55}}52.3%,100%{{opacity:0}}}}
.bolt{{opacity:0;animation:bo {CYCLE}s steps(1) infinite}}
@keyframes bo{{0%,49.9%{{opacity:0}}50%,50.9%{{opacity:1}}51%,51.4%{{opacity:0}}51.5%,52.2%{{opacity:1}}52.3%,100%{{opacity:0}}}}
.r{{animation:rn 1.2s linear infinite}}
@keyframes rn{{0%{{transform:translate(0,-24px)}}100%{{transform:translate(-90px,{H}px)}}}}
.cur{{animation:bl 1.1s steps(1) infinite}}
@keyframes bl{{0%,55%{{opacity:1}}56%,100%{{opacity:.1}}}}
.red2{{animation:bl 2.3s steps(1) infinite}}
.hx{{opacity:0;animation:hx 6s steps(1) infinite}}.hx1{{animation-delay:-4s}}.hx2{{animation-delay:-2s}}
@keyframes hx{{0%,33.2%{{opacity:1}}33.3%,100%{{opacity:0}}}}
.coin{{animation:hb 1.15s linear infinite}}
@keyframes hb{{0%{{opacity:1}}12%{{opacity:.35}}20%{{opacity:.9}}34%,100%{{opacity:.3}}}}
.bar{{animation:bar 4.5s linear infinite}}
@keyframes bar{{0%{{transform:translateY(-40px)}}100%{{transform:translateY({H + 40}px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.n,.gh,.fl,.bolt,.hx0,.hx1{{opacity:0}}.f,.hx2{{opacity:1}}}}
"""
    css = " ".join(line.strip() for line in css.strip().splitlines())

    defs = (
        '<pattern id="sc" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".3"/></pattern>'
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ea2250" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#ea2250" stop-opacity=".07"/><stop offset="1" stop-color="#ea2250" stop-opacity="0"/></linearGradient>'
        # every full-bleed layer fades to nothing at the edges: no visible frame
        '<radialGradient id="fd" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff"/>'
        '<stop offset=".55" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
        f'<mask id="vm" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#fd)"/></mask>'
    )
    body = [
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<rect class="fl" width="{W}" height="{H}" fill="#1b0f26" mask="url(#vm)"/>',
        f'<g>{"".join(rain)}</g>',
        f'<path class="bolt" d="{bolt_d}" fill="none" stroke="#922fdb" stroke-width="3" stroke-linejoin="miter"/>',
        f'<path class="gh" fill="#922fdb" d="{gtop}{gbot}"/>',
        f'<path class="gh g2" fill="#bd173a" d="{gtop}{gbot}"/>',
        f'<g class="top">{"".join(letters_top)}</g>',
        f'<g class="bot">{"".join(letters_bot)}</g>',
        f'<g>{"".join(info)}</g>',
        f'<g mask="url(#vm)"><rect class="bar" width="{W}" height="36" y="-36" fill="url(#bg)"/></g>',
        f'<rect width="{W}" height="{H}" fill="url(#sc)" mask="url(#vm)"/>',
    ]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="SCYLLA CHARYBDIS" shape-rendering="crispEdges">'
        f"<title>SCYLLA CHARYBDIS</title><style>{css}</style>"
        f"<defs>{defs}</defs>{''.join(body)}</svg>"
    )


def main():
    out_dir = os.path.join(ROOT, "assets")
    os.makedirs(out_dir, exist_ok=True)
    for old in glob.glob(os.path.join(out_dir, "*.svg")):
        os.remove(old)
    svg = build_svg()
    h = hashlib.sha1(svg.encode("utf-8")).hexdigest()[:8]
    name = f"gate-{h}.svg"
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"assets/{name}  {len(svg) / 1024:.1f} KB")
    readme = (
        '<p align="center">'
        f'<a href="{SITE}"><img src="assets/{name}" width="100%" alt="SCYLLA CHARYBDIS"></a>'
        "</p>\n"
    )
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    print("README.md")


if __name__ == "__main__":
    main()
