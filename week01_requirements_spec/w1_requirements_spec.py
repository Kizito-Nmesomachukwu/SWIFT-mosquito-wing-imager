"""
WEEK 1: REQUIREMENTS SPEC V1 FOR A LOW-COST MOSQUITO WING IMAGER

Project: SWIFT: A Low-Cost Standardised Imaging System for AI-Based Mosquito Wing Classification
Course:  Frugal Photonics for Global Health, WS 2026/27, FSU Jena
Author:  Kizito Nmesomachukwu ODIZILIKE

SCRIPT PURPOSE/FUNCTION:
  The aim is to know how good the optics really need to be. The classifier from
  BNITM only sees each wing at 300 x 300 pixels [1], so we work backwards from
  that to a field of view (FOV), a magnification m, a minimum NA (the smallest 
  numerical aperture that resolves it) and a test target.
  At the end, we plot the required resolution against wing length.  

USAGE:
  python3 w1_requirements_spec.py
  Prints a table and saves w1_required_resolution.png next to this file.
  Needs numpy and matplotlib.

References:
  [1] Nolte K, Sauer FG, Baumbach J, Kollmannsberger P, Lins C, Luehken R (2024).
      Robust mosquito species identification from diverse body and wing images
      using deep learning. Parasites & Vectors 17:372.
      doi:10.1186/s13071-024-06459-3
  [2] Nolte K, Agboli E, et al. (2025). Comprehensive mosquito wing image
      repository for advancing research on geometric morphometric- and AI-based
      identification. Scientific Data 12:715. doi:10.1038/s41597-025-05043-3
  [3] Schneider JR, Morrison AC, Astete H, Scott TW, Wilson ML (2004).
      Adult size and distribution of Aedes aegypti (Diptera: Culicidae)
      associated with larval habitats in Iquitos, Peru.
      J. Med. Entomol. 41(4):634-642. doi:10.1603/0022-2585-41.4.634
  [4] Raspberry Pi Ltd. Camera hardware documentation, HQ Camera
      (Sony IMX477) specifications.
      https://www.raspberrypi.com/documentation/accessories/camera.html
  [5] Hecht E (2017). Optics, 5th ed. Pearson.
  [6] Goodman JW (2005). Introduction to Fourier Optics, 3rd ed.
      Roberts & Company.
  [7] Inoue S, Spring KR (1997). Video Microscopy: The Fundamentals, 2nd ed.
      Plenum Press, New York.
  [8] MIL-STD-150A (1959). Photographic lenses. US Department of Defense.
      (defines the USAF 1951 resolution target)
  [9] Shannon CE (1949). Communication in the presence of noise.
      Proc. IRE 37(1):10-21.

Anything marked ASSUMPTION is our own design choice, not a fact from a paper.
"""

import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ------------------------------------------------------------------
# BLOCK 1: INPUTS & FIXED PARAMETERS
# ------------------------------------------------------------------

# The CNN gets images cropped, padded to a square and resized to 300 x 300 px [1]
CNN_INPUT_PX = 300

# Benchmark camera on the Olympus SZ61 stereo microscope (DP23) [2]
BENCH_SENSOR_PX = (3088, 2076)

# Wing length of Aedes aegypti females reared from pupae, in mm [3]
WING_MIN_MM = 1.67
WING_MAX_MM = 3.83

# Raspberry Pi HQ camera sensor [4]
PI_SENSOR_W_MM = 6.287      # active area width
PI_SENSOR_H_MM = 4.712      # active area height
PI_SENSOR_PX = (4056, 3040)
PI_PIXEL_UM = 1.55          # pixel pitch

# ASSUMPTION: 20 % extra room so the wing does not have to sit perfectly centred
FOV_MARGIN = 0.20

# ASSUMPTION: white LED, so I design for green light in the middle of the spectrum
WAVELENGTH_UM = 0.55


# ------------------------------------------------------------------
# BLOCK 2: DEFINED SMALL HELPER FUNCTIONS:
# ------------------------------------------------------------------

# 2.1
def cnn_spacing_um(wing_mm):
    """How much of the wing one CNN pixel covers, in micrometres.
    The wing fills the 300 px frame along its long axis [1]."""
    return wing_mm * 1000 / CNN_INPUT_PX

# 2.2
def nyquist_lpmm(spacing_um):
    """Highest spatial frequency a grid with this spacing can carry [9].
    One line pair needs two pixels, so f = 1 / (2 * spacing)."""
    return 1000 / (2 * spacing_um)

