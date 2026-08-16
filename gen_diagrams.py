# gen_diagrams.py
# this is a little helper script i run ONCE to draw all my economics diagrams and save them
# as svg files in static/diagrams/. i don't run it while the app is on, it just makes the
# picture files that the app then shows.
#   run it with:  python3 gen_diagrams.py
#
# every diagram uses the same axes and colours so they all look the same. the curves are
# drawn as straight lines (which is normal for IB econ diagrams). instead of guessing where
# lines cross, i actually work it out with maths so the equilibrium dots sit exactly right.
#
# AI help (Claude): the two tricky bits here were the line-intersection formula in intersect()
# (that determinant maths is not something i'd write from memory) and how svg markers/arrows
# work. Claude helped me with those, and i built all the actual diagrams on top of them myself.

import os

OUT = os.path.join(os.path.dirname(__file__), "static", "diagrams")

# ---- shared setup: the axes + colours everything uses ----
# heads up: in svg, y grows DOWNWARDS, so a smaller y is higher up the price axis. confusing
# at first but you get used to it.
OX, OY = 70, 330          # where the axes start (bottom-left corner)
XMAX, YMIN = 480, 40      # far end of the x-axis / top of the y-axis

INK = "#37352f"           # near-black, for normal lines and text
BLUE = "#2383e2"          # for shifted curves (after a tax, etc.)
RED = "#eb5757"           # welfare loss shading / the gap arrows
GREY = "#9b9a97"          # the dashed helper lines

# the standard demand and supply lines, written as (start point, end point).
# most diagrams reuse these instead of redefining them every time.
D_LINE = ((110, 80), (440, 300))
S_LINE = ((110, 300), (440, 80))
S_UP = ((110, 245), (440, 25))      # supply shifted up (used for tax / MSC)
D_DOWN = ((110, 150), (380, 330))   # demand shifted down-left
D_UP = ((110, 25), (440, 245))      # demand shifted up-right


def intersect(l1, l2):
    # AI help (Claude): this is the standard formula for where two straight lines cross,
    # using their 4 end points. Claude gave me this formula, i just use it to place my
    # equilibrium points exactly on the crossing instead of eyeballing it.
    (x1, y1), (x2, y2) = l1
    (x3, y3), (x4, y4) = l2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return px, py


def x_at_y(line, y):
    # given a height y, how far along the x-axis is the line there? i use this to find where
    # supply/demand sit at a set price (like at a price ceiling) so the shortage arrow lines up.
    (x1, y1), (x2, y2) = line
    return x1 + (y - y1) * (x2 - x1) / (y2 - y1)


# ---- little building blocks: each returns a piece of svg text ----
# a diagram is basically just a load of these strings stuck together.

def text(x, y, s, anchor="start", size=15, color=INK, weight="400",
         style=""):
    # one bit of text at a position
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'style="{style}">{s}</text>')


def line(p1, p2, color=INK, width=2.2, dash="", marker=""):
    # a straight line from p1 to p2. dash makes it dashed, marker puts an arrowhead on the end.
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return (f'<line x1="{p1[0]:.0f}" y1="{p1[1]:.0f}" x2="{p2[0]:.0f}" '
            f'y2="{p2[1]:.0f}" stroke="{color}" stroke-width="{width}"'
            f'{d}{m} stroke-linecap="round"/>')


def curve(l, label, color=INK, dy=-8):
    # a "curve" (really a straight line) with its label (like "D" or "S") at the end
    (x1, y1), (x2, y2) = l
    lx, ly = x2 + 8, y2 + 5
    return line((x1, y1), (x2, y2), color=color) + \
        text(lx, ly + dy + 8, label, size=16, color=color, weight="600")


def guides(px, py, plabel, qlabel):
    # the dashed lines from an equilibrium point across to the price axis and down to the
    # quantity axis, plus the little Pe / Qe labels
    return (
        line((OX, py), (px, py), GREY, 1.4, dash="5 4") +
        line((px, py), (px, OY), GREY, 1.4, dash="5 4") +
        text(OX - 8, py + 5, plabel, anchor="end", size=14) +
        text(px, OY + 20, qlabel, anchor="middle", size=14)
    )


