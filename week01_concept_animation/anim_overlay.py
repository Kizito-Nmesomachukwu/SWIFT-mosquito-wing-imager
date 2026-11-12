"""Adds labels, captions, the capture flash and the captured-image inset to every frame.
Usage: python anim_overlay.py <in_dir> <out_dir> <anchors.json> <timeline.json>"""
import sys, os, json, math, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter

IN, OUT, ANC, TL = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
T = json.load(open(TL))  # same timing as the 3D scene
P, FALL = T["parts"], 1.4
os.makedirs(OUT, exist_ok=True)
FPS = 24
S = 2  # I draw the overlay at double size, then shrink it so the edges stay smooth
a = {k: (v[0] * S, v[1] * S) for k, v in json.load(open(ANC)).items()}
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(BOLD, 15 * S)
capfont = ImageFont.truetype(BOLD, 17 * S)
FILL, EDGE, NAVY = (238, 244, 252), (47, 79, 127), (31, 58, 104)

# text, anchor, box top-left (x, y), time it shows up (s): just after its part lands
land = lambda n: P[n] + FALL
LABELS = [
    ("PMMA belt", "belt", (20, 430), land("belt")),
    ("Glass window", "window", (20, 255), land("window")),
    ("White LED", "led", (120, 495), land("led")),
    ("Light-tight housing", "housing", (20, 45), land("housing")),
    ("HQ Raspberry Pi camera", "camera", (20, 90), land("camera")),
    ("Spacer tube", "spacer", (20, 135), land("lens")),
    ("Lens", "lens", (20, 180), land("lens")),
    ("Raspberry Pi", "pi", (640, 110), land("pi")),
    ("Motor", "motor", (830, 300), land("motor")),
    ("Drive belt", "drivebelt", (640, 495), land("motor")),
    ("ESP32", "esp32", (300, 495), land("electronics")),
    ("Motor driver", "driver", (440, 495), land("electronics")),
    ("Wing on PDMS", "wing", (20, 300), T["wings_end"] - 0.3),
]
MOVES, MT, ST = T["moves"], T["move_time"], T["stop_time"]
LABELS_OFF = T["belt"] - 0.2


def caption(t):
    if t < T["wings"]: return "Step 1: the parts come together"
    if t < T["led"]: return "Step 2: wings on PDMS go onto the belt"
    if t < T["belt"]: return "Step 3: the LED switches on and stays on"
    for k, t0 in enumerate(MOVES):
        if t0 <= t < t0 + MT: return "ESP32 \u2192 driver \u2192 motor turns the belt"
        if t0 + MT <= t < t0 + MT + ST: return f"Wing under the lens: camera captures image {k + 1} of 3"
    return "Images go to the Raspberry Pi for AI classification"


def box_with_arrow(d, text, key, bx, by, alpha):
    bx, by = bx * S, by * S
    tb = d.textbbox((0, 0), text, font=font)
    pw, ph = 9 * S, 5 * S
    x0, y0, x1, y1 = bx, by, bx + tb[2] + 2 * pw, by + tb[3] + 2 * ph
    ax, ay = a[key]
    if ax > x1: p = (x1, (y0 + y1) / 2)
    elif ax < x0: p = (x0, (y0 + y1) / 2)
    elif ay > y1: p = ((x0 + x1) / 2, y1)
    else: p = ((x0 + x1) / 2, y0)
    A = int(255 * alpha)
    d.line([p, (ax, ay)], fill=NAVY + (A,), width=2 * S)
    ang = math.atan2(ay - p[1], ax - p[0]); L, w = 9 * S, 0.42
    d.polygon([(ax, ay), (ax - L * math.cos(ang - w), ay - L * math.sin(ang - w)),
               (ax - L * math.cos(ang + w), ay - L * math.sin(ang + w))], fill=NAVY + (A,))
    d.rounded_rectangle((x0, y0, x1, y1), radius=8 * S, fill=FILL + (A,), outline=EDGE + (A,), width=2 * S)
    d.text((x0 + pw, y0 + ph - tb[1]), text, font=font, fill=NAVY + (A,))


