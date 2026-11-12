# Week 2: Requirements Spec v1 for a Low-Cost Mosquito Wing Imager

**Project:** SWIFT: A Low-Cost Standardised Imaging System for AI-Based Mosquito Wing Classification
**Course:** Frugal Photonics for Global Health, WS 2026/27, Friedrich Schiller University Jena
**Author:** Kizito Nmesomachukwu Odizilike

The BNITM wing classifier sees each wing as a 300 × 300 pixel image [1]. This week works
backwards from that input to the optical performance an imager must deliver: field of view,
magnification, minimum numerical aperture (NA), contrast and a resolution test target. It then
checks whether the Raspberry Pi HQ camera meets the requirement.

**Result:** at the wing, the optics must resolve about 90 lp/mm, which needs only NA ≥ 0.060.
The Pi HQ camera samples about 4.9× finer than that. Resolution is therefore not the
bottleneck; standardised illumination and acquisition are.

## Motivation

CNN mosquito classifiers, trained on wing or body images, lose about 14% mean accuracy on
images from a device not included in training, even with extensive augmentation [1]. A large
public repository of 18,104 wing images was captured without standardised settings, with exposure and lighting varying
between projects [2]. A low-cost imager with fixed, reproducible acquisition addresses both
problems. Before choosing hardware, this week defines how good its optics need to be.

## Physics Background

### (i) What the Classifier Sees: Sampling

The wing is cropped, padded to a square and resized to N = 300 pixels [1], so its long axis
L is spread over 300 pixels. One CNN pixel covers

```math
\delta = \frac{L}{N}
```

of the wing. By the Nyquist-Shannon sampling theorem [9], a grid with spacing δ represents
spatial frequencies up to

```math
f_N = \frac{1}{2\delta} = \frac{150}{L}\ \text{lp/mm} \qquad (L \text{ in mm})
```

because one line pair (a bright and a dark bar) needs at least two pixels. Detail finer than
$f_N$ is lost (or aliased) in the resize, so the optics need not deliver more than $f_N$, but must deliver
this much. Since $f_N$ falls as 1/L, the smallest wing is the worst case.

### (ii) Lens Resolution: Rayleigh Criterion

A lens with a round aperture images a point as an Airy pattern whose first dark ring lies at
$r_R = 0.61\,\lambda/\mathrm{NA}$, measured at the object [5]. Two points are just resolved
when one lies on the other's first dark ring (Rayleigh criterion). The design rule used here
is that two points one CNN pixel apart must be resolved, $r_R \le \delta$, which gives

```math
\mathrm{NA}_{\min} = \frac{0.61\,\lambda}{\delta}
```

with $\mathrm{NA} = n \sin\theta$, where θ is the half-angle of the light cone accepted by the
lens. In air (n = 1) the flat cover slip does not change NA, since Snell's law conserves
$n\sin\theta$ across plane interfaces.

### (iii) Contrast: Modulation Transfer Function

For incoherent illumination, a diffraction-limited lens with a round aperture passes no
contrast above the cutoff frequency [6]

```math
f_c = \frac{2\,\mathrm{NA}}{\lambda}
```

and below it keeps the fraction of contrast [6]

```math
\mathrm{MTF}(\nu) = \frac{2}{\pi}\left[\arccos\nu - \nu\sqrt{1-\nu^{2}}\right],
\qquad \nu = \frac{f}{f_c},\quad 0 \le \nu \le 1 .
```

With NA chosen by the rule in (ii), the classifier limit sits at

```math
\nu = \frac{f_N}{f_c} = \frac{\lambda}{4\,\delta\,\mathrm{NA}} = \frac{1}{4 \times 0.61} = 0.41 ,
```

independent of wing length and wavelength, so a perfect lens at $\mathrm{NA}_{\min}$ keeps
MTF = 0.49 at $f_N$. Contrast at $f_N$ reaches zero when $f_c = f_N$, that is at
$\mathrm{NA} = \lambda f_N / 2$, the absolute lower limit.

### (iv) Depth of Field