def point(px, py, label="", dx=8, dy=-8):
    # a filled dot (like the equilibrium E), with an optional label next to it
    dot = f'<circle cx="{px:.0f}" cy="{py:.0f}" r="4" fill="{INK}"/>'
    if label:
        dot += text(px + dx, py + dy, label, size=14, weight="600")
    return dot


def gap_arrow(x1, x2, y, label, color=RED):
    # a double-headed arrow between two x positions, used to show a shortage/surplus/gap.
    # i draw two arrows pointing opposite ways so it has a head on both ends.
    return (
        line((x1 + 4, y), (x2 - 4, y), color, 1.8, marker="arrR") +
        line((x2 - 4, y), (x1 + 4, y), color, 1.8, marker="arrR") +
        text((x1 + x2) / 2, y - 8, label, anchor="middle", size=13,
             color=color, weight="600")
    )


def shift_arrow(p1, p2, color=BLUE):
    # a single arrow to show a curve shifting from one place to another
    return line(p1, p2, color, 1.8, marker="arrB")


def svg(body, ylabel="Price (P)", xlabel="Quantity (Q)"):
    # wraps whatever i drew (body) with the axes, the arrowheads, and the axis labels,
    # so every diagram gets the same frame. the <defs> at the top define the 3 arrowheads.
    return f'''<svg viewBox="0 0 540 400" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system, 'Segoe UI', sans-serif">
<defs>
<marker id="arrK" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="{INK}"/></marker>
<marker id="arrB" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="{BLUE}"/></marker>
<marker id="arrR" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="{RED}"/></marker>
</defs>
{line((OX, OY), (OX, YMIN), INK, 1.8, marker="arrK")}
{line((OX, OY), (XMAX, OY), INK, 1.8, marker="arrK")}
{text(OX, YMIN - 12, ylabel, size=15, weight="600")}
{text(XMAX, OY + 46, xlabel, anchor="end", size=15, weight="600")}
{text(OX - 8, OY + 18, "0", anchor="end", size=14)}
{body}
</svg>'''


def triangle(p1, p2, p3, color=RED):
    # a faint filled triangle, used for the welfare-loss shading
    pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in (p1, p2, p3))
    return f'<polygon points="{pts}" fill="{color}" opacity="0.14"/>'


# ---- the actual diagrams ----
# each one is a function that builds its body out of the blocks above and returns the svg.
# they all follow the same idea: draw the curves, work out the equilibrium with intersect(),
# add the guide lines + dot, plus whatever is special to that diagram.

def market_equilibrium():
    ex, ey = intersect(D_LINE, S_LINE)      # find where D and S cross
    body = (curve(D_LINE, "D") + curve(S_LINE, "S") +
            guides(ex, ey, "Pe", "Qe") + point(ex, ey, "E"))
    return svg(body)


def price_ceiling():
    yc = 255                                # the height of the price ceiling line
    qs, qd = x_at_y(S_LINE, yc), x_at_y(D_LINE, yc)   # quantity supplied/demanded at that price
    ex, ey = intersect(D_LINE, S_LINE)
    body = (curve(D_LINE, "D") + curve(S_LINE, "S") +
            guides(ex, ey, "Pe", "Qe") + point(ex, ey, "E") +
            line((OX, yc), (460, yc), BLUE, 2.2) +
            text(466, yc + 5, "P max", size=15, color=BLUE, weight="600") +
            line((qs, yc), (qs, OY), GREY, 1.4, dash="5 4") +
            line((qd, yc), (qd, OY), GREY, 1.4, dash="5 4") +
            text(qs, OY + 20, "Qs", anchor="middle", size=14) +
            text(qd, OY + 20, "Qd", anchor="middle", size=14) +
            gap_arrow(qs, qd, 312, "Shortage"))   # the gap between Qs and Qd is the shortage
    return svg(body)


