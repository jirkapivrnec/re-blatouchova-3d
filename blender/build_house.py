# Blatouchová 1111 – parametric house model.
# Run inside Blender (exec via MCP). Builds scene "Blatouchova" from ../pudorys.json,
# every building part is its own object tagged with custom props:
#   stage  – build phase used by the web scroll timeline
#   order  – sort key inside the stage
#   anim   – suggested entrance animation (rise / drop / pop / tile / grow / fade)
# Plan coordinates are centimetres (x right, y down = towards the street).
# Blender: X = x/100, Y = -y/100, Z up (metres).

import bpy, bmesh, math, json
from mathutils import Vector

ROOT = "/Users/jp/Dev/Real Estate/Blatouchova"
PLAN = json.load(open(ROOT + "/pudorys.json"))
OUT_GLB = ROOT + "/web/public/models/house.glb"

# ---------------------------------------------------------------- scene
SCN = "Blatouchova"
scene = bpy.data.scenes.get(SCN) or bpy.data.scenes.new(SCN)


def _rm_coll(c):
    for ch in list(c.children):
        _rm_coll(ch)
        bpy.data.collections.remove(ch)


for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
_rm_coll(scene.collection)
for me in list(bpy.data.meshes):
    if me.users == 0:
        bpy.data.meshes.remove(me)

COLL = {}


def coll(stage):
    if stage not in COLL:
        c = bpy.data.collections.new("B_" + stage)
        scene.collection.children.link(c)
        COLL[stage] = c
    return COLL[stage]


# ---------------------------------------------------------------- materials
def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


MATDEF = {
    "Facade": ("e9d7a0", 0.92, 0),
    "Plaster": ("f0ede7", 0.95, 0),
    "Brick": ("7a3527", 0.85, 0),
    "Concrete": ("8f8b85", 0.95, 0),
    "RoofTile": ("9d4628", 0.72, 0),
    "WoodTrim": ("5a2f19", 0.6, 0),
    "WindowFrame": ("5e3420", 0.5, 0),
    "Glass": ("a9c7d6", 0.05, 0, 0.25),
    "Oak": ("c08a52", 0.6, 0),
    "OakDoor": ("c98a45", 0.55, 0),
    "FloorTile": ("6f6c6a", 0.5, 0),
    "Terracotta": ("94442c", 0.7, 0),
    "StoneTile": ("b9a88e", 0.6, 0),
    "DarkTile": ("4a3f3b", 0.45, 0),
    "Carpet": ("cbbda3", 1.0, 0),
    "CarpetGreen": ("7f8b78", 1.0, 0),
    "White": ("f4f4f2", 0.4, 0),
    "Black": ("1c1c1e", 0.4, 0),
    "Counter": ("2b2b2e", 0.3, 0),
    "Sofa": ("d98c83", 0.95, 0),
    "Cushion": ("e5dba0", 0.95, 0),
    "Linen": ("eeeae2", 0.9, 0),
    "Walnut": ("6a4a35", 0.5, 0),
    "LightWood": ("d8b17a", 0.6, 0),
    "Metal": ("b8bcc0", 0.3, 0.9),
    "Steel": ("3a3d42", 0.4, 0.7),
    "CarPaint": ("2d3a48", 0.25, 0.6),
    "Rubber": ("161616", 0.9, 0),
    "Gutter": ("6b3a22", 0.4, 0.5),
    "Pavers": ("8e5446", 0.85, 0),
    "Lawn": ("4f6b35", 1.0, 0),
    "Hedge": ("2f4a2a", 1.0, 0),
    "Spruce": ("3e5c56", 1.0, 0),
    "Foliage": ("6b3a44", 1.0, 0),
    "Bark": ("4a3426", 1.0, 0),
    "Water": ("4fa3c7", 0.05, 0, 0.6),
    "PoolFrame": ("d5d8db", 0.5, 0),
    "Fireplace": ("141414", 0.3, 0),
    "AccentYellow": ("e2b33a", 0.8, 0),
    "AccentRed": ("9e2a2b", 0.7, 0),
    "AccentBlue": ("3d6e9e", 0.8, 0),
    "Asphalt": ("2e2f31", 0.95, 0),
    "Firewood": ("8a5a36", 1.0, 0),
    "Fabric": ("6d7f8c", 1.0, 0),
    "Fence": ("5b3a28", 0.8, 0),
}


def get_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    hexc, rough, metal, *rest = MATDEF[name]
    alpha = rest[0] if rest else 1.0
    try:
        if not m.use_nodes:
            m.use_nodes = True
    except Exception:
        pass
    rgb = tuple(_lin(int(hexc[i:i + 2], 16)) for i in (0, 2, 4))
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Alpha'].default_value = alpha
    m.diffuse_color = (*rgb, alpha)
    if alpha < 1:
        for attr, val in (("blend_method", 'BLEND'), ("surface_render_method", 'BLENDED')):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    return m


# ---------------------------------------------------------------- mesh builder
class MB:
    def __init__(s):
        s.v, s.f, s.fm, s.mats = [], [], [], []

    def mi(s, name):
        if name not in s.mats:
            s.mats.append(name)
        return s.mats.index(name)

    def prism(s, bot, top, mb, mt=None, ms=None):
        mt = mt or mb
        ms = ms or mb
        n = len(bot)
        i0 = len(s.v)
        s.v.extend(bot)
        s.v.extend(top)
        s.f.append([i0 + k for k in range(n)][::-1]); s.fm.append(s.mi(mb))
        s.f.append([i0 + n + k for k in range(n)]); s.fm.append(s.mi(mt))
        for k in range(n):
            k2 = (k + 1) % n
            s.f.append([i0 + k, i0 + k2, i0 + n + k2, i0 + n + k])
            s.fm.append(s.mi(ms[k] if isinstance(ms, list) else ms))

    def box(s, x0, y0, x1, y1, z0, z1, m, mt=None):
        X0, X1 = sorted((x0 / 100, x1 / 100))
        Ya, Yb = sorted((-y0 / 100, -y1 / 100))
        b = [(X0, Ya, z0), (X1, Ya, z0), (X1, Yb, z0), (X0, Yb, z0)]
        t = [(p[0], p[1], z1) for p in b]
        s.prism(b, t, m, mt, m)

    def cyl_z(s, x, y, r, z0, z1, m, seg=16, r1=None, rot=0.0):
        r1 = r if r1 is None else r1
        b, t = [], []
        for k in range(seg):
            a = 2 * math.pi * k / seg + rot
            b.append((x / 100 + r / 100 * math.cos(a), -y / 100 + r / 100 * math.sin(a), z0))
            t.append((x / 100 + r1 / 100 * math.cos(a), -y / 100 + r1 / 100 * math.sin(a), z1))
        s.prism(b, t, m)

    def cyl_x(s, x0, x1, y, z, r, m, seg=14):
        b, t = [], []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            yy, zz = -y / 100 + r / 100 * math.cos(a), z + r / 100 * math.sin(a)
            b.append((x0 / 100, yy, zz)); t.append((x1 / 100, yy, zz))
        s.prism(b, t, m)

    def cyl_y(s, y0, y1, x, z, r, m, seg=10):
        b, t = [], []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            xx, zz = x / 100 + r / 100 * math.cos(a), z + r / 100 * math.sin(a)
            b.append((xx, -y0 / 100, zz)); t.append((xx, -y1 / 100, zz))
        s.prism(b, t, m)


def make(name, mb, stage, order, anim, **extra):
    if not mb.f:
        return None
    me = bpy.data.meshes.new(name)
    me.from_pydata(mb.v, [], mb.f)
    me.update()
    for nm in mb.mats:
        me.materials.append(get_mat(nm))
    for p, mi in zip(me.polygons, mb.fm):
        p.material_index = mi
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        nx, ny, nz = (abs(c) for c in p.normal)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if nz >= nx and nz >= ny:
                uv = (co.x, co.y)
            elif nx >= ny:
                uv = (co.y, co.z)
            else:
                uv = (co.x, co.z)
            uvl.data[li].uv = uv
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    o = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in me.vertices:
        v.co -= o
    ob = bpy.data.objects.new(name, me)
    ob.location = o
    coll(stage).objects.link(ob)
    ob["stage"] = stage
    ob["order"] = float(order)
    ob["anim"] = anim
    for k, v in extra.items():
        ob[k] = v
    return ob


# ---------------------------------------------------------------- key levels
GF_WALL = 2.90          # interior walls ground floor
SLAB_TOP = 3.13         # structural slab top / ext. wall top GF
UF = 3.15               # upper floor finish level
UF_CEIL = 5.75          # flat part of upper ceiling
H_E = 4.35              # knee wall top at outer face
T = math.tan(math.radians(40))
Y_OUT_F, Y_OUT_B = -5.10, 5.05      # outer faces (Blender Y)
YC = (Y_OUT_F + Y_OUT_B) / 2
D2 = (Y_OUT_B - Y_OUT_F) / 2
X_OUT_L, X_OUT_R = -5.15, 6.90
OV_E, OV_G = 0.60, 0.50             # eave / gable overhang
XE_L, XE_R = X_OUT_L - OV_G, X_OUT_R + OV_G
YE_F, YE_B = Y_OUT_F - OV_E, Y_OUT_B + OV_E
CG_X0, CG_X1 = -1.60, 3.35          # front cross gable (outer)
CG_XC = (CG_X0 + CG_X1) / 2
CG_HALF = (CG_X1 - CG_X0) / 2
CG_T = 1.0                           # 45°
CG_RIDGE = H_E + CG_HALF * CG_T
CG_C_Y = YC - (D2 - (CG_RIDGE - H_E) / T)    # where cross ridge meets main slope
A_L = (CG_X0 - OV_G, YE_F)
A_R = (CG_X1 + OV_G, YE_F)
RAF = 0.16                          # rafter depth
TILE = 0.14                         # tile layer
STEP = 0.035                        # tile course step