The depth of field is the sum of a wave-optical and a geometrical term [7],
$d = \lambda n/\mathrm{NA}^2 + n\,e/(M\,\mathrm{NA})$, where e is the smallest distance the
detector resolves and M the lateral magnification. The script reports the wave term only.
Taking e as one Pi HQ pixel (1.55 µm) at M = 1.37 and NA = 0.060, the geometrical term is
about 19 µm against 151 µm for the wave term.

### (v) Camera Sampling

The magnification maps the field of view onto the sensor width W, $m = W/\mathrm{FOV}$. One
sensor pixel of pitch p then covers $p_{\text{obj}} = p/m$ of the wing, and the camera's own
Nyquist limit at the wing is $f_{\text{cam}} = 1/(2\,p_{\text{obj}})$.

### (vi) Test Target

Element E of group G of the USAF 1951 resolution target [8] has spatial frequency

```math
f = 2^{\,G + (E-1)/6}\ \text{lp/mm}.
```

The script selects the coarsest element at or above $f_N$, which gives an objective
pass/fail test for a prototype.

## Assumptions

| | Assumption | Value | Basis |
|---|---|---|---|
| A1 | Wing long axis fills the 300 px CNN frame | N = 300 | [1] |
| A2 | Wing-length range | 1.67 to 3.83 mm | *Ae. aegypti* females [3] |
| A3 | Design wavelength (white LED, middle of spectrum) | λ = 0.55 µm | design choice |
| A4 | Field-of-view margin for wing placement | 20% | design choice |
| A5 | Diffraction-limited lens, incoherent brightfield illumination | | best case [6] |
| A6 | Air between cover slip and lens | n = 1 | dry lens |

The wing-length range is that of *Ae. aegypti* [3]; other genera are outside this version of
the spec.

## Requirements (Spec v1)

| Quantity | Value | Derivation |
|---|---|---|
| Field of view (long axis) | 4.6 mm | 3.83 mm × 1.2 |
| Magnification (Pi HQ, W = 6.287 mm) | 1.37× | W / FOV |
| Camera pixel at the wing (p = 1.55 µm) | 1.13 µm | p / m |
| CNN pixel at the wing, 3.83 mm / 1.67 mm wing | 12.8 / 5.57 µm | L / 300 [1] |
| CNN Nyquist, 3.83 mm / 1.67 mm wing | 39.2 / 89.8 lp/mm | 1 / (2δ) [9] |
| Minimum NA (Rayleigh rule) | 0.060 (θ = 3.5°) | 0.61 λ / δ [5] |
| Lens cutoff at minimum NA | 219 lp/mm | 2 NA / λ [6] |
| Contrast (MTF) at 89.8 lp/mm | 0.49 | diffraction MTF [6] |
| NA at which that contrast reaches zero | 0.025 | λ f_N / 2 [6] |
| Depth of field at minimum NA (wave term) | 151 µm | λ / NA² [7] |
| USAF 1951 test element | Group 6, Element 4: 90.5 lp/mm | [8] |
| Pi HQ Nyquist at the wing | 441 lp/mm | 1 / (2 p_obj) [9] |
| Camera headroom over requirement | 4.9× | 441 / 89.8 |

**Design requirements carried into Week 2:**

1. Field of view of at least 4.6 mm along the wing axis.
2. Resolve USAF Group 6, Element 4 (90.5 lp/mm) at the wing.
3. NA of at least 0.060, chosen above that value for margin against aberrations and defocus.
4. Fixed exposure, white balance and illumination, since device and setting variation is the
   documented failure mode [1, 2].

![Required resolution against wing length](w1_required_resolution.png)

The curve is the requirement $f_N = 150/L$; the grey band is the *Ae. aegypti* range [3].
Even the smallest wing stays well below the Pi HQ sampling limit.

## Validation

- The hand calculation in Fig. W1-3 reproduces δ, $f_N$, NA, $f_c$, the MTF and the camera
  headroom from the formulas in (i), (ii), (iii) and (v).
- The MTF expression returns 1 at ν = 0 and 0 at ν = 1, as required by its definition.
- The USAF formula is checked against two known elements: G6E4 = 90.5 lp/mm and
  G5E3 = 40.3 lp/mm.
