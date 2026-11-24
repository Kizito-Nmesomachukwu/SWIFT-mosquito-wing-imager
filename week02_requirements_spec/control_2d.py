"""2D block diagram of the imager's control loop on a dark background: signal and data wires,
DC power cables and the mechanical linkage that closes the loop through the limit switch.
Coordinates are in pixels of a 1400 x 700 canvas, with y pointing down.
Usage: python control_2d.py   (writes control_architecture_2d.png)"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Polygon

BG, CARD, EDGE, ORANGE = "#000000", "#1a1a1a", "#4a4a4a", "#e07b1a"
CYAN, WHITE, GREY = "#3fb6f0", "#ffffff", "#b5b5b5"

fig = plt.figure(figsize=(14, 7), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1400); ax.set_ylim(700, 0); ax.axis("off")
fig.patch.set_facecolor(BG)

# faint star field and outer frame
rng = np.random.default_rng(3)
ax.scatter(rng.uniform(0, 1400, 900), rng.uniform(0, 700, 900), s=rng.uniform(0.2, 1.6, 900),
           c="#ffffff", alpha=0.25, linewidths=0)
ax.add_patch(FancyBboxPatch((18, 18), 1364, 664, boxstyle="round,pad=0,rounding_size=8",
                            fc="none", ec="#2c2c2c", lw=1.5))
ax.text(42, 48, "Control architecture of the imager (closed loop)", color=WHITE, fontsize=17,
        fontweight="bold", va="center")
ax.plot([42, 625], [70, 70], color="#555555", lw=1.2)


def card(x0, y0, x1, y1, title, sub, ec=EDGE, tcolor=WHITE, scolor=GREY, ty=None, tx=None):
    # One part: rounded dark card, bold name and a short line on its job.
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=10",
                                fc=CARD, ec=ec, lw=1.6, zorder=2))
    ty = y1 - 55 if ty is None else ty
    tx = (x0 + x1) / 2 if tx is None else tx  # top cards keep their icon on the left, text on the right
    ax.text(tx, ty, title, color=tcolor, fontsize=13.5, fontweight="bold", ha="center", va="center", zorder=5)
    ax.text(tx, ty + 25, sub, color=scolor, fontsize=9, ha="center", va="center", zorder=5)


def wave(x0, y0, x1, y1, colors, amp=4.0, cycles=2.0, spread=3.0, lw=2.0):
    # A bundle of slightly offset sine-shaped wires between two points, one line per colour.
    t = np.linspace(0, 1, 120)
    dx, dy = x1 - x0, y1 - y0
    L = np.hypot(dx, dy); nx, ny = -dy / L, dx / L
    for k, c in enumerate(colors):
        off = (k - (len(colors) - 1) / 2) * spread
        s = amp * np.sin(2 * np.pi * cycles * t + k * 0.6)
        ax.plot(x0 + dx * t + nx * (s + off), y0 + dy * t + ny * (s + off), color=c, lw=lw, zorder=3,
                solid_capstyle="round")


def plug(x, y, w=10, h=14, c="#2b2b2b"):
    # Small connector block where a cable meets a card.
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=c, ec="#555555", lw=0.8, zorder=4))


def arrow(p, q, color=CYAN, both=False, lw=1.3):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>", mutation_scale=11,
                                 color=color, lw=lw, zorder=6))


def tag(x, y, text, color=CYAN, size=10, bold=True):
    # Cable and motion names in italics next to their arrows.
    ax.text(x, y, text, color=color, fontsize=size, style="italic", fontweight="bold" if bold else "normal",
            ha="center", va="center", zorder=6)


# ---------------------------------------------------------------- cards
card(30, 268, 215, 418, "HQ camera", "takes the images")
card(305, 268, 505, 418, "Raspberry Pi", "runs sequence, saves images")
card(595, 268, 805, 418, "ESP32", "real-time motor control")
card(895, 268, 1100, 418, "Motor driver", "steps to coil current")
card(1185, 268, 1370, 418, "Stepper motor", "turns the gear")
card(305, 85, 500, 185, "5 V supply", "USB-C", ec=ORANGE, tcolor="#ffe8c8", scolor=ORANGE, ty=124, tx=427)
card(595, 85, 805, 190, "LED", "illumination from below", ty=124, tx=727)
card(895, 85, 1100, 185, "12 V supply", "motor power", ec=ORANGE, tcolor="#ffe8c8", scolor=ORANGE, ty=124, tx=1023)
card(595, 515, 805, 645, "Limit switch", "marks position zero")
card(1165, 515, 1370, 645, "Rack and holder", "slides move to the camera")

# ---------------------------------------------------------------- icons
# HQ camera: blue board with a lens
ax.add_patch(FancyBboxPatch((96, 290), 52, 50, boxstyle="round,pad=0,rounding_size=3", fc="#1d4fa8", ec="#5b8be0", lw=1, zorder=4))
for cx, cy in ((101, 295), (143, 295), (101, 335), (143, 335)):
    ax.add_patch(Circle((cx, cy), 2, fc="#e8c040", zorder=5))
ax.add_patch(Circle((122, 315), 16, fc="#111111", ec="#888888", lw=1.2, zorder=5))
ax.add_patch(Circle((122, 315), 9, fc="#24364f", ec="#6a87b5", lw=1, zorder=6))
ax.add_patch(Circle((118, 311), 2.5, fc="#9fc4ff", zorder=7))
# Raspberry Pi: green board with header, chip and ports
ax.add_patch(FancyBboxPatch((363, 290), 84, 50, boxstyle="round,pad=0,rounding_size=4", fc="#1f9b4a", ec="#5fd18a", lw=1, zorder=4))
ax.add_patch(Rectangle((370, 293), 50, 7, fc="#222222", zorder=5))
ax.add_patch(Rectangle((388, 308), 18, 18, fc="#d8d8d8", ec="#888888", zorder=5))
for py in (296, 316):
    ax.add_patch(Rectangle((432, py), 16, 15, fc="#c8c8c8", ec="#888888", zorder=5))
# ESP32: shielded module with pins
ax.add_patch(Rectangle((672, 286), 56, 56, fc="#151515", ec="#777777", lw=1, zorder=4))
ax.add_patch(Rectangle((682, 296), 36, 32, fc="#bcbcbc", ec="#888888", zorder=5))
for i in range(8):
    ax.add_patch(Rectangle((675, 290 + i * 6.5), 3, 3, fc="#e8c040", zorder=5))
    ax.add_patch(Rectangle((722, 290 + i * 6.5), 3, 3, fc="#e8c040", zorder=5))
# motor driver: red board with blue heat sink
ax.add_patch(Rectangle((973, 288), 48, 52, fc="#c42a22", ec="#ff6b5e", lw=1, zorder=4))
ax.add_patch(Rectangle((983, 300), 28, 28, fc="#2e6fe0", ec="#9cc0ff", lw=1, zorder=5))
for i in range(5):
    ax.plot([987 + i * 5, 987 + i * 5], [302, 326], color="#9cc0ff", lw=0.8, zorder=6)
ax.add_patch(Circle((997, 293), 2.5, fc="#ffffff", zorder=6))
# stepper motor: square body with rotor
ax.add_patch(FancyBboxPatch((1253, 290), 48, 48, boxstyle="round,pad=0,rounding_size=4", fc="#2c2c2c", ec="#aaaaaa", lw=1.2, zorder=4))
ax.add_patch(Circle((1277, 314), 15, fc="#bbbbbb", ec="#666666", zorder=5))
ax.add_patch(Circle((1277, 314), 6, fc="#333333", zorder=6))
ax.add_patch(Circle((1277, 314), 2.5, fc="#dddddd", zorder=7))
for cx, cy in ((1258, 295), (1296, 295), (1258, 333), (1296, 333)):
    ax.add_patch(Circle((cx, cy), 1.6, fc="#dddddd", zorder=5))
# 5 V supply: plug with a lightning bolt
ax.add_patch(FancyBboxPatch((328, 115), 30, 38, boxstyle="round,pad=0,rounding_size=3", fc="none", ec=ORANGE, lw=1.4, zorder=4))
for px in (336, 350):
    ax.add_patch(Rectangle((px - 2, 107), 4, 9, fc=ORANGE, zorder=4))
ax.add_patch(Polygon([(345, 122), (337, 136), (343, 136), (340, 147), (350, 131), (344, 131), (348, 122)], fc=ORANGE, zorder=5))
# LED: glowing bulb
ax.add_patch(Circle((635, 125), 16, fc="#ffe48a", ec="#e0b030", lw=1.2, zorder=4))
ax.add_patch(Rectangle((628, 139), 14, 12, fc="#bbbbbb", ec="#888888", zorder=4))
ax.plot([630, 633, 637, 640], [127, 121, 127, 121], color="#c07a10", lw=1, zorder=5)
for a in np.linspace(-150, -30, 5):
    r = np.radians(a)
    ax.plot([635 + 21 * np.cos(r), 635 + 27 * np.cos(r)], [125 + 21 * np.sin(r), 125 + 27 * np.sin(r)], color="#e0b030", lw=1.4, zorder=4)
# 12 V supply: power unit with switch and lamps
ax.add_patch(FancyBboxPatch((913, 113), 40, 40, boxstyle="round,pad=0,rounding_size=3", fc="none", ec=ORANGE, lw=1.4, zorder=4))
for i, yy in enumerate((122, 130, 138)):
    ax.plot([919, 931], [yy, yy], color=ORANGE, lw=1.2, zorder=5)
ax.add_patch(Circle((943, 124), 3, fc="#e0302a", zorder=5)); ax.add_patch(Circle((943, 138), 3, fc="#888888", zorder=5))
# limit switch: body, lever and pins
ax.add_patch(Rectangle((677, 545), 44, 24, fc="#2a2a2a", ec="#bbbbbb", lw=1, zorder=4))
ax.plot([681, 718], [544, 535], color="#cccccc", lw=1.6, zorder=5)
ax.add_patch(Circle((722, 535), 4, fc="#e0302a", zorder=6))
for cx in (685, 713):
    ax.add_patch(Circle((cx, 557), 2, fc="#cccccc", zorder=5))
for px in (686, 699, 712):
    ax.plot([px, px], [569, 576], color="#e8c040", lw=1.5, zorder=5)
# rack and holder: slide holder on a toothed rack
ax.add_patch(Rectangle((1234, 560), 68, 10, fc="#555555", zorder=4))
for i in range(7):
    ax.add_patch(Rectangle((1238 + i * 9.5, 556), 4, 4, fc="#dddddd", zorder=5))
ax.add_patch(FancyBboxPatch((1250, 538), 36, 20, boxstyle="round,pad=0,rounding_size=2", fc="#2f8be0", ec="#9cd0ff", lw=1, zorder=5))
ax.add_patch(Rectangle((1256, 532), 24, 6, fc="#9cd0ff", zorder=5))

# ---------------------------------------------------------------- cables (signal, power, linkage)
wave(218, 343, 302, 343, ["#f0a040", "#ffffff", "#3fa0f0", "#f0a040", "#ffffff", "#3fa0f0"], amp=2, cycles=1, spread=2.2, lw=1.4)
plug(218, 343); plug(302, 343)
wave(508, 343, 592, 343, ["#2a2a2a", "#555555"], amp=4, cycles=1, spread=2.5, lw=2.4)
plug(508, 343); plug(592, 343)
wave(808, 343, 892, 343, ["#a050f0", "#3fb6f0", "#5070f0"], amp=5, cycles=1.5, spread=2.5, lw=1.8)
plug(808, 343); plug(892, 343)
wave(1103, 343, 1182, 343, ["#f05050", "#40c060", "#f0c040", "#4080f0"], amp=4, cycles=1, spread=3.2, lw=1.8)
plug(1103, 343, h=24, c="#888888")
wave(403, 185, 403, 266, ["#e02828", "#222222"], amp=5, cycles=1.5, spread=3, lw=2)
plug(403, 264, c="#2b2b2b")
wave(700, 190, 700, 266, ["#f0b030", "#2a80e0"], amp=4, cycles=1.5, spread=3, lw=2)
plug(700, 192); plug(700, 264)
wave(998, 185, 998, 266, ["#f06020", "#e02828", "#222222"], amp=4, cycles=1.5, spread=3, lw=2)
plug(998, 264, c="#2a8a3a")
wave(700, 420, 700, 513, ["#2a80e0", "#888888"], amp=4, cycles=1.5, spread=3, lw=2)
plug(700, 422); plug(700, 511)
# mechanical linkage: threaded rod from motor to holder, push rod from holder to switch
yy = np.linspace(420, 513, 40)
ax.plot([1276] * 40, yy, color="#777777", lw=6, zorder=3)
for y in yy[::2]:
    ax.plot([1272, 1280], [y, y + 2], color="#cccccc", lw=1, zorder=4)
ax.add_patch(Rectangle((806, 581), 358, 9, fc="#3a3a3a", ec="#666666", lw=0.8, zorder=3))
for x in np.arange(812, 1158, 20):
    ax.plot([x, x + 10], [585.5, 585.5], color="#999999", lw=1.5, zorder=4)

# ---------------------------------------------------------------- arrows and labels
arrow((235, 316), (285, 316), both=True); tag(260, 302, "CSI"); tag(260, 367, "images", color=GREY, bold=False)
arrow((525, 316), (577, 316), both=True); tag(551, 302, "USB serial"); tag(551, 369, "commands", color=GREY, bold=False)
arrow((825, 315), (877, 315)); tag(850, 301, "STEP / DIR")
arrow((1120, 315), (1166, 315)); tag(1143, 301, "coils")
arrow((674, 250), (674, 207)); tag(740, 229, "PWM")
arrow((674, 495), (674, 437)); tag(762, 467, "home signal")
arrow((376, 205), (376, 249), color=ORANGE); tag(438, 227, "5 V", color=ORANGE)
arrow((972, 205), (972, 249), color=ORANGE); tag(1040, 227, "12 V", color=ORANGE)
arrow((1256, 435), (1256, 503), color="#dddddd"); tag(1328, 469, "gear and rack", color="#dddddd", size=9)
arrow((1135, 566), (828, 566), color="#dddddd"); tag(985, 550, "holder reaches home", color="#dddddd")

# ---------------------------------------------------------------- legend
ax.add_patch(FancyBboxPatch((32, 538), 320, 106, boxstyle="round,pad=0,rounding_size=8", fc="#141414", ec="#333333", lw=1.2, zorder=2))
t = np.linspace(0, 1, 60)
for k, c in enumerate(("#3fb6f0", "#a050f0")):
    ax.plot(52 + 44 * t, 561 + 3 * np.sin(2 * np.pi * t + k) + k * 3, color=c, lw=2, zorder=3)
for k, c in enumerate(("#e02828", "#444444")):
    ax.plot(52 + 44 * t, 589 + 3 * np.sin(2 * np.pi * t + k) + k * 3, color=c, lw=2, zorder=3)
ax.add_patch(Rectangle((52, 615), 44, 6, fc="#3a3a3a", ec="#777777", lw=0.8, zorder=3))
ax.plot([56, 92], [618, 618], color="#999999", lw=1.2, ls=(0, (3, 2)), zorder=4)
for y, text in ((561, "signal / data wire"), (589, "DC power cable"), (617, "mechanical motion / linkage")):
    ax.text(112, y, text, color="#dddddd", fontsize=10, va="center", zorder=3)

fig.savefig("control_architecture_2d.png", facecolor=BG)
print("saved control_architecture_2d.png")
