"""Crops the 3D render from control_scene.py and adds part names and cable names.
Usage: python label_ctrl.py <render.png> <out.png>
Label positions are pixel positions in an 1800 x 1100 render; another size needs new positions."""
import os, sys, math
from PIL import Image, ImageDraw, ImageFont

SRC, DST = sys.argv[1], sys.argv[2]
OX, OY = 120, 170                      # top-left corner of the crop in the render
S = 2                                  # drawn at twice the size, then reduced, for smooth edges
im = Image.open(SRC).convert("RGB").crop((OX, OY, OX + 1620, OY + 760))
W, H = im.size
big = im.resize((W * S, H * S), Image.LANCZOS)
d = ImageDraw.Draw(big)


def find_font(name):
    # DejaVu is taken from the system font folder if present, otherwise from the copy inside matplotlib.
    path = os.path.join("/usr/share/fonts/truetype/dejavu", name)
    if os.path.exists(path):
        return path
    import matplotlib
    return os.path.join(matplotlib.get_data_path(), "fonts", "ttf", name)


font = ImageFont.truetype(find_font("DejaVuSans-Bold.ttf"), 30 * S)
small = ImageFont.truetype(find_font("DejaVuSans-Oblique.ttf"), 22 * S)
FILL, EDGE, NAVY = (238, 244, 252), (47, 79, 127), (31, 58, 104)
P = lambda x, y: ((x - OX) * S, (y - OY) * S)   # render pixel -> position on the enlarged crop


def arrow(p, q):
    # Straight line with a filled triangular head; the head points along the line direction.
    d.line([p, q], fill=NAVY, width=3 * S)
    ang = math.atan2(q[1] - p[1], q[0] - p[0]); L, w = 16 * S, 0.42
    d.polygon([q, (q[0] - L * math.cos(ang - w), q[1] - L * math.sin(ang - w)),
               (q[0] - L * math.cos(ang + w), q[1] - L * math.sin(ang + w))], fill=NAVY)


def label(text, anchor, box):
    # Rounded box at 'box' with an arrow to 'anchor', leaving from the side that faces the part.
    bx, by = P(*box); ax, ay = P(*anchor)
    tb = d.textbbox((0, 0), text, font=font); pw, ph = 18 * S, 10 * S
    x0, y0, x1, y1 = bx, by, bx + tb[2] + 2 * pw, by + tb[3] + 2 * ph
    if ax > x1: p = (x1, (y0 + y1) / 2)
    elif ax < x0: p = (x0, (y0 + y1) / 2)
    elif ay > y1: p = ((x0 + x1) / 2, y1)
    else: p = ((x0 + x1) / 2, y0)
    arrow(p, (ax, ay))
    d.rounded_rectangle((x0, y0, x1, y1), radius=14 * S, fill=FILL, outline=EDGE, width=3 * S)
    d.text((x0 + pw, y0 + ph - tb[1]), text, font=font, fill=NAVY)


def cable(text, pos):
    # Cable names in grey italics on a white patch, placed next to the cable they name.
    x, y = P(*pos); tb = d.textbbox((0, 0), text, font=small)
    d.rounded_rectangle((x - 6 * S, y - 4 * S, x + tb[2] + 6 * S, y + tb[3] + 4 * S), radius=6 * S, fill=(255, 255, 255))
    d.text((x, y - tb[1] + 2 * S), text, font=small, fill=(80, 80, 80))


# part name, point on the part, top-left corner of the label box (render pixels)
label("Raspberry Pi", (300, 565), (160, 660))
label("HQ camera", (440, 345), (160, 230))
label("ESP32", (790, 548), (690, 650))
label("LED", (820, 362), (620, 250))
label("Driver", (1125, 548), (1060, 400))
label("Motor", (1440, 520), (1520, 360))
label("Switch", (1135, 738), (930, 820))
label("12 V supply", (1500, 770), (1320, 860))
cable("CSI ribbon", (360, 420))
cable("USB serial", (560, 600))
cable("PWM", (690, 420))
cable("STEP / DIR", (930, 505))
cable("Coils", (1230, 498))
cable("Home signal", (935, 610))
cable("Power", (1300, 650))
big.resize((W, H), Image.LANCZOS).save(DST)
print("saved", DST)
