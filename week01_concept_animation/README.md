# Week 1: Concept Animation of the Conveyor Wing Imager

**Project:** Challenge 1A, a low-cost imaging system for AI-based mosquito wing classification

**Course:** Frugal Photonics for Global Health, WS 2026/27, Friedrich Schiller University Jena

**Author:** Kizito Nmesomachukwu Odizilike

A short video of our first prototype concept, made with a Python script in Blender. It
combines the conveyor feeder proposed by Hanna at our team meeting on 11.11.2026, Sam's
suggestion to hold the wings with PDMS, and my optical layout without a diffuser. It is meant
as a guide for building and as a basis for deciding what to adjust or remove at our next
meeting. The model shows the layout only; it is not to scale.

## What the Video Shows

| Time | Step |
|---|---|
| 0 to 18 s | The parts come together one by one, each with its label |
| 18 to 21 s | Three wings on PDMS pads are placed on the PMMA belt |
| 21 to 22 s | The white LED switches on and stays on |
| 22 to 34 s | The ESP32 and driver turn the motor; the belt steps 5 cm, each wing stops under the lens and the camera captures it |
| 34 to 38 s | The images go to the Raspberry Pi for AI classification |

The three "captured images" are simple drawings of different wings, not real camera images.

## Parts in the Model

- PMMA belt on two rollers, driven by a motor through a drive belt
- Wings held on clear PDMS pads
- Glass window under the imaging spot, so the wing stays at one height
- White LED between the two runs of the belt, lighting the wing from below
- Light-tight housing (front wall left out to show the inside)
- Raspberry Pi HQ camera, printed spacer tube and M12 lens
- Raspberry Pi, ESP32 and motor driver

## Repository Structure

```
week01_concept_animation/
├── belt_anim.py                     # builds the 3D scene, animates it and renders the frames
├── anim_overlay.py                  # adds labels, captions, capture flash and captured images
├── make_video.sh                    # runs every step and writes the MP4
├── conveyor_imager_animation.mp4    # the finished video
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

`bpy` is Blender as a Python module and needs Python 3.13. ffmpeg must also be installed
(it is already on Google Colab).

## Usage

Run everything in one go (Linux, macOS or Colab):

```bash
bash make_video.sh
```

This renders the frames, smooths them from 12 to 24 frames per second, adds the labels and
writes `conveyor_imager_animation.mp4`. On a normal laptop CPU this takes about 40 to 90
minutes. For a quick test, render a single frame (here frame 500) at low quality:

```bash
mkdir -p test
python belt_anim.py test/t 480 270 4 500
```

The script also runs through a downloaded Blender instead of `bpy`:

```bash
blender -b -P belt_anim.py -- frames 960 540 8
```

### Google Colab

Upload `belt_anim.py` and `anim_overlay.py`, then run this in one cell:

```bash
%%bash
pip install -q bpy==5.2.3 pillow
apt-get -qq install -y libsm6 libxi6 libxkbcommon0 libxrender1 libxxf86vm1 libgl1 > /dev/null
mkdir -p frames seq interp final
python belt_anim.py frames 960 540 8
i=0; for f in $(ls frames/f_*.png | sort); do cp "$f" "seq/$(printf %04d $i).png"; i=$((i+1)); done
ffmpeg -loglevel error -framerate 12 -i seq/%04d.png -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1" -start_number 0 interp/%04d.png
python anim_overlay.py interp final frames_anchors.json frames_timeline.json
ffmpeg -loglevel error -y -framerate 24 -i final/o_%04d.png -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p conveyor_imager_animation.mp4
```

### Changing the Speed

All timings are at the top of the `# timing` block in `belt_anim.py`, in seconds:

| Setting | Controls |
|---|---|
| `PART_GAP`, `PART_FALL` | Assembly: time between parts and how long each takes to land |
| `WING_GAP`, `WING_FALL` | How the wings are placed on the belt |
| `MOVE_TIME` | How long one belt step takes |
| `STOP_TIME` | How long each wing waits under the lens for its capture |
| `END_HOLD` | How long the final shot stays on screen |

`belt_anim.py` writes the timing to `frames_timeline.json`, so the labels and captions in
`anim_overlay.py` follow any change automatically.
