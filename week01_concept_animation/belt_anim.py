"""Animated conveyor imager: parts come together, wings go on, LED switches on, the belt steps
and the camera captures each wing. Units: 1 BU = 1 cm.
Usage: python belt_anim.py <frames_dir> <W> <H> <samples> [frame]
   or: blender -b -P belt_anim.py -- <frames_dir> <W> <H> <samples> [frame]"""
import sys, math, json
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# works both as "python belt_anim.py ..." and "blender -b -P belt_anim.py -- ..."
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT, W, H, SPP = ARGS[0], int(ARGS[1]), int(ARGS[2]), int(ARGS[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def mat(name, hexcol, metal=0.0, rough=0.5, trans=0.0, ior=1.45, emit=None, estr=0.0, coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"] if m.node_tree else None
    if b is None:
        m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(hexcol), 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*srgb(emit), 1)
        b.inputs["Emission Strength"].default_value = estr
    return m

M = dict(
    housing=mat("housing", "#2e3036", rough=0.55),
    inner=mat("inner", "#3a3d44", rough=0.7),
    alu=mat("alu", "#c4c8ce", metal=1.0, rough=0.25),
    steel=mat("steel", "#dfe2e6", metal=1.0, rough=0.15),
    black=mat("black", "#151618", metal=0.6, rough=0.3),
    lensglass=mat("lensglass", "#2a4f8a", metal=0.2, rough=0.05, coat=1.0),
    spacer=mat("spacer", "#5b5f68", rough=0.6),
    pcb=mat("pcb", "#1f6a3f", rough=0.45, coat=0.3),
    chip=mat("chip", "#111111", rough=0.4),
    belt=mat("belt", "#d6e6f2", rough=0.08, trans=0.92, ior=1.49),
    pdms=mat("pdms", "#eef6fb", rough=0.05, trans=0.95, ior=1.41),
    wing=mat("wing", "#b98a3e", rough=0.4, trans=0.3),
    vein=mat("vein", "#4a3214", rough=0.5),
    glass=mat("glass", "#ffffff", rough=0.0, trans=1.0, ior=1.5),
    plate=mat("plate", "#4a4d55", rough=0.5),
    diffuser=mat("diffuser", "#f7f7f5", rough=0.6, trans=0.5, emit="#fff7e6", estr=2.0),
    led=mat("led", "#fff3cf", emit="#fff3cf", estr=40.0),
    ledpcb=mat("ledpcb", "#e9e9e9", metal=0.6, rough=0.3),
    floor=mat("floor", "#ffffff", rough=0.9),
    ribbon=mat("ribbon", "#e8dcc0", rough=0.5),
    white=mat("white", "#dcdcdc", rough=0.4),
)

def assign(o, m):
    o.data.materials.clear(); o.data.materials.append(m)

def box(sx, sy, sz, loc, m, bevel=0.0, seg=3, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if rot: o.rotation_euler = rot
    assign(o, m)
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = seg; b.limit_method = "ANGLE"
    return o

def cyl(r, h, loc, m, rot=(0, 0, 0), verts=64, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; assign(o, m); bpy.ops.object.shade_smooth()
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    return o

def diff(target, cutter):
    md = target.modifiers.new("bool", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cutter
    md.solver = "EXACT"; cutter.hide_render = True; cutter.hide_viewport = True

GROUPS, _seen = {}, set()
def G(name):
    new = [o for o in bpy.data.objects if o.name not in _seen]
    for o in new: _seen.add(o.name)
    GROUPS[name] = new

# ---------------------------------------------------------------- conveyor
RX, RZ, RR, BW = 17.0, 3.0, 1.6, 7.0          # roller x, axle height, radius, belt width
TOP = RZ + RR                                  # top run height
box(48, 17, 0.5, (2.5, -3.5, 0.25), M["alu"], bevel=0.15)
G("plate")
for sx in (-RX, RX):
    cyl(RR, BW + 0.6, (sx, 0, RZ), M["steel"], rot=(math.pi / 2, 0, 0), bevel=0.06)
    cyl(0.35, BW + 2.2, (sx, 0, RZ), M["steel"], rot=(math.pi / 2, 0, 0))
    for sy in (-(BW / 2 + 0.9), BW / 2 + 0.9):
        box(2.4, 0.4, RZ + 0.2, (sx, sy, (RZ + 0.2) / 2 + 0.5), M["alu"], bevel=0.1)

G("rollers")
# belt loop (stadium path in x-z, extruded along y), then solidified
r = RR + 0.04
pts = []
N = 48
for i in range(N + 1):                                    # right semicircle, top to bottom
    a = math.pi / 2 - math.pi * i / N
    pts.append((RX + r * math.cos(a), RZ + r * math.sin(a)))
for i in range(1, 40):                                    # bottom run, right to left
    pts.append((RX - 2 * RX * i / 40, RZ - r))
for i in range(N + 1):                                    # left semicircle, bottom to top
    a = -math.pi / 2 - math.pi * i / N
    pts.append((-RX + r * math.cos(a), RZ + r * math.sin(a)))
for i in range(1, 40):                                    # top run, left to right
    pts.append((-RX + 2 * RX * i / 40, RZ + r))
me = bpy.data.meshes.new("belt"); bm = bmesh.new()
vs = [(bm.verts.new((x, -BW / 2, z)), bm.verts.new((x, BW / 2, z))) for (x, z) in pts]
for i in range(len(vs)):
    a0, b0 = vs[i]; a1, b1 = vs[(i + 1) % len(vs)]
    bm.faces.new((a0, a1, b1, b0))
bm.to_mesh(me); bm.free()
belt = bpy.data.objects.new("belt", me); scene.collection.objects.link(belt)
belt.data.materials.append(M["belt"])
so = belt.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.1; so.offset = 0
for p in belt.data.polygons: p.use_smooth = True


def glowmat(name, hexcol, strength):
    m = bpy.data.materials.new(name)
    if not m.node_tree: m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*srgb(hexcol), 1); em.inputs[1].default_value = strength
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    return m
M["cone"] = glowmat("cone", "#fff1c4", 1.2)
M["halo"] = glowmat("halo", "#fff6dc", 6.0)
M["redpcb"] = mat("redpcb", "#b8322a", rough=0.45)
M["esp"] = mat("esp", "#1b1d22", rough=0.45, coat=0.3)
M["usb"] = mat("usb", "#3b3e45", rough=0.5)

G("belt")
# wings on PDMS pads, lying flat on the top run; each one hangs on an empty so it can move
WZ = TOP + 0.09
WINGS = []
M["wing_blue"] = mat("wing_blue", "#7f9fc4", rough=0.3, trans=0.3)
M["wing_rainbow"] = mat("wing_rainbow", "#d9d4c8", metal=0.4, rough=0.12, trans=0.2)
try:  # thin-film sheen gives the rainbow look
    M["wing_rainbow"].node_tree.nodes["Principled BSDF"].inputs["Thin Film Thickness"].default_value = 480
except KeyError:
    pass
WINGMAT = {-15.0: "wing_rainbow", -10.0: "wing_blue", -5.0: "wing"}
for x in (-15.0, -10.0, -5.0):
    e = bpy.data.objects.new("wingrig", None); e.location = (x, 0, 0); scene.collection.objects.link(e)
    parts = [box(2.6, 1.8, 0.14, (x, 0, WZ + 0.07), M["pdms"], bevel=0.05)]
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.012, location=(x, 0, WZ + 0.15), vertices=64)
    w = bpy.context.object; w.scale = (1.0, 0.33, 1); assign(w, M[WINGMAT[x]]); parts.append(w)
    for dy, ln in [(-0.12, 1.6), (-0.04, 1.85), (0.05, 1.85), (0.13, 1.6)]:
        parts.append(box(ln, 0.022, 0.012, (x + 0.05, dy, WZ + 0.158), M["vein"]))
    for p in parts:
        p.parent = e; p.matrix_parent_inverse = e.matrix_world.inverted()
    WINGS.append((e, parts, x))
for e, parts, x in WINGS:
    for o in [e] + parts: _seen.add(o.name)

# ---------------------------------------------------------------- housing (dark, light-tight, front open for view)
HX0, HX1, HY0, HY1, HZ0, HZ1, T = -5.5, 5.5, -4.6, 4.6, 0.5, 20.0, 0.35
hcx, hcy, hcz = (HX0 + HX1) / 2, (HY0 + HY1) / 2, (HZ0 + HZ1) / 2
house = box(HX1 - HX0, HY1 - HY0, HZ1 - HZ0, (hcx, hcy, hcz), M["housing"], bevel=0.25, seg=4)
inner = box(HX1 - HX0 - 2 * T, HY1 - HY0 - 2 * T, HZ1 - HZ0 - 2 * T, (hcx, hcy, hcz), M["housing"])
diff(house, inner)
front = box(HX1 - HX0 + 1, 2.0, HZ1 - HZ0 - 2 * T, (hcx, HY0, hcz), M["housing"])
diff(house, front)
slot = box(HX1 - HX0 + 2, BW + 0.6, 2 * r + 0.9, (hcx, 0, RZ), M["housing"])
diff(house, slot)

G("housing")
# window plate with glass under the imaging spot
plate = box(HX1 - HX0 - 2 * T, HY1 - HY0 - 2 * T, 0.15, (hcx, hcy, TOP - 0.13), M["plate"])
hole = box(3.0, 3.0, 1.0, (0, 0, TOP - 0.13), M["plate"])
diff(plate, hole)
box(3.2, 3.2, 0.1, (0, 0, TOP - 0.11), M["glass"])

G("window")
# white LED between the belt runs, shining up through the window
LZ = RZ - 0.2
box(0.3, HY1 - T, 0.3, (0, HY1 / 2 - T / 2, LZ - 0.3), M["plate"])
cyl(0.9, 0.18, (0, 0, LZ - 0.06), M["ledpcb"], verts=6)
box(0.45, 0.45, 0.16, (0, 0, LZ + 0.1), M["led"], bevel=0.03)
bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=1.45, depth=TOP - 0.25 - (LZ + 0.2), location=(0, 0, (TOP - 0.25 + LZ + 0.2) / 2), vertices=64)
assign(bpy.context.object, M["cone"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(0, 0, LZ + 0.22)); assign(bpy.context.object, M["halo"])
lp = bpy.data.lights.new("ledlight", "POINT"); lp.energy = 900; lp.shadow_soft_size = 0.3
lo = bpy.data.objects.new("ledlight", lp); lo.location = (0, 0, LZ + 0.5); scene.collection.objects.link(lo)
sl = bpy.data.lights.new("ledspot", "SPOT"); sl.energy = 3000; sl.spot_size = 0.9; sl.spot_blend = 0.6
so_ = bpy.data.objects.new("ledspot", sl); so_.location = (0, 0, LZ + 0.3); scene.collection.objects.link(so_)
so_.rotation_euler = (math.pi, 0, 0)  # pointing up

G("led")
# camera on an inner shelf, spacer tube, coupling and M12 lens pointing down
CAMZ = 15.0
shelf = box(HX1 - HX0 - 2 * T, HY1 - HY0 - 2 * T, 0.3, (hcx, hcy, CAMZ), M["inner"])
shole = cyl(1.0, 1.0, (0, 0, CAMZ), M["inner"]); diff(shelf, shole)
box(3.8, 3.8, 0.16, (0, 0, CAMZ + 0.4), M["pcb"], bevel=0.03)
cyl(1.25, 0.25, (0, 0, CAMZ + 0.2), M["black"], bevel=0.04)
box(0.8, 0.6, 0.12, (-0.9, -0.9, CAMZ + 0.54), M["chip"])
box(0.4, 2.0, 0.22, (1.6, 0, CAMZ + 0.57), M["white"])
G("camera")
SB = CAMZ - 0.15 - 3.0
cyl(0.85, 3.0, (0, 0, CAMZ - 0.15 - 1.5), M["spacer"], bevel=0.05)
cyl(0.98, 0.45, (0, 0, SB - 0.1), M["alu"], bevel=0.06)
for i in range(10):
    ang = i * 2 * math.pi / 10
    box(0.08, 0.08, 0.4, (1.0 * math.cos(ang), 1.0 * math.sin(ang), SB - 0.1), M["alu"])
cyl(0.62, 0.3, (0, 0, SB - 0.45), M["steel"], bevel=0.03)
for i in range(9):
    cyl(0.58 if i % 2 else 0.55, 0.11, (0, 0, SB - 0.66 - i * 0.11), M["black"], verts=48)
cyl(0.66, 0.8, (0, 0, SB - 2.05), M["black"], bevel=0.05)
cyl(0.6, 0.06, (0, 0, SB - 2.47), M["steel"])
cyl(0.45, 0.03, (0, 0, SB - 2.5), M["lensglass"])

G("lens")
# Raspberry Pi on the right outer wall, straight ribbon through the wall
PX, PZ = HX1 + 0.55, CAMZ - 2.3
for dy in (-3.6, 3.6):
    for dz in (-2.4, 2.4):
        cyl(0.15, 0.45, (HX1 + 0.25, dy, PZ + dz), M["steel"], rot=(0, math.pi / 2, 0), verts=16)
box(0.16, 8.5, 5.6, (PX, 0, PZ), M["pcb"], bevel=0.03)
box(0.12, 1.5, 1.5, (PX + 0.14, 0.6, PZ), M["alu"], bevel=0.03)
box(1.5, 1.6, 1.4, (PX + 0.8, 3.3, PZ + 1.1), M["alu"], bevel=0.05)
box(1.3, 1.6, 1.4, (PX + 0.7, 3.3, PZ - 1.1), M["alu"], bevel=0.05)
box(0.5, 5.0, 0.5, (PX + 0.3, 0.6, PZ + 2.35), M["chip"])
box(1.7 + HX1 - 1.6, 1.6, 0.04, ((1.8 + HX1 + 0.7) / 2, 0, CAMZ + 0.62), M["ribbon"])

G("pi")
# drive: stepper motor, pulleys and drive belt to the right roller
PY_ = -(BW / 2 + 1.75)
cyl(0.35, 2.0, (RX, -(BW / 2 + 1.6), RZ), M["steel"], rot=(math.pi / 2, 0, 0))
RP = cyl(0.75, 0.6, (RX, PY_, RZ), M["alu"], rot=(math.pi / 2, 0, 0), bevel=0.05)
MX, MZ = RX + 5.0, 2.4
cyl(0.18, 1.0, (MX, PY_ + 0.2, MZ), M["steel"], rot=(math.pi / 2, 0, 0))
MP = cyl(0.75, 0.6, (MX, PY_, MZ), M["alu"], rot=(math.pi / 2, 0, 0), bevel=0.05)
MY = PY_ + 0.45 + 2.0
cyl(1.85, 3.6, (MX, MY + 0.2, MZ), M["black"], rot=(math.pi / 2, 0, 0), bevel=0.15)
cyl(1.9, 0.4, (MX, PY_ + 0.55, MZ), M["alu"], rot=(math.pi / 2, 0, 0), bevel=0.08)
c1, c2, rb = Vector((MX, MZ)), Vector((RX, RZ)), 0.8
dv = (c2 - c1).normalized(); nv = Vector((-dv.y, dv.x)); base = math.atan2(nv.y, nv.x)
pts = []
for i in range(25):
    a = base - math.pi * i / 24; pts.append(c2 + rb * Vector((math.cos(a), math.sin(a))))
for i in range(25):
    a = base + math.pi - math.pi * i / 24; pts.append(c1 + rb * Vector((math.cos(a), math.sin(a))))
me = bpy.data.meshes.new("db"); bm = bmesh.new()
vs = [(bm.verts.new((p.x, PY_ - 0.25, p.y)), bm.verts.new((p.x, PY_ + 0.25, p.y))) for p in pts]
for i in range(len(vs)):
    a0, b0 = vs[i]; a1, b1 = vs[(i + 1) % len(vs)]; bm.faces.new((a0, a1, b1, b0))
bm.to_mesh(me); bm.free()
db = bpy.data.objects.new("db", me); scene.collection.objects.link(db); db.data.materials.append(M["black"])
sm = db.modifiers.new("s", "SOLIDIFY"); sm.thickness = 0.12

# orange marks on both pulleys so you can see them turn; each pulley spins on its own empty
M["mark"] = mat("mark", "#eb6834", rough=0.4)
SPIN = []
for pul, (cx, cz) in ((RP, (RX, RZ)), (MP, (MX, MZ))):
    e = bpy.data.objects.new("spin", None); e.location = (cx, PY_, cz); scene.collection.objects.link(e)
    mk = box(0.18, 0.06, 0.55, (cx, PY_ - 0.32, cz + 0.4), M["mark"])
    for o in (pul, mk):
        o.parent = e; o.matrix_parent_inverse = e.matrix_world.inverted()
    SPIN.append(e)
G("motor")
# ESP32 and stepper driver on the base plate in front
EX, EY = 6.0, -8.6
box(5.2, 2.8, 0.15, (EX, EY, 0.6), M["esp"], bevel=0.03)
box(1.8, 1.6, 0.25, (EX + 1.3, EY, 0.8), M["steel"], bevel=0.03)
box(0.8, 0.8, 0.15, (EX - 1.0, EY, 0.75), M["chip"])
box(0.7, 0.8, 0.35, (EX - 2.4, EY, 0.85), M["alu"])
for sgn in (-1, 1):
    box(4.6, 0.25, 0.3, (EX, EY + sgn * 1.25, 0.82), M["chip"])
DX, DY = 12.5, -8.6
box(2.0, 1.6, 0.15, (DX, DY, 0.6), M["redpcb"], bevel=0.03)
box(0.9, 0.9, 0.5, (DX, DY, 0.92), M["alu"])
def wire(pts, col, rad=0.09):
    cu = bpy.data.curves.new("w", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = rad; cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, q in zip(sp.bezier_points, pts):
        bp.co = q; bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new("w", cu); scene.collection.objects.link(o); o.data.materials.append(col)
cols = [M["redpcb"], M["chip"], M["ribbon"], M["lensglass"]]
for k in range(3):
    wire([(EX + 2.6, EY - 0.4 + 0.4 * k, 0.75), (DX - 1.0, DY - 0.4 + 0.4 * k, 0.75)], cols[k], 0.07)
for k in range(4):
    dy = -0.45 + 0.3 * k
    wire([(DX + 1.0, DY + dy, 0.75), (MX - 1.0 + dy, -8.0, 0.7), (MX - 0.3 + dy, PY_ + 1.0, 0.7)], cols[k], 0.07)
wire([(EX - 2.75, EY, 0.85), (EX - 4.5, EY + 1.5, 0.7), (HX1 + 1.2, -6.0, 3.0), (HX1 + 0.9, -3.0, PZ - 2.9)], M["usb"], 0.14)

G("electronics")

RB = RR + 0.04 + 0.06
LTOP = 2 * RX; LARC = math.pi * RB; LOOP = 2 * LTOP + 2 * LARC
def loop_pos(sv):
    # I walk the loop: top run left to right, right arc, bottom run right to left, left arc
    sv %= LOOP
    if sv < LTOP: return (-RX + sv, RZ + RB, 0.0)
    sv -= LTOP
    if sv < LARC:
        a = math.pi / 2 - sv / RB; return (RX + RB * math.cos(a), RZ + RB * math.sin(a), sv / RB)
    sv -= LARC
    if sv < LTOP: return (RX - sv, RZ - RB, math.pi)
    sv -= LTOP
    a = -math.pi / 2 - sv / RB; return (-RX + RB * math.cos(a), RZ + RB * math.sin(a), math.pi + sv / RB)
TICKS = []
for i in range(int(LOOP / 2.0)):
    o = box(0.7, 0.35, 0.02, (0, -BW / 2 + 0.3, 0), M["usb"]); TICKS.append((o, i * LOOP / int(LOOP / 2.0)))

# ---------------------------------------------------------------- studio
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
assign(bpy.context.object, M["floor"])
world = bpy.data.worlds.new("w"); scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

def area(loc, size, power):
    L = bpy.data.lights.new("a", "AREA"); L.size = size; L.energy = power
    o = bpy.data.objects.new("a", L); o.location = loc; scene.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 6)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
area((-25, -30, 45), 35, 60000)
area((35, -15, 25), 25, 18000)
area((5, -14, 12), 6, 1500)

cam = bpy.data.cameras.new("cam"); cam.lens = 50
co = bpy.data.objects.new("cam", cam); scene.collection.objects.link(co); scene.camera = co
co.location = (20.0, -70.0, 22.0)
tgt = Vector((3.5, -3.0, 8.5))
co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()

scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
scene.cycles.samples = SPP; scene.cycles.use_denoising = True
scene.cycles.max_bounces = 10; scene.cycles.transmission_bounces = 10
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.35

# ---------------------------------------------------------------- timing
# Change these numbers to slow the video down or speed it up (all in seconds).
PART_GAP = 1.6     # time between one part and the next during assembly
PART_FALL = 1.4    # how long each part takes to drop into place
WING_GAP = 0.8     # time between one wing and the next
WING_FALL = 1.0    # how long each wing takes to land on the belt
MOVE_TIME = 2.0    # one step of the belt
STOP_TIME = 2.0    # how long a wing waits under the lens (the capture happens here)
END_HOLD = 4.0     # final shot at the end

FPS = 24
scene.render.fps = FPS
F = lambda t: int(round(t * FPS)) + 1
ORDER = ["plate", "rollers", "belt", "window", "led", "housing", "camera", "lens", "pi", "motor", "electronics"]
T_PART = {n: 0.3 + i * PART_GAP for i, n in enumerate(ORDER)}
T_WINGS = T_PART[ORDER[-1]] + PART_FALL + 0.4
T_LED = T_WINGS + 2 * WING_GAP + WING_FALL + 0.4
T_BELT = T_LED + 1.2
MOVES = [T_BELT + k * (MOVE_TIME + STOP_TIME) for k in range(3)]
T_END = MOVES[-1] + MOVE_TIME + STOP_TIME
TOTAL = T_END + END_HOLD
scene.frame_start, scene.frame_end = 1, int(TOTAL * FPS)

def appear(objs, t0, dur, off=(0, 0, 14)):
    # I hide the part until t0, then drop it into place over dur seconds
    for o in objs:
        if o.parent is not None and o.parent in objs: continue
        fin = o.location.copy()
        o.location = fin + Vector(off); o.keyframe_insert("location", frame=F(t0))
        o.location = fin; o.keyframe_insert("location", frame=F(t0 + dur))
    for o in objs:
        for ob in [o] + list(o.children_recursive):
            if ob.type == "EMPTY": continue
            ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1)
            ob.hide_render = True; ob.keyframe_insert("hide_render", frame=max(1, F(t0) - 1))
            ob.hide_render = False; ob.keyframe_insert("hide_render", frame=F(t0))

for name in ORDER:
    t0 = T_PART[name]
    objs = [o for o in GROUPS[name] if not (o.type == "MESH" and o.hide_render)]
    for o in [o for o in GROUPS[name] if o.hide_render]:  # boolean cutters fall with their part
        fin = o.location.copy()
        o.location = fin + Vector((0, 0, 14)); o.keyframe_insert("location", frame=F(t0))
        o.location = fin; o.keyframe_insert("location", frame=F(t0 + PART_FALL))
    off = (8, 0, 0) if name == "pi" else (0, 0, 14)
    appear([o for o in objs if o.type != "LIGHT"], t0, PART_FALL, off)
T_TICKS = T_PART["belt"] + PART_FALL
for o, s0 in TICKS:
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=F(T_TICKS))
for k, (e, parts, x) in enumerate(WINGS):
    appear([e], T_WINGS + WING_GAP * (2 - k), WING_FALL, off=(0, 0, 9))

# LED off until T_LED, then on and staying on
def node_key(m, sock, vals):
    n = next(n for n in m.node_tree.nodes if sock in n.inputs)
    for t, v in vals:
        n.inputs[sock].default_value = v; n.inputs[sock].keyframe_insert("default_value", frame=F(t))
node_key(M["led"], "Emission Strength", [(0, 0.0), (T_LED, 0.0), (T_LED + 0.4, 40.0)])
for nm, full in (("cone", 1.2), ("halo", 6.0)):
    em = next(n for n in M[nm].node_tree.nodes if n.type == "EMISSION")
    for t, v in [(0, 0.0), (T_LED, 0.0), (T_LED + 0.4, full)]:
        em.inputs[1].default_value = v; em.inputs[1].keyframe_insert("default_value", frame=F(t))
for L, full in ((lp, 900), (sl, 3000)):
    for t, v in [(0, 0.0), (T_LED, 0.0), (T_LED + 0.4, full)]:
        L.energy = v; L.keyframe_insert("energy", frame=F(t))

# belt travel d(t): three steps of 5 cm, each followed by a stop under the lens
STEP = 5.0
def travel(t):
    d = 0.0
    for t0 in MOVES:
        u = min(max((t - t0) / MOVE_TIME, 0.0), 1.0)
        d += STEP * u * u * (3 - 2 * u)
    return d
RRb = RR + 0.04
for fr in range(1, scene.frame_end + 1):
    d = travel((fr - 1) / FPS)
    if fr >= F(T_LED):
        for e, parts, x in WINGS:
            e.location = (x + d, 0, 0); e.keyframe_insert("location", frame=fr)
    for e in SPIN:
        e.rotation_euler = (0, d / RRb, 0); e.keyframe_insert("rotation_euler", frame=fr)
    for o, s0 in TICKS:
        px, pz, ang = loop_pos(s0 + d)
        o.location = (px, -BW / 2 + 0.3, pz); o.rotation_euler = (0, ang, 0)
        o.keyframe_insert("location", frame=fr); o.keyframe_insert("rotation_euler", frame=fr)

# spans where something in the 3D scene moves; frames outside them are copies, not renders
BUSY = [(T_PART[n], T_PART[n] + PART_FALL) for n in ORDER] + [(T_TICKS - 0.1, T_TICKS + 0.1)]
BUSY += [(T_WINGS, T_WINGS + 2 * WING_GAP + WING_FALL), (T_LED, T_LED + 0.4)]
BUSY += [(t0, t0 + MOVE_TIME) for t0 in MOVES]
busy = lambda t: any(a0 - 0.1 <= t <= a1 + 0.1 for a0, a1 in BUSY)

# the overlay script reads the same timing so labels and captions stay in step
json.dump({"parts": T_PART, "wings": T_WINGS, "wings_end": T_WINGS + 2 * WING_GAP + WING_FALL,
           "led": T_LED, "belt": T_BELT, "moves": MOVES, "move_time": MOVE_TIME, "stop_time": STOP_TIME,
           "end": T_END, "total": TOTAL}, open(OUT.rstrip("/") + "_timeline.json", "w"), indent=1)

scene.render.use_persistent_data = True
anchors = {
    "camera": (1.9, -1.9, CAMZ + 0.48), "spacer": (0.75, -0.45, CAMZ - 1.6), "lens": (0.62, -0.2, SB - 1.0),
    "lensfront": (0, 0, SB - 2.52), "housing": (HX0 + 0.1, 2.0, 18.0), "wing": (-5.0 + 0.3, -0.1, WZ + 0.16),
    "wingspot": (0, 0, WZ + 0.16), "belt": (-14.0, -BW / 2 + 0.3, TOP + 0.05), "window": (1.55, -1.55, TOP - 0.07),
    "led": (0.0, -0.3, LZ + 0.2), "pi": (PX + 0.1, -3.0, PZ + 1.0), "motor": (MX + 1.3, MY, MZ + 1.3),
    "drivebelt": ((RX + MX) / 2, PY_ - 0.25, (MZ + RZ) / 2 + 0.8), "esp32": (EX - 1.0, EY - 1.4, 0.7),
    "driver": (DX, DY - 0.8, 0.7),
}
bpy.context.view_layer.update()
json.dump({k: [world_to_camera_view(scene, co, Vector(p)).x * W,
               (1 - world_to_camera_view(scene, co, Vector(p)).y) * H] for k, p in anchors.items()},
          open(OUT.rstrip("/") + "_anchors.json", "w"), indent=1)

if len(ARGS) > 4:  # a single frame, handy for a quick check
    scene.frame_set(int(ARGS[4])); scene.render.filepath = OUT.rstrip("/") + "_test.png"
    bpy.ops.render.render(write_still=True)
else:
    import os, shutil
    os.makedirs(OUT, exist_ok=True)
    prev = None
    for fr in range(1, scene.frame_end + 1, 2):  # every second frame, so 12 per second
        path = os.path.join(OUT, f"f_{fr:04d}.png")
        if prev and not busy((fr - 1) / FPS):
            shutil.copy(prev, path); continue
        scene.frame_set(fr); scene.render.filepath = path
        bpy.ops.render.render(write_still=True); prev = path
print("DONE")
