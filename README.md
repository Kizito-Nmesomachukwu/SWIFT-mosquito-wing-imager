# SWIFT: A Low-Cost Standardised Imaging System for AI-Based Mosquito Wing Classification

**Course:** Frugal Photonics for Global Health, WS 2026/27, Friedrich Schiller University Jena
**Challenge:** 1, Variant 1: AI Microscope (partner: Bernhard Nocht Institute for Tropical Medicine, Hamburg)
**Author:** Kizito Nmesomachukwu Odizilike

SWIFT is a frugal imager for mosquito wings: portable, built from widely available parts, and
designed so that every device produces images an AI classifier can use. This repository is the
weekly development log of the project, one folder per week, each with its own code, results,
figures and README.

## Background

Vector-borne diseases such as malaria and dengue cause millions of infections each year, and
their control depends on identifying the mosquito species present [3]. Identification
currently relies on trained entomologists, who are increasingly rare, or on expensive
equipment such as a stereo microscope with an integrated camera system, at about €12,000 [3].

Convolutional neural networks (CNNs) can classify mosquito species from images of their wings,
which outperformed full-body images in a direct comparison (87.6% against 78.9% accuracy) [1].
Two problems limit practical use:

- **Device dependence.** Models lose about 14% mean accuracy on images from a device not
  included in training, even with extensive augmentation [1].
- **Unstandardised data.** An open collection of 18,104 wing images was captured with
  exposure and lighting that varied between projects [2].

In tropical regions such as Ghana, local species often differ from those in existing European
datasets, so an affordable on-site imager would also let the training data grow to cover them
[3].

## Aim

Build and characterise a low-cost wing imager that:

1. delivers image quality sufficient for AI classification, comparable to a stereo
   microscope with camera [3];
2. acquires images under fixed, reproducible settings (illumination, exposure, white balance),
   addressing the device dependence reported in [1];
3. is computer-controlled for automated acquisition and outputs images in the format the
   classifier expects [1, 3];
4. is portable and can be rebuilt from widely available parts [3].

The approach is requirements first: derive the optical performance the classifier actually
needs, design to it, then measure the prototype against it with standard targets and,
finally, with the classifier itself.

## Repository Structure

```
SWIFT-mosquito-wing-imager/
├── README.md                          # this file
├── .gitignore
├── week01_concept_animation/          # one folder per week
│   ├── README.md                      # what the week covers and how to run it
│   ├── belt_anim.py                   # 3D concept model and animation (Blender, Python)
│   ├── anim_overlay.py                # labels, captions and capture flash
│   ├── make_video.sh                  # runs every step and writes the video
│   ├── conveyor_imager_animation.mp4  # output
│   └── requirements.txt               # Python dependencies of the week
└── week02_requirements_spec/
    ├── README.md                      # physics, requirements, results of the week
    ├── w1_requirements_spec.py        # code
    ├── w1_required_resolution.png     # outputs
    ├── requirements.txt
    └── figures/
```

Each week folder runs on its own: install its `requirements.txt` and run its script.

## Weekly Log

| Week | Dates | Folder | Focus | Status |
|---|---|---|---|---|
| 1 | 10 to 17 Nov 2026 | [week01_concept_animation](week01_concept_animation/) | Team organisation, optical layout and concept animation | Complete |
| 2 | 18 to 24 Nov 2026 | [week02_requirements_spec](week02_requirements_spec/) | Image-quality requirements and redesign for mounted glass slides | In progress |
| 3 | 25 Nov to 1 Dec 2026 | | Optical design and bill of materials | Planned |
| 4 | 2 to 8 Dec 2026 | | First bench prototype and resolution test | Planned |
| 5 | 9 to 15 Dec 2026 | | Image-quality metrology pipeline | Planned |
| 6 | 16 to 22 Dec 2026 | | Iteration 1 and printed housing | Planned |
| 7 | 6 to 12 Jan 2027 | | Standardised acquisition software | Planned |
| 8 | 13 to 19 Jan 2027 | | Classifier test on prototype images | Planned |
| 9 | 20 to 26 Jan 2027 | | Iteration 2 and end-to-end pipeline | Planned |
| 10 | 27 Jan to 2 Feb 2027 | | Design freeze and build documentation | Planned |

## Key Result So Far

For a single wing, the optics must resolve about 90 lp/mm at the wing, which needs a numerical
aperture of only 0.060. A Raspberry Pi HQ camera at 1.37× magnification samples about 4.9×
finer than that. Resolution is therefore not the bottleneck; standardised illumination and
acquisition are. Following mentor feedback, Week 2 checks whether all wings of one mounted
slide (about 8) fit in a single frame at this resolution. Details and derivations are in
[Week 2](week02_requirements_spec/).

## Conventions

- Folders: `weekNN_short_topic`. Scripts: `wN_*.py`. Figures: `WN_figK_short_name`,
  captioned "Fig. WN-K".
- Every formula in code carries a bracketed reference to the README of its week.
- Design choices are marked ASSUMPTION in code and listed in each week's README.

## References

1. K. Nolte, F. G. Sauer, J. Baumbach, P. Kollmannsberger, C. Lins, R. Lühken, Robust mosquito
   species identification from diverse body and wing images using deep learning,
   *Parasites & Vectors* 17, 372 (2024). doi:10.1186/s13071-024-06459-3
2. K. Nolte, E. Agboli, et al., Comprehensive mosquito wing image repository for advancing
   research on geometric morphometric- and AI-based identification, *Scientific Data* 12, 715
   (2025). doi:10.1038/s41597-025-05043-3
3. Challenge 1: AI-Based Mosquito Classification, course challenge description, Frugal
   Photonics for Global Health, Friedrich Schiller University Jena (2026).
