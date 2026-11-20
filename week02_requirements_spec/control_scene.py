"""Renders a 3D view of the imager's control hardware: Raspberry Pi, HQ camera, ESP32,
motor driver, stepper motor, limit switch, LED and 12 V supply, with the cables between them.
Units: 1 Blender unit = 1 cm. Sizes are close to the real boards but not exact.
Usage: python control_scene.py <out.png> <width> <height> <samples>"""
import sys, os, math
import bpy
from mathutils import Vector

OUT = os.path.abspath(sys.argv[1])  # Blender only saves to full paths when no .blend file is open
W, H, SPP = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def srgb(h):
    # Hex colours are given in sRGB; Blender works in linear light, so each channel is converted.
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexcol, metal=0.0, rough=0.5, emit=None, estr=0.0):
    # One physically based material per surface type; emission makes the LED glow.
    m = bpy.data.materials.new(name)
    if not m.node_tree: m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(hexcol), 1)
    b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*srgb(emit), 1); b.inputs["Emission Strength"].default_value = estr
    return m


M = dict(pcb=mat("pcb", "#1f6a3f", rough=0.45), esp=mat("esp", "#1b1d22", rough=0.45),
         red=mat("red", "#b8322a", rough=0.45), alu=mat("alu", "#c4c8ce", metal=1.0, rough=0.25),
         steel=mat("steel", "#dfe2e6", metal=1.0, rough=0.15), black=mat("black", "#151618", metal=0.4, rough=0.35),
         chip=mat("chip", "#111111", rough=0.4), white=mat("white", "#e6e6e6", rough=0.4),
         ribbon=mat("ribbon", "#e8dcc0", rough=0.5), usb=mat("usb", "#3b3e45", rough=0.5),
         wred=mat("wred", "#d23b2f", rough=0.5), wblue=mat("wblue", "#2f6fd2", rough=0.5),
         wyel=mat("wyel", "#e0b22a", rough=0.5), wgrn=mat("wgrn", "#2f9e4f", rough=0.5),
         lens=mat("lens", "#2a4f8a", metal=0.2, rough=0.05),
         led=mat("led", "#fff3cf", emit="#fff3cf", estr=30.0), floor=mat("floor", "#ffffff", rough=0.9),
         psu=mat("psu", "#2b2d33", rough=0.6))


def assign(o, m): o.data.materials.clear(); o.data.materials.append(m)


def box(sx, sy, sz, loc, m, bevel=0.0):
    # Rectangular part of size sx, sy, sz centred at loc; a small bevel softens the edges.
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True); assign(o, m)
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    return o