def price_floor():
    yf = 140
    qd, qs = x_at_y(D_LINE, yf), x_at_y(S_LINE, yf)
    ex, ey = intersect(D_LINE, S_LINE)
    body = (curve(D_LINE, "D") + curve(S_LINE, "S") +
            guides(ex, ey, "Pe", "Qe") + point(ex, ey, "E") +
            line((OX, yf), (460, yf), BLUE, 2.2) +
            text(466, yf + 5, "P min", size=15, color=BLUE, weight="600") +
            line((qd, yf), (qd, OY), GREY, 1.4, dash="5 4") +
            line((qs, yf), (qs, OY), GREY, 1.4, dash="5 4") +
            text(qd, OY + 20, "Qd", anchor="middle", size=14) +
            text(qs, OY + 20, "Qs", anchor="middle", size=14) +
            gap_arrow(qd, qs, 118, "Surplus"))
    return svg(body)


def indirect_tax():
    # tax shifts supply up (S_LINE -> S_UP), so equilibrium moves from E1 to E2
    e1 = intersect(D_LINE, S_LINE)
    e2 = intersect(D_LINE, S_UP)
    body = (curve(D_LINE, "D") + curve(S_LINE, "S1") +
            curve(S_UP, "S1 + tax", color=BLUE) +
            shift_arrow((300, 190), (280, 145)) +
            guides(e1[0], e1[1], "P1", "Q1") +
            guides(e2[0], e2[1], "P2", "Q2") +
            point(*e1, "E1", dx=10, dy=14) + point(*e2, "E2"))
    return svg(body)


def subsidy():
    # subsidy shifts supply down, so i start from S_UP and move to S_LINE
    e1 = intersect(D_LINE, S_UP)
    e2 = intersect(D_LINE, S_LINE)
    body = (curve(D_LINE, "D") + curve(S_UP, "S1") +
            curve(S_LINE, "S1 − subsidy", color=BLUE) +
            shift_arrow((280, 145), (300, 190)) +
            guides(e1[0], e1[1], "P1", "Q1") +
            guides(e2[0], e2[1], "P2", "Q2") +
            point(*e1, "E1") + point(*e2, "E2", dx=10, dy=14))
    return svg(body)


def neg_prod_externality():
    em = intersect(D_LINE, S_LINE)      # what the market does (uses MPC)
    eo = intersect(D_LINE, S_UP)        # the socially best point (uses MSC)
    # this maths finds the third corner of the welfare-loss triangle (a point on MSC above Qm)
    msc_above_qm = (em[0], eo[1] + (em[0] - eo[0]) *
                    (S_UP[1][1] - S_UP[0][1]) / (S_UP[1][0] - S_UP[0][0]))
    body = (triangle(eo, em, msc_above_qm) +
            curve(D_LINE, "MPB = MSB (D)") + curve(S_LINE, "MPC (S)") +
            curve(S_UP, "MSC", color=BLUE) +
            guides(em[0], em[1], "Pm", "Qm") +
            guides(eo[0], eo[1], "Popt", "Qopt") +
            point(*em) + point(*eo) +
            text(msc_above_qm[0] + 12, msc_above_qm[1] + 2, "Welfare loss",
                 size=13, color=RED, weight="600"))
    return svg(body)


def neg_cons_externality():
    em = intersect(D_LINE, S_LINE)      # market: MPB meets MPC
    eo = intersect(D_DOWN, S_LINE)      # optimum: MSB meets MSC
    slope_d = (D_LINE[1][1] - D_LINE[0][1]) / (D_LINE[1][0] - D_LINE[0][0])
    mpb_above_qopt = (eo[0], D_LINE[0][1] + (eo[0] - D_LINE[0][0]) * slope_d)
    body = (triangle(eo, em, mpb_above_qopt) +
            curve(D_LINE, "MPB (D)") +
            curve(D_DOWN, "MSB", color=BLUE) +
            curve(S_LINE, "MPC = MSC (S)") +
            guides(em[0], em[1], "Pm", "Qm") +
            guides(eo[0], eo[1], "Popt", "Qopt") +
            point(*em) + point(*eo) +
            text(em[0] + 14, em[1] + 26, "Welfare loss", size=13,
                 color=RED, weight="600"))
    return svg(body)