def make_inset(kind):
    # simple bright-field pictures of three different wings
    import colorsys
    w, h = 200 * S, 150 * S
    im = Image.new("RGB", (w, h), (236, 232, 222))
    g = ImageDraw.Draw(im)
    for r in range(0, 120 * S, 4):  # slight fall-off towards the corners
        c = int(236 - 20 * (r / (120 * S)) ** 2)
        g.ellipse((w / 2 - (120 * S - r) * 1.3, h / 2 - (120 * S - r), w / 2 + (120 * S - r) * 1.3, h / 2 + (120 * S - r)),
                  outline=(c, c - 3, c - 12))
    box = (22 * S, 52 * S, 178 * S, 98 * S)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).ellipse(box, fill=255)
    if kind == "amber":
        fill = Image.new("RGB", (w, h), (205, 165, 95)); vein = (80, 55, 25); edge = (120, 85, 40)
    elif kind == "blue":
        fill = Image.new("RGB", (w, h), (150, 178, 210)); vein = (35, 55, 95); edge = (60, 85, 130)
    else:  # rainbow sheen across the membrane
        fill = Image.new("RGB", (w, h)); fp = fill.load()
        for x in range(w):
            for y in range(h):
                hh = ((x + 0.6 * y) / (w * 0.9)) % 1.0
                r_, g_, b_ = colorsys.hsv_to_rgb(hh, 0.35, 0.93)
                fp[x, y] = (int(r_ * 255), int(g_ * 255), int(b_ * 255))
        vein = (70, 60, 70); edge = (90, 80, 95)
    g = ImageDraw.Draw(fill)  # veins go on the wing layer so the outline clips them
    if kind == "amber":  # straight, parallel veins
        for yy in (60, 67, 74, 81, 88):
            g.line([(30 * S, yy * S), (170 * S, yy * S)], fill=vein, width=2 * S)
    elif kind == "blue":  # veins fanning out from the base, with forks
        for end in (56, 64, 72, 80, 88, 95):
            mx, my = 110, 75 + (end - 75) * 0.6
            g.line([(26 * S, 75 * S), (mx * S, my * S), (172 * S, end * S)], fill=vein, width=2 * S)
            g.line([(mx * S, my * S), (165 * S, (end + 4) * S)], fill=vein, width=S)
    else:  # curved veins and a few cross veins
        for k, yy in enumerate((61, 69, 77, 85)):
            pts = [((30 + i * 7) * S, (yy + 3 * math.sin(i / 3.0 + k)) * S) for i in range(21)]
            g.line(pts, fill=vein, width=2 * S)
        for xx in (70, 105, 140):
            g.line([(xx * S, 60 * S), ((xx + 4) * S, 90 * S)], fill=vein, width=S)
        hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))  # a little shine
        ImageDraw.Draw(hl).ellipse((60 * S, 58 * S, 120 * S, 70 * S), fill=(255, 255, 255, 90))
        fill = Image.alpha_composite(fill.convert("RGBA"), hl.filter(ImageFilter.GaussianBlur(4 * S))).convert("RGB")
    im.paste(fill, (0, 0), mask)
    ImageDraw.Draw(im).ellipse(box, outline=edge, width=2 * S)
    return im


INSETS = [make_inset("amber"), make_inset("blue"), make_inset("rainbow")]
frames = sorted(glob.glob(os.path.join(IN, "*.png")))
jobs = [(i, fp, i / FPS) for i, fp in enumerate(frames)]
if os.environ.get("TEST_T"):  # quick check of single moments on one frame
    jobs = [(int(float(x) * 100), frames[0], float(x)) for x in os.environ["TEST_T"].split(",")]
for i, fp, t in jobs:
    base = Image.open(fp).convert("RGB")
    W, H = base.size
    ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # labels appear as each part lands and fade out once the system starts running
    for text, key, (bx, by), t_on in LABELS:
        al = min(max((t - t_on) / 0.3, 0), 1) * min(max((LABELS_OFF - t) / 0.5, 0), 1)
        if al > 0: box_with_arrow(d, text, key, bx, by, al)
    if t >= T["end"]:
        box_with_arrow(d, "Raspberry Pi", "pi", 640, 110, min((t - T["end"]) / 0.3, 1))

    # capture flash at the start of each stop
    flash = 0.0
    for t0 in MOVES:
        tf = t0 + MT + 0.15
        if tf <= t < tf + 0.5: flash = 1 - (t - tf) / 0.5
    if flash > 0:
        gl = Image.new("RGBA", ov.size, (0, 0, 0, 0)); gg = ImageDraw.Draw(gl)
        lx, ly = a["lensfront"]; wx, wy = a["wingspot"]
        for rad, val in [(110, 90), (70, 170), (35, 255)]:
            for cx, cy in ((lx, ly), (wx, wy)):
                gg.ellipse((cx - rad * S, cy - rad * S, cx + rad * S, cy + rad * S), fill=(255, 255, 255, int(val * flash)))
        gl = gl.filter(ImageFilter.GaussianBlur(18 * S))
        ov = Image.alpha_composite(ov, gl); d = ImageDraw.Draw(ov)
        d.rectangle((0, 0, W * S, H * S), fill=(255, 255, 255, int(70 * flash)))

    # the captured image stays up until the belt moves again
    for k, t0 in enumerate(MOVES):
        if t0 + MT + 0.15 <= t < t0 + MT + ST:
            al = min((t - t0 - MT - 0.15) / 0.25, 1)
            x0, y0 = 730 * S, 190 * S
            title = f"Captured image {k + 1}/3"
            tb = d.textbbox((0, 0), title, font=font)
            d.rounded_rectangle((x0 - 8 * S, y0 - 30 * S, x0 + 208 * S, y0 + 158 * S), radius=10 * S,
                                fill=FILL + (int(255 * al),), outline=EDGE + (int(255 * al),), width=2 * S)
            d.text((x0, y0 - 25 * S - tb[1]), title, font=font, fill=NAVY + (int(255 * al),))
            ins = INSETS[k].convert("RGBA"); ins.putalpha(int(255 * al))
            ov.alpha_composite(ins, (x0, y0)); d = ImageDraw.Draw(ov)

    # caption at the top
    cap = caption(t)
    tb = d.textbbox((0, 0), cap, font=capfont)
    cw = tb[2] + 32 * S
    cx0 = (W * S - cw) / 2
    d.rounded_rectangle((cx0, 6 * S, cx0 + cw, 6 * S + tb[3] + 14 * S), radius=10 * S, fill=NAVY + (235,))
    d.text((cx0 + 16 * S, 6 * S + 7 * S - tb[1]), cap, font=capfont, fill=(255, 255, 255, 255))

    ov = ov.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB").save(os.path.join(OUT, f"o_{i:04d}.png"))
print("overlaid", len(frames))