def main_z(Y):
    return H_E + (D2 - abs(Y - YC)) * T


def cross_z(X):
    return H_E + (CG_HALF - abs(X - CG_XC)) * CG_T


def roof_under(X, Y):
    z = main_z(Y)
    if Y < YC and CG_X0 <= X <= CG_X1:
        z = max(z, cross_z(X))
    return z


def valley_y(X):
    """Y of the valley line at X (front slope), or None outside cross gable."""
    if A_L[0] <= X <= CG_XC:
        return A_L[1] + (X - A_L[0]) / (CG_XC - A_L[0]) * (CG_C_Y - A_L[1])
    if CG_XC <= X <= A_R[0]:
        return A_R[1] + (A_R[0] - X) / (A_R[0] - CG_XC) * (CG_C_Y - A_R[1])
    return None


def plan_roof_under(x, y):
    return roof_under(x / 100, -y / 100)


# ---------------------------------------------------------------- plan data
NODES, WALLS, OPEN = PLAN["nodes"], PLAN["walls"], PLAN["openings"]
UF_DX = 1768


def n_gf(i):
    n = NODES[i]
    return (n["x"], n["y"])


def n_uf(i):
    n = NODES[i]
    y = -490 if abs(n["y"] + 408) < 1 else n["y"]
    return (n["x"] - UF_DX, y)


GF_W = {k: w for k, w in WALLS.items() if NODES[w["a"]]["x"] < 1000}
UF_W = {k: w for k, w in WALLS.items() if NODES[w["a"]]["x"] >= 1000}

GF_FOOT = [(-500, -490), (675, -490), (675, 495), (625, 495), (625, 433), (350, 433), (350, 495),
           (300, 495), (300, 433), (-125, 433), (-125, 495), (-500, 495)]
UF_FOOT = [(-500, -490), (675, -490), (675, 495), (-500, 495)]