# 2.3
def required_lpmm(wing_mm):
    """Resolution the optics must deliver for a wing of this length.
    Same as nyquist_lpmm(cnn_spacing_um(L)), which simplifies to 150 / L."""
    return nyquist_lpmm(cnn_spacing_um(wing_mm))

# 2.4
def incoherent_cutoff_lpmm(na, wavelength_um):
    """Above this frequency a diffraction limited lens passes no contrast
    at all, f_c = 2 NA / lambda, for incoherent light [6]."""
    return 2 * na / (wavelength_um / 1000)

# 2.5 
def diffraction_mtf(f_lpmm, na, wavelength_um):
    """Contrast (MTF) of a perfect lens with a round aperture [6].
    nu is the frequency as a fraction of the cutoff."""
    nu = f_lpmm / incoherent_cutoff_lpmm(na, wavelength_um)
    if nu >= 1:
        return 0.0
    return (2 / math.pi) * (math.acos(nu) - nu * math.sqrt(1 - nu ** 2))

# 2.6
def usaf_lpmm(group, element):
    """Line pairs per mm of a USAF 1951 target element [8]."""
    return 2 ** (group + (element - 1) / 6)

# 2.7
def smallest_usaf_above(f_lpmm):
    """Find the coarsest USAF element that is still at least f_lpmm."""
    best = None
    for g in range(-2, 10):
        for e in range(1, 7):
            f = usaf_lpmm(g, e)
            if f >= f_lpmm and (best is None or f < best[2]):
                best = (g, e, f)
    return best


# ------------------------------------------------------------------
# BLOCK 3: CALCULATIONS
# ------------------------------------------------------------------

rows = []


def add(name, value, unit, how):
    rows.append((name, value, unit, how))


# 3.1: FOV & MAGNIFICATION 

# The longest wing plus margin has to fit across the sensor width.
fov_mm = WING_MAX_MM * (1 + FOV_MARGIN)
add("Field of view (long axis)", fov_mm, "mm", "max wing x (1 + margin)")

mag = PI_SENSOR_W_MM / fov_mm
add("Magnification (Pi HQ)", mag, "x", "sensor width / FOV")

obj_pixel_um = PI_PIXEL_UM / mag
add("Pixel size at the wing", obj_pixel_um, "um", "pixel pitch / magnification")

add("Camera pixels across largest wing", WING_MAX_MM * 1000 / obj_pixel_um,
    "px", "wing length / pixel at wing")

# 3.2:WHAT THE CLASSIFIER ACTUALLY SEES

# The smallest wing is the hardest case, its details get the fewest pixels.
for wing in (WING_MAX_MM, WING_MIN_MM):
    d = cnn_spacing_um(wing)
    add(f"CNN spacing, {wing} mm wing", d, "um/px", "wing length / 300 [1]")
    add(f"CNN Nyquist, {wing} mm wing", nyquist_lpmm(d), "lp/mm",
        "1 / (2 x spacing) [9]")

f_need = required_lpmm(WING_MIN_MM)
d_min = cnn_spacing_um(WING_MIN_MM)

# 3.3: MINIMUM NA OF THE LENS

# Design rule: the Rayleigh distance 0.61 lambda / NA [5] should not be
# bigger than one CNN pixel at the wing.
na_min = 0.61 * WAVELENGTH_UM / d_min
add("Minimum NA (Rayleigh rule)", na_min, "-", "0.61 lambda / spacing [5]")

# Check that rule with the lens contrast at the CNN Nyquist frequency [6].
# ASSUMPTION: bright field with a condenser that fills the lens aperture,
# so we treat the light as incoherent.
add("Lens cutoff at that NA", incoherent_cutoff_lpmm(na_min, WAVELENGTH_UM),
    "lp/mm", "2 NA / lambda [6]")
add("Lens contrast at CNN Nyquist", diffraction_mtf(f_need, na_min, WAVELENGTH_UM),
    "-", "diffraction MTF, round pupil [6]")

# Absolute lower limit: below this NA the frequency is not passed at all.
add("NA where contrast drops to zero", WAVELENGTH_UM / 1000 * f_need / 2,
    "-", "lambda x f / 2 [6]")

# 3.4: DEPTH OF THE FIELD

# Only the wave optics term lambda / NA^2 from [7] (n = 1 in air).
# The second term depends on the camera pixel and is much smaller here.
add("Depth of field at min NA", WAVELENGTH_UM / na_min ** 2, "um",
    "lambda / NA^2 [7]")

# 3.5: TEST TARGET
g, e, f_usaf = smallest_usaf_above(f_need)
add(f"USAF element to resolve: G{g} E{e}", f_usaf, "lp/mm",
    "smallest element above need [8]")