def pos_cons_externality():
    em = intersect(D_LINE, S_LINE)      # market: MPB meets MPC
    eo = intersect(D_UP, S_LINE)        # optimum: MSB meets MSC (MSB is higher here)
    slope_d = (D_LINE[1][1] - D_LINE[0][1]) / (D_LINE[1][0] - D_LINE[0][0])
    mpb_below_qopt = (eo[0], D_LINE[0][1] + (eo[0] - D_LINE[0][0]) * slope_d)
    body = (triangle(em, eo, mpb_below_qopt) +
            curve(D_LINE, "MPB (D)") +
            curve(D_UP, "MSB", color=BLUE) +
            curve(S_LINE, "MPC = MSC (S)") +
            guides(em[0], em[1], "Pm", "Qm") +
            guides(eo[0], eo[1], "Popt", "Qopt") +
            point(*em) + point(*eo) +
            text(em[0] + 40, em[1] - 30, "Welfare loss", size=13,
                 color=RED, weight="600"))
    return svg(body)


# from here down it's the macro + global diagrams. same pattern, just different labels
# (AD/AS instead of D/S, and different axis names via the ylabel/xlabel arguments).

def adas_equilibrium():
    ex, ey = intersect(D_LINE, S_LINE)
    body = (curve(D_LINE, "AD") + curve(S_LINE, "SRAS") +
            guides(ex, ey, "PLe", "Ye") + point(ex, ey, "E"))
    return svg(body, ylabel="Average price level (APL)",
               xlabel="Real GDP (Y)")


def deflationary_gap():
    ex, ey = intersect(D_LINE, S_LINE)
    yp = 340                                 # the vertical LRAS (full employment) line
    body = (curve(D_LINE, "AD") + curve(S_LINE, "SRAS") +
            line((yp, OY), (yp, 60), INK, 2.2) +
            text(yp, 48, "LRAS", anchor="middle", size=16, weight="600") +
            guides(ex, ey, "PLe", "Ye") + point(ex, ey, "E") +
            text(yp, OY + 20, "Yp", anchor="middle", size=14) +
            gap_arrow(ex, yp, 90, "Deflationary gap"))   # gap between Ye and Yp
    return svg(body, ylabel="Average price level (APL)",
               xlabel="Real GDP (Y)")


def inflationary_gap():
    ex, ey = intersect(D_LINE, S_LINE)
    yp = 205
    body = (curve(D_LINE, "AD") + curve(S_LINE, "SRAS") +
            line((yp, OY), (yp, 60), INK, 2.2) +
            text(yp, 48, "LRAS", anchor="middle", size=16, weight="600") +
            guides(ex, ey, "PLe", "Ye") + point(ex, ey, "E") +
            text(yp, OY + 20, "Yp", anchor="middle", size=14) +
            gap_arrow(yp, ex, 90, "Inflationary gap"))
    return svg(body, ylabel="Average price level (APL)",
               xlabel="Real GDP (Y)")


def lras_growth():
    # just two vertical LRAS lines with an arrow showing it moving right (growth)
    x1, x2 = 230, 340
    body = (line((x1, OY), (x1, 60), INK, 2.2) +
            text(x1, 48, "LRAS1", anchor="middle", size=16, weight="600") +
            line((x2, OY), (x2, 60), BLUE, 2.2) +
            text(x2, 48, "LRAS2", anchor="middle", size=16, weight="600",
                 color=BLUE) +
            shift_arrow((x1 + 8, 150), (x2 - 8, 150)) +
            text(x1, OY + 20, "Yp1", anchor="middle", size=14) +
            text(x2, OY + 20, "Yp2", anchor="middle", size=14) +
            text((x1 + x2) / 2, 138, "Growth in potential output",
                 anchor="middle", size=13, color=BLUE, weight="600"))
    return svg(body, ylabel="Average price level (APL)",
               xlabel="Real GDP (Y)")