- The Pi HQ sensor values (4056 × 3040 pixels, 1.55 µm pitch, 6.287 × 4.712 mm image area)
  match the manufacturer's documentation [4].

## Repository Structure

```
week01_requirements_spec/
├── w1_requirements_spec.py          # calculation, table and plot
├── w1_required_resolution.png       # output plot
├── figures/
│   ├── W1_fig1_requirement_chain.jpg
│   ├── W1_fig2_optical_layout.jpg
│   └── W1_fig3_worked_calculation.jpg
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

Dependencies are numpy and matplotlib; everything else is in the Python standard library.

## Usage

```bash
python3 w1_requirements_spec.py
```

The script also runs in Jupyter or Colab. It prints the table below and saves
`w1_required_resolution.png`.

```
Quantity                                Value  Unit    How I got it
-------------------------------------------------------------------------------------
Field of view (long axis)                 4.6  mm      max wing x (1 + margin)
Magnification (Pi HQ)                    1.37  x       sensor width / FOV
Pixel size at the wing                   1.13  um      pixel pitch / magnification
Camera pixels across largest wing    3.38e+03  px      wing length / pixel at wing
CNN spacing, 3.83 mm wing                12.8  um/px   wing length / 300 [1]
CNN Nyquist, 3.83 mm wing                39.2  lp/mm   1 / (2 x spacing) [9]
CNN spacing, 1.67 mm wing                5.57  um/px   wing length / 300 [1]
CNN Nyquist, 1.67 mm wing                89.8  lp/mm   1 / (2 x spacing) [9]
Minimum NA (Rayleigh rule)             0.0603  -       0.61 lambda / spacing [5]
Lens cutoff at that NA                    219  lp/mm   2 NA / lambda [6]
Lens contrast at CNN Nyquist            0.493  -       diffraction MTF, round pupil [6]
NA where contrast drops to zero        0.0247  -       lambda x f / 2 [6]
Depth of field at min NA                  151  um      lambda / NA^2 [7]
USAF element to resolve: G6 E4           90.5  lp/mm   smallest element above need [8]
Pi HQ Nyquist at the wing                 441  lp/mm   1 / (2 x pixel at wing) [9]
Camera headroom over need                4.91  x       Pi Nyquist / CNN Nyquist

Check: USAF G6E4 = 90.5 lp/mm, G5E3 = 40.3 lp/mm
Saved plot to w1_required_resolution.png
```

## Citation Policy

Every formula in the script carries a bracketed reference at the point of use, and every
design choice is marked ASSUMPTION. Numbering is the same in the script and this README.

## References

1. K. Nolte, F. G. Sauer, J. Baumbach, P. Kollmannsberger, C. Lins, R. Lühken, Robust mosquito
   species identification from diverse body and wing images using deep learning,
   *Parasites & Vectors* 17, 372 (2024). doi:10.1186/s13071-024-06459-3
2. K. Nolte, E. Agboli, et al., Comprehensive mosquito wing image repository for advancing
   research on geometric morphometric- and AI-based identification, *Scientific Data* 12, 715
   (2025). doi:10.1038/s41597-025-05043-3
3. J. R. Schneider, A. C. Morrison, H. Astete, T. W. Scott, M. L. Wilson, Adult size and
   distribution of *Aedes aegypti* (Diptera: Culicidae) associated with larval habitats in
   Iquitos, Peru, *J. Med. Entomol.* 41(4), 634-642 (2004). doi:10.1603/0022-2585-41.4.634
4. Raspberry Pi Ltd., Camera hardware documentation, HQ Camera (Sony IMX477) specifications.
   https://www.raspberrypi.com/documentation/accessories/camera.html
5. E. Hecht, *Optics*, 5th ed., Pearson (2017).
6. J. W. Goodman, *Introduction to Fourier Optics*, 3rd ed., Roberts & Company (2005).
7. S. Inoué, K. R. Spring, *Video Microscopy: The Fundamentals*, 2nd ed., Plenum Press,
   New York (1997).
8. MIL-STD-150A, *Photographic Lenses*, US Department of Defense (1959).
9. C. E. Shannon, Communication in the presence of noise, *Proc. IRE* 37(1), 10-21 (1949).