def inside(poly, x, y):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def wall_frame(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    return L, dx, dy, -dy, dx


def u_of(a, dx, dy, at):
    return (at - a[0]) * dx if abs(dx) > 0.5 else (at - a[1]) * dy


def build_wall(mb, a, b, thick, z0, topfn, ops=(), ext=0.0, exterior=False, foot=None,
               zsplit=(), facade=None, dense=False, kinks=()):
    L, dx, dy, nx, ny = wall_frame(a, b)
    sout = 0
    if exterior:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        sout = -1 if inside(foot, mx + nx * 40, my + ny * 40) else 1
    u0, u1 = -ext, L + ext
    cuts = {u0, u1}
    O = []
    for o in ops:
        uc = u_of(a, dx, dy, o["at"])
        O.append((uc - o["w"] / 2, uc + o["w"] / 2, o["sill"], o["head"]))
        cuts |= {uc - o["w"] / 2, uc + o["w"] / 2}
    for k in kinks:
        cuts.add(u_of(a, dx, dy, k))
    if dense:
        k = u0
        while k < u1:
            cuts.add(k)
            k += 20
    cuts = sorted({round(c, 1) for c in cuts if u0 - 1e-6 <= c <= u1 + 1e-6})
    for ua, ub in zip(cuts, cuts[1:]):
        mid = (ua + ub) / 2
        op = next((o for o in O if o[0] - 1e-3 <= mid <= o[1] + 1e-3), None)
        pa = (a[0] + dx * ua, a[1] + dy * ua)
        pb = (a[0] + dx * ub, a[1] + dy * ub)
        ta, tb = topfn(*pa), topfn(*pb)
        spans = []
        if op:
            if op[2] > z0 + 1e-3:
                spans.append((z0, z0, op[2], op[2]))
            if op[3] < min(ta, tb) - 1e-3:
                spans.append((op[3], op[3], ta, tb))
        else:
            spans.append((z0, z0, ta, tb))
        pieces = []
        for sp in spans:
            cur = [sp]
            for zs in zsplit:
                nxt = []
                for (a0, b0, a1, b1) in cur:
                    if abs(a0 - b0) < 1e-6 and a0 < zs < min(a1, b1) - 1e-3:
                        nxt += [(a0, b0, zs, zs), (zs, zs, a1, b1)]
                    else:
                        nxt.append((a0, b0, a1, b1))
                cur = nxt
            pieces += cur
        pm = (a[0] + dx * mid, a[1] + dy * mid)
        for (za0, zb0, za1, zb1) in pieces:
            zmid = (za0 + zb0 + za1 + zb1) / 4
            prof = [(ua, za0), (ub, zb0), (ub, zb1), (ua, za1)]

            def P3(u, z, side):
                x = a[0] + dx * u + nx * side * thick / 2
                y = a[1] + dy * u + ny * side * thick / 2
                return (x / 100, -y / 100, z)

            bot = [P3(u, z, -1) for u, z in prof]
            top = [P3(u, z, 1) for u, z in prof]
            if exterior:
                fac = facade(pm[0], pm[1], zmid) if facade else "Facade"
                m_minus = fac if sout == -1 else "Plaster"
                m_plus = fac if sout == 1 else "Plaster"
                mb.prism(bot, top, m_minus, m_plus, fac)
            else:
                mb.prism(bot, top, "Plaster")
    return sout, (dx, dy, nx, ny, L)


def facade_fn(x, y, z):
    if z < 0.45:
        return "Brick"
    if abs(x - 675) < 30 and 75 <= y <= 225:
        return "Brick"
    return "Facade"


# ---------------------------------------------------------------- openings spec
def op(at, w, sill, head, kind):
    return {"at": at, "w": w, "sill": sill, "head": head, "kind": kind}


def json_door(oid, a, b, sill=0.0, head=2.05, w=None):
    o = OPEN[oid]
    L, dx, dy, nx, ny = wall_frame(a, b)
    p = (a[0] + dx * o["t"], a[1] + dy * o["t"])
    at = p[0] if abs(dx) > 0.5 else p[1]
    return op(at, w or o["width"], sill, head, "door_int")


GF_OPS = {
    "w35": [op(-320, 140, 0.9, 2.3, "win")],
    "w39": [op(121, 150, 0.0, 2.35, "door_ext")],
    "w48": [op(487, 250, 0.0, 2.2, "garage")],
    "w33": [op(330, 140, 0.9, 2.3, "win"), op(150, 90, 0.0, 2.3, "french"),
            op(-90, 90, 0.0, 2.3, "french"), op(-330, 140, 0.9, 2.3, "win")],
    "w28": [op(-330, 140, 0.9, 2.3, "win"), op(-20, 150, 1.05, 2.3, "win")],
    "w76": [op(300, 140, 0.9, 2.3, "win")],
    "w81": [op(588, 60, 1.5, 2.1, "win")],
    "w120": [op(-200, 70, 1.4, 2.1, "win")],
    "w92": [op(150, 100, 1.0, 2.1, "win")],
}
GF_DOORS = {"o106": "w102", "o110": "w99", "o111": "w90", "o112": "w105", "o122": "w118", "o108": "w88"}
GF_EXTRA_DOORS = {"w116": [op(290, 80, 0.0, 2.05, "door_int")]}

UF_OPS = {
    "w146": [op(87.5, 240, UF, UF + 2.30, "french")],
    "w130": [op(150, 90, UF, UF + 2.25, "french")],
    "w166": [op(-90, 90, UF, UF + 2.25, "french")],
    "w151": [op(150, 100, UF, UF + 2.25, "french")],
    "w127": [op(-250, 70, UF + 1.30, UF + 1.90, "win")],
}
UF_DOORS = {"o177": "w164", "o178": "w135", "o179": "w152", "o180": "w171", "o181": "w159", "o182": "w139"}


# ---------------------------------------------------------------- opening objects
def build_opening(name, a, b, thick, o, sout, z_floor, stage, order):
    L, dx, dy, nx, ny = wall_frame(a, b)
    uc = u_of(a, dx, dy, o["at"])
    u0, u1 = uc - o["w"] / 2, uc + o["w"] / 2
    sill, head, kind = o["sill"], o["head"], o["kind"]
    mb = MB()

    def lbox(ua, ub, na, nb, za, zb, m):
        pts = [(a[0] + dx * u + nx * n, a[1] + dy * u + ny * n) for u in (ua, ub) for n in (na, nb)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        mb.box(min(xs), min(ys), max(xs), max(ys), za, zb, m)

    if kind == "door_int":
        jd = thick / 2 + 1.5
        fw = 6
        lbox(u0, u0 + fw, -jd, jd, sill, head, "OakDoor")
        lbox(u1 - fw, u1, -jd, jd, sill, head, "OakDoor")
        lbox(u0, u1, -jd, jd, head - 0.06, head, "OakDoor")
        lbox(u0 + fw, u1 - fw, -2, 2, sill + 0.01, head - 0.06, "Oak")
        gl0, gl1 = u0 + fw + 18, u1 - fw - 18
        for k in range(4):
            za = sill + 0.35 + k * 0.38
            lbox(gl0, gl1, -2.6, 2.6, za, za + 0.28, "Glass")
        lbox(u1 - fw - 10, u1 - fw - 4, -5, 5, sill + 1.0, sill + 1.04, "Metal")
        return make(name, mb, stage, order, "pop")

    off = sout * (thick / 2 - 7)
    na, nb = off - 4, off + 4
    fw = 7
    if kind == "garage":
        n0 = sout * (thick / 2 - 4)
        lbox(u0, u1, n0 - 3, n0 + 3, sill, head, "WindowFrame")
        for k in range(1, 5):
            z = sill + k * (head - sill) / 5
            lbox(u0 + 2, u1 - 2, n0 + sout * 3 - 0.6, n0 + sout * 3 + 0.6, z - 0.012, z + 0.012, "Gutter")
        return make(name, mb, stage, order, "rise")
    lbox(u0, u0 + fw, na, nb, sill, head, "WindowFrame")
    lbox(u1 - fw, u1, na, nb, sill, head, "WindowFrame")
    lbox(u0, u1, na, nb, head - fw / 100, head, "WindowFrame")
    lbox(u0, u1, na, nb, sill, sill + fw / 100, "WindowFrame")
    mull = []
    if kind == "door_ext":
        mull = [u0 + 32, u1 - 32]
        lbox(uc - 2, uc + 2, nb, nb + 2, sill + 1.0, sill + 1.25, "Metal")
    elif o["w"] >= 110:
        mull = [uc]
    for m in mull:
        lbox(m - 3.5, m + 3.5, na, nb, sill, head, "WindowFrame")
    if kind == "win" and head - sill > 1.0:
        zt = head - 0.45
        lbox(u0, u1, na, nb, zt - 0.03, zt + 0.03, "WindowFrame")
    lbox(u0 + fw, u1 - fw, off - 1, off + 1, sill + fw / 100, head - fw / 100, "Glass")
    if kind == "win" and z_floor < 1:
        face = sout * thick / 2
        lbox(u0 - 3, u1 + 3, face - sout * 2, face + sout * 6, sill - 0.03, sill, "Gutter")
    return make(name, mb, stage, order, "pop")


# ---------------------------------------------------------------- build: site
def site():
    mb = MB()
    mb.box(-1300, -1700, 1500, 1600, -0.35, -0.15, "Lawn")
    make("Site_Lawn", mb, "site", 0, "none")
    mb = MB()
    mb.box(-3200, 1630, 3400, 2400, -0.32, -0.20, "Asphalt")
    mb.box(-3200, 1600, 3400, 1630, -0.32, -0.12, "Concrete")
    make("Site_Street", mb, "site", 1, "none")


# ---------------------------------------------------------------- build: foundation & floors
def foundation():
    mb = MB()
    for r in [(-515, -505, 690, 448), (-515, 448, -110, 510), (285, 448, 365, 510), (610, 448, 690, 510)]:
        mb.box(*r, -0.55, 0.0, "Concrete")
    make("Foundation_Slab", mb, "foundation", 0, "rise")
    mb = MB()
    mb.box(-110, 448, 285, 660, -0.2, -0.02, "Terracotta")
    make("Foundation_Porch", mb, "foundation", 1, "rise")


ROOMS_GF = [
    ("Living", "Oak", [(-500, -27, -135, 495)]),
    ("Kitchen", "FloorTile", [(-500, -490, 99, -27)]),
    ("Hall", "FloorTile", [(-135, -27, 350, 252), (99, -169, 350, -27)]),
    ("Entry", "FloorTile", [(-135, 252, 350, 433)]),
    ("Bedroom", "Oak", [(99, -490, 501, -169)]),
    ("Boiler", "FloorTile", [(501, -490, 675, -358)]),
    ("Bath", "StoneTile", [(350, -169, 675, -39), (501, -358, 675, -169)]),
    ("Garage", "Terracotta", [(350, -39, 675, 433)]),
]
ROOMS_UF = [
    ("BedroomFront", "Carpet", [(-500, 45, -62.5, 495)]),
    ("KidsRoom", "CarpetGreen", [(-500, -490, -62.5, 45)]),
    ("Gallery", "Oak", [(-62.5, -185, 120, 495), (215, -185, 324.7, 495), (120, -185, 215, -100),
                        (120, 235, 215, 495), (324.7, -185, 454.7, -65)]),
    ("WC", "DarkTile", [(-62.5, -490, 115.9, -185)]),
    ("Closet", "DarkTile", [(115.9, -490, 293.9, -185)]),
    ("Bathroom", "DarkTile", [(293.9, -490, 675, -185), (454.7, -185, 675, -65)]),
    ("Office", "Carpet", [(324.7, -65, 675, 495)]),
]


def floors(rooms, z0, stage, prefix):
    for i, (nm, mat, rects) in enumerate(rooms):
        mb = MB()
        for r in rects:
            mb.box(*r, z0, z0 + 0.02, mat)
        make(f"{prefix}_Floor_{nm}", mb, stage, i, "fade")


# ---------------------------------------------------------------- build: walls
def angle_order(a, b):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ang = math.atan2(my - 0, mx - 90)
    return (ang + math.pi) / (2 * math.pi)


def gf_walls():
    for k, w in GF_W.items():
        a, b = n_gf(w["a"]), n_gf(w["b"])
        ext = w["type"] == "exterior"
        ops = list(GF_OPS.get(k, [])) + list(GF_EXTRA_DOORS.get(k, []))
        for oid, wid in GF_DOORS.items():
            if wid == k:
                ops.append(json_door(oid, a, b))
        mb = MB()
        if ext:
            kinks = [75, 225] if abs(a[0] - 675) < 1 and abs(b[0] - 675) < 1 else []
            sout, _ = build_wall(mb, a, b, w["thickness"], 0.0, lambda x, y: SLAB_TOP, ops, ext=15,
                                 exterior=True, foot=GF_FOOT, zsplit=(0.45,), facade=facade_fn, kinks=kinks)
            make(f"GF_ExtWall_{k}", mb, "gf_walls_ext", angle_order(a, b), "rise")
        else:
            sout, _ = build_wall(mb, a, b, w["thickness"], 0.0, lambda x, y: GF_WALL, ops, ext=4)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            make(f"GF_IntWall_{k}", mb, "gf_walls_int", math.hypot(mx - 90, my), "rise")
        for i, o in enumerate(ops):
            make_o = build_opening(f"GF_{'Door' if o['kind'] in ('door_int', 'door_ext', 'garage') else 'Window'}_{k}_{i}",
                                   a, b, w["thickness"], o, sout if ext else 0, 0.0, "gf_openings",
                                   angle_order(a, b) + i * 0.01)
            if make_o and o["kind"] in ("win", "french", "door_ext"):
                make_o["glow"] = 1


def uf_walls():
    for k, w in UF_W.items():
        a, b = n_uf(w["a"]), n_uf(w["b"])
        ext = w["type"] == "exterior"
        ops = list(UF_OPS.get(k, []))
        for oid, wid in UF_DOORS.items():
            if wid == k:
                o = OPEN[oid]
                # door t refers to the original (unshifted) node geometry
                a0 = (NODES[w["a"]]["x"] - UF_DX, NODES[w["a"]]["y"])
                b0 = (NODES[w["b"]]["x"] - UF_DX, NODES[w["b"]]["y"])
                d = json_door(oid, a0, b0, UF, UF + 2.05)
                ops.append(d)
        mb = MB()
        along_y = abs(a[0] - b[0]) < 1
        if ext:
            kinks = [-YC * 100] if along_y else [CG_X0 * 100, CG_XC * 100, CG_X1 * 100]
            if along_y and abs(a[0] - 675) < 1:
                kinks += [75, 225]
            sout, _ = build_wall(mb, a, b, w["thickness"], SLAB_TOP, plan_roof_under, ops, ext=15,
                                 exterior=True, foot=UF_FOOT, facade=facade_fn, dense=True, kinks=kinks)
            make(f"UF_ExtWall_{k}", mb, "uf_walls_ext", angle_order(a, b), "rise")
        else:
            top = lambda x, y: min(UF_CEIL, plan_roof_under(x, y) - 0.01)
            sout, _ = build_wall(mb, a, b, w["thickness"], UF, top, ops, ext=4, dense=along_y,
                                 kinks=[-YC * 100] if along_y else [])
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            make(f"UF_IntWall_{k}", mb, "uf_walls_int", math.hypot(mx - 90, my), "rise")
        for i, o in enumerate(ops):
            ob = build_opening(f"UF_{'Door' if o['kind'] == 'door_int' else 'Window'}_{k}_{i}", a, b,
                               w["thickness"], o, sout if ext else 0, UF, "uf_openings",
                               angle_order(a, b) + i * 0.01)
            if ob and o["kind"] in ("win", "french"):
                ob["glow"] = 1


def chimney():
    mb = MB()
    mb.box(-135, -27, -54, 38, 0.0, 3.13, "Plaster")
    make("GF_Chimney", mb, "gf_walls_int", 0, "rise")
    mb = MB()
    mb.box(-135, -27, -54, 38, 3.13, 8.4, "Plaster")
    make("UF_Chimney", mb, "uf_walls_int", 0, "rise")
    mb = MB()
    mb.box(-135, -27, -54, 38, 8.4, 9.55, "Facade")
    mb.box(-142, -34, -47, 45, 9.55, 9.65, "Concrete")
    mb.box(-125, -17, -64, 28, 9.65, 9.72, "Steel")
    make("Roof_Chimney", mb, "roof_details", 0, "rise")


# ---------------------------------------------------------------- slab, balconies
def slab():
    xs = [-500, -380, -260, -140, -10, 120, 215, 335, 455, 565, 675]
    i = 0
    for x0, x1 in zip(xs, xs[1:]):
        mb = MB()
        if x0 == 120:
            mb.box(x0, -490, x1, -100, GF_WALL, SLAB_TOP, "Plaster", "Concrete")
            mb.box(x0, 235, x1, 495, GF_WALL, SLAB_TOP, "Plaster", "Concrete")
        else:
            mb.box(x0, -490, x1, 495, GF_WALL, SLAB_TOP, "Plaster", "Concrete")
        make(f"Slab_Panel_{i:02d}", mb, "gf_slab", i, "drop")
        i += 1


def glass_rail(mb, pts, z0, h=1.0, posts=True):
    """pts: list of plan (x,y) corners forming an open polyline."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(x0 - x1) < 1:
            mb.box(x0 - 1, min(y0, y1), x0 + 1, max(y0, y1), z0 + 0.06, z0 + h - 0.05, "Glass")
            mb.box(x0 - 2.5, min(y0, y1), x0 + 2.5, max(y0, y1), z0 + h - 0.05, z0 + h, "Metal")
        else:
            mb.box(min(x0, x1), y0 - 1, max(x0, x1), y0 + 1, z0 + 0.06, z0 + h - 0.05, "Glass")
            mb.box(min(x0, x1), y0 - 2.5, max(x0, x1), y0 + 2.5, z0 + h - 0.05, z0 + h, "Metal")
    if posts:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(L // 110))
            for k in range(n + 1):
                px, py = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                mb.box(px - 2, py - 2, px + 2, py + 2, z0, z0 + h, "Metal")


def balconies():
    # front balcony over porch
    mb = MB()
    mb.box(-160, 495, 335, 650, 2.98, SLAB_TOP, "Concrete", "Terracotta")
    mb.box(-160, 495, 335, 650, 2.90, 2.98, "Brick")
    make("Balcony_Front_Slab", mb, "balcony", 2, "drop")
    for i, (cx, cy) in enumerate([(-135, 622), (310, 622)]):
        mb = MB()
        mb.box(cx - 16, cy - 16, cx + 16, cy + 16, -0.02, 2.90, "Facade")
        mb.box(cx - 19, cy - 19, cx + 19, cy + 19, -0.02, 0.35, "Brick")
        make(f"Balcony_Front_Column_{i}", mb, "balcony", i, "rise")
    mb = MB()
    glass_rail(mb, [(-155, 495), (-155, 645), (330, 645), (330, 495)], SLAB_TOP)
    make("Balcony_Front_Rail", mb, "balcony", 3, "pop")
    # side balcony on the left gable
    mb = MB()
    mb.box(-665, -240, -500, 270, 2.98, SLAB_TOP, "Concrete", "Terracotta")
    mb.box(-665, -240, -500, 270, 2.90, 2.98, "Brick")
    make("Balcony_Side_Slab", mb, "balcony", 6, "drop")
    for i, (cx, cy) in enumerate([(-640, -215), (-640, 245)]):
        mb = MB()
        mb.box(cx - 16, cy - 16, cx + 16, cy + 16, -0.12, 2.90, "Facade")
        mb.box(cx - 19, cy - 19, cx + 19, cy + 19, -0.12, 0.35, "Brick")
        make(f"Balcony_Side_Column_{i}", mb, "balcony", 4 + i, "rise")
    mb = MB()
    glass_rail(mb, [(-515, -235), (-660, -235), (-660, 265), (-515, 265)], SLAB_TOP)
    make("Balcony_Side_Rail", mb, "balcony", 7, "pop")
    # juliet balcony on the right gable (office)
    mb = MB()
    glass_rail(mb, [(692, 95), (692, 205)], UF, 1.0)
    make("Balcony_Juliet_Rail", mb, "balcony", 8, "pop")
    # gallery balustrade around the stair opening (exit across x=120 stays open)
    mb = MB()
    glass_rail(mb, [(120, -5), (120, 235), (215, 235), (215, -100), (120, -100)], UF)
    make("UF_Stair_Rail", mb, "uf_openings", 2, "pop")


# ---------------------------------------------------------------- stairs
R = UF / 16


def stairs():
    order = 0
    for i in range(1, 11):
        y0, y1 = 235 - 24 * i, 235 - 24 * (i - 1)
        top = i * R
        mb = MB()
        mb.box(120, y0, 215, y1, max(0.0, top - 0.32), top, "Oak")
        make(f"GF_Stair_{i:02d}", mb, "gf_stairs", order, "drop"); order += 1
    px, py = 120, -5
    for k in range(5):
        ta, tb = math.radians(18 * k), math.radians(18 * (k + 1))

        def ray(t):
            c, s = math.cos(t), math.sin(t)
            d = min(95 / c if c > 1e-6 else 1e9, 95 / s if s > 1e-6 else 1e9)
            return (px + c * d, py - s * d)

        pts = [(px, py), ray(ta)]
        if ta < math.radians(45) < tb:
            pts.append((215, -100))
        pts.append(ray(tb))
        top = (11 + k) * R
        bot = [(x / 100, -y / 100, top - 0.32) for x, y in pts]
        tp = [(x / 100, -y / 100, top) for x, y in pts]
        mb = MB()
        mb.prism(bot, tp, "Oak")
        make(f"GF_Stair_{11 + k:02d}", mb, "gf_stairs", order, "drop"); order += 1
    # glass balustrade along the straight flight
    # the left side stays open for the first three steps so the flight is reachable from the hall
    for side, x, y0 in (("L", 120, 163), ("R", 215, 235)):
        z0 = R + (235 - y0) / 24 * R
        mb = MB()
        prof = [(y0, z0), (-5, 11 * R), (-5, 11 * R + 0.9), (y0, z0 + 0.9)]
        bot = [((x - 1) / 100, -y / 100, z) for y, z in prof]
        tp = [((x + 1) / 100, -y / 100, z) for y, z in prof]
        mb.prism(bot, tp, "Glass")
        hp = [(y0, z0 + 0.9), (-5, 11 * R + 0.9), (-5, 11 * R + 0.95), (y0, z0 + 0.95)]
        mb.prism([((x - 3) / 100, -y / 100, z) for y, z in hp], [((x + 3) / 100, -y / 100, z) for y, z in hp], "Oak")
        make(f"GF_Stair_Rail_{side}", mb, "gf_stairs", order, "pop"); order += 1


# ---------------------------------------------------------------- furniture
def F(name, stage, order, anim="drop"):
    class Ctx:
        def __init__(s):
            s.mb = MB()

        def __enter__(s):
            return s.mb

        def __exit__(s, *a):
            make(name, s.mb, stage, order, anim)
    return Ctx()


def chair(mb, cx, cy, back, z, mat="LightWood"):
    mb.box(cx - 22, cy - 22, cx + 22, cy + 22, z + 0.43, z + 0.47, mat)
    for sx in (-19, 16):
        for sy in (-19, 16):
            mb.box(cx + sx, cy + sy, cx + sx + 3, cy + sy + 3, z, z + 0.43, mat)
    bx = {"+y": (cx - 22, cy + 18, cx + 22, cy + 22), "-y": (cx - 22, cy - 22, cx + 22, cy - 18),
          "+x": (cx + 18, cy - 22, cx + 22, cy + 22), "-x": (cx - 22, cy - 22, cx - 18, cy + 22)}[back]
    mb.box(*bx, z + 0.47, z + 0.92, mat)


def table(mb, x0, y0, x1, y1, z, h, top_mat, leg_mat):
    mb.box(x0, y0, x1, y1, z + h - 0.04, z + h, top_mat)
    for lx in (x0 + 3, x1 - 9):
        for ly in (y0 + 3, y1 - 9):
            mb.box(lx, ly, lx + 6, ly + 6, z, z + h - 0.04, leg_mat)


def furniture_gf():
    z = 0.02
    st = "gf_furniture"
    o = 0
    with F("GF_Sofa", st, o) as mb:
        mb.box(-480, 395, -215, 478, z, z + 0.42, "Sofa")
        mb.box(-480, 150, -397, 395, z, z + 0.42, "Sofa")
        mb.box(-480, 458, -215, 478, z + 0.42, z + 0.85, "Sofa")
        mb.box(-480, 150, -460, 458, z + 0.42, z + 0.85, "Sofa")
        mb.box(-458, 398, -237, 456, z + 0.42, z + 0.52, "Cushion")
        mb.box(-458, 172, -399, 398, z + 0.42, z + 0.52, "Cushion")
        mb.box(-237, 395, -215, 458, z + 0.42, z + 0.64, "Sofa")
        mb.box(-480, 150, -397, 172, z + 0.42, z + 0.64, "Sofa")
        mb.box(-300, 440, -255, 456, z + 0.52, z + 0.82, "Fabric")
        mb.box(-458, 300, -444, 345, z + 0.52, z + 0.82, "Fabric")
    o += 1
    with F("GF_CoffeeTable", st, o) as mb:
        table(mb, -370, 250, -250, 320, z, 0.43, "Walnut", "Walnut")
        mb.box(-366, 254, -254, 316, z + 0.10, z + 0.12, "Walnut")
    o += 1
    with F("GF_Rug", st, o, "fade") as mb:
        mb.box(-360, 70, -240, 230, z, z + 0.012, "Fabric")
    o += 1
    with F("GF_TV", st, o) as mb:
        mb.box(-185, 250, -142, 470, z, z + 0.42, "White")
        for k, c in enumerate(["AccentRed", "AccentBlue", "AccentYellow", "LightWood"]):
            yy = 260 + k * 52
            mb.box(-188, yy, -184, yy + 40, z + 0.05, z + 0.35, c)
        mb.box(-150, 300, -146, 430, z + 0.95, z + 1.65, "Black")
    o += 1
    with F("GF_Fireplace", st, o, "rise") as mb:
        mb.box(-195, -60, -140, 70, z, z + 0.35, "Fireplace")
        mb.box(-188, -45, -140, 55, z + 0.35, z + 0.95, "Fireplace")
        mb.box(-189, -32, -188, 42, z + 0.45, z + 0.85, "Glass")
        mb.box(-182, -45, -140, 55, z + 0.95, GF_WALL, "AccentYellow")
        mb.box(-250, -60, -195, 70, z, z + 0.01, "Walnut")
    o += 1
    with F("GF_DiningTable", st, o) as mb:
        table(mb, -390, -330, -230, -240, z, 0.76, "White", "White")
    o += 1
    for i, (cx, cy, bk) in enumerate([(-355, -355, "-y"), (-265, -355, "-y"), (-355, -215, "+y"),
                                       (-265, -215, "+y"), (-412, -285, "-x"), (-208, -285, "+x")]):
        with F(f"GF_DiningChair_{i}", st, o + i * 0.1) as mb:
            chair(mb, cx, cy, bk, z)
    o += 1
    with F("GF_Pendants", st, o) as mb:
        for k, xx in enumerate((-350, -310, -270)):
            mb.box(xx - 8, -293, xx + 8, -277, 1.85, 2.05, "Glass")
            mb.box(xx - 1, -286, xx + 1, -284, 2.05, GF_WALL, "Steel")
    o += 1
    with F("GF_KitchenCounter", st, o, "rise") as mb:
        mb.box(-130, -485, 30, -425, z, z + 0.86, "White")
        mb.box(-130, -487, 32, -423, z + 0.86, z + 0.90, "Counter")
        mb.box(-130, -489, 94, -487, z + 0.90, z + 1.50, "AccentRed")
        mb.box(-130, -485, -75, -450, 1.50, 2.25, "White")
        mb.box(-60, -480, 0, -432, z + 0.90, z + 0.905, "Black")
        mb.box(-130, -489, 94, -487, 1.50, GF_WALL, "AccentRed")
    o += 1
    with F("GF_KitchenHood", st, o) as mb:
        mb.box(-65, -485, -5, -440, 1.45, 1.52, "Black")
        mb.box(-45, -485, -25, -465, 1.52, GF_WALL, "Black")
    o += 1
    with F("GF_KitchenTall", st, o, "rise") as mb:
        mb.box(32, -485, 94, -250, z, 2.25, "White")
        mb.box(30, -360, 32, -300, z + 0.9, z + 1.5, "Black")
        mb.box(30, -440, 32, -375, z + 1.0, z + 2.0, "Black")
    o += 1
    with F("GF_KitchenIsland", st, o, "rise") as mb:
        mb.box(-110, -270, 60, -205, z, z + 0.86, "White")
        mb.box(-112, -272, 62, -203, z + 0.86, z + 0.90, "Counter")
        mb.box(-112, -212, 62, -188, z + 1.05, z + 1.09, "Counter")
        for xx in (-100, 50):
            mb.box(xx - 1.5, -202, xx + 1.5, -198, z + 0.9, z + 1.05, "Metal")
        mb.box(-20, -250, 0, -235, z + 0.90, z + 1.10, "AccentRed")
    o += 1
    with F("GF_Wardrobe", st, o, "rise") as mb:
        mb.box(180, 258, 340, 318, z, 2.4, "White")
        for xx in (215, 260, 305):
            mb.box(xx, 318, xx + 3, 321, 1.0, 1.4, "LightWood")
    o += 1
    with F("GF_Bench", st, o) as mb:
        mb.box(-125, 300, -85, 400, z, z + 0.45, "LightWood")
    o += 1
    with F("GF_Teepee", st, o) as mb:
        mb.cyl_z(20, 70, 50, z, z + 1.55, "Linen", seg=4, r1=1, rot=math.pi / 4)
    o += 1
    with F("GF_KidsBed", st, o) as mb:
        mb.box(270, -330, 470, -190, z, z + 0.22, "Linen")
        mb.box(340, -330, 470, -190, z + 0.22, z + 0.25, "Cushion")
    o += 1
    with F("GF_WallBars", st, o, "rise") as mb:
        mb.box(104, -420, 112, -414, z, 2.4, "LightWood")
        mb.box(104, -336, 112, -330, z, 2.4, "LightWood")
        for k in range(12):
            zz = 0.15 + k * 0.19
            mb.box(105, -414, 111, -336, zz, zz + 0.03, "LightWood")
    o += 1
    with F("GF_KidsTable", st, o) as mb:
        table(mb, 120, -475, 185, -420, z, 0.5, "White", "White")
        mb.box(195, -460, 225, -430, z, z + 0.3, "White")
    o += 1
    with F("GF_Shower", st, o) as mb:
        mb.box(590, -353, 670, -273, z, z + 0.06, "White")
        mb.box(589, -353, 591, -273, z + 0.06, 2.0, "Glass")
        mb.box(590, -275, 670, -273, z + 0.06, 2.0, "Glass")
    o += 1
    with F("GF_Toilet", st, o) as mb:
        mb.box(662, -250, 670, -205, z, 1.1, "StoneTile")
        mb.box(615, -245, 662, -210, z + 0.2, z + 0.42, "White")
    o += 1
    with F("GF_Sink", st, o) as mb:
        mb.box(380, -164, 460, -120, 0.75, 0.80, "StoneTile")
        mb.cyl_z(420, -142, 18, 0.80, 0.95, "StoneTile", r1=21)
        mb.box(506, -300, 509, -250, 0.4, 1.5, "White")
    o += 1
    with F("GF_Boiler", st, o) as mb:
        mb.box(600, -485, 660, -452, 1.2, 1.95, "White")
        mb.box(615, -400, 660, -370, 0.8, 0.95, "White")
    o += 1
    with F("GF_Car", st, o) as mb:
        mb.box(427, 5, 603, 425, 0.25, 0.85, "CarPaint")
        mb.box(437, 115, 593, 330, 0.85, 1.40, "CarPaint")
        mb.box(435, 120, 595, 325, 0.92, 1.33, "Glass")
        for xx0, xx1 in ((421, 445), (585, 609)):
            for yy in (75, 355):
                mb.cyl_x(xx0, xx1, yy, 0.33, 33, "Rubber")
        for xx in (440, 550):
            mb.box(xx, 2, xx + 40, 6, 0.62, 0.74, "White")
            mb.box(xx, 424, xx + 40, 428, 0.66, 0.76, "AccentRed")
    o += 1
    with F("GF_GarageShelf", st, o, "rise") as mb:
        for yy in (20, 200, 380):
            for xx in (357, 397):
                mb.box(xx, yy, xx + 4, yy + 4, z, 2.1, "Steel")
        for zz in (0.4, 0.95, 1.5, 2.05):
            mb.box(357, 20, 401, 384, zz, zz + 0.03, "Steel")
        cols = ["LightWood", "Fabric", "AccentRed", "LightWood", "AccentBlue", "Black"]
        for k in range(8):
            zz = (0.43, 0.98, 1.53)[k % 3]
            yy = 30 + k * 44
            mb.box(362, yy, 395, yy + 36, zz, zz + 0.3, cols[k % len(cols)])


def furniture_uf():
    z = UF + 0.02
    st = "uf_furniture"
    o = 0
    with F("UF_Bed", st, o) as mb:
        mb.box(-277, 180, -72, 370, z, z + 0.35, "Black")
        mb.box(-272, 185, -77, 365, z + 0.35, z + 0.55, "Linen")
        mb.box(-82, 180, -72, 370, z + 0.35, z + 1.0, "Black")
        mb.box(-125, 195, -85, 272, z + 0.55, z + 0.67, "Linen")
        mb.box(-125, 280, -85, 357, z + 0.55, z + 0.67, "Linen")
        mb.box(-262, 183, -135, 367, z + 0.55, z + 0.60, "Cushion")
    o += 1
    with F("UF_Dresser", st, o) as mb:
        mb.box(-420, 55, -300, 100, z, z + 0.8, "White")
        mb.box(-422, 53, -298, 102, z + 0.8, z + 0.83, "LightWood")
    o += 1
    with F("UF_KidsBed", st, o) as mb:
        mb.box(-290, -100, -90, 35, z, z + 0.30, "LightWood")
        mb.box(-285, -95, -100, 30, z + 0.30, z + 0.48, "Linen")
        mb.box(-100, -100, -90, 35, z + 0.30, z + 0.85, "LightWood")
        mb.box(-280, -95, -180, 30, z + 0.48, z + 0.52, "AccentYellow")
    o += 1
    with F("UF_KidsDresser", st, o) as mb:
        mb.box(-485, -280, -435, -160, z, z + 0.8, "LightWood")
    o += 1
    with F("UF_CubeShelf", st, o) as mb:
        mb.box(-330, -480, -200, -445, z, z + 0.95, "White")
        for k, c in enumerate(["AccentRed", "AccentBlue", "AccentYellow"]):
            xx = -322 + k * 42
            mb.box(xx, -445, xx + 34, -443, z + 0.08, z + 0.40, c)
    o += 1
    with F("UF_PowerTower", st, o) as mb:
        mb.box(15, 380, 115, 440, z, z + 0.05, "Black")
        mb.box(20, 405, 25, 415, z, z + 2.1, "Black")
        mb.box(105, 405, 110, 415, z, z + 2.1, "Black")
        mb.box(15, 405, 115, 415, z + 2.05, z + 2.1, "AccentRed")
    o += 1
    with F("UF_Drums", st, o) as mb:
        mb.cyl_y(300, 330, 250, z + 0.28, 26, "Black", seg=16)
        for xx, yy in ((225, 300), (275, 300)):
            mb.cyl_z(xx, yy, 16, z + 0.55, z + 0.72, "Black")
        mb.cyl_z(200, 335, 24, z + 1.0, z + 1.01, "AccentYellow")
        mb.box(199, 334, 201, 336, z, z + 1.0, "Metal")
    o += 1
    with F("UF_WC", st, o) as mb:
        mb.box(0, -485, 55, -470, z, z + 1.0, "DarkTile")
        mb.box(5, -470, 45, -415, z + 0.2, z + 0.42, "White")
        mb.box(90, -300, 111, -260, z + 0.8, z + 0.9, "White")
    o += 1
    cols = ["AccentRed", "Fabric", "CarpetGreen", "Sofa", "Linen", "Black", "AccentBlue", "AccentYellow"]
    for side, (x0, x1) in enumerate(((122, 160), (250, 288))):
        with F(f"UF_ClothesRack_{side}", st, o) as mb:
            mb.box(x0 + 17, -470, x0 + 21, -466, z, z + 1.6, "Metal")
            mb.box(x0 + 17, -214, x0 + 21, -210, z, z + 1.6, "Metal")
            mb.box(x0 + 17, -470, x0 + 21, -210, z + 1.56, z + 1.6, "Metal")
            yy = -462
            k = 0
            while yy < -220:
                mb.box(x0 + 2, yy, x1 - 2, yy + 4, z + 0.7 + (k % 3) * 0.08, z + 1.5, cols[k % len(cols)])
                yy += 9
                k += 1
        o += 1
    with F("UF_ClosetShelf", st, o) as mb:
        mb.box(170, -483, 240, -445, z, z + 1.0, "White")
    o += 1
    with F("UF_Bathtub", st, o) as mb:
        mb.box(540, -482, 668, -360, z, z + 0.55, "White")
        mb.box(552, -470, 656, -372, z + 0.55, z + 0.56, "Water")
    o += 1
    with F("UF_Shower", st, o) as mb:
        mb.box(300, -482, 390, -392, z, z + 0.08, "White")
        mb.box(388, -482, 390, -392, z + 0.08, z + 2.0, "Glass")
        mb.box(300, -394, 390, -392, z + 0.08, z + 2.0, "Glass")
    o += 1
    with F("UF_Laundry", st, o) as mb:
        for y0 in (-385, -323):
            mb.box(300, y0, 360, y0 + 60, z, z + 0.85, "White")
            mb.cyl_x(360, 362, -(-(y0 + 30)), z + 0.45, 17, "Black")
    o += 1
    with F("UF_Vanity", st, o) as mb:
        mb.box(615, -170, 662, -75, z + 0.55, z + 0.85, "White")
        mb.box(661, -165, 663, -80, z + 1.2, z + 1.9, "Glass")
    o += 1
    with F("UF_Desk", st, o) as mb:
        mb.box(600, 210, 668, 478, z + 0.72, z + 0.75, "White")
        mb.box(440, 405, 600, 478, z + 0.72, z + 0.75, "White")
        for xx, yy in ((640, 215), (640, 470), (445, 470), (600, 470)):
            mb.box(xx, yy - 6, xx + 4, yy - 2, z, z + 0.72, "Steel")
        for y0 in (250, 330):
            mb.box(645, y0, 649, y0 + 70, z + 0.95, z + 1.35, "Black")
            mb.box(650, y0 + 30, 656, y0 + 40, z + 0.75, z + 0.95, "Steel")
    o += 1
    with F("UF_GamingChair", st, o) as mb:
        mb.cyl_z(570, 330, 30, z, z + 0.06, "Black", seg=5)
        mb.cyl_z(570, 330, 4, z + 0.06, z + 0.45, "Steel")
        mb.box(540, 300, 600, 360, z + 0.45, z + 0.56, "Black")
        mb.box(538, 302, 548, 358, z + 0.56, z + 1.30, "Black")
        mb.box(537, 322, 538, 338, z + 0.95, z + 1.2, "AccentRed")
    o += 1
    with F("UF_Wardrobe", st, o, "rise") as mb:
        mb.box(332, 20, 335, 280, z, z + 2.2, "White")
        mb.box(332, 20, 392, 23, z, z + 2.2, "White")
        mb.box(332, 277, 392, 280, z, z + 2.2, "White")
        mb.box(332, 20, 392, 280, z + 2.17, z + 2.2, "White")
        mb.box(332, 20, 392, 280, z, z + 0.5, "White")
        yy, k = 30, 0
        while yy < 268:
            mb.box(345, yy, 380, yy + 4, z + 1.05 + (k % 3) * 0.06, z + 1.9, cols[(k * 3) % len(cols)])
            yy += 9
            k += 1


# ---------------------------------------------------------------- roof
def clip(poly, axis, val, keep_greater):
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        pin = (p[axis] >= val) if keep_greater else (p[axis] <= val)
        qin = (q[axis] >= val) if keep_greater else (q[axis] <= val)
        if pin:
            out.append(p)
        if pin != qin:
            t = (val - p[axis]) / (q[axis] - p[axis])
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


S40, C40 = math.sin(math.radians(40)), math.cos(math.radians(40))
S45 = math.sin(math.radians(45))
SLOPES = {
    # name: (z(X,Y), normal, band axis (0=X,1=Y), eave value, ridge value, polygons)
    "F": (lambda X, Y: main_z(Y), (0, -S40, C40), 1, YE_F, YC,
          [[(XE_L, YE_F), A_L, (CG_XC, CG_C_Y), (CG_XC, YC), (XE_L, YC)],
           [(CG_XC, CG_C_Y), A_R, (XE_R, YE_F), (XE_R, YC), (CG_XC, YC)]]),
    "B": (lambda X, Y: main_z(Y), (0, S40, C40), 1, YE_B, YC,
          [[(XE_L, YC), (XE_R, YC), (XE_R, YE_B), (XE_L, YE_B)]]),
    "CL": (lambda X, Y: cross_z(X), (-S45, 0, S45), 0, A_L[0], CG_XC,
           [[A_L, (CG_XC, YE_F), (CG_XC, CG_C_Y)]]),
    "CR": (lambda X, Y: cross_z(X), (S45, 0, S45), 0, A_R[0], CG_XC,
           [[(CG_XC, YE_F), A_R, (CG_XC, CG_C_Y)]]),
}


def roof_pt(slope, X, Y, off):
    zf, n = SLOPES[slope][0], SLOPES[slope][1]
    z = zf(X, Y)
    return (X + n[0] * off, Y + n[1] * off, z + n[2] * off)


def roof_rows():
    for sname, (zf, n, ax, e, r, polys) in SLOPES.items():
        span = abs(r - e)
        rows = max(1, round(span / (0.30 if ax == 1 else 0.32)))
        step = span / rows
        sgn = 1 if r > e else -1
        for i in range(rows):
            lo = e + sgn * step * i
            hi = e + sgn * step * (i + 1)
            mn, mx = min(lo, hi), max(lo, hi)
            mb = MB()
            for poly in polys:
                p = clip(clip(poly, ax, mn, True), ax, mx, False)
                if len(p) < 3:
                    continue
                area = 0
                for k in range(len(p)):
                    area += p[k][0] * p[(k + 1) % len(p)][1] - p[(k + 1) % len(p)][0] * p[k][1]
                if abs(area) < 1e-4:
                    continue
                bot, top = [], []
                for (X, Y) in p:
                    w = abs((X, Y)[ax] - hi) / step   # 1 at the lower (eave-side) edge
                    bot.append(roof_pt(sname, X, Y, RAF))
                    top.append(roof_pt(sname, X, Y, RAF + TILE + STEP * w))
                mb.prism(bot, top, "WoodTrim", "RoofTile", "RoofTile")
            make(f"Roof_Tiles_{sname}_{i:02d}", mb, "roof_tiles", i + {"F": 0, "B": 0.5, "CL": 0.2, "CR": 0.7}[sname], "tile",
                 slope=sname)


def rafter(mb, slope, pts):
    bot = [roof_pt(slope, X, Y, 0) for X, Y in pts]
    top = [roof_pt(slope, X, Y, RAF) for X, Y in pts]
    mb.prism(bot, top, "WoodTrim")


def roof_frame():
    o = 0
    X = XE_L + 0.06
    xs = []
    while X < XE_R - 0.05:
        xs.append(X)
        X += 0.9
    xs[-1] = XE_R - 0.06
    for X in xs:
        mb = MB()
        y0 = YE_F
        v = valley_y(X)
        if v is not None:
            y0 = v + 0.05
        rafter(mb, "F", [(X - 0.04, y0), (X + 0.04, y0), (X + 0.04, YC), (X - 0.04, YC)])
        rafter(mb, "B", [(X - 0.04, YC), (X + 0.04, YC), (X + 0.04, YE_B), (X - 0.04, YE_B)])
        make(f"Roof_Rafter_{o:02d}", mb, "roof_frame", o, "drop"); o += 1
    Y = YE_F + 0.1
    while Y < CG_C_Y - 0.3:
        mb = MB()
        f = (Y - YE_F) / (CG_C_Y - YE_F)
        xl = A_L[0] + f * (CG_XC - A_L[0])
        xr = A_R[0] - f * (A_R[0] - CG_XC)
        rafter(mb, "CL", [(xl, Y - 0.04), (CG_XC, Y - 0.04), (CG_XC, Y + 0.04), (xl, Y + 0.04)])
        rafter(mb, "CR", [(CG_XC, Y - 0.04), (xr, Y - 0.04), (xr, Y + 0.04), (CG_XC, Y + 0.04)])
        make(f"Roof_Rafter_{o:02d}", mb, "roof_frame", o, "drop"); o += 1
        Y += 0.9
    mb = MB()
    zr = main_z(YC)
    mb.prism([(XE_L, YC - 0.08, zr - 0.22), (XE_R, YC - 0.08, zr - 0.22), (XE_R, YC + 0.08, zr - 0.22), (XE_L, YC + 0.08, zr - 0.22)],
             [(XE_L, YC - 0.08, zr + 0.1), (XE_R, YC - 0.08, zr + 0.1), (XE_R, YC + 0.08, zr + 0.1), (XE_L, YC + 0.08, zr + 0.1)], "WoodTrim")
    make("Roof_RidgeBeam", mb, "roof_frame", -1, "drop")


def ceilings():
    """Plasterboard under the rafters: sloped parts up to UF_CEIL, flat above."""
    dz = 0.02
    band = D2 - (UF_CEIL - H_E) / T          # |Y-YC| where the main roof reaches UF_CEIL
    cband = CG_HALF - (UF_CEIL - H_E) / CG_T  # |X-XC| where the cross roof reaches UF_CEIL
    mb = MB()

    def sloped(slope, poly):
        if len(poly) < 3:
            return
        bot = [roof_pt(slope, X, Y, -dz) for X, Y in poly]
        top = [roof_pt(slope, X, Y, 0) for X, Y in poly]
        mb.prism(bot, top, "Plaster")

    def rect_clip(poly, x0, x1, y0, y1):
        for ax, v, g in ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)):
            poly = clip(poly, ax, v, g)
            if len(poly) < 3:
                return []
        return poly

    for poly in SLOPES["F"][5]:
        sloped("F", rect_clip(poly, X_OUT_L, X_OUT_R, Y_OUT_F, YC - band))
    for poly in SLOPES["B"][5]:
        sloped("B", rect_clip(poly, X_OUT_L, X_OUT_R, YC + band, Y_OUT_B))
    for poly in SLOPES["CL"][5]:
        sloped("CL", rect_clip(poly, CG_X0, CG_XC - cband, Y_OUT_F, YC))
    for poly in SLOPES["CR"][5]:
        sloped("CR", rect_clip(poly, CG_XC + cband, CG_X1, Y_OUT_F, YC))
    flat = [(X_OUT_L, YC - band, X_OUT_R, YC + band), (CG_XC - cband, Y_OUT_F, CG_XC + cband, YC - band)]
    for X0, Y0, X1, Y1 in flat:
        mb.box(X0 * 100, -Y0 * 100, X1 * 100, -Y1 * 100, UF_CEIL, UF_CEIL + dz, "Plaster")
    make("Roof_Ceiling", mb, "roof_details", 0.5, "fade")


def roof_details():
    o = 1
    th = RAF + TILE + 0.06
    # barge boards on main gables
    mb = MB()
    for X in (XE_L, XE_R):
        for (ya, yb) in ((YE_F, YC), (YC, YE_B)):
            prof = [(ya, main_z(ya) - 0.10), (yb, main_z(yb) - 0.10), (yb, main_z(yb) + th / C40), (ya, main_z(ya) + th / C40)]
            mb.prism([(X - 0.03, y, z) for y, z in prof], [(X + 0.03, y, z) for y, z in prof], "WoodTrim")
    # cross gable barge boards
    for (xa, xb) in ((A_L[0], CG_XC), (CG_XC, A_R[0])):
        prof = [(xa, cross_z(xa) - 0.10), (xb, cross_z(xb) - 0.10), (xb, cross_z(xb) + th / S45), (xa, cross_z(xa) + th / S45)]
        mb.prism([(x, YE_F - 0.03, z) for x, z in prof], [(x, YE_F + 0.03, z) for x, z in prof], "WoodTrim")
    make("Roof_BargeBoards", mb, "roof_details", o, "pop"); o += 1
    # ridge caps
    mb = MB()
    zr = main_z(YC) + th / C40
    mb.prism([(XE_L, YC - 0.17, zr - 0.12), (XE_R, YC - 0.17, zr - 0.12), (XE_R, YC + 0.17, zr - 0.12), (XE_L, YC + 0.17, zr - 0.12)],
             [(XE_L, YC - 0.12, zr + 0.06), (XE_R, YC - 0.12, zr + 0.06), (XE_R, YC + 0.12, zr + 0.06), (XE_L, YC + 0.12, zr + 0.06)], "RoofTile")
    zc = CG_RIDGE + th / S45
    mb.prism([(CG_XC - 0.17, YE_F, zc - 0.12), (CG_XC + 0.17, YE_F, zc - 0.12), (CG_XC + 0.17, CG_C_Y, zc - 0.12), (CG_XC - 0.17, CG_C_Y, zc - 0.12)],
             [(CG_XC - 0.12, YE_F, zc + 0.06), (CG_XC + 0.12, YE_F, zc + 0.06), (CG_XC + 0.12, CG_C_Y, zc + 0.06), (CG_XC - 0.12, CG_C_Y, zc + 0.06)], "RoofTile")
    make("Roof_RidgeCaps", mb, "roof_details", o, "pop"); o += 1
    # gutters + downpipes
    mb = MB()
    for (ye, sg) in ((YE_F, -1), (YE_B, 1)):
        ze = main_z(ye)
        spans = [(XE_L, A_L[0]), (A_R[0], XE_R)] if sg < 0 else [(XE_L, XE_R)]
        for xa, xb in spans:
            mb.prism([(xa, ye, ze - 0.12), (xb, ye, ze - 0.12), (xb, ye + sg * 0.14, ze - 0.12), (xa, ye + sg * 0.14, ze - 0.12)],
                     [(xa, ye, ze + 0.02), (xb, ye, ze + 0.02), (xb, ye + sg * 0.14, ze + 0.02), (xa, ye + sg * 0.14, ze + 0.02)], "Gutter")
        for xp in (X_OUT_L + 0.25, X_OUT_R - 0.25):
            yp = (Y_OUT_F - 0.06) if sg < 0 else (Y_OUT_B + 0.06)
            mb.box(xp * 100 - 4, -yp * 100 - 4, xp * 100 + 4, -yp * 100 + 4, -0.1, ze - 0.1, "Gutter")
            mb.prism([(xp - 0.04, yp - 0.04, ze - 0.14), (xp + 0.04, yp - 0.04, ze - 0.14), (xp + 0.04, ye + sg * 0.07, ze - 0.14), (xp - 0.04, ye + sg * 0.07, ze - 0.14)],
                     [(xp - 0.04, yp - 0.04, ze - 0.06), (xp + 0.04, yp - 0.04, ze - 0.06), (xp + 0.04, ye + sg * 0.07, ze - 0.06), (xp - 0.04, ye + sg * 0.07, ze - 0.06)], "Gutter")
    make("Roof_Gutters", mb, "roof_details", o, "pop"); o += 1
    # skylights
    sk = [("B", -2.8), ("B", 0.27), ("B", 2.05), ("B", 4.8), ("F", -2.8)]
    for i, (sl, X) in enumerate(sk):
        d = 3.25
        Yc = YC + d if sl == "B" else YC - d
        hy = 0.59 * C40
        rect = [(X - 0.39, Yc - hy), (X + 0.39, Yc - hy), (X + 0.39, Yc + hy), (X - 0.39, Yc + hy)]
        inner = [(X - 0.31, Yc - hy + 0.06), (X + 0.31, Yc - hy + 0.06), (X + 0.31, Yc + hy - 0.06), (X - 0.31, Yc + hy - 0.06)]
        mb = MB()
        b0 = RAF + TILE
        mb.prism([roof_pt(sl, x, y, b0 - 0.05) for x, y in rect], [roof_pt(sl, x, y, b0 + 0.13) for x, y in rect], "Gutter")
        mb.prism([roof_pt(sl, x, y, b0 + 0.13) for x, y in inner], [roof_pt(sl, x, y, b0 + 0.145) for x, y in inner], "Glass")
        ob = make(f"Roof_Skylight_{i}", mb, "roof_details", o, "pop"); o += 1
        ob["glow"] = 1
    # TV antenna on the ridge
    mb = MB()
    zr = main_z(YC) + th / C40
    mb.cyl_z(560, 0, 2.5, zr, zr + 1.8, "Steel", seg=8)
    for k, w in enumerate((60, 45, 30)):
        zz = zr + 1.2 + k * 0.2
        mb.box(560 - w, -1, 560 + w, 1, zz, zz + 0.02, "Steel")
    make("Roof_Antenna", mb, "roof_details", o, "pop")


# ---------------------------------------------------------------- garden
def thuja(mb, x, y, h=3.2, r=45):
    mb.cyl_z(x, y, r * 0.6, -0.15, 0.6, "Hedge", seg=7, r1=r)
    mb.cyl_z(x, y, r, 0.6, h, "Hedge", seg=7, r1=4)


def garden():
    st = "garden"
    o = 0
    mb = MB()
    mb.box(-720, -800, -80, -490, -0.18, -0.10, "Terracotta")
    mb.box(-720, -490, -515, 300, -0.18, -0.10, "Terracotta")
    make("Garden_Terrace", mb, st, o, "fade"); o += 1
    mb = MB()
    mb.box(-160, 660, 720, 950, -0.20, -0.12, "Pavers")
    mb.box(365, 495, 720, 660, -0.20, -0.12, "Pavers")
    mb.box(300, 950, 720, 1600, -0.20, -0.12, "Pavers")
    mb.box(-560, 520, -110, 620, -0.20, -0.12, "Pavers")
    make("Garden_Driveway", mb, st, o, "fade"); o += 1
    # pool
    mb = MB()
    mb.box(150, -985, 550, -780, -0.15, 0.95, "PoolFrame")
    mb.box(155, -980, 545, -785, 0.95, 0.96, "Water")
    for xx in range(150, 560, 100):
        for yy in (-990, -775):
            mb.box(xx - 3, yy - 3, xx + 3, yy + 3, -0.15, 1.0, "PoolFrame")
    make("Garden_Pool", mb, st, o, "rise"); o += 1
    # terrace furniture
    with F("Garden_TableSet", st, o) as mb:
        table(mb, -470, -720, -330, -630, -0.10, 0.75, "Black", "Steel")
        for cx, cy, bk in ((-440, -745, "-y"), (-360, -745, "-y"), (-440, -605, "+y"), (-360, -605, "+y")):
            chair(mb, cx, cy, bk, -0.10, "Black")
    o += 1
    with F("Garden_PorchSofas", st, o) as mb:
        for x0 in (-100, 185):
            mb.box(x0, 455, x0 + 105, 520, -0.02, 0.40, "Steel")
            mb.box(x0 + 4, 459, x0 + 101, 516, 0.40, 0.48, "Fabric")
            mb.box(x0, 455, x0 + 105, 470, 0.40, 0.75, "Fabric")
    o += 1
    with F("Garden_Grill", st, o) as mb:
        mb.box(-600, 60, -540, 120, -0.10, 0.85, "Black")
        mb.cyl_z(-570, 90, 30, 0.85, 1.05, "Black", r1=22)
    o += 1
    # firewood stacks
    for i, (x0, x1, y, rows) in enumerate(((-330, -160, 520, 5), (-60, 80, -515, 6))):
        mb = MB()
        for rr in range(rows):
            zz = -0.10 + 0.07 + rr * 0.12
            xx = x0 + (rr % 2) * 6
            while xx < x1 - 6:
                mb.cyl_y(y - 20, y + 20, xx, zz, 6, "Firewood", seg=7)
                xx += 12.5
        make(f"Garden_Firewood_{i}", mb, st, o, "drop"); o += 1
    # trampoline
    mb = MB()
    mb.cyl_z(1050, -1250, 170, 0.75, 0.82, "Black", seg=24)
    for k in range(6):
        a = k * math.pi / 3
        mb.box(1050 + 160 * math.cos(a) - 3, -1250 + 160 * math.sin(a) - 3,
               1050 + 160 * math.cos(a) + 3, -1250 + 160 * math.sin(a) + 3, -0.15, 0.75, "Steel")
    make("Garden_Trampoline", mb, st, o, "pop"); o += 1
    # hedges
    lines = [((-1250, -1650), (-1250, 1500)), ((1450, -1650), (1450, 1500)), ((-1170, -1650), (1370, -1650))]
    hid = 0
    for (a, b) in lines:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L // 80)
        pts = [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]
        for c in range(0, len(pts), 8):
            mb = MB()
            for (x, y) in pts[c:c + 8]:
                thuja(mb, x, y, 3.0 + ((int(x * 7 + y * 3) % 5) * 0.12))
            make(f"Garden_Hedge_{hid:02d}", mb, st, o + hid * 0.05, "grow"); hid += 1
    o += 1
    # front fence with sliding gate gap
    for i, (x0, x1) in enumerate(((-1250, -650), (-650, -50), (-50, 300), (740, 1100), (1100, 1450))):
        mb = MB()
        mb.box(x0, 1580, x1, 1600, -0.15, 0.25, "Brick")
        for xx in range(int(x0), int(x1), 200):
            mb.box(xx, 1575, xx + 25, 1605, -0.15, 1.5, "Brick")
        xx = x0 + 28
        while xx < x1 - 8:
            mb.box(xx, 1585, xx + 9, 1595, 0.25, 1.35, "Fence")
            xx += 13
        make(f"Garden_Fence_{i}", mb, st, o + i * 0.1, "rise")
    o += 1
    mb = MB()
    xx = 305
    while xx < 735:
        mb.box(xx, 1585, xx + 9, 1595, 0.0, 1.35, "Fence")
        xx += 13
    mb.box(300, 1585, 740, 1595, 0.0, 0.08, "Steel")
    make("Garden_Gate", mb, st, o, "rise"); o += 1
    # trees
    trees = [((1220, 1250), "Spruce", 1.0), ((-1050, 1300), "Hedge", 0.85), ((1250, -400), "Spruce", 0.9)]
    for i, ((x, y), mat, s) in enumerate(trees):
        mb = MB()
        mb.cyl_z(x, y, 15 * s, -0.15, 1.0, "Bark", seg=8)
        for (r0, r1, z0, z1) in ((230, 120, 0.5, 2.8), (180, 70, 2.4, 4.8), (125, 6, 4.2, 8.0)):
            mb.cyl_z(x, y, r0 * s, z0 * s, z1 * s, mat, seg=9, r1=r1 * s)
        make(f"Garden_Tree_{i}", mb, st, o + i * 0.1, "grow")
    mb = MB()
    mb.cyl_z(-1000, -1250, 14, -0.15, 2.0, "Bark", seg=8)
    mb.cyl_z(-1000, -1250, 90, 1.8, 3.2, "Foliage", seg=9, r1=210)
    mb.cyl_z(-1000, -1250, 210, 3.2, 4.8, "Foliage", seg=9, r1=60)
    make("Garden_Tree_3", mb, st, o + 0.4, "grow")


# ---------------------------------------------------------------- run
site()
foundation()
floors(ROOMS_GF, 0.0, "gf_floor", "GF")
gf_walls()
chimney()
stairs()
furniture_gf()
slab()
balconies()
floors(ROOMS_UF, SLAB_TOP, "uf_floor", "UF")
uf_walls()
furniture_uf()
roof_frame()
roof_rows()
roof_details()
ceilings()
garden()

result = {"objects": len(scene.objects), "stages": {k: len(c.objects) for k, c in COLL.items()}}
