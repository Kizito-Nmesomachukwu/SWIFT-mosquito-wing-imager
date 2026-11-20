"""2D block diagram of the imager's control loop: signals (navy), power (orange, dashed) and the
mechanical feedback path (grey) that closes the loop through the limit switch.
Usage: python control_2d.py   (writes control_architecture_2d.png)"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

FILL, EDGE, NAVY, GREY = "#eef4fc", "#2f4f7f", "#1f3a68", "#555555"
POWER, MECH = "#d0782f", "#8a8a8a"
fig, ax = plt.subplots(figsize=(15, 6.6), dpi=200)
ax.set_xlim(0, 17); ax.set_ylim(-1.0, 6.3); ax.axis("off")

def box(x, y, title, sub, w=2.3, h=1.0, fc=FILL, ec=EDGE):
    # One part: bold name, and a short line on its job underneath.
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc=fc, ec=ec, lw=1.8))
    ax.text(x, y + 0.14, title, ha="center", va="center", fontsize=12, fontweight="bold", color=NAVY)
    ax.text(x, y - 0.22, sub, ha="center", va="center", fontsize=8.5, color=GREY)

def arrow(p, q, color=NAVY, ls="-", lw=1.7, both=False):
    # Double-headed arrows mark two-way links, such as commands down and replies back.
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>", mutation_scale=16,
                                 color=color, lw=lw, linestyle=ls))

def note(x, y, text, ha="center", va="center", color=GREY):
    ax.text(x, y, text, ha=ha, va=va, fontsize=9, style="italic", color=color)

# parts
box(1.5, 2.6, "HQ camera", "takes the images")
box(5.0, 2.6, "Raspberry Pi", "runs sequence, saves images", w=2.6)
box(8.6, 2.6, "ESP32", "real-time motor control")
box(12.1, 2.6, "Motor driver", "steps to coil current")
box(15.4, 2.6, "Stepper motor", "turns the gear", w=2.2)
box(5.0, 4.9, "5 V supply", "USB-C", fc="#fdf1e6", ec=POWER)
box(12.1, 4.9, "12 V supply", "motor power", fc="#fdf1e6", ec=POWER)
box(8.6, 4.9, "LED", "illumination from below")
box(15.4, 0.3, "Rack and holder", "slides move to the camera", w=2.6, fc="#f3f3f3", ec=MECH)
box(8.6, 0.3, "Limit switch", "marks position zero")

# signals (navy)
arrow((2.7, 2.6), (3.65, 2.6), both=True); note(3.18, 2.95, "CSI")
note(3.18, 2.28, "images")
arrow((6.35, 2.6), (7.4, 2.6), both=True); note(6.88, 2.95, "USB serial")
note(6.88, 2.28, "commands")
arrow((9.8, 2.6), (10.9, 2.6)); note(10.35, 2.95, "STEP / DIR")
arrow((13.3, 2.6), (14.25, 2.6)); note(13.78, 2.95, "coils")
arrow((8.6, 3.1), (8.6, 4.4)); note(8.72, 3.75, "PWM", ha="left")
arrow((8.6, 0.8), (8.6, 2.1)); note(8.72, 1.45, "home signal", ha="left")

# power (orange, dashed)
arrow((5.0, 4.4), (5.0, 3.1), color=POWER, ls="--"); note(5.12, 3.75, "5 V", ha="left", color=POWER)
arrow((12.1, 4.4), (12.1, 3.1), color=POWER, ls="--"); note(12.22, 3.75, "12 V", ha="left", color=POWER)

# mechanical feedback (grey): motor moves the holder, the holder reaches the switch
arrow((15.4, 2.1), (15.4, 0.8), color=MECH, lw=2.4); note(15.52, 1.45, "gear and rack", ha="left", color=MECH)
arrow((14.1, 0.3), (9.75, 0.3), color=MECH, lw=2.4); note(11.9, 0.55, "holder reaches home", color=MECH)

# legend
handles = [Line2D([0], [0], color=NAVY, lw=1.8, label="signal / data"),
           Line2D([0], [0], color=POWER, lw=1.8, ls="--", label="power"),
           Line2D([0], [0], color=MECH, lw=2.4, label="mechanical motion")]
ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, 0.04), frameon=False, fontsize=9.5)
ax.text(0.1, 6.25, "Control architecture of the imager (closed loop)", fontsize=13, fontweight="bold",
        color=NAVY, va="top")
ax.text(0.15, -0.95, "The ESP32 is powered from the Raspberry Pi over the same USB cable.", fontsize=9, style="italic", color=GREY)
fig.savefig("control_architecture_2d.png", bbox_inches="tight", facecolor="white")