# 3.6: HOW MUCH ROOM DOES THE CAMERA LEAVE?
pi_nyquist = nyquist_lpmm(obj_pixel_um)
add("Pi HQ Nyquist at the wing", pi_nyquist, "lp/mm",
    "1 / (2 x pixel at wing) [9]")
add("Camera headroom over need", pi_nyquist / f_need, "x",
    "Pi Nyquist / CNN Nyquist")


# ------------------------------------------------------------------
# BLOCK 4: TABLE RETRIEVAL
# ------------------------------------------------------------------

w = max(len(r[0]) for r in rows)
print(f"{'Quantity':<{w}}  {'Value':>10}  {'Unit':<6}  How I got it")
print("-" * (w + 52))
for name, val, unit, how in rows:
    print(f"{name:<{w}}  {val:>10.3g}  {unit:<6}  {how}")

# Quick sanity check on the USAF formula [8]
print(f"\nCheck: USAF G6E4 = {usaf_lpmm(6, 4):.1f} lp/mm, "
      f"G5E3 = {usaf_lpmm(5, 3):.1f} lp/mm")


# ------------------------------------------------------------------
# BLOCK 5: PLOT: REQUIRED RESOLUTION AGAINST WING LENGTH
# ------------------------------------------------------------------

# 5.1
BLUE = "#2a78d6"     # the requirement curve
INK = "#52514e"      # reference lines and text
BAND = "#e8e7e3"     # verified wing range

L = np.linspace(1.5, 4.0, 300)
need = [required_lpmm(x) for x in L]

fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=200)

# 5.2: Grey band: wing lengths we have a verified source for [3]
ax.axvspan(WING_MIN_MM, WING_MAX_MM, color=BAND, zorder=0)
ax.text((WING_MIN_MM + WING_MAX_MM) / 2, 14,
        "Ae. aegypti range", ha="center", va="bottom",
        fontsize=8, color=INK)

# 5.3: The curve: what the classifier needs, 150 / L
ax.plot(L, need, color=BLUE, linewidth=2, zorder=3)
ax.text(3.15, required_lpmm(3.15) * 1.18, "Classifier needs\n(150 / L)",
        color=BLUE, fontsize=8.5, ha="left", va="bottom")

# 5.4: Worst case point: the smallest wing
ax.plot(WING_MIN_MM, f_need, "o", color=BLUE, markersize=6, zorder=4,
        markeredgecolor="white", markeredgewidth=1.5)
ax.annotate(f"{f_need:.0f} lp/mm @ {WING_MIN_MM} mm",
            xy=(WING_MIN_MM, f_need), xytext=(1.62, 38),
            fontsize=8, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, linewidth=0.8))

# 5.5: Reference lines
ax.axhline(pi_nyquist, color=INK, linewidth=1, linestyle="--", zorder=2)
ax.text(3.98, pi_nyquist * 1.06,
        f"Pi HQ cam @ {mag:.2f}x: {pi_nyquist:.0f} lp/mm",
        ha="right", va="bottom", fontsize=8, color=INK)

ax.axhline(f_usaf, color=INK, linewidth=1, linestyle=":", zorder=2)
ax.text(3.98, f_usaf * 1.06,
        f"USAF test element G{g} E{e}: {f_usaf:.1f} lp/mm",
        ha="right", va="bottom", fontsize=8, color=INK)

# 5.6: Axes
ax.set_yscale("log")
ax.set_xlim(1.5, 4.0)
ax.set_ylim(12, 700)
ax.set_yticks([20, 50, 100, 200, 500])
ax.set_yticklabels(["20", "50", "100", "200", "500"])
ax.yaxis.set_minor_formatter(plt.NullFormatter())   # hide the 3x10^1 style labels
ax.set_xlabel("Wing length L (mm)", fontsize=9, color=INK)
ax.set_ylabel("Wing Resolution (lp/mm)", fontsize=9, color=INK)
ax.tick_params(colors=INK, labelsize=8)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK)
ax.grid(axis="y", which="major", color="#ebeae6", linewidth=0.6)

ax.set_title("",
             fontsize=10.5, color="#0b0b0b", loc="left", pad=10)

fig.tight_layout()
# Save next to the script. In Jupyter or Colab there is no __file__,
# so then we save in the current working folder instead.
try:
    out = Path(__file__).with_name("w1_required_resolution.png")
except NameError:
    out = Path.cwd() / "w1_required_resolution.png"
fig.savefig(out)
print(f"Saved plot to {out.name}")