def tariff():
    # a tariff raises the world price line from Pw to Pw+t. i work out the 4 quantities
    # where that crosses domestic supply and demand, then draw the import gaps.
    yw, yt = 280, 230
    q1, q2 = x_at_y(S_LINE, yw), x_at_y(S_LINE, yt)
    q3, q4 = x_at_y(D_LINE, yt), x_at_y(D_LINE, yw)
    body = (curve(D_LINE, "D dom") + curve(S_LINE, "S dom") +
            line((OX, yw), (460, yw), INK, 2.2) +
            text(466, yw + 5, "Sw", size=15, weight="600") +
            line((OX, yt), (460, yt), BLUE, 2.2) +
            text(466, yt + 5, "Sw + t", size=15, color=BLUE, weight="600") +
            text(OX - 8, yw + 5, "Pw", anchor="end", size=14) +
            text(OX - 8, yt + 5, "Pw+t", anchor="end", size=14) +
            # the "".join(... for ...) bit just draws the 4 dashed lines and 4 labels in a loop
            "".join(line((q, y), (q, OY), GREY, 1.4, dash="5 4")
                    for q, y in ((q1, yw), (q2, yt), (q3, yt), (q4, yw))) +
            "".join(text(q, OY + 20, lab, anchor="middle", size=14)
                    for q, lab in ((q1, "Q1"), (q2, "Q2"),
                                   (q3, "Q3"), (q4, "Q4"))) +
            gap_arrow(q2, q3, 218, "Imports after tariff", BLUE) +
            gap_arrow(q1, q4, 300, "Imports before"))
    return svg(body)


def fx_market():
    ex, ey = intersect(D_LINE, S_LINE)
    body = (curve(D_LINE, "D £") + curve(S_LINE, "S £") +
            guides(ex, ey, "ERe", "Qe") + point(ex, ey, "E"))
    return svg(body, ylabel="Price of £ (in US$)",
               xlabel="Quantity of £")


def fx_depreciation():
    # demand for the pound falls (D_LINE -> D_DOWN) so the exchange rate drops
    e1 = intersect(D_LINE, S_LINE)
    e2 = intersect(D_DOWN, S_LINE)
    body = (curve(D_LINE, "D1 £") + curve(D_DOWN, "D2 £", color=BLUE) +
            curve(S_LINE, "S £") +
            shift_arrow((330, 235), (305, 275)) +
            guides(e1[0], e1[1], "ER1", "Q1") +
            guides(e2[0], e2[1], "ER2", "Q2") +
            point(*e1, "E1") + point(*e2, "E2", dx=-34, dy=16) +
            text(150, 60, "Demand for £ falls → depreciation", size=13,
                 color=BLUE, weight="600"))
    return svg(body, ylabel="Price of £ (in US$)",
               xlabel="Quantity of £")


# maps each file name to the function that draws it. adding a new diagram = write a function
# and add one line here.
DIAGRAMS = {
    "market-equilibrium.svg": market_equilibrium,
    "price-ceiling.svg": price_ceiling,
    "price-floor.svg": price_floor,
    "indirect-tax.svg": indirect_tax,
    "subsidy.svg": subsidy,
    "neg-prod-externality.svg": neg_prod_externality,
    "neg-cons-externality.svg": neg_cons_externality,
    "pos-cons-externality.svg": pos_cons_externality,
    "adas-equilibrium.svg": adas_equilibrium,
    "deflationary-gap.svg": deflationary_gap,
    "inflationary-gap.svg": inflationary_gap,
    "lras-growth.svg": lras_growth,
    "tariff.svg": tariff,
    "fx-market.svg": fx_market,
    "fx-depreciation.svg": fx_depreciation,
}

if __name__ == "__main__":
    # make the folder if it doesn't exist, then run every function and save its svg
    os.makedirs(OUT, exist_ok=True)
    for name, fn in DIAGRAMS.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", name)
    print(f"\n{len(DIAGRAMS)} diagrams generated in {OUT}")
