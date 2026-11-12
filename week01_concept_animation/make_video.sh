#!/bin/bash
# Renders the frames, smooths them from 12 to 24 fps, adds the labels and writes the MP4.
# Needs: Blender's Python module (pip install bpy), Pillow and ffmpeg.
set -e
mkdir -p frames
python belt_anim.py frames 960 540 8
mkdir -p seq interp final
i=0; for f in $(ls frames/f_*.png | sort); do cp "$f" "seq/$(printf %04d $i).png"; i=$((i+1)); done
ffmpeg -framerate 12 -i seq/%04d.png -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1" -start_number 0 interp/%04d.png
python anim_overlay.py interp final frames_anchors.json frames_timeline.json
ffmpeg -framerate 24 -i final/o_%04d.png -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p conveyor_imager_animation.mp4