def cyl(r, h, loc, m, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; assign(o, m); bpy.ops.object.shade_smooth(); return o


def wire(pts, m, rad=0.09):
    # A cable is a smooth Bezier curve through the given points, given thickness by a round bevel.
    cu = bpy.data.curves.new("w", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = rad; cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, q in zip(sp.bezier_points, pts):
        bp.co = q; bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new("w", cu); scene.collection.objects.link(o); o.data.materials.append(m)


# Raspberry Pi 4 board (8.5 x 5.6 cm) with USB ports, GPIO header and camera connector
PX, PY = -16.0, 0.0
box(8.5, 5.6, 0.16, (PX, PY, 0.4), M["pcb"], bevel=0.03)
box(1.5, 1.5, 0.12, (PX - 0.8, PY + 0.4, 0.54), M["alu"], bevel=0.03)
box(1.4, 1.6, 1.5, (PX + 3.5, PY - 1.2, 1.2), M["alu"], bevel=0.05)
box(1.4, 1.6, 1.3, (PX + 3.5, PY + 1.0, 1.1), M["alu"], bevel=0.05)
box(5.0, 0.5, 0.5, (PX - 1.0, PY + 2.4, 0.73), M["chip"])
box(0.3, 2.0, 0.25, (PX - 2.2, PY - 0.8, 0.6), M["white"])

# HQ camera board (3.8 x 3.8 cm) with an M12 lens
CX, CY = -16.0, 11.0
box(3.8, 3.8, 0.16, (CX, CY, 0.4), M["pcb"], bevel=0.03)
cyl(1.25, 0.6, (CX, CY, 0.8), M["black"])
cyl(0.72, 2.4, (CX, CY, 2.3), M["black"])
cyl(0.5, 0.05, (CX, CY, 3.52), M["lens"])
box(2.0, 0.3, 0.2, (CX, CY - 1.7, 0.55), M["white"])

# ESP32 development board with its shielded radio module and USB socket
EX, EY = 0.0, 0.0
box(5.2, 2.8, 0.15, (EX, EY, 0.4), M["esp"], bevel=0.03)
box(1.8, 1.6, 0.25, (EX + 1.3, EY, 0.6), M["steel"], bevel=0.03)
box(0.7, 0.8, 0.35, (EX - 2.4, EY, 0.65), M["alu"])
for s in (-1, 1): box(4.6, 0.25, 0.3, (EX, EY + s * 1.25, 0.62), M["chip"])

# stepper driver with heat sink: turns STEP/DIR pulses into coil currents
DX, DY = 11.0, 0.0
box(2.2, 1.6, 0.15, (DX, DY, 0.4), M["red"], bevel=0.03)
box(1.0, 1.0, 0.6, (DX, DY, 0.8), M["alu"])
for i in range(5): box(0.12, 1.0, 0.25, (DX - 0.4 + i * 0.2, DY, 1.2), M["alu"])

# NEMA 17 stepper motor (4.2 cm square body) with shaft
MX, MY = 22.0, 0.0
box(4.2, 4.2, 4.0, (MX, MY, 2.3), M["black"], bevel=0.2)
box(4.2, 4.2, 0.5, (MX, MY, 4.45), M["alu"], bevel=0.15)
cyl(0.5, 0.4, (MX, MY, 4.9), M["alu"]); cyl(0.25, 2.0, (MX, MY, 5.9), M["steel"])

# limit switch with lever: closes when the holder reaches the home position
SX, SY = 11.0, -10.0
box(2.0, 1.0, 1.0, (SX, SY, 0.8), M["black"], bevel=0.05)
box(2.2, 0.1, 0.12, (SX + 0.4, SY - 0.55, 1.4), M["steel"])
cyl(0.18, 0.2, (SX + 1.5, SY - 0.55, 1.45), M["steel"], rot=(math.pi / 2, 0, 0))

# LED on a small heat-sink plate, with the transistor that switches it
LX, LY = 0.0, 11.0
cyl(1.4, 0.15, (LX, LY, 0.4), M["alu"], verts=6)
box(0.6, 0.6, 0.25, (LX, LY, 0.6), M["led"], bevel=0.05)
box(1.0, 0.8, 0.5, (LX + 2.2, LY - 1.0, 0.55), M["chip"])
lp = bpy.data.lights.new("l", "POINT"); lp.energy = 60
lo = bpy.data.objects.new("l", lp); lo.location = (LX, LY, 1.4); scene.collection.objects.link(lo)

# 12 V supply for the motor
VX, VY = 22.0, -11.0
box(5.0, 3.0, 2.2, (VX, VY, 1.3), M["psu"], bevel=0.15)

# cables: USB (Pi to ESP32), CSI ribbon (Pi to camera), STEP/DIR/EN, four motor coils,
# switch pair, LED pair and the 12 V pair
wire([(PX + 4.3, PY - 1.2, 1.2), (PX + 8, PY - 3, 0.5), (EX - 4.5, EY - 1, 0.4), (EX - 2.8, EY, 0.65)], M["usb"], 0.15)
wire([(PX - 2.2, PY + 0.8, 0.7), (PX - 2.2, PY + 5, 0.6), (CX, CY - 4, 0.6), (CX, CY - 1.8, 0.6)], M["ribbon"], 0.06)
for k, m in enumerate((M["wyel"], M["wgrn"], M["wblue"])):
    dy = -0.4 + 0.4 * k
    wire([(EX + 2.6, EY + dy, 0.6), (EX + 6, EY + dy, 0.45), (DX - 1.1, DY + dy, 0.5)], m, 0.07)
for k, m in enumerate((M["wred"], M["wblue"], M["wgrn"], M["esp"])):
    dy = -0.45 + 0.3 * k
    wire([(DX + 1.1, DY + dy, 0.5), (DX + 5, DY + dy, 0.45), (MX - 2.2, MY + dy, 1.0)], m, 0.07)
for k, m in enumerate((M["wred"], M["esp"])):
    d = -0.3 + 0.6 * k
    wire([(SX - 0.3 + d, SY + 0.6, 0.9), (SX - 4, SY + 5, 0.45), (EX + 1.5 + d, EY - 1.4, 0.5)], m, 0.07)
    wire([(EX - 1.5 + d, EY + 1.4, 0.5), (EX - 1 + d, EY + 6, 0.45), (LX + 1.9 + d, LY - 1.4, 0.55)], m, 0.07)
    wire([(VX - 2.5, VY + d, 1.0), (DX + 3, VY + 4, 0.45), (DX + 0.6, DY - 0.8 + d * 0.3, 0.5)], m, 0.08)

# white floor and sky, two soft area lights, camera looking down at about 40 degrees
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0)); assign(bpy.context.object, M["floor"])
world = bpy.data.worlds.new("w"); scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9


def area(loc, size, power):
    Lt = bpy.data.lights.new("a", "AREA"); Lt.size = size; Lt.energy = power
    o = bpy.data.objects.new("a", Lt); o.location = loc; scene.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area((-20, -30, 50), 40, 50000); area((40, -10, 30), 30, 15000)
cam = bpy.data.cameras.new("cam"); cam.lens = 45
co = bpy.data.objects.new("cam", cam); scene.collection.objects.link(co); scene.camera = co
co.location = (4.0, -62.0, 50.0)
co.rotation_euler = (Vector((3.0, 0.0, 0.0)) - co.location).to_track_quat("-Z", "Y").to_euler()

# Cycles path tracing on the CPU; the denoiser allows a low sample count
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
scene.cycles.samples = SPP; scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.3
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("saved", OUT)
